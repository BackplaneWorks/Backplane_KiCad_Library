""" "
This is a module to perform a common action in CI workflows: find a list of
corresponding files in two directories or in different git commits and
present them as pairs that can be used by other tools (e.g. a diff tool).
"""

import abc
import logging
import os
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ResolvedFilePair:
    """
    Represents a pair of files that are to be compared.
    There is no guarantee that either of those files exists.
    The user should call .exists() on them before accessing them.

    If either file is None, it means that there is not a corresponding
    file on that side (e.g. the file was created or deleted, though the
    exact implication of that is up to the user).
    """

    # File A (the old side of a diff)
    file1: Path | None
    # File B (the new side of a diff)
    file2: Path | None
    # The name of the pair (hopefully unique), but stripped of any
    # prefix such that "re-rooting" it in the other file's 'context'
    # would find a counterpart (if it exists).
    #
    # This is useful for constructing the output file names.
    # It can still contain slashes, so it's not directly a file name, but
    # it's a relative path, so it can be used to construct a file name.
    #
    # E.g. for two files A and B, it's just B.
    #      for a files in directories A and C: A/B and C/D, it's D.
    #
    # Note that in either example, the actual file _names_ don't have
    # to match - there could be other criteria for declaring a resolved
    # match.
    name: Path

    def __init__(self, file1, file2, name):
        self.file1 = Path(file1) if file1 is not None else None
        self.file2 = Path(file2) if file2 is not None else None
        self.name = Path(name)

    def __repr__(self):
        return f'ResolvedFilePair("{self.file1}", "{self.file2}", "{self.name}")'


class FileResolver(abc.ABC):
    """
    This is something that can resolve a list of files to be compared.
    """

    @property
    @abc.abstractmethod
    def files(self) -> list[ResolvedFilePair]:
        raise NotImplementedError("This is an abstract method")


class DirectFileResolver(FileResolver):
    """
    Takes two files or lists of files and yields them as pairs.

    Either *path1* or *path2* may be None, in which case every
    pair will have that side set to None (meaning the file was
    created or deleted relative to the other side).
    """

    def __init__(
        self,
        path1: Path | list[Path] | None,
        path2: Path | list[Path] | None,
        file_filter=None,
    ):
        self._files: list[ResolvedFilePair]

        if path1 is not None and not isinstance(path1, list):
            path1 = [path1]
        if path2 is not None and not isinstance(path2, list):
            path2 = [path2]

        if path1 is None and path2 is not None:
            path1 = [None] * len(path2)
        if path2 is None and path1 is not None:
            path2 = [None] * len(path1)
        if path1 is None and path2 is None:
            raise ValueError("At least one path is required")

        if len(path1) != len(path2):
            raise ValueError("The two lists must have the same length")

        self._files = []
        for a, b in zip(path1, path2):
            # None on both sides is meaningless
            if a is None and b is None:
                continue

            # The filter is applied to both sides, so if either side is
            # if filtered out, the pair is skipped.
            if file_filter is not None:
                if a is not None and not file_filter(a):
                    continue
                if b is not None and not file_filter(b):
                    continue
            resolved = ResolvedFilePair(a, b, a or b)
            self._files.append(resolved)

    @property
    def files(self) -> list[ResolvedFilePair]:
        return self._files


class DirectoryFileResolver(FileResolver):
    """
    Takes two directories and yields every file found in either as a
    pair.

    Either *path1* or *path2* may be None, in which case every
    file from the non-None side is paired with None on the
    other side (meaning all files were created or deleted).
    """

    def __init__(self, path1, path2, recursive=True, file_filter=None):

        def list_files(path):
            if not recursive:
                for file in os.listdir(path):
                    yield os.path.join(path, file)
            else:
                for root, _, files in os.walk(path):
                    for file in files:
                        yield os.path.join(root, file)

        def get_relative_paths(path):
            for f in list_files(path):
                rel_path = os.path.relpath(f, path)
                if file_filter is None or file_filter(rel_path):
                    yield rel_path

        # Collect relative paths from each side
        paths1 = set(get_relative_paths(path1)) if path1 is not None else set()
        paths2 = set(get_relative_paths(path2)) if path2 is not None else set()

        # Build the pairs
        self._files: list[ResolvedFilePair] = []
        for rel_path in sorted(paths1 | paths2):
            file1 = os.path.join(path1, rel_path) if path1 is not None else None
            file2 = os.path.join(path2, rel_path) if path2 is not None else None
            self._files.append(ResolvedFilePair(file1, file2, rel_path))

    @property
    def files(self) -> list[ResolvedFilePair]:
        return self._files


class GitDiffResolver(FileResolver):
    """
    Resolves only the files that changed between two git tree-ish
    references (commits, branches, or tags) in the same repository.

    Each side of the diff is materialised as a directory tree in a
    temporary location.  Files that exist on a side are checked out
    there; files that do not exist on a side are represented by a path
    inside the tree that is simply never created (so exists()
    returns False for that side).

    When *new_ref* is None the "new" side is the working tree,
    so the diff shows uncommitted changes relative to *old_ref*.
    """

    def __init__(
        self,
        repo_path: Path,
        old_ref: str,
        new_ref: str | None = None,
        file_filter=None,
    ):
        import tempfile

        import git

        self._repo = git.Repo(str(repo_path))

        old_commit = self._repo.commit(old_ref)

        def sanitize_ref(ref: str) -> str:
            # Git allows slashes in branch names, but we can't use those in
            # temp directory names.  Replace them with underscores.
            return ref.replace("/", "_")

        # Note - tempdirs live until the resolver is deleted
        # TODO: it does not get deleted, because we are not using this as a context
        #       we need to implement the __enter__ and __exit__ method

        # Side A (old): always checked out to a temp directory.
        self._old_temp_dir = tempfile.TemporaryDirectory(
            prefix=f"git-old-{sanitize_ref(old_ref)}-"
        )
        old_root = Path(self._old_temp_dir.name)

        if new_ref is not None:
            # Two-commit mode: check out the new side as well.
            new_commit = self._repo.commit(new_ref)
            diffs = old_commit.diff(new_commit)
            self._new_temp_dir = tempfile.TemporaryDirectory(
                prefix=f"git-new-{sanitize_ref(new_ref)}-"
            )
            new_root = Path(self._new_temp_dir.name)
        else:
            # Working-tree mode: new side is the working directory on disk, so
            # we don't need to check it out to a temp directory.
            diffs = old_commit.diff(None)
            new_root = Path(self._repo.working_tree_dir)
            self._new_temp_dir = None  # No cleanup needed.

        self._files: list[ResolvedFilePair] = []

        for diff in diffs:

            # The path to the file in the repository, relative to the root of the repo.
            # Prefer the new path if it exists, otherwise use the old path, so that
            # filters apply to the new path for renames.
            rel_path = diff.b_path or diff.a_path

            if file_filter is not None and not file_filter(rel_path):
                continue

            file1 = old_root / rel_path
            file2 = new_root / rel_path

            match diff.change_type:
                case "A":
                    # Added: only the new side has content.
                    # file1 is deliberately left unwritten.
                    file1 = None

                    file2.parent.mkdir(parents=True, exist_ok=True)
                    if new_ref is not None:
                        file2.write_bytes(diff.b_blob.data_stream.read())
                    # else: working tree: file2 already on disk.

                case "D":
                    # Deleted: only the old side has content.
                    file1.parent.mkdir(parents=True, exist_ok=True)
                    file1.write_bytes(diff.a_blob.data_stream.read())

                    file2 = None

                case "M":
                    # Modified: both sides have content.
                    file1.parent.mkdir(parents=True, exist_ok=True)
                    file1.write_bytes(diff.a_blob.data_stream.read())
                    file2.parent.mkdir(parents=True, exist_ok=True)
                    if new_ref is not None:
                        file2.write_bytes(diff.b_blob.data_stream.read())
                    # else: working tree: file2 already on disk.

                case "R":
                    # Rename: file1 lives at the old path, file2 at the new.
                    file1 = old_root / diff.a_path
                    file2 = new_root / diff.b_path
                    rel_path = diff.b_path

                    file1.parent.mkdir(parents=True, exist_ok=True)
                    file1.write_bytes(diff.a_blob.data_stream.read())

                    file2.parent.mkdir(parents=True, exist_ok=True)
                    if new_ref is not None:
                        file2.write_bytes(diff.b_blob.data_stream.read())
                    # else: working tree: file2 already on disk at its new location.

                case _:
                    LOGGER.warning(
                        "Unknown change type %s for %s, skipping",
                        diff.change_type,
                        rel_path,
                    )
                    continue

            self._files.append(ResolvedFilePair(file1, file2, rel_path))

        # Untracked files (working-tree mode only)
        # commit.diff(None) only covers tracked changes. New files that
        # have not been staged yet must be picked up separately.
        if new_ref is None:
            for untracked in self._repo.untracked_files:
                if file_filter is not None and not file_filter(untracked):
                    continue
                file1 = None
                file2 = new_root / untracked
                # file1 deliberately left unwritten (absent in old commit).
                # file2 already exists on disk in the working tree.
                self._files.append(ResolvedFilePair(file1, file2, untracked))

    @property
    def files(self) -> list[ResolvedFilePair]:
        return self._files


def get_resolver(
    arg1: str | None = None,
    arg2: str | None = None,
    repo: Path | None = None,
    file_filter=None,
) -> FileResolver:
    """
    Construct a resolver based on the paths given.

    Without --repo (file / directory mode):
      * One file     -> use `DirectFileResolver` with the old side as None (all files are new).
      * One dir      -> use `DirectoryFileResolver` with the old side as None (all files are new).
      * Two files    -> use `DirectFileResolver`
      * Two dirs     -> use `DirectoryFileResolver`
      * arg1 missing on disk but arg2 present
                     -> the new side is treated as all-created
                     (e.g. a library that is new in this MR).
      * arg2 missing on disk but arg1 present
                     -> the old side is treated as all-deleted
                     (e.g. a library that is removed in this MR).

    With --repo (git mode):
      *arg1* and *arg2* are git tree-ish references (commits, branches,
      or tags) resolved against *repo*.
      * Two refs        -> diff between the two commits.
      * One ref         -> diff between that commit and the working tree.
      * No refs         -> diff between HEAD and the working tree.
    """
    if repo is not None:
        if arg1 is not None and arg2 is not None:
            LOGGER.debug("Git diff: %s .. %s in %s", arg1, arg2, repo)
            return GitDiffResolver(repo, arg1, arg2, file_filter)
        elif arg1 is not None:
            LOGGER.debug("Git diff: %s .. working tree in %s", arg1, repo)
            return GitDiffResolver(repo, arg1, None, file_filter)
        else:
            LOGGER.debug("Git diff: HEAD .. working tree in %s", repo)
            return GitDiffResolver(repo, "HEAD", None, file_filter)

    # File / directory mode
    if arg1 is None:
        raise ValueError("At least one path is required when not using --repo.")

    # Single path: treat as creation (all files are new).
    if arg2 is None:
        p = Path(arg1)
        if p.is_file():
            LOGGER.debug("Single file: %s", p)
            return DirectFileResolver(None, p, file_filter)
        elif p.is_dir():
            LOGGER.debug("Single directory: %s", p)
            return DirectoryFileResolver(None, p, file_filter=file_filter)
        else:
            raise ValueError(f"Path does not exist: {arg1}")

    # Two paths: compare them.
    p1 = Path(arg1)
    p2 = Path(arg2)

    # A missing old side (e.g. a library that is new in this MR) is treated
    # as if the old side was empty: every file on the new side is created.
    if not p1.exists():
        if p2.is_dir():
            LOGGER.debug("Missing old side: all files in %s are new", p2)
            return DirectoryFileResolver(None, p2, file_filter=file_filter)
        if p2.is_file():
            LOGGER.debug("Missing old side: %s is new", p2)
            return DirectFileResolver(None, p2, file_filter)

    # A missing new side (e.g. a library that is removed in this MR) is
    # treated as if the new side was empty. every file on the old side is
    # "deleted".
    if not p2.exists():
        if p1.is_dir():
            LOGGER.debug("Missing new side: all files in %s are deleted", p1)
            return DirectoryFileResolver(p1, None, file_filter=file_filter)
        if p1.is_file():
            LOGGER.debug("Missing new side: %s is deleted", p1)
            return DirectFileResolver(p1, None, file_filter)

    if p1.is_file() and p2.is_file():
        LOGGER.debug("File diff: %s vs %s", p1, p2)
        return DirectFileResolver(p1, p2, file_filter)
    elif p1.is_dir() and p2.is_dir():
        LOGGER.debug("Directory diff: %s vs %s", p1, p2)
        return DirectoryFileResolver(p1, p2, file_filter=file_filter)
    else:
        raise ValueError(
            f"Cannot compare {arg1} and {arg2}: "
            "both must be files or both must be directories"
        )
