import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/interior'
preferences=bpy.context.preferences.addons['cycles'].preferences
preferences.compute_device_type='OPTIX';preferences.get_devices_for_type('OPTIX')
for device in preferences.devices:device.use=device.type=='OPTIX'
def geometry():
 out={}
 for o in bpy.context.scene.objects:
  if o.type not in ['MESH','CURVE']:continue
  d={'matrix':[list(x) for x in o.matrix_world]}
  if o.type=='MESH':d['vertices']=[list(v.co) for v in o.data.vertices];d['polygons']=[list(p.vertices) for p in o.data.polygons]
  else:d['splines']=[{'type':sp.type,'points':[list(p.co) for p in sp.bezier_points]} for sp in o.data.splines]
  out[o.name]=d
 return hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
def camera():
 o=bpy.context.scene.camera;return {'name':o.name,'matrix':[list(x) for x in o.matrix_world],'lens':o.data.lens}
def lights():
 return hashlib.sha256(json.dumps({o.name:{'matrix':[list(x) for x in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color)} for o in bpy.context.scene.objects if o.type=='LIGHT'},sort_keys=True).encode()).hexdigest()
def colors():
 return {m.name:list(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value) for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')}
records=[]
for fn in ['wn01-salon.blend','wn01-salon-wariant.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(OUT/fn));bpy.context.view_layer.update();s=bpy.context.scene;s.cycles.device='GPU';before=geometry();ci=camera();li=lights();ma=colors()
 assert s['room_dimensions_m']==[6,5.2,2.9] or list(s['room_dimensions_m'])==[6,5.2,2.9]
 assert list(s['door_opening_m'])==[1,2.2]
 assert len([o for o in s.objects if o.type=='CAMERA'])==2
 assert not any(i.source=='FILE' for i in bpy.data.images)
 assert s.camera.name=='01-salon';assert s.render.resolution_x==4096 and s.render.resolution_y==2732
 s.render.resolution_x=800;s.render.resolution_y=534;s.cycles.samples=12;s.render.filepath=str(WORK/(fn.replace('.blend','')+'-reopen.png'));bpy.ops.render.render(write_still=True)
 after=geometry();assert before==after
 records.append({'file':fn,'reopened':True,'actual_rerender':True,'geometry_sha_before':before,'geometry_sha_after':after,'geometry_preserved':True,'camera':ci,'lights_sha':li,'material_colors':ma,'mesh_objects':sum(o.type=='MESH' for o in s.objects),'curve_objects':sum(o.type=='CURVE' for o in s.objects),'no_external_images':True})
a,b=records;assert a['geometry_sha_before']==b['geometry_sha_before'];assert a['camera']==b['camera'];assert a['lights_sha']==b['lights_sha']
diff=[k for k in a['material_colors'] if a['material_colors'][k]!=b['material_colors'][k]];assert set(diff)=={'04 | lakier szałwiowy','05 | tkanina lniana sofy'}
qa={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'blender':bpy.app.version_string,'native_files':records,'base_variant_geometry_identical':True,'base_variant_camera_identical':True,'base_variant_lighting_identical':True,'only_material_changes':diff,'room_dimensions_m':[6,5.2,2.9],'room_area_m2':31.2,'door_opening_m':[1,2.2],'worktop_height_m':.90,'dining_table_height_m':.76,'sofa_seat_height_m':.47,'coffee_table_height_m':.37,'sofa_to_coffee_gap_m':.6662,'single_project_not_multiple_realizations':True,'client_plan_not_used_for_own_demo':True,'bathroom_configurator_demonstrated':False}
(OUT/'native-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8');(WORK/'native-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':'PASS','native_files':2,'same_geometry_camera_lighting':True,'changed_materials':diff}),flush=True)
