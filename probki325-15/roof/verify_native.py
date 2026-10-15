import sys, pathlib, json, hashlib
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tools'/'bpy-native'))
import bpy
OUT=HERE if (HERE/'layered-roof-own-sample.blend').exists() else HERE/'publishable'
path=OUT/'layered-roof-own-sample.blend'
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
layers=sorted([c for c in bpy.data.collections if c.get('independent_layer')],key=lambda c:c.name)
assert len(layers)==8
checks=[]
for col in layers:
    objects=list(col.objects)
    assert objects and all(o.type=='MESH' for o in objects)
    assert all(len(o.data.vertices)>0 for o in objects)
    assert all(len(o.data.polygons)>0 for o in objects)
    assert all(len(o.data.materials)>0 for o in objects)
    assert not col.hide_render
    before={o.name:o.visible_get() for o in objects}
    assert all(before.values())
    col.hide_viewport=True;bpy.context.view_layer.update()
    hidden={o.name:o.visible_get() for o in objects}
    assert not any(hidden.values()), col.name
    col.hide_viewport=False;bpy.context.view_layer.update()
    assert all(o.visible_get() for o in objects)
    checks.append({'collection':col.name,'meshes':len(objects),'hide_show_verified':True,
                   'vertices':sum(len(o.data.vertices) for o in objects),
                   'polygons':sum(len(o.data.polygons) for o in objects)})
underlying=[o.name for col in layers[:4] for o in col.objects]
removed=[]
for col in layers[4:]:
    for ob in list(col.objects):
        removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
assert all(bpy.data.objects.get(name) for name in underlying)
assert len(underlying)==58
assert not any(image.filepath and image.source=='FILE' for image in bpy.data.images)
result={'status':'PASS','native_engine':'Blender '+bpy.app.version_string,
        'reopened_saved_blend':True,'layer_count':len(layers),'layer_checks':checks,
        'remove_upper_layers_test':{'removed_meshes':len(removed),'underlying_meshes_retained':len(underlying),'passed':True},
        'client_assets_embedded':False,'external_image_dependencies':0,
        'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'saved_file_left_unchanged':True}
(OUT/'native-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
