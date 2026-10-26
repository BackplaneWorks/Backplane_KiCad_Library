#!/usr/bin/env bash
set -e

kfg_root=$(realpath "$(dirname ${BASH_SOURCE[0]})/../../..")
source "${kfg_root}/library_utils/tools/gitlabci/common.sh"

LAYERS="F.Cu,B.Cu,F.SilkS,B.SilkS,F.Fab,B.Fab,F.CrtYd,B.CrtYd,F.Adhes,B.Adhes"
CHANGES=$(git diff-tree --diff-filter=AMR --no-commit-id --name-only -r "$BASE_SHA" "$TARGET_SHA")
TMP_BOARD_DIR=`mktemp -d`
mkdir -p screenshots

for change in $CHANGES; do
    if [[ $change =~ .*\.kicad_mod ]]; then
        echo "Creating a board with footprint: $change"
        python3 "${kfg_root}/library_utils/scripts/create_board.py" "/$CI_PROJECT_DIR/$change" \
            "$TMP_BOARD_DIR/board.kicad_pcb"
        echo "Exporting svg"
        kicad-cli pcb export svg --page-size-mode 2 -l "$LAYERS" \
            -o "screenshots/$change.svg" "$TMP_BOARD_DIR/board.kicad_pcb"
        echo
        echo "Converting to png"
        mkdir -p screenshots/$(dirname "$change")
        inkscape -w 800 -b "#001023" "screenshots/$change.svg" -o "screenshots/$change.png"
    fi
done
