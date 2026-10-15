import sys,pathlib,json,math,hashlib,time
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUNTIME=ROOT/'work/useme325-2026-10-15/tools/bpy-native'
sys.path.insert(0,str(RUNTIME))
import bpy
from mathutils import Vector
OUT=HERE if (HERE/'native-manifest.json').exists() else ROOT/'outputs/probki-plus28-2026-10-15/allegro';OUT.mkdir(parents=True,exist_ok=True)
START=time.time();N=2560

def mat(name,color,rough=.35,metal=0,wood=False,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 if wood:
  nodes=m.node_tree.nodes;links=m.node_tree.links;coord=nodes.new('ShaderNodeTexCoord');scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(3,55,8);tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=4;tex.inputs['Detail'].default_value=2.5;links.new(coord.outputs['Generated'],scale.inputs[0]);links.new(scale.outputs[0],tex.inputs['Vector']);ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(.17,.065,.025,1);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(.61,.31,.11,1);links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],p.inputs['Base Color']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00035;links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
 return m

def meshmark(o,m):
 o.data.materials.append(m);o['own_procedural_geometry']=True
 for p in o.data.polygons:p.use_smooth=True
 return o

def box(name,loc,dims,m,bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Real rounded edge geometry','BEVEL');mod.width=bevel;mod.segments=4
  mod=o.modifiers.new('Weighted vertex normals','WEIGHTED_NORMAL')
 return meshmark(o,m)

def cyl(name,loc,radius,depth,m,rotation=(0,0,0),bevel=.002):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=radius,depth=depth,location=loc,rotation=rotation);o=bpy.context.object;o.name=name
 if bevel:mod=o.modifiers.new('Machined edge','BEVEL');mod.width=bevel;mod.segments=3
 return meshmark(o,m)

def rod(name,a,b,radius,m):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,radius,(b-a).length,m);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def new_scene(id,title,dims):
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name=id;s.unit_settings.system='METRIC';s['sample_kind']='Own fictional product, procedural native 3D geometry, no commercial client';s['product_name']=title;s['nominal_dimensions_m']=dims;s['no_external_textures']=True;s['no_generated_bitmap']=True;return s

def lamp():
 s=new_scene('01-lampa-led','Lampa LED — własny model demonstracyjny','0.225 × 0.190 × 0.410');bronze=mat('Satin champagne aluminium',(.46,.32,.18),.26,.78);dark=mat('Warm graphite foot',(.035,.038,.04),.3,.7);white=mat('Opal LED diffuser',(.95,.84,.57),.3,0,emission=.25)
 cyl('Weighted round base',(0,0,.014),.095,.028,dark,bevel=.007);cyl('Champagne inset base',(0,0,.031),.084,.007,bronze,bevel=.002)
 rod('Slender upright',(-.042,.018,.034),(-.042,.018,.34),.007,bronze);rod('Angled head support',(-.042,.018,.34),(.018,.018,.392),.007,bronze)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=(.026,.018,.392));o=bpy.context.object;o.name='Elliptic LED head';o.scale=(.104,.057,.018);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);meshmark(o,bronze)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=24,location=(.026,.018,.383));o=bpy.context.object;o.name='Recessed opal emitter';o.scale=(.092,.049,.009);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);meshmark(o,white)
 cyl('Touch control on base',(.048,-.022,.037),.009,.0015,dark,bevel=.0005)
 return s,(.65,-1,.55)

def wall():
 s=new_scene('02-kinkiet-led','Kinkiet LED — własny model demonstracyjny','0.120 × 0.121 × 0.261');black=mat('Anthracite powder coat',(.022,.027,.035),.34,.62);gold=mat('Brushed brass inner rings',(.46,.25,.085),.3,.75);opal=mat('Warm opal ends',(.99,.78,.38),.45,0,.0 if False else False,emission=.24)
 box('Rear mounting block',(0,.028,.14),(.11,.042,.19),black,.008);cyl('Tall cylindrical luminaire',(0,-.012,.14),.060,.26,black,bevel=.007)
 for sign in [-1,1]:
  z=.14+sign*.127;cyl('Brass recess ring '+str(sign),(0,-.012,z),.052,.005,gold,bevel=.001);cyl('Inset warm diffuser '+str(sign),(0,-.012,z+sign*.001),.043,.005,opal,bevel=.001)
 for z in [.07,.21]:cyl('Rear fixing screw',(.038,.006,z),.003,.003,gold,rotation=(math.pi/2,0,0),bevel=.0005)
 return s,(.85,-1,.62)

def tray():
 s=new_scene('03-organizer','Organizer z drewna — własny model demonstracyjny','0.290 × 0.190 × 0.090');walnut=mat('Walnut procedural grain',(.34,.18,.08),.4,wood=True);base=mat('Walnut base grain',(.31,.15,.06),.43,wood=True)
 box('Solid rounded bottom',(0,0,.009),(.29,.19,.018),base,.008)
 box('Front rim',(0,-.087,.035),(.29,.016,.07),walnut,.005);box('Back rim',(0,.087,.045),(.29,.016,.09),walnut,.005)
 for x in [-.137,.137]:box('Side rim '+str(x),(x,0,.04),(.016,.166,.08),walnut,.004)
 box('Long inner divider',(.04,0,.033),(.012,.158,.058),walnut,.003)
 box('Short inner divider',(-.049,.017,.033),(.164,.012,.058),walnut,.003)
 return s,(.8,-1,.95)

manifest=[]
for build in [lamp,wall,tray]:
 s,view=build();bpy.context.view_layer.update();id=s.name;product=[o for o in s.objects if o.type=='MESH'];bounds=[o.matrix_world@Vector(corner) for o in product for corner in o.bound_box];low=Vector(tuple(min(p[i] for p in bounds) for i in range(3)));high=Vector(tuple(max(p[i] for p in bounds) for i in range(3)));target=(low+high)/2
 bpy.ops.object.camera_add(location=target+Vector(view).normalized()*2);cam=bpy.context.object;cam.name='Camera — exact framed product';cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';s.camera=cam
 bpy.context.view_layer.update()
 local=[cam.matrix_world.inverted()@p for p in bounds];xs=[p.x for p in local];ys=[p.y for p in local];width=max(xs)-min(xs);height=max(ys)-min(ys);right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));cam.location+=right*((max(xs)+min(xs))/2)+up*((max(ys)+min(ys))/2)
 for name,delta,energy,size in [('Large key',(-1,-1,1.5),30,1.3),('Long edge rim',(1,.6,.9),40,.8),('Front fill',(-.6,.3,.4),15,.7)]:
  bpy.ops.object.light_add(type='AREA',location=target+Vector(delta));o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 s.world=bpy.data.worlds.new('Neutral studio lighting');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.85,.95,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.render.film_transparent=True;s.render.dither_intensity=0;s.render.resolution_x=N;s.render.resolution_y=N;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard'
 # Explicit flat-white compositor, independent of light intensity and tone mapping.
 nt=bpy.data.node_groups.new('White background compositor','CompositorNodeTree');nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');s.compositing_node_group=nt;render=nt.nodes.new('CompositorNodeRLayers');over=nt.nodes.new('CompositorNodeAlphaOver');over.inputs['Background'].default_value=(1,1,1,1);nt.links.new(render.outputs['Image'],over.inputs['Foreground']);comp=nt.nodes.new('NodeGroupOutput');nt.links.new(over.outputs['Image'],comp.inputs['Image'])
 for v,factor in [('before',1.65),('miniatura',1.12)]:
  cam.data.ortho_scale=max(width,height)*factor;s.render.filepath=str(OUT/f'{id}-{v}.png');bpy.ops.render.render(write_still=True)
  if v=='miniatura':
   s.render.image_settings.file_format='JPEG';s.render.image_settings.color_mode='RGB';s.render.image_settings.quality=95;bpy.data.images['Render Result'].save_render(str(OUT/f'{id}-miniatura.jpg'),scene=s);s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{id}.blend'))
 # Keep a useful source script inside the native file as well as beside it.
 script=bpy.data.texts.new('build_sample.py');script.write(pathlib.Path(__file__).read_text('utf-8'));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{id}.blend'))
 verts=sum(len(o.data.vertices) for o in product);faces=sum(len(o.data.polygons) for o in product);info={'id':id,'product':s['product_name'],'native_file':id+'.blend','thumbnail_png':id+'-miniatura.png','thumbnail_jpg':id+'-miniatura.jpg','before_png':id+'-before.png','mesh_objects':len(product),'vertices':verts,'faces':faces,'scene_units':'METRIC','nominal_dimensions_m':s['nominal_dimensions_m'],'actual_scene_bbox_m':list(high-low),'image_dimensions':[N,N],'full_product_preserved':True,'background':'explicit white RGBA composite, no logos/text/frames','created_with':bpy.app.version_string,'external_images':len([i for i in bpy.data.images if i.source=='FILE'])};manifest.append(info);(OUT/'native-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(info),flush=True)
print('DONE seconds',time.time()-START,flush=True)



