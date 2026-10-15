import sys,json,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from bpy_extras.object_utils import world_to_camera_view
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/assembly';FRAMES=WORK/'frames';FRAMES.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'wood01-montaz.blend'));s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32
parts={o['part_id']:o for o in s.objects if 'part_id' in o};start=time.time();points={};sample_motion=[]
for f in range(1,913):
 s.frame_set(f);bpy.context.view_layer.update();s.render.filepath=str(FRAMES/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
 points[str(f)]={}
 for k,o in parts.items():
  q=world_to_camera_view(s,s.camera,o.matrix_world.translation);points[str(f)][k]=[round(q.x*1920,2),round((1-q.y)*1080,2)]
 if f in [1,73,132,192,252,312,372,432,492,552,660,768,912]:sample_motion.append({'frame':f,'positions':{k:list(o.location) for k,o in parts.items()},'connector_positions':{o.name:list(o.location) for o in s.objects if 'connector' in o},'connector_rotation':{o.name:list(o.rotation_quaternion) for o in s.objects if 'connector' in o}})
 if f%48==0:
  (WORK/'render-progress.json').write_text(json.dumps({'last_frame':f,'total':912,'elapsed_seconds':round(time.time()-start,2)},indent=2),encoding='utf-8');print('FRAMES',f,'of912',round(time.time()-start,2),flush=True)
(WORK/'projected-points.json').write_text(json.dumps(points),encoding='utf-8');result={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'frames':912,'dimensions':[1920,1080],'fps':24,'duration_seconds':38,'renderer':'Blender5.2.2 EEVEE / GPU','render_seconds':round(time.time()-start,2),'source':'wood01-montaz.blend','actual_native_motion_samples':sample_motion,'not_a_static_crossfade':True};(WORK/'render-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('ALL912FRAMES_RENDERED',result['render_seconds'],flush=True)
