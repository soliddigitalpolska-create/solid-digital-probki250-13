import sys,json,math,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector,Quaternion
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/assembly';OUT.mkdir(parents=True,exist_ok=True);FRAMES=WORK/'frames';FRAMES.mkdir(exist_ok=True)
SOURCE=ROOT/'outputs/probki-plus28-2026-10-15/wood-plan/regal-wood01.blend';before_source=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.name='WOOD 01 | assembly animation';s.frame_start=1;s.frame_end=912;s.render.fps=24;s['own_demo']='Autorska animacja montażu własnego regału';s['duration_seconds']=38
P=bpy.context.preferences.addons['cycles'].preferences;P.compute_device_type='OPTIX';P.get_devices_for_type('OPTIX')
for d in P.devices:d.use=d.type=='OPTIX'
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=True;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.render.dither_intensity=0
def material(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.7;return m
white=material('Instruction | neutral board',(.88,.88,.88));black=material('Instruction | actual black edges',(.015,.015,.015));metal=material('Instruction | connector',(.16,.16,.16))
parts={o['part_id']:o for o in s.objects if 'part_id' in o};original={k:o.location.copy() for k,o in parts.items()};screws=[o for o in s.objects if ('connector' in o) or (o.name.startswith('H') and 'wkr' in o.name)];assert len(screws)==32
for k,o in parts.items():
 o.data.materials.clear();o.data.materials.append(white)
 wire=bpy.data.objects.new('Edge geometry | '+k,o.data.copy());s.collection.objects.link(wire);wire.data.materials.clear();wire.data.materials.append(black);wire.matrix_world=o.matrix_world
 w=wire.modifiers.new('Physical outline geometry','WIREFRAME');w.thickness=.0025;w.offset=1;w.use_replace=True;con=wire.constraints.new('COPY_TRANSFORMS');con.target=o
for o in screws:o.data.materials.clear();o.data.materials.append(metal)
for name,energy in [('Key',65),('Rim',55),('Fill',30)]:
 if bpy.data.objects.get(name):bpy.data.objects[name].data.energy=energy
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
nt=bpy.data.node_groups.new('Instruction white background','CompositorNodeTree');nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');s.compositing_node_group=nt;rl=nt.nodes.new('CompositorNodeRLayers');over=nt.nodes.new('CompositorNodeAlphaOver');over.inputs['Background'].default_value=(1,1,1,1);nt.links.new(rl.outputs['Image'],over.inputs['Foreground']);go=nt.nodes.new('NodeGroupOutput');nt.links.new(over.outputs['Image'],go.inputs['Image'])
s.camera.data.type='ORTHO';s.camera.data.ortho_scale=2.6;s.camera.data.shift_x=.12;s.camera.data.shift_y=-.02
def key(o,frame,loc):o.location=loc;o.keyframe_insert(data_path='location',frame=frame)
for k,o in parts.items():
 base=original[k];delta=Vector((-.30 if k=='A1' else .30 if k=='A2' else 0,.32 if k.startswith('C') else -.45 if k.startswith('B') else 0,0));start,end=(73,192) if k.startswith('A') else (193,312) if k.startswith('C') else (313,432) if k=='B1' else (433,552)
 for f,pos in [(1,base+delta),(start,base+delta),(end,base),(912,base)]:key(o,f,pos)
hardware=[]
for o in screws:
 base=o.location.copy();side=-1 if base.x<0 else 1;rotation=o.rotation_euler.to_quaternion();o.rotation_mode='QUATERNION'
 for f,dx in [(1,.40),(73,.40),(192,.10),(552,.10)]:key(o,f,base+Vector((side*dx,0,0)));o.rotation_quaternion=rotation;o.keyframe_insert(data_path='rotation_quaternion',frame=f)
 for f in range(553,769,12):
  t=(f-553)/215;key(o,f,base+Vector((side*.10*(1-t),0,0)));o.rotation_quaternion=Quaternion((1,0,0),8*math.pi*t*side)@rotation;o.keyframe_insert(data_path='rotation_quaternion',frame=f)
 for f in [768,912]:key(o,f,base);o.rotation_quaternion=Quaternion((1,0,0),8*math.pi*side)@rotation;o.keyframe_insert(data_path='rotation_quaternion',frame=f)
 hardware.append(o.name)
# Explicit bevel-edge/slotted head marks make the fastener rotation visible.
for head in [o for o in screws if o.name.startswith('H')]:
 s.frame_set(912);base=head.location.copy();side=-1 if base.x<0 else 1
 bpy.ops.mesh.primitive_cube_add(size=1,location=(base.x+side*.0007,base.y,base.z));slot=bpy.context.object;slot.name='Visible screw slot | '+head.name;slot.dimensions=(.0004,.0055,.001);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);slot.data.materials.append(black);slot.parent=head;slot.matrix_parent_inverse=head.matrix_world.inverted()
# Use clamped Bezier curves for smooth paths with stationary holds.
for o in list(parts.values())+screws:
 action=o.animation_data.action
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
s.frame_set(1);bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
script=bpy.data.texts.new('build_motion.py');script.write(Path(__file__).read_text(encoding='utf-8'));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'wood01-montaz.blend'))
for f in [1,132,252,372,492,660,840]:
 s.frame_set(f);s.render.filepath=str(WORK/f'preview-{f:04d}.png');bpy.ops.render.render(write_still=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before_source
manifest={'status':'BUILT_PREVIEWS_RENDERED','source_native':str(SOURCE),'source_sha256_preserved':before_source,'frame_start':1,'frame_end':912,'fps':24,'duration_seconds':38,'dimensions':[1920,1080],'native_file':'wood01-montaz.blend','moving_board_ids':list(parts),'moving_connector_objects':hardware,'real_3D_motion':True,'render_engine':'BLENDER_EEVEE32samples / RTX4080SUPER','style':'Actual monochrome geometry with native black edge meshes; white background','created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()};(WORK/'motion-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('MOTION_BUILT_PASS',flush=True)
