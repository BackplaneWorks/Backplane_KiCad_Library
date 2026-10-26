#!/usr/bin/env python3
"""Helper functions extracted from lib_stats.py

Contains date parsing, simple statistics helpers and formatting utilities.
"""

import statistics
from datetime import datetime, timezone


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def iso_date(dt: datetime):
    """Convert a datetime to GitLab ISO 8601 format (UTC, 'Z' suffix)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parseUtcTime(created_at_str):
    """Parse GitLab time strings ending with 'Z' into an aware UTC datetime.

    Handles both fractional seconds and whole-second timestamps.
    """
    # Expect formats like: 2024-11-01T12:34:56.123Z or 2024-11-01T12:34:56Z
    try:
        dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        dt = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.replace(tzinfo=timezone.utc)


def averageTimeFromSeconds(seconds_list):
    """Return average of a list of seconds (0 if list empty)."""
    if not seconds_list:
        return 0
    return sum(seconds_list) / len(seconds_list)


def medianTimeFromSeconds(seconds_list):
    """Return median of a list of seconds (0 if list empty)."""
    if not seconds_list:
        return 0
    return statistics.median(seconds_list)


def maxTimeFromSeconds(seconds_list):
    """Return maximum seconds (0 if list empty)."""
    if not seconds_list:
        return 0
    return max(seconds_list)


def minTimeFromSeconds(seconds_list):
    """Return minimum seconds (0 if list empty)."""
    if not seconds_list:
        return 0
    return min(seconds_list)


def stdDevPopulationTimeFromSeconds(seconds_list):
    """Return population standard deviation of seconds (0 if list empty)."""
    if not seconds_list:
        return 0
    return statistics.pstdev(seconds_list)


def stdDevSampleTimeFromSeconds(seconds_list):
    """Return sample standard deviation of seconds (0 if list empty or has less then 2 entries)."""
    if not seconds_list or len(seconds_list) < 2:
        return 0
    return statistics.stdev(seconds_list)


def secondsToHours(seconds):
    """Convert seconds to hours (float)."""
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return 0.0

    if total < 0:
        return 0.0

    hours = total / 3600.0
    return hours


def secondsToDays(seconds):
    """Convert seconds to days (float)."""
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return 0.0

    if total < 0:
        return 0.0

    days = total / 86400.0
    return days


def secondsToHMS(seconds):
    """Convert seconds to d HH:MM:SS."""
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "0d 00:00:00"

    if total < 0:
        return "0d 00:00:00"

    days = total // 86400
    rem = total % 86400
    hours = rem // 3600
    rem = rem % 3600
    minutes = rem // 60
    secs = rem % 60
    return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
