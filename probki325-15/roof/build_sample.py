"""Own procedural Blender sample. No client artwork, images or geometry are embedded."""
import sys, pathlib, math, json, hashlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools' / 'bpy-native'))
import bpy
from mathutils import Vector

OUT = HERE if (HERE / 'README.txt').exists() else HERE / 'publishable'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene['purpose'] = 'Own demonstration of editable layered geometry; not an engineering specification or a paid client realization.'
scene['source'] = 'Procedural geometry and materials, authored for this sample. No external textures.'

def material(name, color, roughness=.5, metallic=0, texture=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    bsdf = n.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if texture:
        tex = n.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 90 if texture == 'mineral' else 4
        tex.inputs['Detail'].default_value = 3
        coords = n.new('ShaderNodeTexCoord')
        mapping = n.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
        mapping.inputs[1].default_value = (2, 45, 5) if texture == 'wood' else (1, 1, 1)
        mat.node_tree.links.new(coords.outputs['Generated'], mapping.inputs[0])
        mat.node_tree.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        ramp = n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .18
        ramp.color_ramp.elements[0].color = (*(v*.65 for v in color), 1)
        ramp.color_ramp.elements[1].position = .82
        ramp.color_ramp.elements[1].color = (*(min(v*1.22,1) for v in color), 1)
        mat.node_tree.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
        mat.node_tree.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
        bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .13
        bump.inputs['Distance'].default_value = .004 if texture == 'mineral' else .001
        mat.node_tree.links.new(tex.outputs['Fac'], bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat

wood = material('Timber | procedural grain', (.46,.26,.12), .57, texture='wood')
board = material('Fibre board | procedural surface', (.66,.62,.51), .8, texture='mineral')
insulation = material('Insulation | mint mineral fibres', (.20,.49,.44), .92, texture='mineral')
white = material('Soffit | warm white', (.76,.79,.76), .62, texture='mineral')
meshmat = material('Reinforcing grid | graphite', (.16,.22,.23), .7)
metal = material('Roof finish | graphite metal', (.045,.075,.105), .33, .55)
guttermat = material('Rainwater detail | pale metal', (.58,.67,.71), .27, .68)
membrane = material('Underlay | petrol blue', (.035,.18,.23), .7, texture='mineral')

root = bpy.data.objects.new('Roof sample | slope controller', None)
scene.collection.objects.link(root)
root.rotation_euler.x = math.radians(18)

layers = []
def layer(name, description):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    c['description'] = description
    c['independent_layer'] = True
    layers.append(c)
    return c

def move_to(obj, collection):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = root
    return obj

def cube(name, pos, size, mat, collection, bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    ob = bpy.context.object; ob.name = name
    ob.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new('Edge softness', 'BEVEL'); mod.width = bevel; mod.segments = 3
        ob.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return move_to(ob, collection)

c = layer('01 | Soffit panel', 'Continuous base panel; real mesh beneath other layers.')
cube('Soffit | continuous solid panel', (0,0,.025), (2.8,1.85,.05), white, c)

c = layer('02 | Reinforcement grid', 'Independent grid made from real crossed mesh strips.')
for i in range(30):
    x=-1.37+i*2.74/29
    cube(f'Grid longitudinal {i+1:02}', (x,0,.06), (.008,1.85,.008), meshmat,c,0)
for i in range(22):
    y=-.9+i*1.8/21
    cube(f'Grid transverse {i+1:02}', (0,y,.067), (2.8,.008,.008),meshmat,c,0)

c = layer('03 | Insulation', 'Three closed insulation blocks: exposed surfaces remain after hiding the roof.')
for i in range(3):
    cube(f'Insulation slab {i+1}',(-.94+i*.94,.03,.15),(.91,1.65,.15),insulation,c,.012)

c = layer('04 | Deck and membrane', 'Solid fibreboard deck and a separate underlay; neither is an image plane.')
cube('Deck | fibreboard', (0,.11,.255), (2.8,1.55,.055),board,c,.008)
cube('Underlay | solid sheet', (0,.13,.288), (2.79,1.50,.012),membrane,c,.002)

c = layer('05 | Counter battens', 'Four individually editable wooden members.')
for i in range(4):
    cube(f'Counter batten {i+1}',(-1.30+i*.866,.16,.33),(.085,1.42,.075),wood,c,.006)

c = layer('06 | Roof battens', 'Four separate transverse wooden members.')
for i in range(4):
    cube(f'Roof batten {i+1}',(0,-.36+i*.36,.405),(2.75,.072,.075),wood,c,.006)

c = layer('07 | Roof covering', 'Four separate folded metal sheets with real corrugated cross sections.')
for row in range(4):
    xa=-1.4+row*.7
    verts=[]
    # The short demonstration covering intentionally reveals the lower layers.
    for y in [-.10,.90]:
        for i in range(25):
            x=xa+i*.7/24
            z=.468+.027*(1+math.cos(i/24*math.tau*3))
            verts.append((x,y,z))
    faces=[]
    for i in range(24):faces.append((i,i+1,26+i,25+i))
    me=bpy.data.meshes.new(f'Folded roof sheet geometry {row+1}')
    me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(f'Roof sheet {row+1}',me);c.objects.link(ob);ob.parent=root
    ob.data.materials.append(metal)
    solid=ob.modifiers.new('Actual sheet thickness','SOLIDIFY');solid.thickness=.008
    be=ob.modifiers.new('Soft folded ridges','BEVEL');be.width=.003;be.segments=2

c = layer('08 | Fascia and gutter', 'Fascia, half-round gutter and downpipe, each independently editable.')
cube('Fascia board', (0,-.94,.16),(2.86,.07,.30),wood,c,.008)
verts=[]
for x in [-1.48,1.48]:
    for i in range(25):
        a=math.pi+i*math.pi/24
        verts.append((x,-1.08+.105*math.cos(a),.12+.105*math.sin(a)))
faces=[(i,i+1,26+i,25+i) for i in range(24)]
me=bpy.data.meshes.new('Gutter half round shell');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('Gutter | half round open channel',me);c.objects.link(ob);ob.parent=root
ob.data.materials.append(guttermat)
solid=ob.modifiers.new('Metal thickness','SOLIDIFY');solid.thickness=.008
for poly in me.polygons:poly.use_smooth=True
# A real hollow downpipe; the wall is a modifier, not a capped solid cylinder.
bpy.ops.mesh.primitive_circle_add(vertices=32, radius=.052, fill_type='NOTHING', location=(1.24,-1.08,-.18))
ob=bpy.context.object;ob.name='Downpipe | hollow tube';move_to(ob,c)
bpy.context.view_layer.objects.active=ob
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={'value':(0,0,.28)})
bpy.ops.object.mode_set(mode='OBJECT');ob.data.materials.append(guttermat)
solid=ob.modifiers.new('Pipe wall','SOLIDIFY');solid.thickness=.005
for poly in ob.data.polygons:poly.use_smooth=True

# Editorial, neutral studio lighting. All data is saved inside the native file.
studio=bpy.data.collections.new('Studio | camera and lighting');scene.collection.children.link(studio)
def studio_link(ob):
    for col in list(ob.users_collection): col.objects.unlink(ob)
    studio.objects.link(ob)

bpy.ops.object.camera_add(location=(4.6,-6.1,4.5))
camera=bpy.context.object;camera.name='Camera | isometric';studio_link(camera)
target=Vector((0,0,.48));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=4.8;scene.camera=camera
for name,loc,power,size in [('Key softbox',(-3,-4,6),1100,5),('Rim softbox',(4,3,5),1400,4),('Fill softbox',(-4,2,2),750,4)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    lamp=bpy.context.object;lamp.name=name;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size
    lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler();studio_link(lamp)
if scene.world is None:scene.world=bpy.data.worlds.new('Neutral studio world')
scene.world.color=(.3,.3,.3)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.73,.78,.80,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=5
        for space in area.spaces:
            if space.type=='FILE_BROWSER' and space.params:
                space.params.directory=b'//'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='DESELECT')
for ob in layers[2].objects: ob.select_set(True)
bpy.context.view_layer.objects.active=next(iter(layers[2].objects))

# Generate a human-readable materials/layers manifest; do not embed any reference picture.
manifest={'blender_version':bpy.app.version_string,'own_sample':True,'client_assets_embedded':False,
 'layer_count':len(layers),'layers':[{'name':c.name,'description':c['description'],'mesh_objects':len(c.objects)} for c in layers],
 'material_count':len(bpy.data.materials),'external_image_textures':len(bpy.data.images),
 'limitations':'Illustrative geometry only. Dimensions and layer composition are fictional. Not construction documentation or a specification of a certified roof system.'}
(OUT/'layers.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'layered-roof-own-sample.blend'))
scene.render.filepath=str(OUT/'01-assembled.png');bpy.ops.render.render(write_still=True)

# Revealing underlying objects is the central proof required by the client.
for c in layers[4:]:c.hide_render=True
scene.render.filepath=str(OUT/'02-underlying-layers.png');bpy.ops.render.render(write_still=True)
for c in layers[4:]:c.hide_render=False

# Exploded illustration is rendered from the same native meshes, not generated as a bitmap.
original={ob.name:tuple(ob.location) for c in layers for ob in c.objects}
for i,c in enumerate(layers):
    for ob in c.objects:ob.location.z+=i*.22
camera.data.ortho_scale=5.6
camera.location=(4.6,-6.1,5.5)
target=Vector((0,0,1.2));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'03-exploded.png');bpy.ops.render.render(write_still=True)
print(json.dumps({'saved':str(OUT/'layered-roof-own-sample.blend'),'renders':3,'layers':8,'native_version':bpy.app.version_string}))
