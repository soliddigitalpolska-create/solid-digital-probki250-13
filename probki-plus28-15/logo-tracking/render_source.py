import sys, math, json, random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/probki-plus28-2026-10-15/logo-tracking';OUT.mkdir(parents=True,exist_ok=True)
FRAMES=HERE/'source-frames';FRAMES.mkdir(exist_ok=True)
W,H,N=800,450,60
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=True
s.render.resolution_x=W;s.render.resolution_y=H;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=20
s.view_settings.view_transform='Standard';s.view_settings.exposure=-1.3;s.render.film_transparent=False
s.world=bpy.data.worlds.new('Studio world');s.world.color=(.16,.16,.16)
def mat(name,col,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.4;return m
def cube(name,loc,scale,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);mod=o.modifiers.new('Rounded mechanical edges','BEVEL');mod.width=.06;mod.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL');return o
orange=mat('Own robot orange',(.63,.22,.055),.35);dark=mat('Graphite',(.08,.105,.13),.5);floor=mat('Studio floor',(.18,.22,.25));covermat=mat('Foreground occluding beam',(.055,.095,.13),.25)
cube('Base',(0,0,.23),(2.6,1.8,.4),dark)
cube('Pedestal',(0,.28,.9),(.65,.7,1.3),orange)
arm=cube('Robot arm panel',(.3,0,1.45),(2.15,.7,.62),orange)
head=cube('Robot head',(-.3,-.02,2.45),(1.55,.85,.98),orange)
cube('Ground',(0,0,-.08),(200,200,.12),floor)
cover=cube('Occluder',(0,-1.8,1.7),(.28,.22,3.6),covermat)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',72)
planes=[]
for i,(parent,width,height,label) in enumerate([(head,1.32,.65,'STARY A'),(arm,1.7,.42,'STARY B')]):
 im=Image.new('RGB',(640,300),'#e9e9e4');d=ImageDraw.Draw(im);rng=random.Random(61+i)
 for j in range(170):
  x,y=rng.randrange(15,625),rng.randrange(15,285);r=rng.choice([3,4,6]);d.ellipse((x-r,y-r,x+r,y+r),fill=rng.choice(['#a0a4a0','#687471','#c4c6bf']))
 d.rounded_rectangle((40,75,600,220),radius=18,fill='#eeeeea');d.text((110,100),label,font=font,fill='#2a403c')
 path=HERE/f'own-old-label-{i}.png';im.save(path)
 m=bpy.data.materials.new('Own procedural tracking texture '+str(i));m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path));m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.55
 y=-parent.dimensions.y/2-.006
 verts=[(-width/2,y,height/2),(width/2,y,height/2),(width/2,y,-height/2),(-width/2,y,-height/2)]
 mesh=bpy.data.meshes.new('Label plane mesh');mesh.from_pydata(verts,[],[(0,3,2,1)]);mesh.update();o=bpy.data.objects.new('Label plane '+str(i),mesh);s.collection.objects.link(o);o.parent=parent;o.location=(0,0,0);o.data.materials.append(m)
 uv=mesh.uv_layers.new(name='UVMap')
 coords={0:(0,1),1:(1,1),2:(1,0),3:(0,0)}
 for poly in mesh.polygons:
  for li in poly.loop_indices:uv.data[li].uv=coords[mesh.loops[li].vertex_index]
 planes.append(o)
bpy.ops.object.camera_add(location=(3.8,-8,4.1));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=48;s.camera=cam
for loc,power,size in [((1,-4,7),1300,5),((-4,-1,4),850,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
def proj(v):
 p=world_to_camera_view(s,cam,v);return [p.x*W,(1-p.y)*H]
data=[]
for f in range(N):
 s.frame_set(f+1)
 t=f/(N-1);head.rotation_euler=(.1*math.sin(t*math.tau),.18*math.sin(t*math.tau),.23*math.sin(t*math.tau));arm.rotation_euler=(.13*math.sin(t*math.tau+.8),-.1*math.sin(t*math.tau),-.15*math.sin(t*math.tau))
 cover.location.x=-2.9+5.8*t
 for ob in (head,arm,cover):
  ob.keyframe_insert('location',frame=f+1);ob.keyframe_insert('rotation_euler',frame=f+1)
 bpy.context.view_layer.update()
 quads=[[proj(o.matrix_world@v.co) for v in o.data.vertices] for o in planes]
 occluder=[proj(cover.matrix_world@Vector(v)) for v in cover.bound_box]
 data.append({'frame':f,'label_quads':quads,'occluder_projected_vertices':occluder})
 s.render.filepath=str(FRAMES/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
s.frame_start=1;s.frame_end=N
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'own-source-robot.blend'))
(HERE/'ground-truth.json').write_text(json.dumps({'width':W,'height':H,'fps':20,'frames':data},indent=2),encoding='utf-8')
print('RENDER_SOURCE_COMPLETE',N)
