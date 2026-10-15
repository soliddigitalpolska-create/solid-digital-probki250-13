import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/interior'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'wn01-salon.blend'));s=bpy.context.scene
cam=bpy.data.objects['02-kuchnia'];cam.name='02-strefa-wypoczynku';cam.location=(4.8,3.10,1.57);cam.rotation_euler=(Vector((.85,1.80,1.06))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32
# Reuse only our own actual native product geometry. No external client asset.
source=ROOT/'outputs/probki-plus28-2026-10-15/allegro/01-lampa-led.blend'
with bpy.data.libraries.load(str(source),link=False) as (data_from,data_to):
 data_to.objects=[name for name in data_from.objects if name in ['Weighted round base','Champagne inset base','Slender upright','Angled head support','Elliptic LED head','Recessed opal emitter','Touch control on base']]
for o in data_to.objects:
 s.collection.objects.link(o);o.location+=Vector((.72,3.96,.55));o['asset_provenance']='Own real lamp geometry from own Allegro sample; no commercial client'
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.24,depth=.035,location=(.72,3.96,.53));o=bpy.context.object;o.name='Oak side table top';o.data.materials.append(bpy.data.materials['03 | dąb orzechowy']);m=o.modifiers.new('Round edge','BEVEL');m.width=.005;m.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
for a in [0,2.094,4.189]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.018,depth=.5,location=(.72+.16*math.cos(a),3.96+.16*math.sin(a),.26));o=bpy.context.object;o.name='Side table leg';o.data.materials.append(bpy.data.materials['03 | dąb orzechowy'])
bpy.ops.object.light_add(type='AREA',location=(.74,3.96,.922));o=bpy.context.object;o.name='Real desk lamp illumination';o.data.energy=3;o.data.size=.13;o.data.color=(1,.79,.52);o.rotation_euler=(0,0,0)
# Fine woven normal pattern stays procedural in the native material.
m=bpy.data.materials['05 | tkanina lniana sofy'];n=m.node_tree.nodes;l=m.node_tree.links;wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X';wave.inputs['Scale'].default_value=140;wave.inputs['Distortion'].default_value=1.4;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],wave.inputs['Vector']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.14;b.inputs['Distance'].default_value=.00035;l.new(wave.outputs['Color'],b.inputs['Height']);old=next(x for x in n if x.type=='BUMP' and x!=b);l.new(old.outputs['Normal'],b.inputs['Normal']);l.new(b.outputs['Normal'],n['Principled BSDF'].inputs['Normal'])
s.camera=bpy.data.objects['01-salon'];s.render.resolution_x=4096;s.render.resolution_y=2732;s.cycles.samples=64;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'wn01-salon.blend'))
s.camera=cam;s.render.resolution_x=1100;s.render.resolution_y=734;s.cycles.samples=24;s.render.filepath=str(WORK/'preview-02-refined.png');bpy.ops.render.render(write_still=True)
print('Refined scene and second camera saved',flush=True)
