#!/bin/sh
#
# This script file is used to compare to sexpr files
# with sexpr python file. Spaces and line positioning will be ignored
#

set -eu


if [ $# -ne 1 ] && [ $# -ne 2 ]; then
    echo >&2 "Usage: $0 fileA [fileB]"
    exit 1
fi

INPUT_FILE1="$1"
# the second file may be omitted - in this case we read from stdin
INPUT_FILE2="${2:-}"


# generate the canonical representation of a sexpr file (read from stdin, write to stdout)
normalize_sexpr() {
    PYTHONPATH="$(dirname "$0")/../common" python3 -c '
import sexpr, sys
print(sexpr.format_sexp(sexpr.build_sexp(sexpr.parse_sexp(sys.stdin.read()))))
'
}


o1="$(mktemp)"
o2="$(mktemp)"

# remove the files when the script exits somehow
cleanup() { rm -f "$o1" "$o2"; }
trap cleanup EXIT

normalize_sexpr <"$INPUT_FILE1" >"$o1"
if [ -z "$INPUT_FILE2" ]; then cat; else cat "$INPUT_FILE2"; fi | normalize_sexpr >"$o2"

# use git compare since it does a nice colorful output
git --no-pager diff --no-index --color-words "$o1" "$o2"
