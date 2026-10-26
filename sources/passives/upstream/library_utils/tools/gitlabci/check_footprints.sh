#!/bin/bash
kfg_root=$(realpath "$(dirname ${BASH_SOURCE[0]})/../../..")
source "${kfg_root}/library_utils/tools/gitlabci/common.sh"

SCRIPT="${kfg_root}/library_utils/klc-check/check_footprint.py"

echo "Comparing range $BASE_SHA to $TARGET_SHA"


mod_files=()

for change in $(git diff-tree --diff-filter=AMRD --no-commit-id --name-only -r "$BASE_SHA" "$TARGET_SHA"); do
    if [[ $change =~ .*\.kicad_mod ]]; then
        if [ -f "$CI_PROJECT_DIR/$change" ]; then
            mod_files+=("$CI_PROJECT_DIR/$change")
            echo "Checking: $change"
        else
            echo "Skipping deleted footprint: $change"
        fi
    fi
done

if [ ${#mod_files[@]} -eq 0 ]; then
    echo "No changed footprints to check, skipping KLC check"
    KLC_ERRORS=0
else
    # Run the KLC checker on all the files
    python3 "$SCRIPT" -vv \
        --junit junit.xml \
        ${mod_files[@]}

    KLC_ERRORS=$?
fi

# check lib table
python3 "${kfg_root}/library_utils/klc-check/check_lib_table.py" $CI_PROJECT_DIR/*.pretty \
    --table $CI_PROJECT_DIR/fp-lib-table \
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
