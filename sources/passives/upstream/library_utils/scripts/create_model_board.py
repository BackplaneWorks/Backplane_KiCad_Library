import argparse
import os
from pathlib import Path

import pcbnew

print("KiCad version", pcbnew.FullVersion())

parser = argparse.ArgumentParser(description="Creates a board with a single footprint")
parser.add_argument("-f", "--footprint", help="Path to .kicad_mod file")
parser.add_argument("-w", "--wrl", help="Path to .wrl file")
parser.add_argument("-s", "--step", help="Path to .step file")
parser.add_argument("board", help="Path to output board")

args, _ = parser.parse_known_args()
fp_path = Path(os.path.abspath(args.footprint))

io = pcbnew.PCB_IO_KICAD_SEXPR()
b = pcbnew.BOARD()


def duplicate_fp(fp):
    try:
        dup = fp.Duplicate(False)  # KiCad 10+
    except TypeError:
        dup = fp.Duplicate()  # KiCad <=9

    return pcbnew.Cast_to_FOOTPRINT(dup)


fp = io.ImportFootprint(str(fp_path), fp_path.stem)
fp.Models()[0].m_Filename = str(Path(os.path.abspath(args.step)))
b.Add(fp)
fp.SetReference("FP")
fp.SetPosition(pcbnew.VECTOR2I_MM(100, 100))
bb = fp.GetCourtyard(0).BBox()
fp_wrl = duplicate_fp(fp)
fp_step = duplicate_fp(fp)
fp_transp = duplicate_fp(fp)
fp.Models()[0].m_Show = False
b.Add(fp_wrl)
fp_wrl.SetPosition(
    pcbnew.VECTOR2I_MM(
        100 + 2 * pcbnew.ToMM(bb.GetWidth()), 100 + 2 * pcbnew.ToMM(bb.GetHeight())
    )
)
fp_wrl.SetReference("WRL")
fp_wrl.Models()[0].m_Filename = str(Path(os.path.abspath(args.wrl)))
fp_wrl.Models()[0].m_Show = True

b.Add(fp_step)
fp_step.SetReference("STEP")
fp_step.SetPosition(pcbnew.VECTOR2I_MM(100, 100 + 2 * pcbnew.ToMM(bb.GetHeight())))
fp_step.Models()[0].m_Filename = str(Path(os.path.abspath(args.step)))
fp_step.Models()[0].m_Show = True

b.Add(fp_transp)
fp_transp.SetReference("70%")
fp_transp.SetPosition(pcbnew.VECTOR2I_MM(100 + 2 * pcbnew.ToMM(bb.GetWidth()), 100))
fp_transp.Models()[0].m_Filename = str(Path(os.path.abspath(args.step)))
fp_transp.Models()[0].m_Show = True
fp_transp.Models()[0].m_Opacity = 0.7

b.Save(args.board)
