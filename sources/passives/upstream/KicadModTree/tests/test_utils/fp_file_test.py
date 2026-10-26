
import os
from pathlib import Path

import pytest

from KicadModTree.KicadFileHandler import KicadFileHandler


# When updating formats in a train of commits, this decorator can be used to mark all
# serialisation tests as expected to fail until the golden files are up-revved at the
# end of the process.
# @pytest.mark.xfail(reason="Expected failure for all SerialisationTest tests until golden files are up-revved")
class SerialisationTest:

    RESULTS_DIR_NAME = "results"  # Default directory, can be overridden by subclasses

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, request):
        """Automatically injects `assert_serialises_as` into the class."""

        request.cls.results_dir = os.path.join(os.path.dirname(request.fspath), self.RESULTS_DIR_NAME)
        request.cls.assert_serialises_as = self._assert_serialises_as

    def _assert_serialises_as(self, kicad_mod, exp_content_file: Path):
        """
        Serialise the given kicad_mod and compare it to the expected value.

        If the WRITE_GOLDEN_FILES environment variable is set, the expected value will be
        written to the test data directory instead of being compared.

        :param kicad_mod: The kicad_mod to serialise
        :param expected: The expected serialised value
        """
        file_handler = KicadFileHandler(kicad_mod)

        rendered = file_handler.serialize()

        exp_file = os.path.join(self.results_dir, exp_content_file)

        write_golden_files = os.getenv('WRITE_GOLDEN_FILES', False)

        if write_golden_files:
            with open(exp_file, 'w') as file:
                file.write(rendered)
        else:
            # load the expected file and do the test
            expected_content = open(exp_file, 'r').read()

            assert rendered == expected_content
