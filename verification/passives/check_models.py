"""Load saved STEP files through FreeCAD; validate shape and record measured boxes."""
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
from pathlib import Path
import FreeCAD
import Part

root=Path.cwd()
result=[]
try:
 for path in sorted((root/'3dmodels').glob('*.3dshapes/*.step')):
  shape=Part.read(str(path))
  if shape.isNull() or not shape.isValid():raise RuntimeError('Invalid shape: '+str(path))
  box=shape.BoundBox
  result.append({'file':str(path.relative_to(root)),'valid':True,'solids':len(shape.Solids),'volume_mm3':shape.Volume,'box_mm':[box.XLength,box.YLength,box.ZLength]})
 (root/'verification/passives/model-validation.json').write_text(json.dumps(result,indent=2)+'\n')
except BaseException as exc:
 (root/'verification/passives/model-validation-error.log').write_text(repr(exc))
 os._exit(1)
os._exit(0)
