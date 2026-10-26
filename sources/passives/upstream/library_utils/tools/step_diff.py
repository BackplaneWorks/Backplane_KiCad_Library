#! /usr/bin/env python

# Note: cadquery is not imported here, because importing it is slow
# and this could be done just before the lines which make use of it.

import argparse
import logging
import re
import signal
import sys
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
import file_resolver

logger = logging.getLogger(__name__)


class _LoadStepFileError(Exception):
    def __init__(self, path: Path):
        self.path = path
        self.message = f"Can't load STEP file: {path}"
        super().__init__(self.message)


@dataclass
class DiffColors:
    unchanged: "cq.Color"
    added: "cq.Color"
    removed: "cq.Color"


@dataclass
class StepDiffStats:
    """
    All the statistics about the volume difference between two STEP files.
    """

    old_volume: float
    new_volume: float
    added_volume: float
    removed_volume: float

    @property
    def changed_volume(self) -> float:
        return self.added_volume + self.removed_volume

    @property
    def added_volume_proportion(self) -> float:
        if self.old_volume == 0:
            if self.new_volume == 0:
                return 0.0
            return float("inf")

        return self.added_volume / self.old_volume

    @property
    def removed_volume_proportion(self) -> float:
        if self.old_volume == 0:
            return 0.0

        return self.removed_volume / self.old_volume

    @property
    def changed_volume_proportion(self) -> float:
        if self.old_volume == 0:
            if self.new_volume == 0:
                return 0.0
            return float("inf")

        return self.changed_volume / self.old_volume


@dataclass
class StepDiffResult:
    """All the information about the difference between two STEP files."""

    model_name: str
    old_model: "cq.Workplane"
    new_model: "cq.Workplane"
    model_added: "cq.Workplane"
    model_removed: "cq.Workplane"
    stats: StepDiffStats


@dataclass
class DiffConfig:
    """All the configuration options for the diff process."""

    epsilon: float
    output_path: Path | None
    output_as_file: bool
    colors: DiffColors
    show_stats: bool


@dataclass
class DiffProcessResult:
    step_diff_stats: StepDiffStats | None = None
    """The actual result if any"""
    error: str | None = None
    """The error message if an error occurred"""
    files_checked: bool = False
    """Whether the files were actually checked"""


def load_step_file(path: Path) -> "cq.Workplane":
    import cadquery as cq

    try:
        model = cq.importers.importStep(str(path))
        return model
    except ValueError:
        raise _LoadStepFileError(path)


def shape_volume(model: "cq.Workplane | None") -> float:
    """Total volume of a model, summed over its solids.

    cadquery (at least 2.8.0) ``Shape.Volume()`` raises ``StopIteration`` on
    some STEP files whose compound structure contains an empty nested compound.
    Summing the individual solids avoids the crash and is equivalent.

    Remove this function if this is fixed in a future cadquery version.
    See: https://github.com/CadQuery/cadquery/issues/2078
    """
    if model is None:
        return 0.0

    shape = model.val()

    # Shape could be a Vector is the model is empty
    if not isinstance(shape, cq.occ_impl.shapes.Shape):
        return 0.0

    return sum(s.Volume() for s in shape.Solids())


def get_step_diff(old_path: Path | None, new_path: Path | None) -> StepDiffResult:
    """Compute the difference between two STEP files.

    Either *old_path* or *new_path* may be ``None``, meaning that side
    is absent (the file was created or deleted).
    """

    old_model = load_step_file(old_path) if old_path is not None else None
    new_model = load_step_file(new_path) if new_path is not None else None

    old_volume = shape_volume(old_model)
    new_volume = shape_volume(new_model)

    if (
        old_model is not None
        and new_model is not None
        and old_volume > 0
        and new_volume > 0
    ):
        model_added = new_model.cut(old_model)
        model_removed = old_model.cut(new_model)
    else:
        model_added = new_model
        model_removed = old_model

    added_volume = shape_volume(model_added)
    removed_volume = shape_volume(model_removed)

    model_name = old_path.stem if old_path is not None else new_path.stem

    return StepDiffResult(
        model_name=model_name,
        old_model=old_model,
        new_model=new_model,
        model_added=model_added,
        model_removed=model_removed,
        stats=StepDiffStats(
            old_volume=old_volume,
            new_volume=new_volume,
            added_volume=added_volume,
            removed_volume=removed_volume,
        ),
    )


def save_step_diff(
    step_diff: StepDiffResult, output_file_path: Path, colors: DiffColors
) -> None:
    import cadquery as cq

    if output_file_path.is_dir():
        print(f"Can't overwrite directory: {output_file_path}")
        return

    try:
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Make directory permission denied: {output_file_path.parent}")
        return
    except (FileExistsError, NotADirectoryError):
        print(f"Can't make directory: {output_file_path.parent}")
        return

    try:
        output_file_path.touch()
    except PermissionError:
        print(f"Write permission denied: {output_file_path}")
        return

    if shape_volume(step_diff.old_model) == 0:
        unchanged = step_diff.old_model
    else:
        unchanged = step_diff.old_model.intersect(step_diff.new_model)

    assembly = cq.Assembly(name=step_diff.model_name)
    assembly = assembly.add(
        unchanged,
        name="unchanged",
        color=colors.unchanged,
    )
    assembly = assembly.add(
        step_diff.model_added,
        name="added",
        color=colors.added,
    )
    assembly = assembly.add(
        step_diff.model_removed,
        name="removed",
        color=colors.removed,
    )
    assembly.export(str(output_file_path), "STEP")


def process_file_pair(
    pair: file_resolver.ResolvedFilePair, config: DiffConfig
) -> DiffProcessResult:
    """
    Process a pair of files and return the result.

    Either *file1* or *file2* may be ``None``, meaning the file was
    absent on that side of the diff (created or deleted).

    This function is designed to be run in parallel for multiple file
    pairs.
    """

    old_file = pair.file1
    new_file = pair.file2

    result = DiffProcessResult()
    result.files_checked = True

    try:
        step_diff = get_step_diff(old_file, new_file)
    except _LoadStepFileError as e:
        result.error = f"WARNING: {e.message}"
        return result
    except Exception:
        logger.exception(
            "Failed to diff %s (old=%s, new=%s)",
            pair.name,
            old_file,
            new_file,
        )
        raise

    result.step_diff_stats = step_diff.stats

    if old_file is None:
        result.error = f"CREATED ({step_diff.stats.new_volume:.2f} mm^3)"
    elif new_file is None:
        result.error = f"DELETED ({step_diff.stats.old_volume:.2f} mm^3)"
    elif step_diff.stats.changed_volume_proportion > config.epsilon:
        result.error = (
            f"CHANGED ({step_diff.stats.changed_volume_proportion * 100:.2f}%)"
        )

    # Diff output (modified files only)
    if config.output_path and old_file is not None and new_file is not None:
        diff_file = (
            config.output_path
            if config.output_as_file
            else config.output_path / pair.name
        )
        try:
            save_step_diff(step_diff, diff_file, config.colors)
        except Exception:
            logger.exception(
                "Failed to save diff for %s (old=%s, new=%s)",
                pair.name,
                old_file,
                new_file,
            )
            raise

    return result


def color(arg) -> tuple[float, float, float, float]:
    arg_re = re.compile(r"^([^,]*),([^,]*),([^,]*)(,[^,]*)?$")
    arg_match = arg_re.match(arg)
    assert arg_match
    arg = arg.split(",")
    if len(arg) == 3:
        arg.append("1.0")
    arg = tuple(map(float, arg))

    assert len(arg) == 4
    assert all(0.0 <= c <= 1.0 for c in arg)

    import cadquery as cq

    return cq.Color(*arg)


def format_diff_stats(stats: StepDiffStats) -> None:
    s = f"""\
  Old volume:     {stats.old_volume:.2f}
  New volume:     {stats.new_volume:.2f}
  Added volume:   {stats.added_volume:.2f} ({stats.added_volume_proportion * 100:.2f}%)
  Removed volume: {stats.removed_volume:.2f} ({stats.removed_volume_proportion * 100:.2f}%)
  Changed volume: {stats.changed_volume:.2f} ({stats.changed_volume_proportion * 100:.2f}%)"""

    return s


def _worker_init(log_level):
    """Configure worker processes.

    Workers are forked from a forkserver, so they do not inherit the main
    process's logging configuration. Ignore SIGINT there as well; the main
    process handles the interrupt and terminates the workers.
    """
    logging.basicConfig(level=log_level)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=("""
Check STEP files for changes.

You can provide one or two paths to compare. The paths can be:

* File path of a single STEP file:
    * File-to-file mode:             [file1] [file2]
    * Single file (show stats):      [file]

* Directory path containing STEP files:
    * Directory-to-directory mode:   [dir1] [dir2]
    * Single directory (show stats): [dir]

If you set --repo, then the paths are interpreted as Git commits
(e.g. commit hash, branch name, or tag name) in that repo:

    * Commit-to-commit               [commit1] [commit2]
    * Commit-to-working-copy:        [commit1]
    * HEAD-to-working-copy:          []
"""),
    )
    parser.add_argument(
        "path1",
        type=str,
        nargs="?",
        help="STEP file, directory, or local Git commit (depending on --repo).",
    )
    parser.add_argument(
        "path2", type=str, nargs="?", help="Second STEP file, directory, or commit."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be specified multiple times).",
    )
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        help="Path to a local Git repository, implies that the paths are Git commits or branches.",
    )
    parser.add_argument(
        "-g",
        "--glob",
        action="append",
        help="Filter files with a GLOB expression.",
    )
    parser.add_argument(
        "-e",
        "--epsilon",
        type=float,
        default="0.001",
        help="Volume change epsilon (default 0.1%%).",
    )
    parser.add_argument(
        "-o", "--diff-output", type=Path, help="Diff output directory or file."
    )
    parser.add_argument(
        "-s",
        "--stats",
        action="store_true",
        help="Print statistics about the differences found.",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="Number of parallel jobs to run (default: 0 - use as many as possible).",
    )

    # Note: The colors here are have different values for each main
    # color channel on purpose. If one color is "0.0, 0.0, 0.5", and
    # another is "0.0, 0.5, 0.0", then KiCad draws those two color as
    # if they are the same!
    parser.add_argument(
        "--diff-unchanged-color",
        type=color,
        default=color("0.0, 0.0, 0.50001, 1.0"),
        help="Diff unchanged color (default '0.0, 0.0, 0.5, 1.0').",
    )
    parser.add_argument(
        "--diff-added-color",
        type=color,
        default=color("0.0, 0.50002, 0.0, 1.0"),
        help="Diff added color (default '0.0, 0.5, 0.0, 1.0').",
    )
    parser.add_argument(
        "--diff-removed-color",
        type=color,
        default=color("0.50003, 0.0, 0.0, 1.0"),
        help="Diff removed color (default '0.5, 0.0, 0.0, 1.0').",
    )

    args = parser.parse_args()

    if args.verbose >= 2:
        log_level = logging.DEBUG
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level)

    def filter_files(path: Path) -> bool:
        path = Path(path)

        if path.suffix.lower() != ".step":
            return False

        if args.glob:
            return any(path.full_match(g) for g in args.glob)
        else:
            return True

    errors_count = 0
    files_checked = 0
    resolver = file_resolver.get_resolver(
        args.path1, args.path2, repo=args.repo, file_filter=filter_files
    )

    config = DiffConfig(
        epsilon=args.epsilon,
        output_path=args.diff_output,
        output_as_file=args.diff_output.is_file() if args.diff_output else False,
        colors=DiffColors(
            unchanged=args.diff_unchanged_color,
            added=args.diff_added_color,
            removed=args.diff_removed_color,
        ),
        show_stats=args.stats,
    )

    from concurrent.futures import ProcessPoolExecutor, as_completed

    with ProcessPoolExecutor(
        max_workers=args.jobs if args.jobs and args.jobs > 0 else None,
        initializer=_worker_init,
        initargs=(log_level,),
    ) as executor:

        futures = {}

        for pair in sorted(resolver.files, key=lambda pair: pair.name):
            future = executor.submit(process_file_pair, pair, config)
            futures[future] = pair

        # Wait for futures to complete and gather results
        try:
            for future in as_completed(futures):

                pair = futures[future]

                diff_result: DiffProcessResult = future.result()

                print(f"{pair.name}: ", end="")

                if diff_result.error:
                    print(diff_result.error)
                    errors_count += 1
                else:
                    print("OK")

                if diff_result.files_checked:
                    files_checked += 1

                if config.show_stats and diff_result.step_diff_stats:
                    print(format_diff_stats(diff_result.step_diff_stats))

        except KeyboardInterrupt:

            # Kill running worker processes immediately
            for proc in executor._processes.values():
                proc.terminate()

            executor.shutdown(cancel_futures=True, wait=False)
            print("Interrupted by user, shutting down...")
            return 2

    if errors_count:
        print(
            f"WARNING: {errors_count} {'error' if errors_count == 1 else 'errors'} found"
        )
    elif not files_checked:
        print("WARNING: No files checked")

    return 1 if errors_count else 0


if __name__ == "__main__":
    sys.exit(main())
