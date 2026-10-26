# STM32 library generator

This script generates KiCad symbol libraries from XML files defining pins for
STM32 devices.

## Prerequisites

* Python packages listed in requirements.txt. Note that lxml depends on libxml2,
  which should be installed on your system already. When in doubt, try to
  install lxml using your distro's package manager.
* kicad-cli. It's is used to format the generated files.
* XML files, taken from STM32CubeMX install (from db/mcu folder). If you do not
  have a copy of the IDE around, you can get a copy of these files here:
  https://gitlab.com/neinseg/stm32square/-/tree/release

## Running

If you have the correct XML files, `./generate_all_libraries.sh xmldir` , where
`xmldir` is a directory containing all the necessary XML files. Note that the
script will do a few thousand network requests to validate the computed
datasheet URLs on its first run. The responses are cached, and during subsequent
runs only those URLs that could not be found the last time will be re-requested.

