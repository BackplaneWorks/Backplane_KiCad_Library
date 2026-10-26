#!/bin/bash

# How to test locally:
# Inside the kicad-symbols folder, run
#     export BASE_SHA=$(git rev-parse master)
#     export TARGET_SHA=$(git rev-parse HEAD)
#     export TMP_BUILD_DIR=`mktemp -d` # or supply any temp directory
#     ./library_utils/tools/gitlabci/check_symbols.sh

kfg_root=$(realpath "$(dirname ${BASH_SOURCE[0]})/../../..")
source "${kfg_root}/library_utils/tools/gitlabci/common.sh"

# print python version
python3 -V

# Assert that $BASE_SHA and $TARGET_SHA are set
if [ -z "$CI_PROJECT_DIR" ]; then
  echo "CI_PROJECT_DIR is not set"
  exit 1
fi
if [ -z "$BASE_SHA" ]; then
  echo "BASE_SHA is not set"
  exit 1
fi
if [ -z "$TARGET_SHA" ]; then
  echo "TARGET_SHA is not set"
  exit 1
fi
if [ -z "$TMP_BUILD_DIR" ]; then
  echo "TMP_BUILD_DIR is not set, creating a temp dir. You might want to delete it later."
  TMP_BUILD_DIR=`mktemp -d`
fi


echo "BASE_SHA: $BASE_SHA"
echo "TARGET_SHA: $TARGET_SHA"
echo "CI_PROJECT_DIR: $CI_PROJECT_DIR"
echo "TMP_BUILD_DIR: $TMP_BUILD_DIR"

# clone required repos
if [ ! -x "$TMP_BUILD_DIR/kicad-footprints" ]; then
  echo "Cloning footprint repo"
  git clone --depth 1 https://gitlab.com/kicad/libraries/kicad-footprints.git $TMP_BUILD_DIR/kicad-footprints
else
  echo "Found existing kicad-footprints directory"
fi
# get the list of files we want to compare - this also works with unpacked libraries
echo "Comparing range $BASE_SHA to $TARGET_SHA"
CHANGED_SYMBOLS=$(git diff-tree --diff-filter=AM --no-commit-id --oneline --name-only -r "$BASE_SHA" "$TARGET_SHA" | grep '\.kicad_sym$')
DELETED_SYMBOLS=$(git diff-tree --diff-filter=D  --no-commit-id --oneline --name-only -r "$BASE_SHA" "$TARGET_SHA" | grep '\.kicad_sym$')

# do some debug output
echo "Found changed Symbols: $CHANGED_SYMBOLS"
echo "Found deleted Symbols: $DELETED_SYMBOLS"

# checkout the previous version of the 'old' files so we can compare against them
mkdir -p $TMP_BUILD_DIR/kicad-symbols-prev
for LIBNAME in $CHANGED_SYMBOLS; do
  TARGET_FILENAME="$TMP_BUILD_DIR/kicad-symbols-prev/$LIBNAME"
  # the LIBAME will look like "Video.kicad_symdir/SI582.kicad_sym".
  # So we need to create the directory Video.kicad_symdir first
  # we do this hacky, my creating it with mkdir -p and then deleting the
  # subdirectory SI582.kicad_sym
  mkdir -p "$TARGET_FILENAME"
  rmdir "$TARGET_FILENAME"
  # now extract the old version of the changed library from git
  git cat-file blob "$BASE_SHA:$LIBNAME" > "$TMP_BUILD_DIR/kicad-symbols-prev/$LIBNAME"
done

# now run comparelibs
"${kfg_root}/library_utils/klc-check/comparelibs.py" -v \
  --old $TMP_BUILD_DIR/kicad-symbols-prev/* \
  --new $CHANGED_SYMBOLS \
  --check --check-derived \
  --footprint_directory $TMP_BUILD_DIR/kicad-footprints \
  -m \
  --junit junit.xml
KLC_ERRORS=$?

# check lib table
${kfg_root}/library_utils/klc-check/check_lib_table.py $CI_PROJECT_DIR/*.kicad_symdir \
    --table $CI_PROJECT_DIR/sym-lib-table \
    --junit junit.xml

TABLE_ERRORS=$?

echo "KLC_ERRORS: $KLC_ERRORS"
echo "TABLE_ERRORS: $TABLE_ERRORS"

# Table errors are always bad
if [ $TABLE_ERRORS -ne 0 ]; then
    echo "Library table errors"
    exit 1
fi

if [ $KLC_ERRORS -eq 2 ]; then
    # Warnings
    echo "KLC checks have warnings only"
    exit 2
elif [ $KLC_ERRORS -ne 0 ]; then
    # Errors (or something else, assume bad)
    echo "KLC checks have errors"
    exit 1
fi

echo "All checks passed"
exit 0
