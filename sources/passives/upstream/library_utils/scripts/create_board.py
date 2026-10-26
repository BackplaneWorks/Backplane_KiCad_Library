import argparse
import os
import sys
from pathlib import Path

try:
    import pcbnew
except ImportError:
    KICAD_NIGHTLY_PATH = "/usr/lib/kicad-nightly/lib/python3/dist-packages"
    if KICAD_NIGHTLY_PATH not in sys.path:
        sys.path.insert(0, KICAD_NIGHTLY_PATH)

    import pcbnew

print("KiCad version", pcbnew.FullVersion())

parser = argparse.ArgumentParser(description="Creates a board with a single footprint")
parser.add_argument("footprint", help="Path to .kicad_mod file")
parser.add_argument("board", help="Path to output board")

args, _ = parser.parse_known_args()
fp_path = Path(os.path.abspath(args.footprint))

board = pcbnew.BOARD()
io = pcbnew.PCB_IO_KICAD_SEXPR()
fp: pcbnew.FOOTPRINT = io.ImportFootprint(str(fp_path), fp_path.stem)
board.Add(fp)
# put the footprint at the center-ish, away from the page borders
fp.SetPosition(pcbnew.VECTOR2I_MM(150, 100))
board.Save(args.board)
