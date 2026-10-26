# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

class CommonMetadata:
    """
    Class that reads "standard" metadata out of a dict, probably
    from YAML and puts a typed interface on it.

    This avoids every generator having to define its own reading
    and validation for things that are common to all footprints.

    Individual generators can still define their own metadata,
    and can opt to ignore or override this class if it's somehow
    not suitable, and can impose their own requirements (like saying
    datasheets are mandatory). Basically this calls just standardised
    the datatypes and the dict keys/layouts.
    """

    datasheet: str | None
    """The datasheet for the footprint. Most footprints will have this
    set, but some generators may generate the URL otherwise."""

    description: str | None
    """A description of the footprint. Most generators will generate this
    but some may allow or expect it to be set by the YAML. They may still
    append or otherwise modify it."""

    manufacturer: str | None
    """Some footprints are manufacturer-specific, annd may define this."""

    part_number: str | None
    """Some footprints are unique to a particular part number (MPN)"""

    additional_tags: list[str]
    """
    A list of additional keywords that can be used to search for this footprint
    in the KiCad UI.
    Note: "tags" is a bad name, these are _search keywords_. But all the YAML uses
    "tags", so changing it only here would be more confusing."""

    compatible_mpns: list[str]
    """A list of compatible MPNs (i.e. other manufacturer's part numbers,
    drawing numbers, standards, etc) that this footprint is compatible with."""

    custom_name_format: str | None
    """Set if the footprint def defines its own name format
    Actually applying this format (and which variables it has) is the
    responsibility of the generator."""

    library_name: str | None
    """Set if the footprint def defines its own library name."""

    def __init__(self, spec: dict):

        self.description = spec.get("description", None)
        self.datasheet = spec.get("datasheet", spec.get("size_source", None))

        self.manufacturer = spec.get("manufacturer", None)
        self.part_number = spec.get("part_number", None)

        self.additional_tags = spec.get("additional_tags", [])
        self.compatible_mpns = spec.get("compatible_mpns", [])

        self.custom_name_format = spec.get("custom_name_format", None)
        self.library_name = spec.get("library_name", spec.get("lib_name", None))
