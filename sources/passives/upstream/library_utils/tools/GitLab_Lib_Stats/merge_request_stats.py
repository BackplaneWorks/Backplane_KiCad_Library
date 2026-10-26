#!/usr/bin/env python3
"""Merge request fetching, filtering, statistics and analysis.

This module depends on `lib_stats_helpers` for parsing and time helpers.
"""

import csv
import os
import sys
from datetime import datetime, timedelta, timezone

import gitlab
import matplotlib.pyplot as plt
from lib_stats_helpers import (
    averageTimeFromSeconds,
    bcolors,
    maxTimeFromSeconds,
    medianTimeFromSeconds,
    minTimeFromSeconds,
    parseUtcTime,
    secondsToDays,
    secondsToHMS,
    secondsToHours,
    stdDevPopulationTimeFromSeconds,
    stdDevSampleTimeFromSeconds,
)

#
# GitLab API functions using python-gitlab
#


def getMergeRequests(project_id, token, created_after=None, created_before=None):
    """Fetch merge requests from GitLab for a given project ID."""
    gl = gitlab.Gitlab("https://gitlab.com", private_token=token, timeout=10)
    if len(token) > 0:
        gl.auth()

    if project_id is None or project_id == "":
        raise ValueError("Project ID must be provided.")

    # Fetch project with retries to handle transient API/network issues
    project = None
    max_attempts = 10
    proj_attempt = 0
    while proj_attempt < max_attempts:
        proj_attempt += 1
        try:
            project = gl.projects.get(project_id)
            break
        except gitlab.exceptions.GitlabGetError as e:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}Attempt {proj_attempt}/{max_attempts}"
                f" - Error getting project {project_id}: {e}{bcolors.ENDC}",
                file=sys.stderr,
            )
            if proj_attempt >= max_attempts:
                raise
            try:
                import time

                time.sleep(min(2 ** (proj_attempt - 1), 30))
            except Exception:
                # If sleep fails, continue immediately
                pass
        except Exception as e:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}Attempt {proj_attempt}/{max_attempts}"
                f" - Unexpected error getting project {project_id}: {e}{bcolors.ENDC}",
                file=sys.stderr,
            )
            if proj_attempt >= max_attempts:
                raise
            try:
                import time

                time.sleep(min(2 ** (proj_attempt - 1), 30))
            except Exception:
                # If sleep fails, continue immediately
                pass
    if project is None:
        # Shouldn't happen, but guard defensively
        raise RuntimeError(f"Failed to fetch project {project_id}")

    params = {
        "state": "all",
        "order_by": "created_at",
        "sort": "asc",
        "per_page": 100,
    }
    if created_after:
        params["created_after"] = created_after
    if created_before:
        params["created_before"] = created_before

    merge_requests = []

    list_attempt = 0
    # Exponential backoff: 1s, 2s, 4s, ... (capped)
    while list_attempt < max_attempts:
        list_attempt += 1
        try:
            merge_requests = [
                mr
                for mr in project.mergerequests.list(
                    iterator=True, **params, timeout=30.0
                )
            ]
            # success
            break
        except gitlab.exceptions.GitlabGetError as e:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}Attempt {list_attempt}/{max_attempts}"
                f" - Error getting merge requests: {e}{bcolors.ENDC}",
                file=sys.stderr,
            )
            if list_attempt >= max_attempts:
                # re-raise the last exception after exhausting attempts
                raise
            # backoff before retrying
            try:
                sleep_seconds = min(2 ** (list_attempt - 1), 30)
                import time

                time.sleep(sleep_seconds)
            except Exception:
                # If sleep fails for any reason, continue immediately to retry
                pass
        except Exception as e:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}Attempt {list_attempt}/{max_attempts}"
                f" - Unexpected error getting merge requests: {e}{bcolors.ENDC}",
                file=sys.stderr,
            )
            if list_attempt >= max_attempts:
                # re-raise the last exception after exhausting attempts
                raise
            # backoff before retrying
            try:
                sleep_seconds = min(2 ** (list_attempt - 1), 30)
                import time

                time.sleep(sleep_seconds)
            except Exception:
                # If sleep fails for any reason, continue immediately to retry
                pass

    return merge_requests


#
# Export Functions
#

# CSV Export Functions


def exportMergeRequestsToCSV(merge_requests, filename):
    """Export a list of merge requests to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "IID",
            "Title",
            "State",
            "Author",
            "Created At",
            "Merged At",
            "URL",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for mr in merge_requests:
            writer.writerow(
                {
                    "IID": mr.iid,
                    "Title": mr.title,
                    "State": mr.state,
                    "Author": getattr(mr, "author", {}).get("username", "n/a"),
                    "Created At": mr.created_at,
                    "Merged At": getattr(mr, "merged_at", "n/a"),
                    "URL": mr.web_url,
                }
            )


def exportMergeRequestStatsToCSV(statistics_list, file_name, field_names, project_name):
    """Export merge request statistics to a CSV file."""

    os.makedirs(f"./{project_name}", exist_ok=True)

    with open(
        f"./{project_name}/{file_name}.csv",
        mode="w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for statistic_row in statistics_list:

            row = {}

            for field in field_names:
                row[field] = statistic_row.get(field, "")

            writer.writerow(row)


# Plotting Functions


def plotStatListDataField(
    stat_list,
    data_field,
    title,
    ylabel,
    project_name,
    file_prefix="",
    stdDeviationField=None,
    stdDeviationMultiplier=2,
):
    """Plot merge request statistics over time for a specified time field. Optionally include standard deviation bands.
    Default Multiplier is 2 for ~95% confidence interval."""

    x = []
    y = []

    for stat in stat_list:
        year = stat["year"]
        month = stat.get("month", 1)  # Default to January if month not present
        x.append(datetime(year, month, 1))
        y.append(stat[data_field])

    plt.figure(figsize=(10, 5))
    plt.plot(x, y, marker="o", color="blue")
    if stdDeviationField:
        plt.errorbar(
            x,
            y,
            yerr=[
                stdDeviationMultiplier * stat[stdDeviationField] for stat in stat_list
            ],
            fmt="o",
            ecolor="blue",
        )
        # , alpha=0.5, label=f'±{stdDeviationMultiplier} Std Dev', uplims=True, lolims=True
        # y_upper = [val + stdDeviationMultiplier * stat[stdDeviationField] for val, stat in zip(y, stat_list)]
        # y_lower = [max(0, val - stdDeviationMultiplier * stat[stdDeviationField]) for val, stat in zip(y, stat_list)]
        # plt.fill_between(x, y_lower, y_upper, color='gray', alpha=0.3, label=f'±{stdDeviationMultiplier} Std Dev')
        # plt.legend()
    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    # plt.show()
    os.makedirs(f"./{project_name}/plot", exist_ok=True)
    os.makedirs(f"./{project_name}/plot/png", exist_ok=True)
    os.makedirs(f"./{project_name}/plot/svg", exist_ok=True)
    os.makedirs(f"./{project_name}/plot/pdf", exist_ok=True)
    plt.savefig(f"./{project_name}/plot/png/{file_prefix}_{data_field}.png")
    plt.savefig(f"./{project_name}/plot/svg/{file_prefix}_{data_field}.svg")
    plt.savefig(f"./{project_name}/plot/pdf/{file_prefix}_{data_field}.pdf")
    plt.close()


#
# Filter Functions
#


# Filters based on created_at
def filterMergeRequestsByCreatedAtYear(merge_requests, year):
    filtered_mrs = []
    for mr in merge_requests:
        created_at = parseUtcTime(mr.created_at)
        if created_at.year == year:
            filtered_mrs.append(mr)
    return filtered_mrs


def filterMergeRequestsByCreatedAtMonth(merge_requests, year, month):
    filtered_mrs = []
    for mr in merge_requests:
        created_at = parseUtcTime(mr.created_at)
        if created_at.year == year and created_at.month == month:
            filtered_mrs.append(mr)
    return filtered_mrs


def filterMergeRequestsByCreatedAtTimeRange(merge_requests, start_date, end_date):
    filtered_mrs = []
    for mr in merge_requests:
        created_at = parseUtcTime(mr.created_at)
        if start_date <= created_at <= end_date:
            filtered_mrs.append(mr)
    return filtered_mrs


# Filters based on merged_at (only include MRs where merged_at is set)
def filterMergeRequestsByMergedAtYear(merge_requests, year):
    filtered_mrs = []
    for mr in merge_requests:
        if getattr(mr, "merged_at", None) is None:
            continue
        merged_at = parseUtcTime(mr.merged_at)
        if merged_at.year == year:
            filtered_mrs.append(mr)
    return filtered_mrs


def filterMergeRequestsByMergedAtMonth(merge_requests, year, month):
    filtered_mrs = []
    for mr in merge_requests:
        if getattr(mr, "merged_at", None) is None:
            continue
        merged_at = parseUtcTime(mr.merged_at)
        if merged_at.year == year and merged_at.month == month:
            filtered_mrs.append(mr)
    return filtered_mrs


def filterMergeRequestsByMergedAtTimeRange(merge_requests, start_date, end_date):
    filtered_mrs = []
    for mr in merge_requests:
        if getattr(mr, "merged_at", None) is None:
            continue
        merged_at = parseUtcTime(mr.merged_at)
        if start_date <= merged_at <= end_date:
            filtered_mrs.append(mr)
    return filtered_mrs


# Filters based on closed_at (only include MRs where closed_at is set)
def filterMergeRequestsByClosedAtYear(merge_requests, year):
    filtered_mrs = []
    for mr in merge_requests:
        if getattr(mr, "closed_at", None) is None:
            continue
        closed_at = parseUtcTime(mr.closed_at)
        if closed_at.year == year:
            filtered_mrs.append(mr)
    return filtered_mrs


def filterMergeRequestsByClosedAtMonth(merge_requests, year, month):
    filtered_mrs = []
    for mr in merge_requests:
        if getattr(mr, "closed_at", None) is None:
            continue
        closed_at = parseUtcTime(mr.closed_at)
        if closed_at.year == year and closed_at.month == month:
            filtered_mrs.append(mr)
    return filtered_mrs


def filterMergeRequestsByClosedAtTimeRange(merge_requests, start_date, end_date):
    filtered_mrs = []
    for mr in merge_requests:
        if getattr(mr, "closed_at", None) is None:
            continue
        closed_at = parseUtcTime(mr.closed_at)
        if start_date <= closed_at <= end_date:
            filtered_mrs.append(mr)
    return filtered_mrs


# Filters open MRs
def filterMergeRequestsOpenFinished(merge_requests):
    filtered_open_mrs = []
    filtered_finished_mrs = []
    filtered_merged_mrs = []
    filtered_closed_mrs = []
    for mr in merge_requests:
        if getattr(mr, "state", None) is None:
            continue
        state = mr.state
        if state == "opened":
            filtered_open_mrs.append(mr)
        else:
            filtered_finished_mrs.append(mr)

        if state == "merged":
            filtered_merged_mrs.append(mr)

        if state == "closed":
            filtered_closed_mrs.append(mr)
    return (
        filtered_open_mrs,
        filtered_finished_mrs,
        filtered_merged_mrs,
        filtered_closed_mrs,
    )


#
# Grouping Functions
#


def groupMergeRequestsByDateFieldMonth(merge_requests, date_field):
    """Group merge requests by year and month based on a specified date field."""
    grouped = {}
    for mr in merge_requests:
        date_str = getattr(mr, date_field, None)
        if date_str is None:
            continue
        date = parseUtcTime(date_str)
        year_month = (date.year, date.month)
        if year_month not in grouped:
            grouped[year_month] = []
        grouped[year_month].append(mr)
    grouped = dict(sorted(grouped.items()))
    return grouped


def groupMergeRequestsByDateFieldYear(merge_requests, date_field):
    """Group merge requests by year based on a specified date field."""
    grouped = {}
    for mr in merge_requests:
        date_str = getattr(mr, date_field, None)
        if date_str is None:
            continue
        date = parseUtcTime(date_str)
        year = date.year
        if year not in grouped:
            grouped[year] = []
        grouped[year].append(mr)
    grouped = dict(sorted(grouped.items()))
    return grouped


#
# Statistics Functions
#


def mergeRequestStats(merge_requests):
    """Compute statistics for a list of merge requests."""
    stats = {
        "total": len(merge_requests),
        "merged": 0,
        "open": 0,
        "closed": 0,
        "finished": 0,
        "percentageMerged": 0,
        "percentageClosed": 0,
        "percentageFinished": 0,
        # Statistics on time to merge
        "avgTimeToMergeSeconds": 0,
        "avgTimeToMergeHours": 0,
        "avgTimeToMergeDays": 0,
        "avgTimeToMergeDHMS": "",
        "medianTimeToMergeSeconds": 0,
        "medianTimeToMergeHours": 0,
        "medianTimeToMergeDays": 0,
        "medianTimeToMergeDHMS": "",
        "maxTimeToMergeSeconds": 0,
        "maxTimeToMergeHours": 0,
        "maxTimeToMergeDays": 0,
        "maxTimeToMergeDHMS": "",
        "minTimeToMergeSeconds": 0,
        "minTimeToMergeHours": 0,
        "minTimeToMergeDays": 0,
        "minTimeToMergeDHMS": "",
        "stdDevPopulationTimeToMergeSeconds": 0,
        "stdDevPopulationTimeToMergeHours": 0,
        "stdDevPopulationTimeToMergeDays": 0,
        "stdDevPopulationTimeToMergeDHMS": "",
        "stdDevSampleTimeToMergeSeconds": 0,
        "stdDevSampleTimeToMergeHours": 0,
        "stdDevSampleTimeToMergeDays": 0,
        "stdDevSampleTimeToMergeDHMS": "",
        # Statistics on time to close
        "avgTimeToCloseSeconds": 0,
        "avgTimeToCloseHours": 0,
        "avgTimeToCloseDays": 0,
        "avgTimeToCloseDHMS": "",
        "medianTimeToCloseSeconds": 0,
        "medianTimeToCloseHours": 0,
        "medianTimeToCloseDays": 0,
        "medianTimeToCloseDHMS": "",
        "maxTimeToCloseSeconds": 0,
        "maxTimeToCloseHours": 0,
        "maxTimeToCloseDays": 0,
        "maxTimeToCloseDHMS": "",
        "minTimeToCloseSeconds": 0,
        "minTimeToCloseHours": 0,
        "minTimeToCloseDays": 0,
        "minTimeToCloseDHMS": "",
        "stdDevPopulationTimeToCloseSeconds": 0,
        "stdDevPopulationTimeToCloseHours": 0,
        "stdDevPopulationTimeToCloseDays": 0,
        "stdDevPopulationTimeToCloseDHMS": "",
        "stdDevSampleTimeToCloseSeconds": 0,
        "stdDevSampleTimeToCloseHours": 0,
        "stdDevSampleTimeToCloseDays": 0,
        "stdDevSampleTimeToCloseDHMS": "",
    }

    timeToMergeSeconds = []
    timeToCloseSeconds = []

    for mr in merge_requests:
        state = mr.state
        if state == "merged":
            stats["merged"] += 1
            stats["finished"] += 1
            if mr.merged_at is not None and mr.created_at is not None:
                timeToMergeSeconds.append(
                    (
                        parseUtcTime(mr.merged_at) - parseUtcTime(mr.created_at)
                    ).total_seconds()
                )
        elif state == "opened":
            stats["open"] += 1
        elif state == "closed":
            stats["closed"] += 1
            stats["finished"] += 1
            if mr.closed_at is not None and mr.created_at is not None:
                timeToCloseSeconds.append(
                    (
                        parseUtcTime(mr.closed_at) - parseUtcTime(mr.created_at)
                    ).total_seconds()
                )

    if stats["total"] > 0:
        percentage_merged = (stats["merged"] / stats["total"]) * 100
        stats["percentageMerged"] = percentage_merged
        percentage_closed = (stats["closed"] / stats["total"]) * 100
        stats["percentageClosed"] = percentage_closed
        percentage_finished = (
            (stats["merged"] + stats["closed"]) / stats["total"]
        ) * 100
        stats["percentageFinished"] = percentage_finished

    if len(timeToMergeSeconds) > 0:
        stats["avgTimeToMergeSeconds"] = averageTimeFromSeconds(timeToMergeSeconds)
        stats["avgTimeToMergeHours"] = secondsToHours(stats["avgTimeToMergeSeconds"])
        stats["avgTimeToMergeDays"] = secondsToDays(stats["avgTimeToMergeSeconds"])
        stats["avgTimeToMergeDHMS"] = secondsToHMS(stats["avgTimeToMergeSeconds"])
        stats["medianTimeToMergeSeconds"] = medianTimeFromSeconds(timeToMergeSeconds)
        stats["medianTimeToMergeHours"] = secondsToHours(
            stats["medianTimeToMergeSeconds"]
        )
        stats["medianTimeToMergeDays"] = secondsToDays(
            stats["medianTimeToMergeSeconds"]
        )
        stats["medianTimeToMergeDHMS"] = secondsToHMS(stats["medianTimeToMergeSeconds"])
        stats["maxTimeToMergeSeconds"] = maxTimeFromSeconds(timeToMergeSeconds)
        stats["maxTimeToMergeHours"] = secondsToHours(stats["maxTimeToMergeSeconds"])
        stats["maxTimeToMergeDays"] = secondsToDays(stats["maxTimeToMergeSeconds"])
        stats["maxTimeToMergeDHMS"] = secondsToHMS(stats["maxTimeToMergeSeconds"])
        stats["minTimeToMergeSeconds"] = minTimeFromSeconds(timeToMergeSeconds)
        stats["minTimeToMergeHours"] = secondsToHours(stats["minTimeToMergeSeconds"])
        stats["minTimeToMergeDays"] = secondsToDays(stats["minTimeToMergeSeconds"])
        stats["minTimeToMergeDHMS"] = secondsToHMS(stats["minTimeToMergeSeconds"])
        stats["stdDevPopulationTimeToMergeSeconds"] = stdDevPopulationTimeFromSeconds(
            timeToMergeSeconds
        )
        stats["stdDevPopulationTimeToMergeHours"] = secondsToHours(
            stats["stdDevPopulationTimeToMergeSeconds"]
        )
        stats["stdDevPopulationTimeToMergeDays"] = secondsToDays(
            stats["stdDevPopulationTimeToMergeSeconds"]
        )
        stats["stdDevPopulationTimeToMergeDHMS"] = secondsToHMS(
            stats["stdDevPopulationTimeToMergeSeconds"]
        )
        stats["stdDevSampleTimeToMergeSeconds"] = stdDevSampleTimeFromSeconds(
            timeToMergeSeconds
        )
        stats["stdDevSampleTimeToMergeHours"] = secondsToHours(
            stats["stdDevSampleTimeToMergeSeconds"]
        )
        stats["stdDevSampleTimeToMergeDays"] = secondsToDays(
            stats["stdDevSampleTimeToMergeSeconds"]
        )
        stats["stdDevSampleTimeToMergeDHMS"] = secondsToHMS(
            stats["stdDevSampleTimeToMergeSeconds"]
        )

    if len(timeToCloseSeconds) > 0:
        stats["avgTimeToCloseSeconds"] = averageTimeFromSeconds(timeToCloseSeconds)
        stats["avgTimeToCloseHours"] = secondsToHours(stats["avgTimeToCloseSeconds"])
        stats["avgTimeToCloseDays"] = secondsToDays(stats["avgTimeToCloseSeconds"])
        stats["avgTimeToCloseDHMS"] = secondsToHMS(stats["avgTimeToCloseSeconds"])
        stats["medianTimeToCloseSeconds"] = medianTimeFromSeconds(timeToCloseSeconds)
        stats["medianTimeToCloseHours"] = secondsToHours(
            stats["medianTimeToCloseSeconds"]
        )
        stats["medianTimeToCloseDays"] = secondsToDays(
            stats["medianTimeToCloseSeconds"]
        )
        stats["medianTimeToCloseDHMS"] = secondsToHMS(stats["medianTimeToCloseSeconds"])
        stats["maxTimeToCloseSeconds"] = maxTimeFromSeconds(timeToCloseSeconds)
        stats["maxTimeToCloseHours"] = secondsToHours(stats["maxTimeToCloseSeconds"])
        stats["maxTimeToCloseDays"] = secondsToDays(stats["maxTimeToCloseSeconds"])
        stats["maxTimeToCloseDHMS"] = secondsToHMS(stats["maxTimeToCloseSeconds"])
        stats["minTimeToCloseSeconds"] = minTimeFromSeconds(timeToCloseSeconds)
        stats["minTimeToCloseHours"] = secondsToHours(stats["minTimeToCloseSeconds"])
        stats["minTimeToCloseDays"] = secondsToDays(stats["minTimeToCloseSeconds"])
        stats["minTimeToCloseDHMS"] = secondsToHMS(stats["minTimeToCloseSeconds"])
        stats["stdDevPopulationTimeToCloseSeconds"] = stdDevPopulationTimeFromSeconds(
            timeToCloseSeconds
        )
        stats["stdDevPopulationTimeToCloseHours"] = secondsToHours(
            stats["stdDevPopulationTimeToCloseSeconds"]
        )
        stats["stdDevPopulationTimeToCloseDays"] = secondsToDays(
            stats["stdDevPopulationTimeToCloseSeconds"]
        )
        stats["stdDevPopulationTimeToCloseDHMS"] = secondsToHMS(
            stats["stdDevPopulationTimeToCloseSeconds"]
        )
        stats["stdDevSampleTimeToCloseSeconds"] = stdDevSampleTimeFromSeconds(
            timeToCloseSeconds
        )
        stats["stdDevSampleTimeToCloseHours"] = secondsToHours(
            stats["stdDevSampleTimeToCloseSeconds"]
        )
        stats["stdDevSampleTimeToCloseDays"] = secondsToDays(
            stats["stdDevSampleTimeToCloseSeconds"]
        )
        stats["stdDevSampleTimeToCloseDHMS"] = secondsToHMS(
            stats["stdDevSampleTimeToCloseSeconds"]
        )

    return stats


def getStatListTimeFieldMonthly(merge_requests, time_field):
    stat_list = []

    for (
        grouped_year,
        grouped_month,
    ), mrs_in_month in groupMergeRequestsByDateFieldMonth(
        merge_requests, time_field
    ).items():
        stats = mergeRequestStats(mrs_in_month)
        stats["year"] = grouped_year
        stats["month"] = grouped_month
        stat_list.append(stats)

    print(len(stat_list), "monthly stats found.")

    return stat_list


def getStatListTimeFieldYearly(merge_requests, time_field):
    stat_list = []

    for grouped_year, mrs_in_year in groupMergeRequestsByDateFieldYear(
        merge_requests, time_field
    ).items():
        stats = mergeRequestStats(mrs_in_year)
        stats["year"] = grouped_year
        stat_list.append(stats)

    print(len(stat_list), "yearly stats found.")

    return stat_list


#
# Summary Functions
#

# Partial Summary's


# Created At
def summaryPlotMergeRequestsByCreatedAt(stat_list, project_name, file_prefix):
    plotStatListDataField(
        stat_list,
        "avgTimeToMergeDays",  # Field to plot
        "Average Time to Merge Over Time grouped by Creation Date",  # Tile
        "Average Time to Merge (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
        "stdDevSampleTimeToMergeDays",  # Standard Deviation field
        2,  # Std.Dev. Multiplier
    )
    plotStatListDataField(
        stat_list,
        "medianTimeToMergeDays",  # Field to plot
        "Median Time to Merge Over Time grouped by Creation Date",  # Tile
        "Median Time to Merge (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )

    plotStatListDataField(
        stat_list,
        "avgTimeToCloseDays",  # Field to plot
        "Average Time to Close Over Time grouped by Creation Date",  # Tile
        "Average Time to Close (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
        "stdDevSampleTimeToCloseDays",  # Standard Deviation field
        2,  # Std.Dev. Multiplier
    )
    plotStatListDataField(
        stat_list,
        "medianTimeToCloseDays",  # Field to plot
        "Median Time to Close Over Time grouped by Creation Date",  # Tile
        "Median Time to Close (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )

    plotStatListDataField(
        stat_list,
        "total",  # Field to plot
        "Total number of created Merge Requests, grouped by Creation Date",  # Tile
        "Merge Requests",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )


# Monthly
def summaryCSVMergeRequestsByCreatedAtMonthly(stat_list, project_name):

    os.makedirs(f"./{project_name}", exist_ok=True)

    field_names = [
        "year",
        "month",
        "total",
        "merged",
        "open",
        "closed",
        "finished",
        "percentageMerged",
        "percentageClosed",
        "percentageFinished",
        "avgTimeToMergeSeconds",
        "avgTimeToMergeDHMS",
        "medianTimeToMergeSeconds",
        "medianTimeToMergeDHMS",
        "maxTimeToMergeSeconds",
        "maxTimeToMergeDHMS",
        "minTimeToMergeSeconds",
        "minTimeToMergeDHMS",
        "stdDevPopulationTimeToMergeSeconds",
        "stdDevPopulationTimeToMergeDHMS",
        "stdDevSampleTimeToMergeSeconds",
        "stdDevSampleTimeToMergeDHMS",
        "avgTimeToCloseSeconds",
        "avgTimeToCloseDHMS",
        "medianTimeToCloseSeconds",
        "medianTimeToCloseDHMS",
        "maxTimeToCloseSeconds",
        "maxTimeToCloseDHMS",
        "minTimeToCloseSeconds",
        "minTimeToCloseDHMS",
        "stdDevPopulationTimeToCloseSeconds",
        "stdDevPopulationTimeToCloseDHMS",
        "stdDevSampleTimeToCloseSeconds",
        "stdDevSampleTimeToCloseDHMS",
    ]

    exportMergeRequestStatsToCSV(
        stat_list, "mrStatsGroupedByCreatedAtMonthly", field_names, project_name
    )

    return stat_list


# Yearly
def summaryCSVMergeRequestsByCreatedAtYearly(stat_list, project_name):

    os.makedirs(f"./{project_name}", exist_ok=True)

    field_names = [
        "year",
        "total",
        "merged",
        "open",
        "closed",
        "finished",
        "percentageMerged",
        "percentageClosed",
        "percentageFinished",
        "avgTimeToMergeSeconds",
        "avgTimeToMergeDHMS",
        "medianTimeToMergeSeconds",
        "medianTimeToMergeDHMS",
        "maxTimeToMergeSeconds",
        "maxTimeToMergeDHMS",
        "minTimeToMergeSeconds",
        "minTimeToMergeDHMS",
        "stdDevPopulationTimeToMergeSeconds",
        "stdDevPopulationTimeToMergeDHMS",
        "stdDevSampleTimeToMergeSeconds",
        "stdDevSampleTimeToMergeDHMS",
        "avgTimeToCloseSeconds",
        "avgTimeToCloseDHMS",
        "medianTimeToCloseSeconds",
        "medianTimeToCloseDHMS",
        "maxTimeToCloseSeconds",
        "maxTimeToCloseDHMS",
        "minTimeToCloseSeconds",
        "minTimeToCloseDHMS",
        "stdDevPopulationTimeToCloseSeconds",
        "stdDevPopulationTimeToCloseDHMS",
        "stdDevSampleTimeToCloseSeconds",
        "stdDevSampleTimeToCloseDHMS",
    ]

    exportMergeRequestStatsToCSV(
        stat_list, "mrStatsGroupedByCreatedAtYearly", field_names, project_name
    )

    return stat_list


# Last n days
def summaryMDMergeRequestsByCreatedAtLastNDays(merge_requests, project_name, n_days):
    end_date = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_date = end_date - timedelta(days=n_days)
    filtered_mrs = filterMergeRequestsByCreatedAtTimeRange(
        merge_requests, start_date, end_date
    )
    stats = mergeRequestStats(filtered_mrs)

    markdown_multi_line = (
        f"## Merge Request Summary for the Last {n_days} Days (Created At)\n\n"
    )
    markdown_multi_line += f"- Total Merge Requests Created: {stats['total']}\n"
    markdown_multi_line += (
        f"- Of those Merged: {stats['merged']} ({stats['percentageMerged']:.2f}%)\n"
    )
    markdown_multi_line += f"- Of those Open: {stats['open']}\n"
    markdown_multi_line += (
        f"- Of those Closed: {stats['closed']} ({stats['percentageClosed']:.2f}%)\n"
    )
    markdown_multi_line += f"- Of those Finished: {stats['finished']} ({stats['percentageFinished']:.2f}%)\n"
    markdown_multi_line += f"- Average Time to Merge: {stats['avgTimeToMergeDHMS']}\n"
    markdown_multi_line += f"- Average Time to Close: {stats['avgTimeToCloseDHMS']}\n"
    markdown_multi_line += "\n"

    markdown_single_line = f"Created: {stats['total']}; "

    with open(
        f"./{project_name}/mrSummaryLast{n_days}Days.md", mode="a", encoding="utf-8"
    ) as mdfile:
        mdfile.write(markdown_multi_line)

    print(f"Markdown summary for last {n_days} days (created_at) created.")

    return markdown_multi_line, markdown_single_line, stats


# -------------------------------------------------------------------------------------------------
# Merged At
def summaryPlotMergeRequestsByMergedAt(stat_list, project_name, file_prefix):
    plotStatListDataField(
        stat_list,
        "avgTimeToMergeDays",  # Field to plot
        "Average Time to Merge Over Time grouped by Merge Date",  # Tile
        "Average Time to Merge (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
        "stdDevSampleTimeToMergeDays",  # Standard Deviation field
        2,  # Std.Dev. Multiplier
    )
    plotStatListDataField(
        stat_list,
        "medianTimeToMergeDays",  # Field to plot
        "Median Time to Merge Over Time grouped by Merge Date",  # Tile
        "Median Time to Merge (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )

    plotStatListDataField(
        stat_list,
        "total",  # Field to plot
        "Total number of merged Merge Requests, grouped by Merge Date",  # Tile
        "Merge Requests",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )


# Monthly
def summaryCSVMergeRequestsByMergedAtMonthly(stat_list, project_name):

    os.makedirs(f"./{project_name}", exist_ok=True)

    field_names = [
        "year",
        "month",
        "total",
        "merged",
        "percentageMerged",
        "avgTimeToMergeSeconds",
        "avgTimeToMergeDHMS",
        "medianTimeToMergeSeconds",
        "medianTimeToMergeDHMS",
        "maxTimeToMergeSeconds",
        "maxTimeToMergeDHMS",
        "minTimeToMergeSeconds",
        "minTimeToMergeDHMS",
        "stdDevPopulationTimeToMergeSeconds",
        "stdDevPopulationTimeToMergeDHMS",
        "stdDevSampleTimeToMergeSeconds",
        "stdDevSampleTimeToMergeDHMS",
    ]

    exportMergeRequestStatsToCSV(
        stat_list, "mrStatsGroupedByMergedAtMonthly", field_names, project_name
    )

    return stat_list


# Yearly
def summaryCSVMergeRequestsByMergedAtYearly(stat_list, project_name):
    os.makedirs(f"./{project_name}", exist_ok=True)

    field_names = [
        "year",
        "total",
        "merged",
        "open",
        "closed",
        "finished",
        "percentageMerged",
        "percentageClosed",
        "percentageFinished",
        "avgTimeToMergeSeconds",
        "avgTimeToMergeDHMS",
        "medianTimeToMergeSeconds",
        "medianTimeToMergeDHMS",
        "maxTimeToMergeSeconds",
        "maxTimeToMergeDHMS",
        "minTimeToMergeSeconds",
        "minTimeToMergeDHMS",
        "stdDevPopulationTimeToMergeSeconds",
        "stdDevPopulationTimeToMergeDHMS",
        "stdDevSampleTimeToMergeSeconds",
        "stdDevSampleTimeToMergeDHMS",
    ]

    exportMergeRequestStatsToCSV(
        stat_list, "mrStatsGroupedByMergedAtYearly", field_names, project_name
    )

    return stat_list


# Last n days
def summaryMDMergeRequestsByMergedAtLastNDays(merge_requests, project_name, n_days):
    end_date = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_date = end_date - timedelta(days=n_days)
    filtered_mrs = filterMergeRequestsByMergedAtTimeRange(
        merge_requests, start_date, end_date
    )
    stats = mergeRequestStats(filtered_mrs)

    markdown_multi_line = (
        f"## Merge Request Summary for the Last {n_days} Days (Merged At)\n\n"
    )
    markdown_multi_line += f"- Total Merge Requests Merged: {stats['total']}\n"
    markdown_multi_line += f"- Average Time to Merge: {stats['avgTimeToMergeDHMS']}\n"
    markdown_multi_line += "\n"

    markdown_single_line = f"Merged: {stats['total']}; "

    with open(
        f"./{project_name}/mrSummaryLast{n_days}Days.md", mode="a", encoding="utf-8"
    ) as mdfile:
        mdfile.write(markdown_multi_line)

    print(f"Markdown summary for last {n_days} days (merged_at) created.")

    return markdown_multi_line, markdown_single_line, stats


# -------------------------------------------------------------------------------------------------
# Closed At
def summaryPlotMergeRequestsByClosedAt(stat_list, project_name, file_prefix):

    plotStatListDataField(
        stat_list,
        "avgTimeToCloseDays",  # Field to plot
        "Average Time to Close Over Time grouped by Closing Date",  # Tile
        "Average Time to Close (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
        "stdDevSampleTimeToCloseDays",  # Standard Deviation field
        2,  # Std.Dev. Multiplier
    )
    plotStatListDataField(
        stat_list,
        "medianTimeToCloseDays",  # Field to plot
        "Median Time to Close Over Time grouped by Closing Date",  # Tile
        "Median Time to Close (days)",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )

    plotStatListDataField(
        stat_list,
        "total",  # Field to plot
        "Total number of created Merge Requests, grouped by Closing Date",  # Tile
        "Merge Requests",  # Y-axis label
        project_name,  # Project name for directory
        file_prefix,  # File prefix
    )


# Monthly
def summaryCSVMergeRequestsByClosedAtMonthly(stat_list, project_name):

    os.makedirs(f"./{project_name}", exist_ok=True)

    field_names = [
        "year",
        "month",
        "total",
        "closed",
        "percentageClosed",
        "avgTimeToCloseSeconds",
        "avgTimeToCloseDHMS",
        "medianTimeToCloseSeconds",
        "medianTimeToCloseDHMS",
        "maxTimeToCloseSeconds",
        "maxTimeToCloseDHMS",
        "minTimeToCloseSeconds",
        "minTimeToCloseDHMS",
        "stdDevPopulationTimeToCloseSeconds",
        "stdDevPopulationTimeToCloseDHMS",
        "stdDevSampleTimeToCloseSeconds",
        "stdDevSampleTimeToCloseDHMS",
    ]

    exportMergeRequestStatsToCSV(
        stat_list, "mrStatsGroupedByClosedAtMonthly", field_names, project_name
    )

    return stat_list


# Yearly
def summaryCSVMergeRequestsByClosedAtYearly(stat_list, project_name):

    os.makedirs(f"./{project_name}", exist_ok=True)

    field_names = [
        "year",
        "total",
        "closed",
        "percentageClosed",
        "avgTimeToCloseSeconds",
        "avgTimeToCloseDHMS",
        "medianTimeToCloseSeconds",
        "medianTimeToCloseDHMS",
        "maxTimeToCloseSeconds",
        "maxTimeToCloseDHMS",
        "minTimeToCloseSeconds",
        "minTimeToCloseDHMS",
        "stdDevPopulationTimeToCloseSeconds",
        "stdDevPopulationTimeToCloseDHMS",
        "stdDevSampleTimeToCloseSeconds",
        "stdDevSampleTimeToCloseDHMS",
    ]

    exportMergeRequestStatsToCSV(
        stat_list, "mrStatsGroupedByClosedAtYearly", field_names, project_name
    )

    return stat_list


# Last n days
def summaryMDMergeRequestsByClosedAtLastNDays(merge_requests, project_name, n_days):
    end_date = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_date = end_date - timedelta(days=n_days)
    filtered_mrs = filterMergeRequestsByClosedAtTimeRange(
        merge_requests, start_date, end_date
    )
    stats = mergeRequestStats(filtered_mrs)

    markdown_multi_line = (
        f"## Merge Request Summary for the Last {n_days} Days (Closed At)\n\n"
    )
    markdown_multi_line += f"- Total Merge Requests: {stats['total']}\n"
    markdown_multi_line += f"- Average Time to Close: {stats['avgTimeToCloseDHMS']}\n"
    markdown_multi_line += "\n"

    markdown_single_line = f"Closed: {stats['total']}; "

    with open(
        f"./{project_name}/mrSummaryLast{n_days}Days.md", mode="a", encoding="utf-8"
    ) as mdfile:
        mdfile.write(markdown_multi_line)

    print(f"Markdown summary for last {n_days} days (closed_at) created.")

    return markdown_multi_line, markdown_single_line, stats


# -------------------------------------------------------------------------------------------------
# Total Open and Finished
def summaryMDMergeRequestsOpenFinished(merge_requests, project_name):
    (
        filtered_open_mrs,
        filtered_finished_mrs,
        filtered_merged_mrs,
        filtered_closed_mrs,
    ) = filterMergeRequestsOpenFinished(merge_requests)

    markdown_multi_line = (
        "## Merge Request Summary Open and Finished(Merged or Closed)\n\n"
    )
    markdown_multi_line += f"- Total Merge Requests: {len(filtered_open_mrs) + len(filtered_finished_mrs)}\n"
    markdown_multi_line += f"- Of those Open: {len(filtered_open_mrs)}\n"
    markdown_multi_line += f"- Of those Merged: {len(filtered_merged_mrs)}\n"
    markdown_multi_line += f"- Of those Closed: {len(filtered_closed_mrs)}\n"
    markdown_multi_line += f"- Of those Finished: {len(filtered_finished_mrs)}\n"
    markdown_multi_line += "\n"

    markdown_single_line = (
        f"Total: {len(filtered_open_mrs) + len(filtered_finished_mrs)}; "
        f"Open: {len(filtered_open_mrs)};"
        f" Merged: {len(filtered_merged_mrs)}; "
        f"Closed: {len(filtered_closed_mrs)}; "
        f"Finished {len(filtered_finished_mrs)}; "
    )

    with open(
        f"./{project_name}/mrSummaryOpenFinished.md", mode="a", encoding="utf-8"
    ) as mdfile:
        mdfile.write(markdown_multi_line)

    print("Markdown summary for open and finished created.")

    return markdown_multi_line, markdown_single_line


def analyzeProjectMergeRequests(
    project_id, project_name, token, created_after=None, created_before=None
):
    markdown_summary = ""

    os.makedirs(f"./{project_name}", exist_ok=True)

    print("Fetching merge requests for project:", project_id, "/", project_name)

    merge_requests = getMergeRequests(project_id, token, created_after, created_before)
    print(len(merge_requests), "merge requests found and saved.")

    exportMergeRequestsToCSV(merge_requests, f"./{project_name}/merge_requests.csv")
    print("Merge requests exported to merge_requests.csv")

    markdown_summary = analyzeMergeRequests(project_name, merge_requests)

    return merge_requests, markdown_summary


def analyzeMergeRequests(project_name, merge_requests):
    markdown_summary = ""

    print(f"----- Analyse {project_name} Merge Requests -----")

    print("----- Open Finished Filters -----")
    markdown_multi_line_open_finished, markdown_single_line_open_finished = (
        summaryMDMergeRequestsOpenFinished(merge_requests, project_name)
    )

    print("----- Created At Filters -----")
    stat_list = getStatListTimeFieldMonthly(merge_requests, "created_at")
    summaryCSVMergeRequestsByCreatedAtMonthly(stat_list, project_name)
    summaryPlotMergeRequestsByCreatedAt(stat_list, project_name, "mrCreatedAtMonthly")

    stat_list = getStatListTimeFieldYearly(merge_requests, "created_at")
    summaryCSVMergeRequestsByCreatedAtYearly(stat_list, project_name)
    summaryPlotMergeRequestsByCreatedAt(stat_list, project_name, "mrCreatedAtYearly")

    (
        markdown_multi_line_cre_at_l30,
        markdown_single_line_cre_at_l30,
        stats_cre_at_l30,
    ) = summaryMDMergeRequestsByCreatedAtLastNDays(merge_requests, project_name, 30)

    print("----- Merged At Filters -----")
    stat_list = getStatListTimeFieldMonthly(merge_requests, "merged_at")
    summaryCSVMergeRequestsByMergedAtMonthly(stat_list, project_name)
    summaryPlotMergeRequestsByMergedAt(stat_list, project_name, "mrMergedAtMonthly")

    stat_list = getStatListTimeFieldYearly(merge_requests, "merged_at")
    summaryCSVMergeRequestsByMergedAtYearly(stat_list, project_name)
    summaryPlotMergeRequestsByMergedAt(stat_list, project_name, "mrMergedAtYearly")

    (
        markdown_multi_line_mer_at_l30,
        markdown_single_line_mer_at_l30,
        stats_mer_at_l30,
    ) = summaryMDMergeRequestsByMergedAtLastNDays(merge_requests, project_name, 30)

    print("----- Closed At Filters -----")
    stat_list = getStatListTimeFieldMonthly(merge_requests, "closed_at")
    summaryCSVMergeRequestsByClosedAtMonthly(stat_list, project_name)
    summaryPlotMergeRequestsByClosedAt(stat_list, project_name, "mrClosedAtMonthly")

    stat_list = getStatListTimeFieldYearly(merge_requests, "closed_at")
    summaryCSVMergeRequestsByClosedAtYearly(stat_list, project_name)
    summaryPlotMergeRequestsByClosedAt(stat_list, project_name, "mrClosedAtYearly")

    (
        markdown_multi_line_clo_at_l30,
        markdown_single_line_clo_at_l30,
        stats_clo_at_l30,
    ) = summaryMDMergeRequestsByClosedAtLastNDays(merge_requests, project_name, 30)

    end_date = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    markdown_summary += f"\n\n### Merge Request Summary of {project_name}\n"
    markdown_summary += (
        "**Total Merge Request**: " + markdown_single_line_open_finished + "<br>\n"
    )

    start_date = end_date - timedelta(days=30)
    markdown_summary += (
        f"**Last 30 Days** (From {start_date.strftime('%Y-%m-%d')} To"
        f" {end_date.strftime('%Y-%m-%d')}): "
    )
    markdown_summary += markdown_single_line_cre_at_l30
    markdown_summary += markdown_single_line_mer_at_l30
    markdown_summary += "New " + markdown_single_line_cre_at_l30
    markdown_summary += markdown_single_line_clo_at_l30
    markdown_summary += (
        f"<br>\nLast 30 Days median time to merge new: {stats_cre_at_l30['medianTimeToMergeDHMS']}, "
        f"median time to merge: {stats_mer_at_l30['medianTimeToMergeDHMS']}; "
    )

    return markdown_summary
