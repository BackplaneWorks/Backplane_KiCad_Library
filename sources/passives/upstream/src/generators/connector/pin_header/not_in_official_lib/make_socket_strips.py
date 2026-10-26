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

# Run this script from the root of the repository with the venv activated and optional output_dir:
# Unix:			./scripts/Pin-Headers_Socket-Strips/pin_headers_gen.py --output-dir ../footprints/
# Powershell: 	python .\scripts\Pin-Headers_Socket-Strips\pin_headers_gen.py --output-dir ..\footprints\

# check README.md in repository root for installing venv
# on windows powershell: (deactivate script does not always work)
# .\venv\Scripts\Activate.ps1
# & {. .\venv\Scripts\Activate.ps1; deactivate}

from pathlib import Path
import argparse, sys
import logging
from typing import Any

from scripts.tools.footprint_generator import FootprintGenerator
from scripts.tools.footprint_scripts_pin_headers import FPconfiguration #, makePinHeadOrSocket
from def_makePinHeadStraight import makePinHeadStraight
from def_makeSocketStripAngled import makeSocketStripAngled
from def_makePinHeadStraightSMD import makePinHeadStraightSMD

class PinSocketGenerator(FootprintGenerator):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	def generateFootprint(
		self, spec: dict[str, Any], pkg_id: str, header_info: dict[str, Any]
	) -> None:
		fp_config = FPconfiguration(spec)
				
		for pos_count in fp_config.pos_range:
			fp_config.pos_count = pos_count
			#print(fp_config.pos_range, fp_config.pos_count)

			if (	fp_config.mount_type == "THT"
					and fp_config.orientation == "Vertical"
			):
				makePinHeadStraight(self, fp_config)
				pass
			elif (	fp_config.mount_type =="THT"
					and fp_config.orientation == "Horizontal"
			):
				makeSocketStripAngled(self, fp_config)
				pass
			elif (	fp_config.mount_type == "SMD"
					and fp_config.orientation == "Vertical"
			):
				makePinHeadStraightSMD(self, fp_config)
				pass
			else:
				raise ValueError(
					f"Unsupported mount/orientation combination: {fp_config.mount_type}/{fp_config.orientation}"
				)


if __name__ == "__main__":

	parser = argparse.ArgumentParser(
		description="use config .yaml files to create socket strips."
	)
	parser.add_argument(
		"files",
		metavar="file",
		type=str,
		nargs="*",
		help="list of files holding information about what devices should be created.",
	)
	args = FootprintGenerator.add_standard_arguments(parser)
	if args.output_dir == None:
		args.output_dir = Path.cwd() # working directory: usually root of repository
	logging.info("Generating in dir {}".format(args.output_dir.resolve(),))

	# Do not use the autofind feature of FootprintGenerator.run_on_files() so we can have multiple generators+yaml combos
	if not args.files:
		script_dir = sys.path[0] # Only use the yaml definitions in this folder.
		args.files = list(Path(script_dir).rglob('pin_sockets_*.yaml'))
		logging.info("No .yaml files given, using default .yaml file(s): {}".format(args.files))

	FootprintGenerator.run_on_files(PinSocketGenerator, args)
