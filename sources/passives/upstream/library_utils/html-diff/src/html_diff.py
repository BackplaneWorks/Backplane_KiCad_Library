#!/usr/bin/env python3

import argparse
import fnmatch
import functools
import logging
import multiprocessing
import os
import re
import string
import subprocess
import sys
import tempfile
import textwrap
import traceback
import warnings
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import wsdiff
from pygments import token
from pygments.formatters import HtmlFormatter
from pygments.lexer import RegexLexer
from witchhazel import WitchHazelStyle

try:
    # Try importing kicad_mod to figure out whether the kicad-library-utils stuff is in path
    import kicad_mod  # NOQA: F401
except ImportError:
    if (
        common := Path(__file__).parent.parent.with_name("common").absolute()
    ) not in sys.path:
        sys.path.insert(0, str(common))
try:
    # file_resolver lives in klu/tools, so make sure that is on the path too
    import file_resolver
except ImportError:
    if (tools := Path(__file__).parent.parent.parent / "tools") not in sys.path:
        sys.path.insert(0, str(tools))
    import file_resolver
import jinja2
import kicad_mod  # NOQA: F811
import kicad_sym
import print_fp_properties
import print_sym_properties
import render_fp
import render_index_html
import render_sym

ERROR_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<title>Diff error</title>
</head>
<body>
<h4>Python exception in diff formatter</h4>
<pre>${error}</pre>
</body>
"""

loader = jinja2.FileSystemLoader(Path(__file__).parent.with_name("templates"))
j2env = jinja2.Environment(loader=loader, autoescape=jinja2.select_autoescape())


class SexprLexer(RegexLexer):
    name = "KiCad S-Expression"
    aliases = ["sexp"]
    filenames = ["*.kicad_mod", "*.kicad_sym"]

    tokens = {
        "root": [
            (r"\s+", token.Whitespace),
            (r"[()]", token.Punctuation),
            (r"([+-]?\d+\.\d+)(?=[)\s])", token.Number),
            (r"(-?\d+)(?=[)\s])", token.Number),
            (r'"((?:[^"]|\\")*)"(?=[)\s])', token.String),
            (r'([^()"\s]+)(?=[)\s])', token.Name),
        ]
    }


def _construct_syntax_css() -> str:
    """
    Constructs some suitable light/dark mode CSS for the diff syntax highlighting.
    """
    light_css = HtmlFormatter(classprefix="wsd-", style="xcode").get_style_defs()
    dark_css = HtmlFormatter(classprefix="wsd-", style=WitchHazelStyle).get_style_defs()

    syntax_css = textwrap.dedent(f"""@media print, (prefers-color-scheme: light) {{
            {light_css}
        }}

        @media (prefers-color-scheme: dark) {{
            {dark_css}
        }}""")
    return syntax_css


def html_stacktrace(fun):
    """
    Decorator to wrap a function and catch exceptions, formatting them as HTML.

    This means that unrecoverable errors in the diff formatter:
        - don't crash the whole diff generation
        - are reported in the HTML output instead of being only hidden in the
          console output
    """

    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except Exception as e:
            formatted_exc = "".join(traceback.format_exception(e))
            warnings.warn(f"Error formatting diff: {formatted_exc}")
            return string.Template(ERROR_TEMPLATE).substitute(error=formatted_exc)

    return wrapper


@contextmanager
def _item_error_context(item_type: str, item_name: str):
    """Add the item name as an exception note to any error raised in the block.

    Args:
        item_type: The type of the item being processed (e.g., "symbol", "footprint").
        item_name: The name of the item being processed.
    """
    try:
        yield
    except Exception as e:
        e.add_note(f"while processing {item_type} {item_name}")
        raise


def button(title, url, _id=None):
    if _id:
        return f'<a id="{_id}" href="{url}" class="button link">{title}</a>'
    else:
        return f'<a href="{url}" class="button link">{title}</a>'


def button_if(title, url, _id=None):
    if url and _id:
        return f'<a id="{_id}" href="{url}" class="button link">{title}</a>'
    elif url:
        return f'<a href="{url}" class="button link">{title}</a>'
    else:
        return ""


def js_str_list(l):  # NOQA: E741
    js_template_strs = ["`" + elem.replace("$", r"\$") + "`" for elem in l if elem]
    return "[" + ", ".join(js_template_strs) + "]"


def get_unit_suffix(unit_num: int) -> str:
    """
    Get the suffix: A, B, ..., Z, AA, AB, ...

    Unit num is 1-based like unit indexes in KiCad
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    unit_num -= 1  # convert to 0-based

    if unit_num < 0:
        raise ValueError("Unit number must be non-negative")

    suffix = ""
    while unit_num >= 0:
        suffix = alphabet[unit_num % 26] + suffix
        unit_num = unit_num // 26 - 1

    return suffix


def file_matches_glob(path: Path, globs: list[str] | None) -> bool:
    """
    Return whether a library file matches the --glob filter.

    With no globs, every file matches.
    """
    if not globs:
        return True
    return any(fnmatch.fnmatch(str(path), g) for g in globs)


def temporary_symbol_library(symbol_lines: list[str]) -> str:
    if symbol_lines and not symbol_lines[0].strip().startswith("(symbol"):
        warnings.warn(
            f"Leading garbage in same line before symbol definition or broken symbol index"  # NOQA: E501, F541
        )

    if symbol_lines and not symbol_lines[-1].strip().endswith(")"):
        warnings.warn(
            f"Trailing garbage in same line after symbol definition or broken symbol index"  # NOQA: E501, F541
        )

    content = "\n".join(symbol_lines)
    return f"(kicad_symbol_lib (version 20231120) (generator kicad_html_diff)\n{content}\n)"


def build_symlib_index(libfile: Path):
    """
    Yields the names and line ranges (start, end) of all symbols in a library.

    Note, end is the line after the last line of the symbol.
    """
    if not libfile.is_file():
        return

    lineno = 0
    last_start = 0
    last_name: str | None = None

    # Note that this exploits the KiCad v8+ formatting:
    # symbols always indent with exactly one tab, and end with "\t)".
    #
    # If it gets more complex, either we need to autodetect indentation
    # or do more complex parsing (or delegate to kicad API one day?)

    symbol_start_patt = re.compile(r'^\t\(symbol\s+"(\S+)"')

    for line in libfile.read_text().splitlines():

        # Start of a symbol?
        if match := re.match(symbol_start_patt, line):
            last_name = match.group(1)
            last_start = lineno

        # End of a symbol?
        elif line == "\t)":
            if last_name:
                yield last_name, (last_start, lineno + 1)
                last_name = None

        lineno += 1


def render_symbol_kicad_cli(libfile, symname, outdir):
    outdir.mkdir(parents=True, exist_ok=True)

    kicad_cli = os.environ.get("KICAD_CLI", "kicad-cli")
    try:
        cmd = [kicad_cli, "sym", "export", "svg"]

        if symname:
            cmd.extend(["-s", symname])

        cmd.extend(["-o", str(outdir), str(libfile)])

        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
    except FileNotFoundError:
        warnings.warn(
            "Cannot find kicad-cli, no reference screenshots will be exported."
        )


def render_footprint_kicad_cli(libdir: Path, fpname: str | None, outfile: Path):
    """
    Render a library (or a single footprint) using kicad-cli.
    """
    outfile.parent.mkdir(parents=True, exist_ok=True)

    kicad_cli = os.environ.get("KICAD_CLI", "kicad-cli")
    try:
        cmd = [kicad_cli, "fp", "export", "svg"]

        if fpname:
            cmd.extend(["--fp", fpname])

        cmd.extend(["-o", str(outfile), str(libdir)])

        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
    except FileNotFoundError:
        warnings.warn(
            "Cannot find kicad-cli, no reference screenshots will be exported."
        )


class BatchRenderLibrary:
    """
    Render a library of parts (symbols or footprints) using kicad-cli.

    This class is used to render a batch of parts from a library at once.
    This is radically faster than rendering each part individually in a
    separate kicad-cli invocation.
    """

    def __init__(self, libdir, outdir: Path):
        self.stems: set[str] = set()
        self.libdir = libdir
        self.outdir = outdir

    def add_stem(self, stem: str):
        self.stems.add(stem)

    def get_files_for_stem(self, stem) -> list[Path]:
        """
        Get all existing files for a given stem, in order as suitable
        (e.g. by unit for symbols).
        """
        raise NotImplementedError()

    def _clear_unwanted(self):

        # Can't be anything to delete if the output directory doesn't exist
        if not self.outdir.is_dir():
            return

        # find all SVG files in the output directory
        # that we didn't ask for and delete them
        wanted_files = set()

        for stem in self.stems:
            for file in self.get_files_for_stem(stem):
                wanted_files.add(file)

        for f in self.outdir.iterdir():
            if f.suffix == ".svg":
                if f not in wanted_files:
                    f.unlink()


class BatchRenderFootprints(BatchRenderLibrary):

    def render(self):

        fp: str | None = None

        # if there's only one footprint, we can render it directly
        if len(self.stems) == 1:
            fp = min(self.stems)

        render_footprint_kicad_cli(self.libdir, fp, self.outdir)

        self._clear_unwanted()

    def get_files_for_stem(self, stem):
        # Very simple: name and extension
        # no useful unit for FPs

        if self.outdir.is_dir():
            fn = self.outdir / f"{stem}.svg"
            if fn.is_file():
                return [fn]

        return []


class BatchRenderSymbols(BatchRenderLibrary):

    def render(self):

        # First, clear the output directory of any matching files
        # in case we deleted a unit

        for symname in self.stems:
            for file in self.get_files_for_stem(symname):
                file.unlink()

        sym: str | None = None

        # if there's only one symbol, we can render it directly
        if len(self.stems) == 1:
            sym = min(self.stems)

        render_symbol_kicad_cli(self.libdir, sym, self.outdir)

        self._clear_unwanted()

    def get_files_for_stem(self, stem):
        if not self.outdir.is_dir():
            return []

        if os.path.isfile(self.outdir / f"{stem}.svg"):
            return [self.outdir / f"{stem}.svg"]

        # Since V9, there's always a uniform unitN suffix
        regex = re.compile(f"{re.escape(stem)}_unit([0-9]+).svg")

        files = []
        for file in self.outdir.iterdir():
            if match := regex.match(file.name):
                files.append((int(match.group(1)), file))

        # Sort by the number in the filename
        files.sort(key=lambda x: x[0])
        # Return just the files
        return [file for _, file in files]


class HTMLDiff:

    output: Path
    name_glob: str
    changes_only: bool
    screenshot_dir: Path
    # If present, the directory where the diff old/new files are written to
    diff_svg_output_dir: Optional[Path]
    max_workers: int

    def __init__(
        self,
        output,
        meta,
        name_glob="*",
        changes_only=True,
        screenshot_dir=None,
        diff_svg_output_dir=None,
    ):
        self.output = output
        self.base_output = output
        self.name_glob = name_glob
        self.changes_only = changes_only
        self.name_map = {}
        self.diff_index = []
        self.max_workers = 1
        self.git_mode = False

        if screenshot_dir is None:
            tmp = self.screenshot_tmpdir = tempfile.TemporaryDirectory()
            self.screenshot_dir = Path(tmp.name)
        else:
            self.screenshot_dir = screenshot_dir

        self.diff_svg_output_dir = diff_svg_output_dir

        if self.diff_svg_output_dir is not None:
            self.diff_svg_output_dir.mkdir(parents=True, exist_ok=True)

        self.meta = meta

        if "CI_MERGE_REQUEST_ID" in os.environ:
            self.mr_url = (
                f'{os.environ["CI_MERGE_REQUEST_PROJECT_URL"]}'
                f"/-/merge_requests/{os.environ['CI_MERGE_REQUEST_IID']}"
            )
        else:
            self.mr_url = None

        if meta.get("old_git") is not None:
            revname, commit_id = meta["old_git"]
            new_path = meta.get("new_path")
            old_path = meta.get("old_path")

            if old_path is not None and old_path == new_path:
                self.source_revisions = f"Comparing {new_path} against rev {commit_id}"
            elif old_path is not None:
                self.source_revisions = (
                    f"Comparing {new_path} against {old_path} at {commit_id}"
                )
            else:
                self.source_revisions = f"Comparing against rev {commit_id}"

            if revname:
                self.source_revisions += f" alias {revname}"
        else:
            old_path = meta.get("old_path")
            new_path = meta.get("new_path")
            self.source_revisions = (
                f'Comparing {new_path or "?"} against {old_path or "?"}'
            )

    @staticmethod
    def _library_key(name: Path, file: Path) -> Path:
        """
        Return a stable key identifying the library a pair belongs to.

        The key must be the same for every pair of a library, regardless of
        which side of the diff the file exists on. In git mode (and whenever
        the compared roots sit above the libraries), ``name`` is the
        repository-relative path, so its parent identifies the library and is
        identical for old and new sides. When the name has no parent component
        (the roots are the library files or directories themselves), fallback
        to the file's own path.
        """
        parent = name.parent

        if parent != Path("."):
            if (
                name.suffix.lower() == ".kicad_sym"
                and parent.suffix.lower() != ".kicad_symdir"
            ):
                # A packed symbol library is its own library.
                return name
            return parent

        if (
            file.suffix.lower() == ".kicad_sym"
            and file.parent.suffix.lower() != ".kicad_symdir"
        ):
            return file
        return file.parent

    def _add_pair_to_library(
        self,
        mod_libs: dict[Path, list[file_resolver.ResolvedFilePair]],
        sym_libs: dict[Path, list[file_resolver.ResolvedFilePair]],
        pair: file_resolver.ResolvedFilePair,
    ) -> None:
        """Add a resolved pair to the group of its library."""
        file = pair.file2 if pair.file2 is not None else pair.file1
        if file is None:
            return
        file = Path(file)

        key = self._library_key(pair.name, file)
        if file.suffix.lower() == ".kicad_mod":
            mod_libs.setdefault(key, []).append(pair)
        elif file.suffix.lower() == ".kicad_sym":
            sym_libs.setdefault(key, []).append(pair)
        else:
            logging.warning("Ignoring unsupported file: %s", file)

    def _git_old_name(self, pair: file_resolver.ResolvedFilePair) -> Path | None:
        """
        Return the reconstructed old (repo-relative) name of a git pair.

        In git mode the old side is checked out under a temporary root, so
        the old path is ``<lib>/<file>`` relative to that root. Returns None
        when the name cannot be reconstructed (not git mode, or the old side
        is missing).
        """
        if not self.git_mode or pair.file1 is None:
            return None

        old_file = Path(pair.file1)
        return Path(old_file.parent.name) / old_file.name

    def _rename_old_name(self, pair: file_resolver.ResolvedFilePair) -> Path | None:
        """
        Return the old (repo-relative) name if the pair is a rename within
        one library, otherwise None.

        Cross-library moves return None (they are split into delete + create
        instead of being shown as a rename), as do non-git pairs (see
        _git_old_name).
        """
        if pair.file2 is None:
            return None

        old_name = self._git_old_name(pair)
        if old_name is None or old_name == pair.name:
            return None

        old_key = self._library_key(old_name, Path(pair.file1))
        new_key = self._library_key(pair.name, Path(pair.file2))

        if old_key != new_key:
            # Cross-library move.
            return None

        return old_name

    def diff_pairs(
        self,
        pairs: list[file_resolver.ResolvedFilePair],
        *,
        git_mode: bool = False,
    ) -> None:
        """
        Diff the given resolved file pairs, grouping them into libraries.

        Footprint pairs (.kicad_mod) are grouped by their .pretty directory.
        Symbol pairs (.kicad_sym) are grouped by their .kicad_symdir directory,
        or treated as their own library if they are packed library files.

        In git mode, a rename within one library is rendered as a single
        change (with the old name shown). A move between libraries is split
        into a deletion and an addition.
        """
        self.git_mode = git_mode

        mod_libs: dict[Path, list[file_resolver.ResolvedFilePair]] = {}
        sym_libs: dict[Path, list[file_resolver.ResolvedFilePair]] = {}

        for pair in pairs:
            # Split cross-library moves into delete + create
            # Keep in-library renames as a single change.
            old_name = self._git_old_name(pair)
            if (
                old_name is not None
                and old_name != pair.name
                and self._rename_old_name(pair) is None
            ):
                old_file = Path(pair.file1)
                new_file = Path(pair.file2)
                self._add_pair_to_library(
                    mod_libs,
                    sym_libs,
                    file_resolver.ResolvedFilePair(old_file, None, old_name),
                )
                self._add_pair_to_library(
                    mod_libs,
                    sym_libs,
                    file_resolver.ResolvedFilePair(None, new_file, pair.name),
                )
                continue

            self._add_pair_to_library(mod_libs, sym_libs, pair)

        num_libs = len(mod_libs) + len(sym_libs)
        if (
            self.base_output is not None
            and self.base_output.suffix == ".diff"
            and num_libs > 1
        ):
            raise ValueError(
                "When diffing multiple libraries, --output must be a directory "
                f"to hold the <library>.diff outputs, not a single file ({self.base_output})."  # NOQA: E501
            )

        # Sort by library name for deterministic output
        for lib in sorted(mod_libs, key=lambda p: p.name):
            self._diff_mod_library(lib, mod_libs[lib])
        for lib in sorted(sym_libs, key=lambda p: p.name):
            self._diff_sym_library(lib, sym_libs[lib])

    def _library_output_dir(self, lib_key: Path) -> Path:
        """
        Return the output directory for a library, honoring --output.

        lib_key is the library's directory (e.g. "Foo.pretty" or
        "Foo.kicad_symdir") or a packed .kicad_sym file. The output directory
        is named after the library with a ".diff" suffix.
        """
        lib_diff = Path(lib_key.name).with_suffix(".diff")

        if self.base_output is None:
            return lib_diff

        if self.base_output.suffix == ".diff":
            # --output was given as the exact diff directory (single library)
            return self.base_output

        return self.base_output / lib_diff

    def _pair_urls(
        self, pair: file_resolver.ResolvedFilePair
    ) -> tuple[str | None, str | None]:
        """
        Compute GitLab "Old File"/"New File" blob URLs for a resolved pair.

        Only meaningful in a GitLab merge-request pipeline, where the CI_*
        variables are set and the pair was resolved from git (--repo).

        Returns (old_url, new_url). Either one may be None if it cannot be
        built (e.g. the file was created or deleted on that side).
        """
        if self.mr_url is None:
            return None, None

        old_git = self.meta.get("old_git")
        if old_git is None:
            return None, None

        old_sha = old_git[1] or old_git[0]
        source_branch = os.environ.get("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME")
        project_url = os.environ.get("CI_PROJECT_URL")
        mr_source_project_url = os.environ.get("CI_MERGE_REQUEST_SOURCE_PROJECT_URL")

        # If the MR URL is set we expect the other variables
        if not all([old_sha, source_branch, project_url, mr_source_project_url]):
            warnings.warn(
                "Cannot build old file/new file URLs: missing CI variables or old_git info"
            )
            return None, None

        old_url = None
        new_url = None

        if pair.file1 is not None:
            old_name = self._rename_old_name(pair)
            old_rel = old_name if old_name is not None else pair.name
            old_url = f"{project_url}/-/blob/{old_sha}/{old_rel}"
            if "old_line_range" in self.meta:
                start, end = self.meta["old_line_range"]
                old_url += f"#L{start}-{end}"
        if pair.file2 is not None:
            new_url = f"{mr_source_project_url}/-/blob/{source_branch}/{pair.name}"
            if "new_line_range" in self.meta:
                start, end = self.meta["new_line_range"]
                new_url += f"#L{start}-{end}"

        return old_url, new_url

    @staticmethod
    def format_index(diff_index, part_name: str):

        index = ""
        prefetch = None
        prefetch_next = False

        for filename, created, changed, deleted in diff_index:
            classes = []
            if created:
                classes.append("created")
            elif deleted:
                classes.append("deleted")
            elif changed:
                classes.append("changed")
            else:
                classes.append("unchanged")

            if prefetch_next:
                prefetch = filename.name
                prefetch_next = False

            if filename.stem == part_name:
                classes.append("index-self")
                prefetch_next = True

            link = f'<a href="{filename.name}">{filename.stem}</a>'
            index += f'  <div class="{" ".join(classes)}">{link}</div>\n'

        return index, prefetch

    def _format_html_diff(
        self,
        part_name: str,
        lib_name: str,
        next_diff: str,
        prev_diff: str,
        enable_layers,
        hide_text_in_diff,
        unit_names=[],
        old_name=None,
        old_url=None,
        new_url=None,
        **kwargs,
    ):

        index, prefetch = self.format_index(self.diff_index, part_name)

        display_name = part_name
        if old_name is not None:
            display_name = f"{old_name} -> {part_name}"

        return j2env.get_template("diff.html").render(
            page_title=f"diff: {display_name} in {lib_name}",
            part_name=part_name,
            display_name=display_name,
            unit_names=unit_names,
            source_revisions=self.source_revisions,
            enable_layers="true" if enable_layers else "false",
            hide_text_in_diff="true" if hide_text_in_diff else "false",
            code_diff_css=wsdiff.MAIN_CSS,
            diff_syntax_css=_construct_syntax_css(),
            prev_button=button("<", prev_diff, _id="nav-bt-prev"),
            next_button=button(">", next_diff, _id="nav-bt-next"),
            diff_index=index,
            prefetch_url=prefetch,
            pipeline_button=button_if("Pipeline", os.environ.get("CI_PIPELINE_URL")),
            old_file_button=button_if("Old File", old_url),
            new_file_button=button_if("New File", new_url),
            merge_request_button=button_if("Merge Request", self.mr_url),
            **kwargs,
        )

    @html_stacktrace
    def mod_diff(
        self,
        part_name: str,
        lib_name: str,
        old_text: list[str],
        new_text: list[str],
        prev_diff: str,
        next_diff: str,
        ref_svg,
        old_name=None,
        old_url=None,
        new_url=None,
    ):

        old_mod = None
        new_mod = None
        old_svg_text = ""
        new_svg_text = ""

        if old_text:
            old_mod = kicad_mod.KicadMod(data=old_text)
            old_svg_text = render_fp.render_mod(old_mod)

        if new_text:
            new_mod = kicad_mod.KicadMod(data=new_text)
            new_svg_text = render_fp.render_mod(new_mod)

        # Write the SVGs to disk for debugging or use in other tools
        if self.diff_svg_output_dir is not None:
            old_svg_path = self.diff_svg_output_dir / f"{part_name}.old.svg"
            new_svg_path = self.diff_svg_output_dir / f"{part_name}.new.svg"

            if old_svg_text:
                old_svg_path.write_text(old_svg_text)

            if new_svg_text:
                new_svg_path.write_text(new_svg_text)

        properties_table = print_fp_properties.format_properties(old_mod, new_mod)

        return self._format_html_diff(
            part_name=part_name,
            lib_name=lib_name,
            old_name=old_name,
            next_diff=next_diff,
            prev_diff=prev_diff,
            enable_layers=True,
            canvas_background="#001023",
            hide_text_in_diff=True,
            properties_table=properties_table,
            code_diff=wsdiff.html_diff_block(
                old_text, new_text, filename="", lexer=SexprLexer()
            ),
            old_svg=js_str_list([old_svg_text]),
            new_svg=js_str_list([new_svg_text]),
            reference_svg=js_str_list([ref_svg]),
            old_url=old_url,
            new_url=new_url,
        )

    def _get_ref_fn(self, new_file):
        return (
            self.screenshot_dir
            / new_file.parent.name
            / f"{new_file.stem}.kicad_mod.svg"
        )

    def _diff_mod_library(
        self, lib_key: Path, pairs: list[file_resolver.ResolvedFilePair]
    ) -> None:
        """
        Diff a library of footprints, given the resolved file pairs that
        belong to it.
        """
        self.output = self._library_output_dir(lib_key)

        self.diff_index, changed_pairs = self._get_changed_pairs(pairs)

        if not changed_pairs:
            # No footprints to show in this library: skip it entirely rather
            # than leaving an empty .diff directory behind (and skip the
            # pointless reference render).
            return

        self.output.mkdir(exist_ok=True, parents=True)

        lib_name = lib_key.stem

        new_dir = next(
            (Path(pair.file2).parent for pair in pairs if pair.file2 is not None),
            None,
        )
        if new_dir is None:
            # Everything on the new side was deleted: there is nothing to
            # render a reference of, but the renderer still needs a directory.
            new_dir = lib_key

        screenshot_dir = self.screenshot_dir / lib_key.name
        os.makedirs(screenshot_dir, exist_ok=True)

        # Render reference SVGs all at once.
        # This is a lot faster than rendering them one by one, even if we end up over-rendering
        renderer = BatchRenderFootprints(new_dir, screenshot_dir)

        for pair in changed_pairs:
            renderer.add_stem(pair.name.stem)

        try:
            renderer.render()
        except Exception as e:
            warnings.warn(f"Error exporting reference render using kicad-cli: {e}")

        with multiprocessing.Pool(processes=self.max_workers) as pool:

            args = []

            for i, pair in enumerate(changed_pairs):
                prev_pair = changed_pairs[(i - 1) % len(changed_pairs)]
                next_pair = changed_pairs[(i + 1) % len(changed_pairs)]
                out_file = self._diff_name(pair.name)
                args.append((lib_name, pair, prev_pair, next_pair, out_file))
            try:
                pool.starmap(self._process_one_mod, args)
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
            except Exception as e:
                warnings.warn(f"Error processing footprints: {e}")
                raise e

    def _process_one_mod(
        self,
        lib_name: str,
        pair: file_resolver.ResolvedFilePair,
        prev_pair: file_resolver.ResolvedFilePair,
        next_pair: file_resolver.ResolvedFilePair,
        out_file: Path,
    ):
        with _item_error_context("footprint", pair.name.stem):
            old_file = Path(pair.file1) if pair.file1 is not None else None
            new_file = Path(pair.file2) if pair.file2 is not None else None

            old_text = (
                old_file.read_text()
                if old_file is not None and old_file.is_file()
                else ""
            )
            new_text = (
                new_file.read_text()
                if new_file is not None and new_file.is_file()
                else ""
            )

            ref_svg = ""

            if new_file is not None and new_file.is_file():
                ref_fn = self._get_ref_fn(new_file)
                if ref_fn.is_file():
                    ref_svg = ref_fn.read_text()
                else:
                    ref_fn = ref_fn.with_name(f"{new_file.stem}.svg")
                    ref_svg = ref_fn.read_text()

            old_url, new_url = self._pair_urls(pair)

            old_name = self._rename_old_name(pair)
            old_name = old_name.stem if old_name is not None else None

            diff_text = self.mod_diff(
                part_name=pair.name.stem,
                lib_name=lib_name,
                new_text=new_text,
                old_text=old_text,
                prev_diff=self._diff_name(prev_pair.name).name,
                next_diff=self._diff_name(next_pair.name).name,
                ref_svg=ref_svg,
                old_name=old_name,
                old_url=old_url,
                new_url=new_url,
            )
            out_file.write_text(diff_text)

    @dataclass
    class SymLibDiffInfo:
        """
        Metadata describing a symbol library diff.

        This might be for a packed or unpacked library.
        """

        new_lib_path: Path

        # The old and new symbol libraries (may be None if deleted/created)
        old_lib: kicad_sym.KicadLibrary | None
        new_lib: kicad_sym.KicadLibrary | None

    @dataclass
    class SymbolDiffInfo:
        """
        Information about the files related to a symbol diff
        for a single symbol.
        """

        # Output HTML file
        out_file: Path

        # Old and new kicad_sym file
        old_kicad_sym: Path | None
        new_kicad_sym: Path | None

        # Line ranges of the symbol in the old and new kicad_sym files, for code-level diffs
        old_lines: tuple[int, int]
        new_lines: tuple[int, int]

        # Name of the symbol in the new kicad_sym file
        new_name: str

        # Name of the symbol in the old kicad_sym file
        old_name: str

        # GitLab blob URLs for the old and new symbol library files
        old_url: str | None = None
        new_url: str | None = None

    def _diff_name(self, new_file: Path) -> Path:
        return self.output / new_file.with_suffix(".html").name

    def _get_changed_pairs(
        self, pairs: list[file_resolver.ResolvedFilePair]
    ) -> tuple[list, list]:
        """
        Filter the given resolved file pairs by name and change status.

        Returns a tuple (diff_index, files) where diff_index contains
        (diff_name, created, changed, deleted) tuples and files contains
        the pairs to actually diff.
        """

        diff_index = []
        files = []

        for pair in pairs:

            # Skip if the name doesn't match the glob
            if not fnmatch.fnmatch(pair.name.stem, self.name_glob):
                continue

            old_file = Path(pair.file1) if pair.file1 is not None else None
            new_file = Path(pair.file2) if pair.file2 is not None else None

            old_text = (
                old_file.read_text()
                if old_file is not None and old_file.is_file()
                else ""
            )
            new_text = (
                new_file.read_text()
                if new_file is not None and new_file.is_file()
                else ""
            )
            changed = old_text != new_text
            if self._rename_old_name(pair) is not None:
                # A rename counts as a change even if the content is identical.
                changed = True
            created = old_file is None or not old_file.is_file()
            deleted = new_file is None or not new_file.is_file()

            if self.changes_only and not changed:
                continue

            diff_index.append((self._diff_name(pair.name), created, changed, deleted))
            files.append(pair)

        return diff_index, files

    def _process_sym_diffs(
        self, symdir_info: SymLibDiffInfo, syms: list[SymbolDiffInfo]
    ):
        """
        Process a list of symbol diffs for a symbol library.
        """

        screenshot_subdir = self.screenshot_dir / symdir_info.new_lib_path.stem
        os.makedirs(screenshot_subdir, exist_ok=True)

        # Render reference SVGs all at once
        # This is a lot faster than rendering them one by one, even if we end up over-rendering
        renderer = BatchRenderSymbols(symdir_info.new_lib_path, screenshot_subdir)

        for diffed_sym in syms:
            # Don't try to render deleted symbols, since they won't be in the new library
            # and kicad-cli will error out
            if diffed_sym.new_lines != (0, 0):
                renderer.add_stem(diffed_sym.new_name)

        try:
            renderer.render()
        except Exception as e:
            warnings.warn(f"Error exporting reference render using kicad-cli: {e}")

        # Sort the symbols by their new name
        sorted_syms = sorted(syms, key=lambda s: s.new_name)

        with multiprocessing.Pool(processes=self.max_workers) as pool:

            args = []

            for i, sym_diff_info in enumerate(sorted_syms):

                prev_sym = sorted_syms[(i - 1) % len(sorted_syms)]
                next_sym = sorted_syms[(i + 1) % len(sorted_syms)]

                prev_file = self._diff_name(Path(prev_sym.new_name)).name
                next_file = self._diff_name(Path(next_sym.new_name)).name

                unit_files = renderer.get_files_for_stem(sym_diff_info.new_name)
                args.append(
                    (symdir_info, sym_diff_info, unit_files, next_file, prev_file)
                )

            try:
                pool.starmap(self._process_one_sym, args)
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
            except Exception as e:
                warnings.warn(f"Error processing symbols: {e}")
                raise e

    def _get_symbol_diffs(
        self,
        old_kicad_sym_path: Path | None,
        new_kicad_sym_path: Path | None,
    ) -> list[SymbolDiffInfo]:
        """
        Get all the symbol diff infos for the symbols in the given kicad_sym files.

        self.output must already point at the library's output directory.
        Either path may be None, meaning that side of the library was absent.
        """
        # Get the raw s-expr lines of the symbol libraries for code-level diffs
        index_old = (
            dict(build_symlib_index(old_kicad_sym_path))
            if old_kicad_sym_path is not None
            else {}
        )
        index_new = (
            dict(build_symlib_index(new_kicad_sym_path))
            if new_kicad_sym_path is not None
            else {}
        )
        old_lines = (
            old_kicad_sym_path.read_text().splitlines()
            if old_kicad_sym_path is not None and old_kicad_sym_path.is_file()
            else []
        )
        new_lines = (
            new_kicad_sym_path.read_text().splitlines()
            if new_kicad_sym_path is not None and new_kicad_sym_path.is_file()
            else []
        )

        files: list[HTMLDiff.SymbolDiffInfo] = []

        to_diff = []

        # Add all the new items
        for name, (start, end) in index_new.items():
            if not fnmatch.fnmatch(name, self.name_glob):
                continue
            to_diff.append((name, (start, end)))

        # Add any deleted items
        for name, (start, end) in index_old.items():
            if not fnmatch.fnmatch(name, self.name_glob):
                continue
            if name not in index_new:
                to_diff.append((name, (0, 0)))

        # Sort in name order
        to_diff.sort(key=lambda x: x[0])

        for name, (start, end) in to_diff:

            old_name = self.name_map.get(name, name)
            old_start, old_end = index_old.get(old_name, (0, 0))

            changed = old_lines[old_start:old_end] != new_lines[start:end]

            if self.changes_only and not changed:
                continue

            out_file = self.output / f"{name}.html"

            files.append(
                self.SymbolDiffInfo(
                    out_file=out_file,
                    new_name=name,
                    new_lines=(start, end),
                    old_name=old_name,
                    old_lines=(old_start, old_end),
                    old_kicad_sym=old_kicad_sym_path,
                    new_kicad_sym=new_kicad_sym_path,
                )
            )

        return files

    def _diff_sym_library(
        self, lib_key: Path, pairs: list[file_resolver.ResolvedFilePair]
    ) -> None:
        """
        Diff a library of symbols, given the resolved file pairs that
        belong to it.
        """
        self.output = self._library_output_dir(lib_key)

        # Library path on the new side, used for rendering reference SVGs.
        # If the whole library was deleted, fall back to the old side so the
        # renderer has something to point at (it will find no new symbols).
        new_lib_path = next(
            (
                (
                    Path(pair.file2).parent
                    if Path(pair.file2).parent.suffix.lower() == ".kicad_symdir"
                    else Path(pair.file2)
                )
                for pair in pairs
                if pair.file2 is not None
            ),
            None,
        )
        if new_lib_path is None:
            new_lib_path = next(
                (
                    (
                        Path(pair.file1).parent
                        if Path(pair.file1).parent.suffix.lower() == ".kicad_symdir"
                        else Path(pair.file1)
                    )
                    for pair in pairs
                    if pair.file1 is not None
                ),
                lib_key,
            )

        sym_diff_infos: list[HTMLDiff.SymbolDiffInfo] = []

        for pair in pairs:
            old_kicad_sym_path = Path(pair.file1) if pair.file1 is not None else None
            new_kicad_sym_path = Path(pair.file2) if pair.file2 is not None else None

            new_infos = self._get_symbol_diffs(old_kicad_sym_path, new_kicad_sym_path)

            old_url, new_url = self._pair_urls(pair)
            for info in new_infos:
                info.old_url = old_url
                info.new_url = new_url

            sym_diff_infos += new_infos

        if not sym_diff_infos:
            # No symbols to show in this library: skip it entirely rather
            # than leaving an empty .diff directory behind (and skip the
            # pointless reference render).
            return

        self.output.mkdir(exist_ok=True, parents=True)

        # Build the per-symbol diff index, for the sidebar navigation
        self.diff_index = []
        for info in sym_diff_infos:
            created = info.old_lines == (0, 0)
            deleted = info.new_lines == (0, 0)
            self.diff_index.append(
                (info.out_file, created, not created and not deleted, deleted)
            )

        # This is the common info about the library diff that applies to all
        # symbol diffs in this library.
        symdir_info = self.SymLibDiffInfo(
            old_lib=None,
            new_lib=None,
            new_lib_path=new_lib_path,
        )

        # Finally, process all the symbol diffs
        self._process_sym_diffs(symdir_info, sym_diff_infos)

    def _process_one_sym(
        self,
        symdir_diff_info: SymLibDiffInfo,
        sym_diff_info: SymbolDiffInfo,
        unit_files,
        next_file,
        prev_file,
    ):
        with _item_error_context("symbol", sym_diff_info.new_name):
            screenshots_content = [f.read_text() for f in unit_files]

            svgs_old = []
            svgs_new = []

            old_content = ""
            new_content = ""

            new_sym = None
            old_sym = None

            def _get_sym_data(kicad_sym_path: Path, sym_name: str):
                """
                Extract symbol data - the raw s-expr lines, the parsed symbol and the rendered SVGs,
                for a given symbol in a given kicad_sym file.
                """
                lib = kicad_sym.KicadLibrary.from_file(kicad_sym_path)
                content = kicad_sym_path.read_text()
                sym = lib.get_symbol(sym_name)

                svgs = [
                    str(x) for x in render_sym.render_sym(sym, lib, default_style=False)
                ]

                return content, sym, svgs

            if sym_diff_info.old_lines != (0, 0):
                old_content, old_sym, svgs_old = _get_sym_data(
                    sym_diff_info.old_kicad_sym, sym_diff_info.old_name
                )

            if sym_diff_info.new_lines != (0, 0):
                new_content, new_sym, svgs_new = _get_sym_data(
                    sym_diff_info.new_kicad_sym, sym_diff_info.new_name
                )

            # Write the SVGs to disk for debugging or use in other tools
            if self.diff_svg_output_dir is not None:
                for i, svg in enumerate(svgs_old, start=1):
                    (
                        self.diff_svg_output_dir
                        / f"{sym_diff_info.new_name}.old.unit{i}.svg"
                    ).write_text(svg)
                for i, svg in enumerate(svgs_new, start=1):
                    (
                        self.diff_svg_output_dir
                        / f"{sym_diff_info.new_name}.new.unit{i}.svg"
                    ).write_text(svg)

            sexpr_diff = wsdiff.html_diff_block(
                old_content,
                new_content,
                filename="",
                lexer=SexprLexer(),
            )

            prop_table = print_sym_properties.format_properties(old_sym, new_sym)

            unit_names: list[str] = []

            # Currently, matching units between old and new is not done.
            # That's quite tricky as units can be added, removed or reordered.
            # For now, just show the unit names of the new symbol.
            if new_sym is not None:
                for unit in range(new_sym.unit_count):
                    unit_name = new_sym.unit_names.get(unit + 1)
                    unit_suffix = get_unit_suffix(unit + 1)

                    if unit_name is not None:
                        # Still show the suffix as this may be useful when looking at ref-des
                        unit_name = f"{unit_suffix}: {unit_name}"
                    else:
                        unit_name = f"Unit {unit_suffix}"

                    unit_names.append(unit_name)

            sym_diff_info.out_file.write_text(
                self._format_html_diff(
                    lib_name=symdir_diff_info.new_lib_path.stem,
                    part_name=sym_diff_info.new_name,
                    next_diff=next_file,
                    prev_diff=prev_file,
                    enable_layers=False,
                    canvas_background="#e0e0e0",
                    hide_text_in_diff=False,
                    properties_table=prop_table,
                    code_diff=sexpr_diff,
                    old_svg=js_str_list(svgs_old),
                    new_svg=js_str_list(svgs_new),
                    reference_svg=js_str_list(screenshots_content),
                    unit_names=unit_names,
                    old_url=sym_diff_info.old_url,
                    new_url=sym_diff_info.new_url,
                )
            )


def _build_meta(args) -> dict:
    meta: dict = {}

    if args.repo is not None:
        import git

        repo = git.Repo(args.repo)
        meta["git_toplevel"] = Path(repo.working_tree_dir)

        old_ref = args.path1 or "HEAD"
        try:
            commit_id = repo.git.rev_parse(old_ref, short=True)
        except Exception:
            commit_id = old_ref
        meta["old_git"] = (old_ref, commit_id)

        if args.path2 is not None:
            meta["old_path"] = old_ref
            meta["new_path"] = args.path2
    else:
        meta["old_git"] = None
        if args.path1 is not None:
            meta["old_path"] = str(Path(args.path1))
        if args.path2 is not None:
            meta["new_path"] = str(Path(args.path2))

    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""html-diff.py generates a visual, HTML-formatted diff between two libraries. It outputs one file per library item into a folder named after the library with suffix ".diff". Included in the diff are:

* An S-Expression diff
* A visual diff
* A render using kicad-cli
* For footprints: A layer-by-layer preview

You can provide one or two paths to compare. The paths can be:

* A single file or a directory containing library files:
    * File-to-file mode:             [file1] [file2]
    * Directory-to-directory mode:   [dir1] [dir2]
    * Single file (show diffs):      [file]
    * Single directory (show diffs): [dir]

If you set --repo, then the paths are interpreted as Git commits
(e.g. commit hash, branch name, or tag name) in that repository:

    * Commit-to-commit:              [commit1] [commit2]
    * Commit-to-working-copy:        [commit1]
    * HEAD-to-working-copy:          []

If kicad-cli is not in PATH, you can give its location by setting the KICAD_CLI environment variable.
""",
    )
    parser.add_argument(
        "path1",
        nargs="?",
        help="Old version to compare against. A .kicad_sym/.kicad_mod file, a library directory, "
        "or (with --repo) a Git commit.",
    )
    parser.add_argument(
        "path2",
        nargs="?",
        help="New version to compare. A .kicad_sym/.kicad_mod file, a library directory, "
        "or (with --repo) a Git commit.",
    )
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        help="Path to a local Git repository. Makes path1/path2 refer to Git commits or branches.",
    )
    parser.add_argument(
        "-g",
        "--glob",
        action="append",
        help="Only diff files matching the given glob (can be given multiple times).",
    )
    parser.add_argument(
        "-n",
        "--only-names",
        default="*",
        help="Only output symbols or footprints whose name matches the given glob",
    )
    parser.add_argument(
        "-u",
        "--unchanged",
        action="store_true",
        help="Also output unchanged symbols or footprints",
    )
    parser.add_argument(
        "-s",
        "--screenshot-dir",
        type=Path,
        help="Read (footprints) or write (symbols) screenshots generated with kicad-cli"
        + " to given directory instead of re-generating them on the fly.",
    )
    parser.add_argument(
        "-S",
        "--diff-svg-output-dir",
        type=Path,
        help="Write the diff A/B files to the given directory instead of a temporary directory.",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=1,
        help="Number of parallel jobs to run when rendering symbols or footprints. Default is 1, "
        "0 is use all available cores.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity. Can be given multiple times.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Root directory for the diff output. Each library is written to a "
        + "<library>.diff subdirectory inside it. If the path ends in .diff, "
        + "it is used directly as the output directory of a single library.",
    )
    parser.add_argument(
        "-O",
        "--open-result",
        action="store_true",
        help="Open the generated diff in a web browser after generating the diff.",
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
        if path.suffix.lower() not in (".kicad_mod", ".kicad_sym"):
            return False
        return file_matches_glob(path, args.glob)

    try:
        resolver = file_resolver.get_resolver(
            args.path1, args.path2, repo=args.repo, file_filter=filter_files
        )
    except ValueError as e:
        logging.error(str(e))
        sys.exit(2)

    meta = _build_meta(args)

    workers = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
    logging.info(f"Running with {workers} parallel jobs")

    html_diff = HTMLDiff(
        args.output,
        meta,
        args.only_names,
        changes_only=(not args.unchanged),
        screenshot_dir=args.screenshot_dir,
        diff_svg_output_dir=args.diff_svg_output_dir,
    )
    html_diff.max_workers = workers
    html_diff.diff_pairs(
        resolver.files,
        git_mode=isinstance(resolver, file_resolver.GitDiffResolver),
    )

    # Generate the top-level index.html
    if args.output is not None and args.output.suffix != ".diff":
        # Create the output directory if it does not exist (e.g. for a null diff)
        os.makedirs(args.output, exist_ok=True)
        index_html = render_index_html.generate_index_html(args.output, prefix="")

        index_file = args.output / "index.html"
        index_file.write_text(index_html, encoding="utf-8")

        logging.info("Generated index.html in %s", args.output)

    # Open the appropriate diff file in the web browser if requested.
    if args.open_result and args.output is not None:
        file_to_open = None
        if args.output.suffix != ".diff":
            file_to_open = args.output / "index.html"
        else:
            # Open the first diff file in the output directory
            diff_files = list(args.output.glob("*.html"))
            if diff_files:
                file_to_open = diff_files[0]

        if file_to_open is not None and file_to_open.is_file():
            logging.info("Opening %s in web browser", file_to_open)
            webbrowser.open(file_to_open.as_uri())
