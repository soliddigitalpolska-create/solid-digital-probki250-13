import sys,json,math,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
OUT=ROOT/'outputs/probki-plus28-2026-10-15/wood-plan';OUT.mkdir(parents=True,exist_ok=True)
WORK=Path(__file__).resolve().parent
START=time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='WOOD-01 — assembly';s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS';s['own_sample']='Własna dokumentacja demonstracyjna, nie realizacja klienta';s['nominal_mm']=[800,350,600]
parts=[
 {'id':'A1','name':'Bok lewy','size_mm':[18,350,600],'center_mm':[-391,0,300],'cut_mm':[600,350,18],'family':'A'},
 {'id':'A2','name':'Bok prawy','size_mm':[18,350,600],'center_mm':[391,0,300],'cut_mm':[600,350,18],'family':'A'},
 {'id':'B1','name':'Półka dolna','size_mm':[764,350,18],'center_mm':[0,0,109],'cut_mm':[764,350,18],'family':'B'},
 {'id':'B2','name':'Półka górna','size_mm':[764,350,18],'center_mm':[0,0,559],'cut_mm':[764,350,18],'family':'B'},
 {'id':'C1','name':'Rygiel tylny dolny','size_mm':[764,18,70],'center_mm':[0,166,65],'cut_mm':[764,70,18],'family':'C'},
 {'id':'C2','name':'Rygiel tylny górny','size_mm':[764,18,70],'center_mm':[0,166,515],'cut_mm':[764,70,18],'family':'C'},
]
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.4;return m
wood=mat('Sklejka brzozowa — własny shader',(.62,.40,.20));metal=mat('Łączniki — stal',(.12,.14,.16));metal.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.8
n=wood.node_tree.nodes;l=wood.node_tree.links;p=n['Principled BSDF'];tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=6;tex.inputs['Detail'].default_value=2;coord=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(2,40,4);l.new(coord.outputs['Generated'],v.inputs[0]);l.new(v.outputs[0],tex.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.38,.20,.075,1);r.color_ramp.elements[1].color=(.76,.55,.30,1);l.new(tex.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
objects={};holes=[];screws=[]
for d in parts:
 bpy.ops.mesh.primitive_cube_add(size=1,location=[v/1000 for v in d['center_mm']]);o=bpy.context.object;o.name=d['id']+' | '+d['name'];o.dimensions=[v/1000 for v in d['size_mm']];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(wood);o['part_id']=d['id'];o['cut_mm']=d['cut_mm'];o['material']='Sklejka brzozowa 18 mm';objects[d['id']]=o

# A real native drill guide marks every connection; the guide is retained in
# the source as a separate non-rendering collection. It is not a fake texture.
guides=bpy.data.collections.new('DRILL_GUIDES — 16 osi pilota Ø3');s.collection.children.link(guides)
for level in [0,1]:
 for side in [-1,1]:
  for y in [-115,115]:holes.append({'target':'B'+str(level+1),'side':side,'y_mm':y,'z_mm':[109,559][level]})
  for z in [[45,85],[495,535]][level]:holes.append({'target':'C'+str(level+1),'side':side,'y_mm':166,'z_mm':z})
for i,h in enumerate(holes,1):
 side=h['side'];center=(side*.38,h['y_mm']/1000,h['z_mm']/1000)
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.0015,depth=.044,location=center,rotation=(0,math.pi/2,0));g=bpy.context.object;g.name=f'P{i:02d} — pilot Ø3';g['hole']=h
 for c in list(g.users_collection):c.objects.unlink(g)
 guides.objects.link(g);g.hide_render=True;g.hide_set(True)
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.002,depth=.04,location=center,rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=f'S{i:02d} — wkręt 4×40';o.data.materials.append(metal);o['connector']='4×40 mm';o['target']=h['target'];screws.append(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.004,depth=.001,location=(side*.4005,h['y_mm']/1000,h['z_mm']/1000),rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=f'H{i:02d} — łeb wkręta';o.data.materials.append(metal);screws.append(o)

for o in objects.values():
 mod=o.modifiers.new('Zaokrąglenie krawędzi 0.6 mm','BEVEL');mod.width=.0006;mod.segments=3;o.modifiers.new('Normalne','WEIGHTED_NORMAL')

target=Vector((0,0,.3))
bpy.ops.object.camera_add(location=(1.5,-1.8,1.35));cam=bpy.context.object;cam.name='Camera — same source geometry';cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;s.camera=cam
for name,loc,power,size in [('Key',(-1.5,-1.5,2.5),320,2),('Rim',(1.8,.8,1.6),250,1.6),('Fill',(.5,-2,.5),110,1.5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.9,.94,1,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.film_transparent=True;s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='AgX'
bpy.context.preferences.filepaths.save_version=0
script=bpy.data.texts.new('build_native.py');script.write(Path(__file__).read_text(encoding='utf-8'))
bpy.context.view_layer.update()
saved={k:list(v.location) for k,v in objects.items()}
def render(name):
 s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('RENDER',name,flush=True)
render('01-regal-zlozony')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'regal-wood01.blend'))
for o in screws:o.hide_render=True
exploded={'A1':(-.2,0,0),'A2':(.2,0,0),'B1':(0,-.26,-.04),'B2':(0,-.26,.12),'C1':(0,.25,0),'C2':(0,.25,.08)}
for k,o in objects.items():o.location=Vector(saved[k])+Vector(exploded[k])
cam.data.ortho_scale=2.0;render('02-widok-rozstrzelony')
for k,o in objects.items():o.location=saved[k]
cam.data.ortho_scale=1.45
for idx,ids in enumerate([['A1','A2','C1','C2'],['A1','A2','C1','C2','B1'],['A1','A2','C1','C2','B1','B2'],list(objects)],1):
 for k,o in objects.items():o.hide_render=k not in ids
 for o in screws:o.hide_render=idx!=4
 render('etap-'+str(idx))
for o in objects.values():o.hide_render=False
for o in screws:o.hide_render=False
bpy.context.view_layer.update()
# Native source always reopens in the assembled state.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'regal-wood01.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in objects.values():o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'regal-wood01.glb'),export_format='GLB',use_selection=True)
manifest={'created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'blender':bpy.app.version_string,'nominal_mm':[800,350,600],'parts':parts,'pilot_axes':holes,'pilot_diameter_mm':3,'screws_count':16,'screw_nominal_mm':[4,40],'material_thickness_mm':18,'cut_dimensions_are_finished_dimensions':True,'saw_kerf_mm':3,'panel_total_m2':round(sum(d['cut_mm'][0]*d['cut_mm'][1] for d in parts)/1e6,6),'no_external_images':not any(i.source=='FILE' for i in bpy.data.images),'renders':['01-regal-zlozony','02-widok-rozstrzelony','etap-1','etap-2','etap-3','etap-4'],'native_assembly_saved':True,'seconds':round(time.time()-START,2)}
(OUT/'geometry-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False),flush=True)
