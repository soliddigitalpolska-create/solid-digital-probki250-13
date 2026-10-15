import sys,json,math,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/bathroom';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='BA-01 | bathroom variants';s.unit_settings.system='METRIC';s['own_project']='Autorska próbka wariantowania łazienki';s['room_dimensions_m']=[3,2.5,2.7];s['room_area_m2']=7.5
P=bpy.context.preferences.addons['cycles'].preferences;P.compute_device_type='OPTIX';P.get_devices_for_type('OPTIX')
for d in P.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU'
def mat(name,c,rough=.45,metal=0,grain=False):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n['Principled BSDF'];p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if grain:
  tx=n.new('ShaderNodeTexNoise');tx.inputs['Scale'].default_value=7;tx.inputs['Detail'].default_value=3;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],tx.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=tuple(v*.82 for v in c)+(1,);r.color_ramp.elements[1].color=tuple(min(v*1.08,1) for v in c)+(1,);l.new(tx.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.13;b.inputs['Distance'].default_value=.0003;l.new(tx.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
 return m
tile=mat('Tile | warm limestone',(.63,.58,.48),.38,grain=True);grout=mat('Grout',(.57,.55,.49),.8);white=mat('Ceramic white',(.85,.87,.84),.19);brass=mat('Brushed brass',(.48,.29,.10),.25,.8);dark=mat('Drain / dark metal',(.045,.047,.041),.25,.7);oak=mat('Oak vanity',(.34,.21,.10),.4,grain=True);ceiling=mat('Ceiling plaster',(.8,.79,.73),.8);glass=mat('Real shower glass',(.97,.99,1),.03);glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=1;glass.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.45;mirror=mat('Mirror',(.90,.92,.91),.025,1)
collections={}
for name in ['ROOM','COMMON_FIXTURES','SHOWER_SCREEN','TRAY','LINEAR_DRAIN','BATH','BATH_SCREEN']:
 c=bpy.data.collections.new(name);s.collection.children.link(c);collections[name]=c
active='ROOM'
def move(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 collections[active].objects.link(o);o['logical_group']=active;return o
def box(name,loc,dims,m,bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:q=o.modifiers.new('Edge radius','BEVEL');q.width=bevel;q.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return move(o)
def cyl(name,loc,r,depth,m,rotation=None,verts=64):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 if rotation:o.rotation_euler=rotation
 q=o.modifiers.new('Rim radius','BEVEL');q.width=.002;q.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL');return move(o)
def rod(name,a,b,r,m):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(a-b).length,m,verts=32);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def ring_loft(name,center,profiles,m,power=2,N=96):
 # Profiles (z,rx,ry) form a continuous outer-to-inner surface. Rings are
 # genuine editable meshes, including the visible interior of each vessel.
 vs=[];fs=[]
 for z,rx,ry in profiles:
  for i in range(N):
   a=2*math.pi*i/N;cx=math.cos(a);cy=math.sin(a);vs.append((center[0]+rx*math.copysign(abs(cx)**(2/power),cx),center[1]+ry*math.copysign(abs(cy)**(2/power),cy),z))
 for j in range(len(profiles)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);o=bpy.data.objects.new(name,me);collections[active].objects.link(o);o['logical_group']=active
 for p in me.polygons:p.use_smooth=True
 return o
def subtract_rect(rect,hole):
 x0,y0,x1,y1=rect;a,b,c,d=hole
 if x1<=a or x0>=c or y1<=b or y0>=d:return [rect]
 out=[]
 if x0<a:out.append((x0,y0,a,y1))
 if x1>c:out.append((c,y0,x1,y1))
 u,v=max(x0,a),min(x1,c)
 if y0<b:out.append((u,y0,v,b))
 if y1>d:out.append((u,d,v,y1))
 return [r for r in out if r[2]-r[0]>.001 and r[3]-r[1]>.001]

# Room shell with a real window and a one-metre entrance.
box('Floor slab',(1.5,1.25,-.10),(3.16,2.66,.16),grout,0)
box('Left wall',(-.07,1.25,1.35),(.14,2.64,2.7),grout,0);box('Right wall',(3.07,1.25,1.35),(.14,2.64,2.7),grout,0)
for name,loc,dims in [('Back wall left',(.1,2.57,1.35),(.2,.14,2.7)),('Back wall right',(2.2,2.57,1.35),(1.6,.14,2.7)),('Back window sill',(.8,2.57,.9),(1.2,.14,1.8)),('Back window lintel',(.8,2.57,2.6),(1.2,.14,.2)),('Front wall left',(.95,-.07,1.35),(1.9,.14,2.7)),('Front wall right',(2.95,-.07,1.35),(.1,.14,2.7)),('Front door lintel',(2.4,-.07,2.5),(1,.14,.4))]:box(name,loc,dims,grout,0)
box('Ceiling',(1.5,1.25,2.77),(3.16,2.66,.14),ceiling,0)
# Visible real tile geometry, grout gaps2mm. Back tiles are clipped at window.
for row in range(9):
 z0=row*.3;z1=min((row+1)*.3,2.7)
 for col in range(5):
  a,b=col*.6,min((col+1)*.6,3)
  for j,(x0,t0,x1,t1) in enumerate(subtract_rect((a,z0,b,z1),(.2,1.8,1.4,2.5))):box(f'Back tile {row}-{col}-{j}',((x0+x1)/2,2.491,(t0+t1)/2),(x1-x0-.002,.018,t1-t0-.002),tile,.001)
 for col in range(5):
  a,b=col*.5,min((col+1)*.5,2.5)
  for x in [.009,2.991]:box(f'Side tile {x}-{row}-{col}',(x,(a+b)/2,(z0+z1)/2),(.018,b-a-.002,z1-z0-.002),tile,.001)
for row in range(5):
 for col in range(5):
  x0,x1=col*.6,min((col+1)*.6,3);y0,y1=row*.5,min((row+1)*.5,2.5)
  for j,(a,b,c,d) in enumerate(subtract_rect((x0,y0,x1,y1),(.26,2.27,.94,2.33))):
   # Flush-entry shower zone has a real shallow floor fall towards drain.
   verts=[]
   for x,y in [(a+.001,b+.001),(c-.001,b+.001),(c-.001,d-.001),(a+.001,d-.001)]:
    z=.016-(max(0,min(y,2.30)-.60)*.014 if x<1.1 and y>.6 else 0);verts.append((x,y,z))
   me=bpy.data.meshes.new('Floor tile');me.from_pydata(verts,[],[(0,1,2,3)]);me.materials.append(tile);o=bpy.data.objects.new(f'Floor tile {row}-{col}-{j}',me);collections['ROOM'].objects.link(o);o['logical_group']='ROOM'
for x in [.2,1.4]:box('Window jamb',(x,2.51,2.15),(.025,.08,.72),white,.002)
for z in [1.8,2.5]:box('Window rail',(.8,2.51,z),(1.22,.08,.025),white,.002)
box('Window glass',(.8,2.55,2.15),(1.17,.008,.67),glass,0)
box('Stone window sill',(.8,2.44,1.80),(1.3,.20,.035),white,.003)

active='COMMON_FIXTURES'
# Floating oak vanity, true hollow ceramic washbasin and mirror.
box('Vanity carcass',(2.68,1.32,.64),(.56,1.35,.43),oak,.012)
for y in [.985,1.655]:box('Vanity drawer',(2.387,y,.65),(.025,.65,.37),oak,.006);rod('Vanity handle',(2.365,y-.19,.78),(2.365,y+.19,.78),.004,brass)
box('Vanity stone top',(2.66,1.32,.88),(.62,1.43,.045),white,.008)
ring_loft('Hollow ceramic washbasin',(2.62,1.30),[(.903,.09,.16),(.92,.16,.24),(1.03,.205,.295),(1.04,.20,.29),(1.04,.18,.27),(.94,.12,.20),(.923,.025,.04)],white,2.5)
cyl('Washbasin waste',(2.62,1.30,.925),.022,.006,brass)
rod('Wall tap spout',(2.98,1.30,1.16),(2.65,1.30,1.16),.012,brass);rod('Spout outlet',(2.65,1.30,1.16),(2.65,1.30,1.12),.012,brass)
cyl('Tap control',(2.968,1.65,1.12),.034,.028,brass,(0,math.pi/2,0))
box('Mirror silver face',(2.974,1.32,1.75),(.014,1.2,1.05),mirror,.022)
for y in [.705,1.935]:box('Mirror frame',(2.96,y,1.75),(.028,.018,1.08),brass,.003)
for z in [1.21,2.29]:box('Mirror frame',(2.96,1.32,z),(.028,1.25,.018),brass,.003)
# Real wall-hung WC with an open bowl and a separate seat ring.
box('WC mount',(1.73,2.455,.37),(.36,.09,.29),white,.04)
ring_loft('WC ceramic bowl',(1.73,2.10),[(.21,.12,.18),(.25,.16,.24),(.36,.195,.31),(.43,.20,.32),(.445,.195,.31),(.445,.15,.25),(.38,.125,.20),(.29,.045,.07),(.28,.008,.012)],white,2.3)
ring_loft('WC seat ring',(1.73,2.10),[(.45,.19,.305),(.47,.195,.31),(.48,.19,.305),(.48,.145,.245),(.46,.14,.24),(.45,.145,.245),(.45,.19,.305)],white,2.3)
box('Dual flush plate',(1.73,2.477,1.10),(.24,.022,.14),brass,.007)
for x in [1.68,1.79]:box('Flush button',(x,2.46,1.10),(.07,.008,.09),brass,.005)
rod('Toilet paper holder',(2.20,2.48,.68),(2.20,2.32,.68),.008,brass);roll=cyl('Toilet paper roll',(2.20,2.31,.68),.052,.11,white,(math.pi/2,0,0))
# Shared real shower pipe, rainhead and controls, stays fixed in all variants.
rod('Shower riser',(.52,2.448,.94),(.52,2.448,2.18),.012,brass);rod('Rainhead arm',(.52,2.448,2.18),(.52,2.05,2.18),.012,brass);cyl('Rain head',(.52,2.05,2.16),.115,.022,brass)
for x in [.45,.60]:cyl('Shower control',(x,2.46,1.10),.028,.028,brass,(math.pi/2,0,0))
rod('Towel rail',(2.973,.45,1.05),(2.66,.45,1.05),.008,brass)
box('Folded hand towel',(2.72,.46,.92),(.14,.10,.26),white,.025)

active='SHOWER_SCREEN'
box('Shower glass fixed panel',(1.10,1.60,1.13),(.010,1.58,2.18),glass,.001)
rod('Glass top brace',(1.10,2.38,2.18),(.02,2.38,2.18),.006,brass)
for y in [.84,2.36]:box('Screen floor clip',(1.10,y,.043),(.026,.045,.06),brass,.003)
active='TRAY'
ring_loft('Raised tray | real shallow basin',(.58,1.5),[(.016,.45,.90),(.080,.45,.90),(.085,.44,.89),(.085,.405,.855),(.050,.40,.85),(.048,.005,.01)],white,8)
cyl('Tray waste',(.60,2.25,.052),.044,.007,brass)
active='LINEAR_DRAIN'
box('Linear drain recessed body',(.60,2.30,-.023),(.68,.06,.026),dark,.002)
for i in range(22):box('Drain grille '+str(i),(.275+i*.031,2.30,-.0113),(.009,.055,.007),brass,.001)
active='BATH'
ring_loft('Bathtub | genuine outer and inner shell',(.56,1.49),[(.016,.30,.69),(.10,.38,.80),(.55,.43,.88),(.59,.43,.88),(.60,.42,.87),(.60,.36,.81),(.52,.34,.77),(.18,.23,.63),(.16,.01,.02)],white,5)
cyl('Bath waste',(.56,2.06,.176),.026,.007,brass)
active='BATH_SCREEN'
box('Bath shower screen',(1.00,1.94,1.20),(.010,.85,1.20),glass,.001)
for z in [.65,1.75]:box('Bath screen hinge',(1.00,2.34,z),(.03,.06,.06),brass,.003)

def area(name,loc,target,energy,size,color):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Daylight through real window',(.8,3.35,2.4),(1.6,1.2,.7),520,1.6,(.84,.91,1))
area('Soft ceiling light',(1.65,1.1,2.65),(1.5,1.25,.4),120,1.3,(1,.88,.72))
area('Camera soft fill',(2.4,.3,2.1),(1.3,1.8,.9),35,1.1,(1,.93,.83))
s.world=bpy.data.worlds.new('Neutral daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.75,.84,1,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.12
bpy.ops.object.camera_add(location=(2.55,-.18,1.65));cam=bpy.context.object;cam.name='BA-01 fixed camera';cam.rotation_euler=(Vector((1.45,1.55,1.20))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=19.5;cam.data.clip_start=.03;s.camera=cam
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.max_bounces=12;s.cycles.transmission_bounces=10;s.cycles.diffuse_bounces=5;s.cycles.glossy_bounces=6;s.cycles.adaptive_threshold=.02;s.render.resolution_x=4096;s.render.resolution_y=3072;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';bpy.context.preferences.filepaths.save_version=0
def select_variant(name):
 enabled={'tray':{'TRAY','SHOWER_SCREEN'},'linear':{'LINEAR_DRAIN','SHOWER_SCREEN'},'bath':{'BATH','BATH_SCREEN'}}[name]
 for k,c in collections.items():
  if k in ['ROOM','COMMON_FIXTURES']:continue
  for o in c.objects:o.hide_render=k not in enabled;o.hide_viewport=k not in enabled
 s['equipment_variant']=name;bpy.context.view_layer.update()
select_variant('tray')
script=bpy.data.texts.new('build_bathroom.py');script.write(Path(__file__).read_text(encoding='utf-8'))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ba01-base.blend'))
s.render.resolution_x=1200;s.render.resolution_y=900;s.cycles.samples=24;s.render.filepath=str(WORK/'preview-tray.png');bpy.ops.render.render(write_still=True)
print('NATIVE_BATHROOM_BUILT',flush=True)
