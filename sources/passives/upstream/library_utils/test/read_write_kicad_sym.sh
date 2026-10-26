#!/bin/sh
#
# Test whether a kicad symbol file can be read and written without being changed.
# This is a test of the parser and the serializer.
#

set -eu

if [ $# -ne 1 ]; then
    echo "Usage: $0 dirWithkicad_sym"
    exit 1
fi

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd -P)

INPUT_DIRECTORY="$1"


check() {
  local input_filename="$1"
  python3 "$BASE_DIR/common/kicad_sym.py" "$input_filename" \
    | "$BASE_DIR/tools/compare_sexpr_files.sh" "$input_filename"
}


for file in "$INPUT_DIRECTORY"/*.kicad_sym; do
  if ! check "$file"; then
    echo >&2 "Error on file $file"
    exit 1
  else
    echo >&2 "Passed $file"
  fi
done
