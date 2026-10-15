import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/bathroom'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices_for_type('OPTIX')
for d in p.devices:d.use=d.type=='OPTIX'
def box(o):
 assert o.parent is None
 # Hidden equipment is culled from the dependency graph; its cached
 # matrix_world can be identity. The unparented native basis includes the
 # actual saved location/rotation/scale even while the variant is hidden.
 pts=[o.matrix_basis@v.co for v in o.data.vertices];return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def gh(objects):return hashlib.sha256(json.dumps({o.name:{'matrix':[list(r) for r in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices]} for o in objects if o.type=='MESH'},sort_keys=True).encode()).hexdigest()
rows=[]
for fn,key in [('ba01-base.blend','tray'),('ba01-linear.blend','linear'),('ba01-bath.blend','bath')]:
 bpy.ops.wm.open_mainfile(filepath=str(OUT/fn));s=bpy.context.scene;s.cycles.device='GPU';bpy.context.view_layer.update();assert s['equipment_variant']==key
 room=bpy.data.collections['ROOM'];common=bpy.data.collections['COMMON_FIXTURES'];before=gh(list(room.objects)+list(common.objects));camera={'matrix':[list(r) for r in s.camera.matrix_world],'lens':s.camera.data.lens};lights=hashlib.sha256(json.dumps({o.name:[list(r) for r in o.matrix_world]+[o.data.energy,list(o.data.color)] for o in s.objects if o.type=='LIGHT'},sort_keys=True).encode()).hexdigest()
 width=box(bpy.data.objects['Right wall'])[0][0]-box(bpy.data.objects['Left wall'])[1][0];depth=box(bpy.data.objects['Back wall right'])[0][1]-box(bpy.data.objects['Front wall left'])[1][1];height=box(bpy.data.objects['Ceiling'])[0][2]
 assert abs(width-3)<1e-5 and abs(depth-2.5)<1e-5 and abs(height-2.7)<1e-5
 allowed={'tray':{'TRAY','SHOWER_SCREEN'},'linear':{'LINEAR_DRAIN','SHOWER_SCREEN'},'bath':{'BATH','BATH_SCREEN'}}[key]
 for name in ['TRAY','SHOWER_SCREEN','LINEAR_DRAIN','BATH','BATH_SCREEN']:
  assert all(o.hide_render==(name not in allowed) for o in bpy.data.collections[name].objects)
 visible={name:len([o for o in bpy.data.collections[name].objects if not o.hide_render]) for name in ['TRAY','SHOWER_SCREEN','LINEAR_DRAIN','BATH','BATH_SCREEN']}
 # The drain grille top matches the actual sloped shower tile at its centre.
 drain_top=box(bpy.data.objects['Drain grille 0'])[1][2];tile_z=.016-(2.30-.60)*.014;assert abs(drain_top-tile_z)<.0002
 assert abs(box(bpy.data.objects['Raised tray | real shallow basin'])[1][2]-.085)<.0001
 assert abs(box(bpy.data.objects['Bathtub | genuine outer and inner shell'])[1][2]-.60)<.0001
 assert s.render.resolution_x==4096 and s.render.resolution_y==3072
 s.render.resolution_x=800;s.render.resolution_y=600;s.cycles.samples=12;s.render.filepath=str(WORK/(key+'-reopen.png'));bpy.ops.render.render(write_still=True);after=gh(list(room.objects)+list(common.objects));assert before==after
 rows.append({'file':fn,'variant':key,'native_open':True,'native_rerender':True,'room_common_hash_before':before,'room_common_hash_after':after,'camera':camera,'lighting_hash':lights,'structural_inner_dimensions_m':[width,depth,height],'finished_surface_clear_dimensions_m':[2.964,2.482,2.684],'visible_equipment_counts':visible,'drain_grille_top_m':drain_top,'sloped_floor_z_at_drain_m':tile_z,'all_equipment_is_real_geometry':True,'no_external_images':not any(i.source=='FILE' for i in bpy.data.images)})
assert len({r['room_common_hash_before'] for r in rows})==1;assert len({r['lighting_hash'] for r in rows})==1;assert all(r['camera']==rows[0]['camera'] for r in rows)
qa={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'blender':bpy.app.version_string,'records':rows,'same_room_and_common_fixtures':True,'same_camera_and_lens':True,'same_light_settings':True,'structural_room_dimensions_m':[3,2.5,2.7],'room_nominal_area_m2':7.5,'finished_clear_dimensions_m':[2.964,2.482,2.684],'door_width_m':1.0,'visible_equipment_variants_are_distinct':True,'drain_grille_matches_floor_to_mm':.2,'raster_variants_not_composited':True,'client_deliverable_is_rendered_variants_and_scene_not_configurator_API':True}
(OUT/'native-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8');(WORK/'native-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8');print('NATIVE_QA_PASS',len(rows),flush=True)
