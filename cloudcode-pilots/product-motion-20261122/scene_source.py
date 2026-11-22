import bpy, math, os
from mathutils import Vector
from pathlib import Path
OUT=str(Path(__file__).parent/'render')
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.5):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; return m
cream=mat('Warm studio',(.8,.76,.66)); green=mat('Forest green',(.035,.15,.10)); rope=mat('Natural rope',(.62,.47,.29)); metal=mat('Dark metal',(.12,.15,.14)); wood=mat('Honey timber',(.40,.22,.09)); seat=mat('Canvas',(.18,.35,.24))
def bar(name,a,b,r,material):
 d=Vector(b)-Vector(a); mid=(Vector(a)+Vector(b))/2
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=d.length,location=mid)
 o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
for x in [-1.7,1.7]:
 for y in [-.8,.8]:bar('Frame',(x,y,0),(x,0,2.7),.075,wood)
bar('Top beam',(-1.82,0,2.7),(1.82,0,2.7),.095,wood)
bpy.ops.object.empty_add(location=(0,0,2.55)); pivot=bpy.context.object;pivot.name='Swing motion'
parts=[]
for x in [-.56,.56]:
 for y in [-.32,.32]:parts.append(bar('Rope',(x,0,2.65),(x,y,.9),.018,rope))
bpy.ops.mesh.primitive_torus_add(major_radius=.65,minor_radius=.055,major_segments=64,minor_segments=12,location=(0,0,.9));ring=bpy.context.object;ring.scale.y=.75;ring.data.materials.append(green);parts.append(ring)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=12,location=(0,0,.885),scale=(.63,.47,.025));o=bpy.context.object;o.data.materials.append(seat);parts.append(o)
for o in parts:
 matrix=o.matrix_world.copy();o.parent=pivot;o.matrix_world=matrix
for f,angle in [(1,-.08),(31,.08),(61,-.08),(91,.08),(121,-.08),(151,.08)]:
 pivot.rotation_euler[0]=angle;pivot.keyframe_insert(data_path='rotation_euler',frame=f)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.03));bpy.context.object.data.materials.append(cream)
bpy.ops.object.camera_add(location=(5,-8,5.2));cam=bpy.context.object;target=Vector((0,0,1.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.2;bpy.context.scene.camera=cam
for f,pos in [(1,(5,-8,5.2)),(151,(3.5,-8.5,4.5))]:
 cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f)
for pos,power,size in [((1,-3,7),1000,5),((-4,1,4),600,4)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False;s.cycles.device='CPU';s.render.threads_mode='FIXED';s.render.threads=8
s.world.color=(.6,.6,.6);s.render.resolution_x=540;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.fps=10;s.frame_start=1;s.frame_end=150;s.render.image_settings.file_format='PNG';s.render.filepath=OUT+'/frame_'
s.view_settings.view_transform='AgX';s.render.film_transparent=False
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/original-scene.blend')
s.frame_set(1);bpy.ops.render.render(animation=True)
