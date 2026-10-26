#!/usr/bin/env python3
"""Thin CLI wrapper for merge request statistics.

This module delegates the heavy lifting to merge_request_stats.py and
lib_stats_helpers.py. It provides a small command line interface that
calls analyzeProjectMergeRequests and analyzeMergeRequests.
"""

from __future__ import annotations

import argparse
import os
from typing import Dict

from lib_stats_helpers import bcolors
from merge_request_stats import analyzeMergeRequests, analyzeProjectMergeRequests

# How it works:
# First, all merge requests for the given project are fetched from GitLab using the GitLab API.
# The fetched merge requests are then filtered based on their creation or merge dates to fit specific time ranges
#   (e.g., last year, last month).
# From these filtered lists, various statistics are computed,
#   such as total number of MRs, average time to merge, etc.
# These statistics are then printed to the console and are also exported to CSV files for further analysis.

# TODO / Idea list:
# * Add issue stats
# * Filter and Analytics for Authors and Mergers
# * Automatically generate a report (Markdown or PDF[preferred]) with the statistics and charts
# * Create Pipeline to run this periodically and update stats
# * Make some classes
# * Write a wiki page explaining usage
#


def load_project_ids(
    path_arg: str | None = None,
) -> tuple[Dict[str, str], Dict[str, str]]:
    """Load project id mappings from `project_ids.py` or the file given in path_arg.

    Supports the following variables inside `project_ids.py` (preferred order):
      - `major_projects` (dict)
      - `minor_projects` (dict)
      - `project_ids` (dict)  # legacy single dict

    Returns a tuple: (major_projects: Dict[str,str], minor_projects: Dict[str,str]).
    If only `project_ids` exists it will be returned as `major_projects` and
    `minor_projects` will be empty.
    """
    print(f"Loading project IDs from: {path_arg}")
    major = {}
    minor = {}
    try:
        import importlib.util

        if path_arg is None:
            spec = importlib.util.spec_from_file_location(
                "project_ids",
                os.path.join(os.path.dirname(__file__), "project_ids.py"),
            )
        else:
            spec = importlib.util.spec_from_file_location(
                "project_ids",
                path_arg,
            )
            print(spec)

        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            # Try preferred variable names first
            major = getattr(mod, "major_project_ids", None) or {}
            minor = getattr(mod, "minor_project_ids", None) or {}
            # Fallback to legacy single mapping
            if not major and hasattr(mod, "project_ids"):
                major = getattr(mod, "project_ids", {}) or {}
    except FileNotFoundError:
        pass
    except Exception:
        pass
    print(major, minor)
    return major, minor


def main() -> None:
    p = argparse.ArgumentParser(description="Generate GitLab MR statistics")
    p.add_argument("--project", help="Project ID or path", default=None)
    p.add_argument(
        "--idFile",
        help="Project ID file path, by default it looks for such a file in the location of the script(project_id.py)",
        default=None,
    )
    p.add_argument(
        "--token",
        help="GitLab token (or set GITLAB_TOKEN)",
        default=os.getenv("GITLAB_TOKEN"),
    )
    p.add_argument("--after", help="created_after ISO date", default=None)
    p.add_argument("--before", help="created_before ISO date", default=None)
    p.add_argument("--path", help="target path to store results", default=None)
    args = p.parse_args()

    if not args.token:
        print("GITLAB token not provided. Set GITLAB_TOKEN or pass --token.")
        args.token = ""

    id_file = None
    if args.idFile:
        id_file = os.path.abspath(args.idFile)

    if args.path:
        os.makedirs(args.path, exist_ok=True)
        os.chdir(args.path)

    merge_requests = []
    markdown_summary = ""

    if args.project:
        merge_requests, markdown_summary = analyzeProjectMergeRequests(
            args.project, "Parameter_Project", args.token, args.after, args.before
        )
    else:
        major_project_ids, minor_project_ids = load_project_ids(id_file)

        # Analyze Major projects
        if major_project_ids:
            for project_name, project_id in major_project_ids.items():
                print(
                    f"{bcolors.OKGREEN}{bcolors.BOLD}===== Analyzing Major Project: {project_name} ====={bcolors.ENDC}"
                )
                tmp_merge_requests, markdown_tmp = analyzeProjectMergeRequests(
                    project_id, project_name, args.token, args.after, args.before
                )
                merge_requests.extend(tmp_merge_requests)
                markdown_summary += markdown_tmp

        # Analyze Minor projects (no Total aggregation for minors)
        if minor_project_ids:
            for project_name, project_id in minor_project_ids.items():
                print(f"===== Analyzing Minor Project: {project_name} =====")
                tmp_merge_requests, markdown_tmp = analyzeProjectMergeRequests(
                    project_id, project_name, args.token, args.after, args.before
                )
                # Do not include minor projects in the Total aggregation
                # but still append summaries for per-project reporting
                markdown_summary += markdown_tmp
                markdown_summary += "<br>\nNot included in Total aggregation."

        # Produce Total aggregation only from Major projects
        print("===== Analyzing Total (Major Projects only) =====")
        os.makedirs("./Total", exist_ok=True)
        # Use merge_requests collected from major projects only
        markdown_total = analyzeMergeRequests("Total", merge_requests)
        markdown_summary = markdown_total + markdown_summary

    print("----- Final Summary -----")
    print(markdown_summary)
    with open("./shortMDSummery.md", mode="w", encoding="utf-8") as mdfile:
        mdfile.write(markdown_summary)


if __name__ == "__main__":
    main()
