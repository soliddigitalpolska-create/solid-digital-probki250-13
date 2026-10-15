import sys,json,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/interior'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'wn01-salon.blend'));s=bpy.context.scene
preferences=bpy.context.preferences.addons['cycles'].preferences
preferences.compute_device_type='OPTIX';preferences.get_devices_for_type('OPTIX')
for device in preferences.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU'
if bpy.data.objects.get('South plaster wall'):
 bpy.data.objects.remove(bpy.data.objects['South plaster wall'],do_unlink=True)
 for o in list(s.objects):
  if o.name.startswith('Skirting') and abs(o.location.y-.015)<.0001:bpy.data.objects.remove(o,do_unlink=True)
 for name,loc,dims in [('South wall left',(2.3,-.08,1.45),(4.6,.16,2.9)),('South wall right',(5.8,-.08,1.45),(.4,.16,2.9)),('Door opening lintel',(5.1,-.08,2.55),(1,.16,.7))]:
  bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(bpy.data.materials['01 | wapienny tynk'])
s['door_opening_m']=[1.0,2.2];s['door_opening_south_x_m']=[4.6,5.6]
for chair in [o for o in s.objects if o.name.startswith('Dining chair assembly')]:
 chair.rotation_euler[2]=__import__('math').pi/2 if chair.location.x<4.55 else -__import__('math').pi/2
cam=bpy.data.objects['02-strefa-wypoczynku'];cam.location=(5.45,2.0,1.60);cam.rotation_euler=(Vector((.6,2.20,1.15))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=36
s.render.resolution_x=4096;s.render.resolution_y=2732;s.render.resolution_percentage=100;s.cycles.samples=64;s.cycles.adaptive_threshold=.02;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.camera=bpy.data.objects['01-salon'];bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'wn01-salon.blend'))
def geometry_hash():
 d={o.name:{'matrix':[list(r) for r in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices] if o.type=='MESH' else None} for o in s.objects if o.type in ['MESH','CURVE']};return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def camera_info(cam):return {'name':cam.name,'matrix':[list(r) for r in cam.matrix_world],'lens':cam.data.lens,'resolution':[s.render.resolution_x,s.render.resolution_y]}
def lighting_hash():
 return hashlib.sha256(json.dumps({o.name:{'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'},sort_keys=True).encode()).hexdigest()
bpy.context.view_layer.update();gh=geometry_hash();lh=lighting_hash();renders=[]
def render(name):
 start=time.time();s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=96;bpy.data.images['Render Result'].save_render(str(OUT/(name+'.jpg')),scene=s);s.render.image_settings.file_format='PNG';renders.append({'file':name+'.png','jpeg':name+'.jpg','seconds':round(time.time()-start,2),'camera':camera_info(s.camera),'geometry_hash':geometry_hash(),'lighting_hash':lighting_hash()});(WORK/'render-progress.json').write_text(json.dumps(renders,ensure_ascii=False,indent=2),encoding='utf-8');print('FINAL_RENDER',name,flush=True)
render('01-salon-4k')
s.camera=cam;render('02-strefa-wypoczynku-4k')
s.camera=bpy.data.objects['01-salon']
changes=[]
for name,color in [('05 | tkanina lniana sofy',(.28,.34,.25,1)),('04 | lakier szałwiowy',(.46,.36,.255,1))]:
 m=bpy.data.materials[name];p=m.node_tree.nodes['Principled BSDF'];changes.append({'material':name,'old':list(p.inputs['Base Color'].default_value),'new':color});p.inputs['Base Color'].default_value=color;m.diffuse_color=color
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'wn01-salon-wariant.blend'));render('03-wariant-materialowy-4k')
assert gh==geometry_hash();assert lh==lighting_hash();assert renders[0]['camera']==renders[2]['camera']
result={'status':'PASS','created_at':datetime.now(timezone.utc).isoformat(),'blender':bpy.app.version_string,'device':'OPTIX NVIDIA GeForce RTX 4080 SUPER','samples_max':64,'project_count':1,'renders':renders,'material_changes':changes,'same_geometry_all_renders':True,'same_lighting_all_renders':True,'same_camera_base_vs_variant':True,'room_dimensions_m':[6,5.2,2.9],'room_area_m2':31.2,'full_native_source_files':['wn01-salon.blend','wn01-salon-wariant.blend'],'no_external_images':not any(i.source=='FILE' for i in bpy.data.images),'mesh_objects':sum(o.type=='MESH' for o in s.objects),'curve_objects':sum(o.type=='CURVE' for o in s.objects),'materials':len(bpy.data.materials),'proof_scope':'One own living-room/kitchen interior, two camera views and one material variant. Not a bathroom-configurator proof and not five separate realizations.'}
(OUT/'render-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False),flush=True)
