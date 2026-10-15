import sys,json,hashlib,itertools
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy
from mathutils import Vector
OUT=ROOT/'outputs/probki-plus28-2026-10-15/wood-plan';WORK=Path(__file__).resolve().parent
manifest=json.loads((OUT/'geometry-manifest.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'regal-wood01.blend'));bpy.context.view_layer.update();s=bpy.context.scene
parts={o['part_id']:o for o in s.objects if 'part_id' in o}
def bounds(o):
 q=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in q)*1000 for i in range(3)],[max(v[i] for v in q)*1000 for i in range(3)]]
def digest():return hashlib.sha256(json.dumps({k:[list(v.co) for v in o.data.vertices] for k,o in parts.items()},sort_keys=True).encode()).hexdigest()
before=digest();checked=[]
for d in manifest['parts']:
 o=parts[d['id']];actual=[v*1000 for v in o.dimensions];error=max(abs(a-b) for a,b in zip(actual,d['size_mm']));assert error<.001
 checked.append({'id':d['id'],'actual_mm':actual,'cut_mm':d['cut_mm'],'dimension_error_mm':error,'pass':True})
boxes={k:bounds(o) for k,o in parts.items()}
overall=[max(b[1][i] for b in boxes.values())-min(b[0][i] for b in boxes.values()) for i in range(3)];assert max(abs(a-b) for a,b in zip(overall,manifest['nominal_mm']))<.001
contacts=[];overlaps=[]
for a,b in itertools.combinations(parts,2):
 aa,bb=boxes[a],boxes[b];delta=[min(aa[1][i],bb[1][i])-max(aa[0][i],bb[0][i]) for i in range(3)]
 if all(v>.001 for v in delta):overlaps.append([a,b,delta])
 if all(v>=-.001 for v in delta) and sum(v>.001 for v in delta)>=2:contacts.append([a,b])
assert not overlaps
assert len(contacts)==10,contacts
for h in manifest['pilot_axes']:
 target=boxes[h['target']];side=boxes['A1' if h['side']<0 else 'A2'];y,z=h['y_mm'],h['z_mm']
 assert target[0][1]<y<target[1][1] and target[0][2]<z<target[1][2]
 assert side[0][1]<y<side[1][1] and side[0][2]<z<side[1][2]
 assert target[0][2]+1.5<z<target[1][2]-1.5
assert len(manifest['pilot_axes'])==16
s.render.resolution_x=800;s.render.resolution_y=600;s.cycles.samples=16;s.render.filepath=str(WORK/'native-reopen-rerender.png');bpy.ops.render.render(write_still=True)
after=digest();assert before==after
assert not any(i.source=='FILE' for i in bpy.data.images)
native_stats={'scene':s.name,'mesh_objects':sum(o.type=='MESH' for o in s.objects),'parts':len(parts),'connector_shafts':sum(o.name.startswith('S') and 'connector' in o for o in s.objects),'drill_guides':len(bpy.data.collections['DRILL_GUIDES — 16 osi pilota Ø3'].objects)}
# Export was created from exactly the six wood panels. Re-import into a fresh
# empty scene rather than merely inspecting the bytes of the exported file.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'regal-wood01.glb'));bpy.context.view_layer.update()
allbounds=[o.matrix_world@Vector(v) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.bound_box]
glbd=[(max(p[i] for p in allbounds)-min(p[i] for p in allbounds))*1000 for i in range(3)];assert max(abs(a-b) for a,b in zip(glbd,manifest['nominal_mm']))<.01
qa={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'blender_version':bpy.app.version_string,'native_file_reopened':True,'actual_rerender':True,'parts':checked,'assembled_dimensions_mm':overall,'wood_part_pair_intersections':overlaps,'contact_pairs':contacts,'contact_count':len(contacts),'all_16_pilot_axes_align_side_and_target':True,'pilot_axes_are_native_geometry_guides_not_claimed_manufactured_holes':True,'mesh_sha_before':before,'mesh_sha_after':after,'geometry_unchanged_after_render':before==after,'no_external_images':True,'glb_fresh_reimport':True,'glb_dimensions_mm':glbd,'native_stats':native_stats,'what_this_proves':'Dimensional, assembly-documentation and native-file workflow on a real own model. Not a physical load test or commercial project history.'}
(OUT/'native-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8');(WORK/'native-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(qa,ensure_ascii=False),flush=True)
