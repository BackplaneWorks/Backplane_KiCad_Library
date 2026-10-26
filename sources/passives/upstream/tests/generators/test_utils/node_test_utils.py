"""
Test utility functions for tests that deal with constructing nodes. Things
like finding nodes in lists, setting up some standard nodes, etc.
"""

import pytest

from KicadModTree import Circle
from kilibs.config import global_config as GC


@pytest.fixture(autouse=True, scope="session")
def testing_global_config():
    """
    Pytest fixture that provides the default global configuration.

    Currently this uses the default global configuration, but if that turns out
    to be too unstable for testing purposes, we can construct a more stable
    one here.
    """
    return GC.DefaultGlobalConfig()


def find_circles(nodes, radius: float | None):

    def match(c: Circle):
        if radius is not None and c.radius != pytest.approx(radius):
            return False

        return True

    return [n for n in nodes if isinstance(n, Circle) and match(n)]
