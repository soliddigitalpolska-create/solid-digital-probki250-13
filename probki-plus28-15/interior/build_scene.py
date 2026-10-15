import sys,math,json,random,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/interior';OUT.mkdir(parents=True,exist_ok=True)
random.seed(19);bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='WN-01 | salon i aneks';s.unit_settings.system='METRIC';s['own_sample']='Jedna własna scena wnętrza, nie płatna realizacja klienta';s['room_dimensions_m']=[6,5.2,2.9];s['room_area_m2']=31.2
def material(name,c,rough=.5,metal=0,noise=0,wood=False):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n['Principled BSDF'];p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise or wood:
  tx=n.new('ShaderNodeTexNoise');tx.inputs['Scale'].default_value=5 if wood else 150;tx.inputs['Detail'].default_value=3
  coord=n.new('ShaderNodeTexCoord')
  if wood:
   scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1,25,5);l.new(coord.outputs['Generated'],scale.inputs[0]);l.new(scale.outputs[0],tx.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=tuple(v*.65 for v in c)+(1,);r.color_ramp.elements[1].color=tuple(min(v*1.2,1) for v in c)+(1,);l.new(tx.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
  else:l.new(coord.outputs['Object'],tx.inputs['Vector'])
  b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.18;b.inputs['Distance'].default_value=.00045 if wood else noise;l.new(tx.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
 return m
plaster=material('01 | wapienny tynk',(.77,.745,.685),.8,noise=.00045);oak=material('02 | dąb naturalny',(.43,.285,.15),.36,wood=True);oakdark=material('03 | dąb orzechowy',(.22,.12,.062),.35,wood=True);sage=material('04 | lakier szałwiowy',(.205,.27,.215),.32);linen=material('05 | tkanina lniana sofy',(.63,.55,.43),.9,noise=.0006);cushion=material('06 | tkanina oliwkowa',(.24,.30,.20),.9,noise=.0005);ivory=material('07 | tkanina jasna',(.84,.80,.70),.85,noise=.0004);black=material('08 | grafit',(.018,.022,.02),.29,.65);brass=material('09 | mosiądz',(.55,.35,.13),.26,.8);terracotta=material('10 | terakota',(.43,.18,.095),.6,noise=.0004);leafmat=material('11 | liść',(.095,.18,.065),.45);stone=material('12 | jasny kamień',(.75,.72,.65),.29,noise=.00018);rug=material('13 | dywan boucle',(.66,.62,.53),.95,noise=.0018);paper=material('14 | papier',(.86,.80,.68),.85);sinkmat=material('15 | granit zlewu',(.045,.05,.044),.44,noise=.0003)
glass=material('16 | szkło okienne',(.97,.98,1),.02);glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=1;glass.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.45
def box(name,loc,dim,mat,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  m=o.modifiers.new('Real bevel','BEVEL');m.width=bevel;m.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cyl(name,loc,radius,depth,mat,verts=64):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(mat);m=o.modifiers.new('Rim bevel','BEVEL');m.width=.003;m.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL');return o
def rod(name,a,b,r,mat):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,mat,24);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def curve(name,pts,r,mat):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=3;sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for q,p in zip(sp.bezier_points,pts):q.co=p;q.handle_left_type=q.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.data.materials.append(mat);return o
def lathe(name,xy,profile,mat):
 vs=[];fs=[];N=64
 for z,r in profile:
  for i in range(N):a=2*math.pi*i/N;vs.append((xy[0]+r*math.cos(a),xy[1]+r*math.sin(a),z))
 for j in range(len(profile)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mat);o=bpy.data.objects.new(name,me);s.collection.objects.link(o)
 for p in me.polygons:p.use_smooth=True
 return o

# Physical room shell: a real window opening, four walls, floor and ceiling.
box('Floor structure',(3,2.6,-.075),(6.2,5.4,.15),plaster,0)
for row in range(26):
 y=.1+row*.2;offset=.6 if row%2 else 0
 for j in range(-1,6):
  a=max(0,j*1.2+offset);b=min(6,(j+1)*1.2+offset)
  if b-a>.02:box(f'Oak plank {row}-{j}',((a+b)/2,y,.008),(b-a-.0015,.1985,.016),oak,.0007)
box('West plaster wall',(-.08,2.6,1.45),(.16,5.36,2.9),plaster,.003);box('North plaster wall',(3,5.28,1.45),(6.16,.16,2.9),plaster,.003)
box('South plaster wall',(3,-.08,1.45),(6.16,.16,2.9),plaster,.003)
for name,loc,dim in [('East sill',(6.08,2.6,.22),(.16,5.2,.44)),('East lintel',(6.08,2.6,2.82),(.16,5.2,.16)),('East front pier',(6.08,.55,1.58),(.16,1.1,2.28)),('East rear pier',(6.08,5,1.58),(.16,.4,2.28))]:box(name,loc,dim,plaster,.003)
box('Ceiling',(3,2.6,2.98),(6.16,5.36,.16),plaster,0)
for y in [1.12,2.34,3.56,4.78]:box('Window frame upright',(6.02,y,1.59),(.07,.035,2.3),black,.002)
for z in [.46,2.72]:box('Window frame sill',(6.02,2.95,z),(.07,3.7,.035),black,.002)
box('Glass',(6.045,2.95,1.59),(.008,3.65,2.22),glass,0)
box('Oak window sill',(5.94,2.95,.46),(.3,3.75,.035),oak,.005)
for loc,dim in [((.015,2.6,.065),(.03,5.2,.10)),((3,5.185,.065),(6,.03,.10)),((3,.015,.065),(6,.03,.10)),((5.985,.55,.065),(.03,1.1,.10))]:box('Skirting',loc,dim,plaster,.003)

# Curtain folds are genuine wavy surfaces, not a composited picture.
for start,length in [(1.12,.55),(4.22,.55)]:
 verts=[];faces=[];NY=72;NZ=8
 for j in range(NZ+1):
  z=.50+2.19*j/NZ
  for i in range(NY+1):y=start+length*i/NY;x=5.82+.045*math.sin(i/NY*10*math.pi)+.008*math.sin(z*2);verts.append((x,y,z))
 for j in range(NZ):
  for i in range(NY):a=j*(NY+1)+i;faces.append((a,a+1,a+NY+2,a+NY+1))
 me=bpy.data.meshes.new('Linen curtain folds');me.from_pydata(verts,[],faces);me.materials.append(ivory);o=bpy.data.objects.new('Curtain | real fabric geometry',me);s.collection.objects.link(o)
 for p in me.polygons:p.use_smooth=True

# Built-in kitchen, 600mm modules. Worktop opening and actual recessed sink.
for i in range(5):
 x=.5+i*.6;box('Kitchen carcass '+str(i),(x,4.87,.46),(.594,.60,.82),sage,.006);box('Kitchen door '+str(i),(x,4.55,.47),(.585,.025,.73),sage,.005);rod('Brass handle',(x-.14,4.528,.73),(x+.14,4.528,.73),.004,brass)
box('Kitchen plinth',(1.7,4.91,.09),(2.98,.48,.13),black,.003)
counter=box('Stone worktop',(1.7,4.85,.90),(3.02,.67,.045),stone,.008)
cut=box('Sink opening cutter',(1.18,4.84,.90),(.57,.40,.3),stone,0);m=counter.modifiers.new('Actual sink opening','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.context.view_layer.objects.active=counter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)
box('Sink bottom',(1.18,4.84,.76),(.55,.38,.025),sinkmat,.025)
for name,loc,dim in [('Sink front',(1.18,4.645,.825),(.57,.018,.14)),('Sink rear',(1.18,5.035,.825),(.57,.018,.14)),('Sink left',(.90,4.84,.825),(.018,.4,.14)),('Sink right',(1.46,4.84,.825),(.018,.4,.14))]:box(name,loc,dim,sinkmat,.006)
cyl('Sink drain',(1.18,4.84,.779),.025,.006,black)
curve('Arched kitchen tap',[(1.18,5.10,.92),(1.18,5.10,1.2),(1.18,4.97,1.28),(1.18,4.84,1.19)],.012,brass);rod('Tap lever',(1.23,5.10,.96),(1.23,5.10,1.08),.008,brass)
box('Hob',(2.65,4.85,.93),(.56,.48,.008),black,.008)
for x in [2.48,2.8]:
 for y in [4.73,4.98]:cyl('Induction ring',(x,y,.935),.075,.002,sinkmat)
box('Backsplash',(1.7,5.185,1.20),(3.02,.025,.58),stone,.002)
box('Oak display shelf',(1.7,5.02,1.87),(3.0,.34,.035),oak,.006)
for x in [.45,1.35,2.5]:
 lathe('Kitchen ceramic jar',(x,4.98),[(1.888,.045),(1.91,.065),(2.01,.065),(2.035,.04),(2.05,.04)],ivory)
for x in [1.76,1.84,1.91]:box('Cookbook',(x,5.04,2.03),(.055,.13,.28),sage,.002)
box('Fridge tall unit',(3.52,4.89,1.22),(.62,.62,2.4),sage,.006)
box('Fridge lower door',(3.52,4.565,.55),(.6,.025,.88),sage,.006);box('Fridge upper door',(3.52,4.565,1.74),(.6,.025,1.46),sage,.006)
rod('Fridge handle',(3.29,4.54,1.25),(3.29,4.54,1.60),.006,brass)

# A three-seat, genuinely modeled linen sofa and separate cushions.
box('Sofa plinth',(.70,2,.25),(.92,2.72,.25),linen,.10)
box('Sofa back',(.23,2,.68),(.23,2.78,.78),linen,.10)
for y in [.55,3.45]:box('Sofa arm',(.70,y,.48),(1.05,.25,.70),linen,.10)
for i,y in enumerate([1.02,1.99,2.96]):
 box('Seat cushion '+str(i),(.74,y,.47),(.86,.92,.20),linen,.085)
 o=box('Back cushion '+str(i),(.42,y,.80),(.25,.92,.58),linen,.105);o.rotation_euler[1]=-.12
for x in [.30,1.03]:
 for y in [.74,3.25]:cyl('Sofa foot',(x,y,.08),.035,.12,oakdark)
for y,z,ma,rot in [(.87,.85,cushion,-.17),(3.12,.83,ivory,.17)]:
 o=box('Loose textile pillow',(.61,y,z),(.17,.48,.48),ma,.075);o.rotation_euler=(.12,.10,rot)
box('Textile rug',(2.4,2.05,.024),(2.55,2.95,.018),rug,.06)
table=cyl('Travertine coffee top',(2.35,2.03,.37),.62,.055,stone);table.scale=(.74,1,1)
base=cyl('Coffee table base',(2.35,2.03,.19),.25,.31,stone);base.scale=(.8,1,1)
for i in range(2):o=box('Coffee table book',(2.25,1.85,.42+i*.023),(.27,.21,.022),paper,.002);o.rotation_euler[2]=-.12+i*.18
lathe('Ceramic coffee cup',(2.49,2.20),[(.40,.028),(.41,.040),(.47,.040),(.48,.037),(.474,.033),(.416,.031)],ivory)

# Original abstract wall art; all colored forms are native geometry.
box('Canvas',(.025,2.2,1.85),(.014,1.65,.95),paper,.001)
for y in [1.35,3.05]:box('Artwork vertical frame',(.044,y,1.85),(.035,.025,1.0),oakdark,.003)
for z in [1.35,2.35]:box('Artwork horizontal frame',(.044,2.2,z),(.035,1.725,.025),oakdark,.003)
o=cyl('Artwork clay disc',(.039,2.0,1.96),.27,.004,terracotta);o.rotation_euler[1]=math.pi/2
box('Artwork sage rectangle',(.043,2.56,1.71),(.008,.34,.42),sage,.002)
curve('Artwork line',[ (.052,1.55,1.57),(.052,1.92,1.55),(.052,2.20,1.75),(.052,2.52,2.18)],.009,black)

# Dining table and two separate, fully modeled oak chairs.
cyl('Dining table top',(4.55,4.05,.76),.56,.035,oak);cyl('Dining pedestal',(4.55,4.05,.38),.12,.70,oakdark)
for x,angle in [(3.62,-math.pi/2),(5.48,math.pi/2)]:
 bpy.ops.object.empty_add(location=(x,4.05,0));parent=bpy.context.object;parent.name='Dining chair assembly';start=set(bpy.data.objects)
 seat=cyl('Chair seat',(0,0,.47),.25,.065,linen);seat.scale=(1,.94,1)
 for xx in [-.16,.16]:
  for yy in [-.16,.16]:rod('Chair leg',(xx,yy,.43),(xx*1.25,yy*1.2,.025),.017,oakdark)
 for xx in [-.21,.21]:rod('Chair back upright',(xx,.17,.44),(xx,.20,.89),.018,oak)
 box('Chair backrest',(0,.20,.79),(.45,.065,.21),oak,.045)
 for o in set(bpy.data.objects)-start:o.parent=parent
 parent.rotation_euler[2]=angle
lathe('Dining vase',(4.6,4.05),[(.78,.06),(.80,.09),(.91,.085),(1.00,.035),(1.02,.037)],terracotta)
for k in range(3):
 x=4.6+(k-1)*.04;curve('Vase branch',[(4.6,4.05,1.0),(x,4.07,1.25),(x+.05,4.10,1.36+k*.025)],.003,oakdark)

# Tall native plant: curved leaf blades, with real veins and stems.
px,py=5.55,4.87
lathe('Plant pot',(px,py),[(.02,.14),(.05,.18),(.40,.22),(.43,.23),(.44,.23),(.44,.20),(.39,.19)],terracotta)
cyl('Pot soil',(px,py,.40),.195,.02,oakdark)
for j in range(17):
 a=random.uniform(0,2*math.pi);z=random.uniform(.8,1.7);reach=random.uniform(.25,.60);p0=Vector((px,py,.4));p1=Vector((px+math.cos(a)*reach*.55,py+math.sin(a)*reach*.55,z));tip=Vector((px+math.cos(a)*reach,py+math.sin(a)*reach,z+.12));curve('Plant stalk',[p0,p1,tip],.0035,leafmat)
 direction=(tip-p1).normalized();side=Vector((-math.sin(a),math.cos(a),0));verts=[];faces=[]
 for k in range(13):
  t=k/12;center=p1+(tip-p1)*t+Vector((0,0,.08*math.sin(t*math.pi)));w=.075*math.sin(t*math.pi)
  for sidefactor in [-1,0,1]:verts.append(tuple(center+side*w*sidefactor+Vector((0,0,-abs(sidefactor)*.018*math.sin(t*math.pi)))))
 for k in range(12):
  for q in range(2):a1=k*3+q;faces.append((a1,a1+1,a1+4,a1+3))
 me=bpy.data.meshes.new('Curved leaf blade');me.from_pydata(verts,[],faces);me.materials.append(leafmat);o=bpy.data.objects.new('Plant leaf',me);s.collection.objects.link(o)
 for p in me.polygons:p.use_smooth=True

# Pendant over dining area, wall plugs and a physical task light.
rod('Pendant cable',(4.55,4.05,2.9),(4.55,4.05,2.10),.003,black)
lathe('Pendant shade',(4.55,4.05),[(2.08,.35),(2.10,.36),(2.24,.27),(2.30,.06)],ivory)
for z in [.28,1.12]:box('Power plate',(.013,3.9,z),(.018,.09,.085),ivory,.008)

def area(name,loc,target,power,size,color=(1,.9,.77),shape='DISK'):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape=shape;o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Window daylight',(7.0,2.8,2.5),(2.2,2.8,1),1250,3.4,(.83,.90,1))
area('Soft photographic fill',(4.3,.4,2.5),(1.5,3.2,.8),100,3,(1,.91,.78))
area('Pendant soft',(4.55,4.05,2.08),(4.55,4.05,.7),30,.34,(1,.76,.50))
area('Kitchen under shelf',(1.7,4.99,1.83),(1.7,4.8,.8),28,2.4,(1,.82,.58))
bpy.ops.object.light_add(type='SUN',location=(9,1,7));sun=bpy.context.object;sun.name='Afternoon sun';sun.rotation_euler=(Vector((1,3,0))-sun.location).to_track_quat('-Z','Y').to_euler();sun.data.energy=1.45;sun.data.angle=.09
s.world=bpy.data.worlds.new('Day sky');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.70,.80,1,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.20
for name,loc,target,lens in [('01-salon',(5.65,.48,1.63),(1.75,3.0,1.25),25),('02-kuchnia',(5.65,4.75,1.62),(1.90,1.6,1.25),26)]:
 bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=name;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;o.data.clip_start=.05;o.data.clip_end=100;o.data.dof.use_dof=False
s.camera=bpy.data.objects['01-salon'];s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.max_bounces=10;s.cycles.diffuse_bounces=5;s.cycles.glossy_bounces=5;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=8;s.cycles.adaptive_threshold=.025;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.resolution_x=4096;s.render.resolution_y=2732;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0
bpy.context.preferences.filepaths.save_version=0
script=bpy.data.texts.new('build_scene.py');script.write(Path(__file__).read_text(encoding='utf-8'))
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'wn01-salon.blend'))
s.render.resolution_x=1100;s.render.resolution_y=734;s.cycles.samples=24;s.render.filepath=str(WORK/'preview-01.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['02-kuchnia'];s.render.filepath=str(WORK/'preview-02.png');bpy.ops.render.render(write_still=True)
manifest={'created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'blender_version':bpy.app.version_string,'room_dimensions_m':[6,5.2,2.9],'room_area_m2':31.2,'own_project_count':1,'camera_count':2,'mesh_objects':sum(o.type=='MESH' for o in s.objects),'curve_objects':sum(o.type=='CURVE' for o in s.objects),'materials':len(bpy.data.materials),'external_textures':sum(i.source=='FILE' for i in bpy.data.images),'native_file':'wn01-salon.blend','style':'Warm contemporary: oak, sage kitchen, linen, natural daylight','client_floorplan_claim':False,'sample_is_60m2_client_apartment':False,'commercial_case_claim':False,'bathroom_configurator_proof':False,'five_realizations_claim':False}
(WORK/'scene-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest),flush=True)
