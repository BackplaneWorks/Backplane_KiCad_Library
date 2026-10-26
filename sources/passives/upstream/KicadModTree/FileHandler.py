# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definitions for an abstract file handler."""

from __future__ import annotations

import abc
import io
from pathlib import Path


class FileHandler(abc.ABC):
    """An abstract implementation of a file handler.

    Implements some basic methods to serialize an object (e.g. a footprint) and save it
    into a file.
    """

    def writeFile(self, filename: Path) -> None:
        """Write the output of FileHandler.serialize to a file.

        Args:
            filename: The path of the output file.
        """
        with io.open(filename, "w", encoding="utf-8") as f:
            output = self.serialize()
            f.write(output)
            f.close()

    @abc.abstractmethod
    def serialize(self) -> str:
        """Serialize the object (e.g. footprint) to a string (to be saved into a file)."""
        raise NotImplementedError("serialize has to be implemented by child class")
