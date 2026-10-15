import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/probki-plus28-2026-10-15/assembly/wood01-montaz.blend'))
s=bpy.context.scene;parts={o['part_id']:o for o in s.objects if 'part_id' in o};points={}
for f in range(1,913):
 s.frame_set(f);bpy.context.view_layer.update();points[str(f)]={}
 for k,o in parts.items():
  p=o.matrix_world.translation.copy()
  if k=='A1':p+=Vector((0,.08,.20))
  q=world_to_camera_view(s,s.camera,p);points[str(f)][k]=[round(q.x*1920,2),round((1-q.y)*1080,2)]
(WORK/'projected-points.json').write_text(json.dumps(points),encoding='utf-8')
print('LABEL_PROJECTIONS_PASS')
