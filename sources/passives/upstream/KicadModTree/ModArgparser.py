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
# (C) 2017 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definition for a general data loading class."""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Any, Callable

try:
    import yaml

except ImportError:
    logging.error("pyyaml not available!")
    sys.exit(1)


class ParserException(Exception):
    def __itruediv__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the ParserException.

        This method acts as the in-place true division operator, but its primary
        purpose here is to initialize the exception base class with provided arguments.

        Args:
            *args: Positional arguments passed to the exception.
            **kwargs: Keyword arguments passed to the exception.
        """
        Exception.__init__(self, *args, **kwargs)


class ModArgparser(object):
    """A general data loading class, which allows to specify parts using .yaml or .csv
    files.

    Using this class allows us to separate between the implementation of a footprint
    generator, and the data which represents a single footprint. To do so, we need to
    define which parameters are expected in those data-files.

    To improve the usability of this class, it is able to do type checks of provided
    parameters, as well as defining default values and do a simple check if a parameter
    can be considered as required or optional.

    Example:
        >>> from KicadModTree import *
        >>> def footprint_gen(args):
        ...    print("create footprint: {}".format(args['name']))
        ...
        >>> parser = ModArgparser(footprint_gen)
        >>> # The root node of .ayml files is parsed as name:
        >>> parser.add_parameter("name", type=str, required=True)
        >>> parser.add_parameter("datasheet", type=str, required=False)
        >>> parser.add_parameter("courtyard", type=float, required=False, default=0.25)
        >>> parser.add_parameter("pincount", type=int, required=True)
        >>> # Now run our script which handles the whole part of parsing the files:
        >>> parser.run()
    """

    def __init__(
        self, footprint_function: Callable[[str, dict[str, Any]], int]
    ) -> None:
        """Create a ModArgparser.

        Args:
            footprint_function: A function which is called for every footprint we want
                to generate.
        """

        # Instance attributes:
        self._footprint_function: Callable[[str, dict[str, Any]], int]
        """A function which is called for every footprint we want to generate."""
        self._params: dict[str, Any]
        """The parameters."""

        self._footprint_function = footprint_function
        self._params = {}

    def add_parameter(self, name: str, **kwargs: Any) -> None:
        """Add a parameter to the ModArgparser.

        Args:
            name: Name of the parameter.
            **kwargs: Additional keyword arguments defining the parameter's properties.
                Possible keys include:

                * `type` (``type``): Type of the argument (e.g., str, int, float, bool).
                * `required` (``bool``): Whether the argument is required or optional.
                  Defaults to False.
                * `default` (``Any``): The default value which is used when there is no
                  value defined for an optional parameter.

        Example:
            >>> from KicadModTree import *
            >>> def footprint_gen(args):
            ...    print("create footprint: {}".format(args['name']))
            ...
            >>> parser = ModArgparser(footprint_gen)
            >>> # The root node of .yaml files is parsed as name:
            >>> parser.add_parameter("name", type=str, required=True)
            >>> parser.add_parameter("datasheet", type=str, required=False)
            >>> parser.add_parameter("courtyard", type=float, required=False,
            ...     default=0.25)
        """

        self._params[name] = kwargs

    def run(self, generator_name: str, arguments: list[str] | None = None) -> int:
        """Execute the ModArgparser and run all tasks defined via the parameter
        `arguments` or, if `None`, via the command line arguments of this script.

        This method parses the commandline arguments to determine which actions to take.
        Beside of parsing .yaml and .csv files, it also allows us to output example
        files.

        Returns:
            The number of footprints created.

        >>> from KicadModTree import *
        >>> def footprint_gen(args):
        ...    print("create footprint: {}".format(args['name']))
        ...
        >>> parser = ModArgparser(footprint_gen)
        >>> # The root node of .yaml files is parsed as name:
        >>> parser.add_parameter("name", type=str, required=True)
        >>> # Now run our script which handles the whole part of parsing the files:
        >>> parser.run()
        """
        parser = argparse.ArgumentParser(
            description="Parse footprint definition file(s) and create matching footprints"
        )
        parser.add_argument(
            "files",
            metavar="file",
            type=str,
            nargs="*",
            help=".yaml or .csv files which contains data",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            help="show some additional information",
            action="store_true",
        )  # TODO
        parser.add_argument(
            "-o",
            "--output-dir",
            type=Path,
            help="Sets the directory to which to write the generated footprints",
        )
        parser.add_argument(
            "--print_yml", help="print example .yaml file", action="store_true"
        )
        parser.add_argument(
            "--print_csv", help="print example .csv file", action="store_true"
        )

        # TODO: allow writing into sub dir

        args = parser.parse_args(arguments)

        if args.print_yml:
            self._print_example_yml()
            return 0

        if args.print_csv:
            self._print_example_csv()
            return 0

        if len(args.files) == 0:
            parser.print_help()
            return 0

        num_footprints_generated = 0
        for filepath in args.files:
            logging.debug("use file: {0}".format(filepath))
            if filepath.endswith(".yml") or filepath.endswith(".yaml"):
                num_footprints_generated += self._parse_and_execute_yml(
                    filepath, generator_name
                )
            elif filepath.endswith(".csv"):
                num_footprints_generated += self._parse_and_execute_csv(
                    filepath, generator_name
                )
            else:
                logging.error("unexpected filetype: {0}".format(filepath))
        return num_footprints_generated

    def _parse_and_execute_yml(self, filepath: str, generator_name: str) -> int:
        """Parse a YAML file and execute the footprint function for each entry.

        This private method reads a YAML file, parses its content, and then iterates
        through each footprint definition, calling the `_execute_script` method with the
        parsed parameters.

        Args:
            filepath: The path to the YAML file.
            generator_name: The name of the generator.

        Raises:
            yaml.YAMLError: If there is an error parsing the YAML file.

        Returns:
            The number of generated footprints.
        """
        num_footprints_generated = 0
        with open(filepath, "r", encoding="utf-8") as stream:
            try:
                parsed = yaml.safe_load(stream)  # parse file

                if parsed is None:
                    logging.error("Empty file!")
                    return 0

                for footprint in parsed:
                    kwargs = parsed.get(footprint)

                    # name is a reserved key
                    if "name" in kwargs:
                        logging.error("Name is already used for root name!")
                        continue
                    kwargs["name"] = footprint

                    num_footprints_generated += self._execute_script(
                        filepath, generator_name, **kwargs
                    )  # now we can execute the script

            except yaml.YAMLError as exc:
                logging.error(exc)
        return num_footprints_generated

    def _create_example_data_required(self, **kwargs: Any) -> dict[str, Any]:
        """Create a dictionary of example data containing only required parameters.

        This private method iterates through the defined parameters and generates
        example values for those marked as 'required'. It can optionally include the
        'name' parameter.

        Args:
            **kwargs: Optional keyword arguments.
                * `include_name` (``bool``): If True, the 'name' parameter will be
                  included in the example data even if it's typically handled as
                  a root node in YAML. Defaults to False.

        Returns:
            A dictionary of required parameters with example values.
        """
        params: dict[str, Any] = {}
        for k, v in self._params.items():
            if kwargs.get("include_name", False) is False and k == "name":
                continue
            if v.get("required", False):
                params[k] = self._create_example_datapoint(
                    v.get("type", str), v.get("default")
                )
        return params

    def _create_example_data_full(self, **kwargs: Any) -> dict[str, Any]:
        """Create a dictionary of example data containing all defined parameters.

        This private method iterates through all defined parameters and generates
        example values for each, including both required and optional parameters.
        It can optionally include the 'name' parameter.

        Args:
            **kwargs: Optional keyword arguments.
                * `include_name` (``bool``): If True, the 'name' parameter will be
                  included in the example data even if it's typically handled as
                  a root node in YAML. Defaults to False.

        Returns:
            A dictionary of all parameters with example values.
        """
        params: dict[str, Any] = {}
        for k, v in self._params.items():
            if kwargs.get("include_name", False) is False and k == "name":
                continue
            params[k] = self._create_example_datapoint(
                v.get("type", str), v.get("default")
            )
        return params

    def _create_example_datapoint(
        self,
        t: type[bool] | type[int] | type[float] | type[str],
        default: bool | int | float | str,
    ) -> bool | int | float | str:
        """Create an example data point based on its type and default value.

        This private method generates a sensible example value for a given type,
        prioritizing the provided default value if available.

        Args:
            t: The type of the data point (e.g., bool, int, float, str, list).
            default: The default value for the data point. Can be None.

        Returns:
            An example value for the specified type.
        """
        if default:
            return t(default)
        elif t is bool:
            return False
        elif t is int:
            return 0
        elif t is float:
            return 0.0
        elif t is str:
            return "some string"
        else:
            return "??"

    def _print_example_yml(self) -> None:
        """Print an example YAML file to standard output.

        This private method generates and prints a YAML-formatted example showing both
        required and full parameter sets, useful for users to understand the expected
        structure of input YAML files.
        """
        data = {
            "footprint_required": self._create_example_data_required(),
            "footprint_full": self._create_example_data_full(),
        }
        print(yaml.dump(data, default_flow_style=False))

    def _parse_and_execute_csv(self, filepath: str, generator_name: str) -> int:
        """Parse a CSV file and execute the footprint function for each row.

        This private method reads a CSV file, parses each row as a dictionary of
        parameters, and then calls the `_execute_script` method with these parameters.

        Args:
            filepath: The path to the CSV file.

        Returns:
            The number of generated footprints.
        """
        num_footprints_generated = 0
        with open(filepath, "r", encoding="utf-8") as stream:
            # dialect = csv.Sniffer().sniff(stream.read(1024))
            # check which type of formatting the csv file likel has
            # stream.seek(0)

            reader = csv.DictReader(stream, dialect=csv.excel)  # parse file

            for row in reader:
                # we want to remove spaces before and after the fields
                kwargs: dict[str, Any] = {}
                for k, v in row.items():
                    kwargs[k.strip()] = v.strip()

                num_footprints_generated += self._execute_script(
                    filepath, generator_name, **kwargs
                )
        return num_footprints_generated

    def _print_example_csv(self) -> None:
        """Print an example CSV file to standard output.

        This private method generates and prints a CSV-formatted example showing the
        expected headers and sample data, useful for users to understand the expected
        structure of input CSV files.
        """
        writer = csv.DictWriter(sys.stdout, fieldnames=self._params.keys())
        writer.writeheader()
        writer.writerow(self._create_example_data_required(include_name=True))
        writer.writerow(self._create_example_data_full(include_name=True))

    def _execute_script(self, filepath: str, generator_name: str, **kwargs: Any) -> int:
        """Execute the assigned footprint generation function with parsed arguments.

        This private method validates and processes the provided keyword arguments
        against the defined parameters, handling required fields, type conversions,
        and default values. It then calls the `_footprint_function` with the processed
        arguments.

        Args:
            **kwargs: Keyword arguments representing the parameters for a single
                footprint.

        Raises:
            ParserException: If a required parameter is missing or a type conversion
                fails.

        Returns:
            The number of generated footprints.
        """
        parsed_args: dict[str, Any] = {}
        error = False

        for k, v in self._params.items():
            try:
                if kwargs.get(k) not in [None, ""]:
                    parsed_args[k] = v.get("type", str)(kwargs[k])
                elif v.get("required", False):
                    raise ParserException("parameter expected: {}".format(k))
                else:
                    type = v.get("type", str)
                    if type is bool:
                        parsed_args[k] = type(v.get("default", False))
                    elif type is int:
                        parsed_args[k] = type(v.get("default", 0))
                    elif type is float:
                        parsed_args[k] = type(v.get("default", 0.0))
                    elif type is str:
                        parsed_args[k] = type(v.get("default", ""))
                    elif type is list:
                        parsed_args[k] = type(v.get("default", []))
                    else:
                        parsed_args[k] = type(v.get("default"))
            except (ValueError, ParserException) as e:
                error = True
                logging.error("ERROR: {}".format(e))

        if error:
            return 0

        return self._footprint_function(generator_name, parsed_args)
