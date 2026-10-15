import sys,json,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/bathroom'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'ba01-base.blend'));s=bpy.context.scene
bpy.context.preferences.filepaths.save_version=0
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices_for_type('OPTIX')
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.resolution_x=4096;s.render.resolution_y=3072;s.cycles.samples=64;s.render.resolution_percentage=100
def hash_objects(objects):
 a={o.name:{'matrix':[list(r) for r in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices] if o.type=='MESH' else None} for o in objects};return hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest()
def camera():return {'matrix':[list(r) for r in s.camera.matrix_world],'lens':s.camera.data.lens,'resolution':[s.render.resolution_x,s.render.resolution_y]}
def light_hash():return hashlib.sha256(json.dumps({o.name:{'energy':o.data.energy,'matrix':[list(r) for r in o.matrix_world],'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'},sort_keys=True).encode()).hexdigest()
def variant(name):
 allowed={'tray':{'TRAY','SHOWER_SCREEN'},'linear':{'LINEAR_DRAIN','SHOWER_SCREEN'},'bath':{'BATH','BATH_SCREEN'}}[name]
 for key in ['TRAY','LINEAR_DRAIN','SHOWER_SCREEN','BATH','BATH_SCREEN']:
  for o in bpy.data.collections[key].objects:o.hide_render=key not in allowed;o.hide_viewport=key not in allowed
 s['equipment_variant']=name;bpy.context.view_layer.update()
results=[]
for key,label,native in [('tray','01-brodzik-4k','ba01-base.blend'),('linear','02-odplyw-liniowy-4k','ba01-linear.blend'),('bath','03-wanna-prysznic-4k','ba01-bath.blend')]:
 variant(key);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/native));s.render.filepath=str(OUT/(label+'.png'));start=time.time();bpy.ops.render.render(write_still=True);s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=96;bpy.data.images['Render Result'].save_render(str(OUT/(label+'.jpg')),scene=s);s.render.image_settings.file_format='PNG'
 r={'key':key,'native_file':native,'image':label+'.png','jpeg':label+'.jpg','camera':camera(),'room_hash':hash_objects(bpy.data.collections['ROOM'].objects),'common_fixtures_hash':hash_objects(bpy.data.collections['COMMON_FIXTURES'].objects),'lighting_hash':light_hash(),'visible_equipment':sorted(o.name for c in ['TRAY','LINEAR_DRAIN','SHOWER_SCREEN','BATH','BATH_SCREEN'] for o in bpy.data.collections[c].objects if not o.hide_render),'seconds':round(time.time()-start,2)};results.append(r);(WORK/'render-progress.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print('RENDERED',label,r['seconds'],flush=True)
assert len({r['room_hash'] for r in results})==1;assert len({r['common_fixtures_hash'] for r in results})==1;assert len({r['lighting_hash'] for r in results})==1;assert all(r['camera']==results[0]['camera'] for r in results)
manifest={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'blender':bpy.app.version_string,'device':'OPTIX RTX4080SUPER','native_room_dimensions_m':[3,2.5,2.7],'native_room_area_m2':7.5,'one_base_room_model':True,'equipment_variants':3,'material_palette':'warm limestone / oak / brass','image_dimensions':[4096,3072],'renders':results,'same_room_geometry':True,'same_common_fixtures':True,'same_camera':True,'same_lighting':True,'shadow_note':'Light sources and settings are fixed. Shadows are physically recomputed for actual equipment changes; not pasted or forced pixel-identical.','deliverable_requested_by_client':'A base3Dscene and15–20variantimages for an existing configurator; no software/API/configurator-development requirement in full publicbrief.'}
(OUT/'variants-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('ALL_VARIANTS_PASS',flush=True)
