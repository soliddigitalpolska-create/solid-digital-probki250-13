import sys,math,json,wave,subprocess,shutil,zipfile,hashlib,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'work/useme325-2026-10-15/tools/bpy-native'))
import bpy,numpy as np
from mathutils import Vector
from PIL import Image,ImageDraw,ImageFont
OUT=ROOT/'outputs/probki-plus28-2026-10-15/block-animation';OUT.mkdir(parents=True,exist_ok=True)
FRAMES=HERE/'frames';FRAMES.mkdir(exist_ok=True)
phrases=json.loads((HERE/'voice-text.json').read_text(encoding='utf-8-sig'))
audio=[];cues=[];position=0
for i,p in enumerate(sorted((HERE/'audio').glob('vo-*.wav'))):
 with wave.open(str(p),'rb') as w:rate=w.getframerate();channels=w.getnchannels();width=w.getsampwidth();data=w.readframes(w.getnframes())
 assert channels==1 and width==2
 pause=bytes(int(rate*.25)*2);audio.append(data+pause);duration=len(data)/2/rate
 cues.append({'text':phrases[i],'start_seconds':round(position,3),'end_seconds':round(position+duration,3)})
 position+=duration+.25
with wave.open(str(OUT/'own-system-voice.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b''.join(audio))
samples=np.frombuffer(b''.join(audio),dtype=np.int16).astype(float)/32768
FPS=12;N=math.ceil(position*FPS);W=H=640
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=True;s.render.resolution_x=W;s.render.resolution_y=H;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=FPS;s.frame_start=1;s.frame_end=N;s.view_settings.view_transform='Standard';s.world=bpy.data.worlds.new('Own studio');s.world.color=(.21,.21,.21)
def mat(name,c,rough=.5):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;return m
skin=mat('Own avatar skin',(.65,.4,.22));shirt=mat('Own avatar shirt',(.06,.31,.36));trousers=mat('Own avatar trousers',(.065,.10,.15));dark=mat('Own face',(.012,.02,.024));floor=mat('Own stage',(.11,.15,.19));coral=mat('Orange prop',(.75,.24,.08));mint=mat('Mint prop',(.13,.55,.43))
def cube(name,loc,size,m,bevel=.04):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:mod=o.modifiers.new('Own edge bevel','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return o
bodyparts=[]
bodyparts.append((cube('Torso',(0,0,1.7),(1.05,.58,1.15),shirt),'spine'))
bodyparts.append((cube('Head',(0,0,2.66),(.83,.7,.82),skin),'head'))
for side,x in [('L',-.79),('R',.79)]:
 bodyparts.append((cube('Upper arm '+side,(x,0,1.87),(.42,.48,.6),shirt),'upper_'+side))
 bodyparts.append((cube('Forearm '+side,(x,0,1.29),(.4,.45,.58),skin),'fore_'+side))
 bodyparts.append((cube('Leg '+side,(-.28 if side=='L' else .28,0,.66),(.46,.52,.95),trousers),'leg_'+side))
cube('Left eye',(-.18,-.356,2.74),(.065,.025,.09),dark,.012);cube('Right eye',(.18,-.356,2.74),(.065,.025,.09),dark,.012)
mouth=cube('Audio amplitude mouth',(0,-.365,2.46),(.19,.03,.065),dark,.018)
cube('Hair cap',(0,.01,3.035),(.88,.72,.16),trousers,.05)
cube('Floor',(0,0,.145),(200,200,.08),floor)
propA=cube('Orange cube',(-1.7,.2,.435),(.5,.5,.5),coral);propB=cube('Mint cube',(1.7,.2,.435),(.5,.5,.5),mint)
# Real armature, editable keyframes, and weighted rigid block meshes.
rigdata=bpy.data.armatures.new('Own block avatar rig');rig=bpy.data.objects.new('OWN_RIG_NOT_ROBLOX_ASSET',rigdata);s.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
bones=[('root',(0,0,0),(0,0,.3),None),('spine',(0,0,1.1),(0,0,2.2),'root'),('head',(0,0,2.25),(0,0,3.05),'spine')]
for side,x in [('L',-.79),('R',.79)]:
 bones += [('upper_'+side,(x,0,2.18),(x,0,1.58),'spine'),('fore_'+side,(x,0,1.58),(x,0,.99),'upper_'+side),('leg_'+side,(-.28 if side=='L' else .28,0,1.1),(-.28 if side=='L' else .28,0,.19),'root')]
for name,head,tail,parent in bones:
 b=rigdata.edit_bones.new(name);b.head=head;b.tail=tail
 if parent:b.parent=rigdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for o,bone in bodyparts:
 bpy.context.view_layer.objects.active=o;rig.select_set(False);o.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Actual weighted armature','ARMATURE');mod.object=rig;o.select_set(False)
for p in rig.pose.bones:p.rotation_mode='XYZ'
def envelope(t,start,end):
 if t<start or t>end:return 0
 return math.sin(math.pi*(t-start)/(end-start))
for f in range(N):
 t=f/FPS;s.frame_set(f+1)
 for p in rig.pose.bones:p.rotation_euler=(0,0,0)
 a=envelope(t,cues[0]['start_seconds'],cues[0]['end_seconds']);b=envelope(t,cues[1]['start_seconds'],cues[1]['end_seconds']);c=envelope(t,cues[2]['start_seconds'],cues[2]['end_seconds']);d=envelope(t,cues[3]['start_seconds'],cues[3]['end_seconds'])
 rig.pose.bones['upper_L'].rotation_euler.z=-a*.95-b*.2+c*.5
 rig.pose.bones['upper_R'].rotation_euler.z=a*.95+b*1.4-c*.5+d*.7
 rig.pose.bones['fore_R'].rotation_euler.x=-b*.9-d*.7
 for p in rig.pose.bones:p.keyframe_insert('rotation_euler',frame=f+1)
 u=max(0,min(1,(t-cues[2]['start_seconds'])/max(.1,cues[2]['end_seconds']-cues[2]['start_seconds'])));u=u*u*(3-2*u)
 propA.location.x=-1.7+3.4*u;propA.location.y=.2-.6*math.sin(math.pi*u);propB.location.x=1.7-3.4*u;propB.location.y=.2+.6*math.sin(math.pi*u)
 for o in [propA,propB]:o.keyframe_insert('location',frame=f+1)
 sound=samples[int(t*rate):int((t+.08)*rate)];rms=float(np.sqrt(np.mean(sound**2))) if len(sound) else 0
 mouth.scale.z=.35+min(3.8,rms*17);mouth.keyframe_insert('scale',frame=f+1)
bpy.ops.object.camera_add(location=(4.3,-8.6,4.4));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.4;s.camera=cam
for loc,power,size in [((0,-4,7),950,5),((-4,1,4),1100,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'own-block-rig.blend'))
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',23);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
for f in range(N):
 s.frame_set(f+1);s.render.filepath=str(FRAMES/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
 im=Image.open(FRAMES/f'{f:04d}.png').convert('RGB');draw=ImageDraw.Draw(im);draw.rectangle((0,0,W,44),fill='#132933');draw.text((22,14),'WŁASNA POSTAĆ BLOKOWA / DEMO BLENDER',font=small,fill='#d6e8de');draw.rectangle((0,552,W,H),fill='#132933')
 cue=next((c for c in cues if c['start_seconds']<=f/FPS<c['end_seconds']),None)
 if cue:
  for j,line in enumerate(textwrap.wrap(cue['text'],43)):draw.text((24,569+j*30),line,font=font,fill='#f2f5ed')
 im.save(FRAMES/f'{f:04d}.png')
ffmpeg=ROOT/'work/useme-pakiet35-2026-10-11/vendor/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
subprocess.run([str(ffmpeg),'-y','-loglevel','error','-framerate',str(FPS),'-i',str(FRAMES/'%04d.png'),'-i',str(OUT/'own-system-voice.wav'),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(OUT/'animation.mp4')],check=True)
evidence={'status':'OWN_DEMO_NOT_CLIENT_ASSET','software':'Native Blender5.2.2, actual weighted armature and keyframed meshes','armature_bones':len(rigdata.bones),'weighted_body_objects':len(bodyparts),'frames':N,'fps':FPS,'duration_seconds':round(position,3),'audio':'Own Polish script, Microsoft Paulina Desktop system speech synthesis via local Windows SAPI; not human voice, no voice clone, not client voiceover.','sync':'Semantic gestures and prop order align to phrase timing. Mouth opening follows waveform amplitude, not phoneme-accurate lip sync.','cues':cues,'rights':'Original simple block character, props, rig, animation and script. No Roblox marketplace assets or third-party character copied.','native_Roblox_Studio_project':False,'client_brief_tool_requirement':'Public brief only asks to animate characters to voiceover,50–60sec; no literal Roblox Studio/native .rbxl requirement. Confirm required output and supplied character/voiceover before contract.'}
(OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(OUT/'voice-script.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');shutil.copyfile(HERE/'build.py',OUT/'build.py');shutil.copyfile(HERE/'voice.ps1',OUT/'voice.ps1')
for f in [0,int(N*.25),int(N*.53),N-1]:Image.open(FRAMES/f'{f:04d}.png').save(OUT/f'frame-{f:03d}.jpg',quality=90)
page=f'''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Postać blokowa — animacja pod lektora</title><style>body{{margin:0;background:#edf1e7;color:#18362f;font:16px/1.7 Arial,sans-serif}}main{{max-width:1000px;margin:auto;padding:35px 24px}}h1{{font-size:clamp(38px,6vw,65px);line-height:1.08;letter-spacing:-2px}}h2{{font-size:28px}}video{{width:min(100%,640px);border-radius:12px}}.note{{background:#e0e8d5;padding:22px;font-size:13px}}section{{background:white;padding:27px;margin:28px 0;border-radius:12px}}a{{color:#28644f}}.frames{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}img{{max-width:100%;height:auto}}.tag{{font-size:11px;text-transform:uppercase;letter-spacing:1.5px}}</style></head><body><main><p class="tag">Autorska próbka / natywne 3D</p><h1>Postać reaguje.<br>Gest pasuje do zdania.</h1><p>Własna postać blokowa, rzeczywisty rig i animacja w Blenderze. {position:.1f} s przykładu z autorskim polskim skryptem i lektorem systemowym.</p><p class="note">Nie jest to postać z Roblox Marketplace ani projekt Roblox Studio. Nie kopiowano cudzych modeli. Nagranie używa systemowego syntezatora Microsoft Paulina Desktop; nie jest ludzkim głosem i nie jest lektorem klienta.</p><section><video controls preload="metadata" src="animation.mp4" poster="frame-000.jpg"></video><p>Gest „całość”, wskazanie szczegółu i zamiana kolejności rekwizytów wynikają z treści kolejnych zdań. Otwarcie ust reaguje na amplitudę dźwięku; nie udaje dokładnej synchronizacji fonemów.</p></section><section><h2>Co zawiera rzeczywisty plik</h2><ul><li>{len(rigdata.bones)} kości w armaturze, {len(bodyparts)} obiektów z wagami i modyfikatorami Armature.</li><li>{N} wyrenderowanych klatek, {FPS} kl./s. Ruchy i rekwizyty mają edytowalne klatki kluczowe.</li><li>Własne proste modele, materiały, oświetlenie, kamera, skrypt i kod generujący.</li><li>WAV i karta czasów pozwalają sprawdzić dopasowanie gestów do wypowiedzi.</li></ul><p><a href="../block-animation-zrodla.zip">Pobierz komplet źródeł ZIP</a> · <a href="own-block-rig.blend">Źródłowy Blender .blend</a> · <a href="evidence.json">Dane kontroli</a> · <a href="voice-script.json">Tekst i czasy</a> · <a href="own-system-voice.wav">Autorski skrypt w lektorze systemowym</a></p></section><section><h2>Kontrola ujęć</h2><div class="frames">{''.join(f'<a href="frame-{f:03d}.jpg"><img src="frame-{f:03d}.jpg" alt="Klatka animacji {f}"></a>' for f in [0,int(N*.25),int(N*.53),N-1])}</div></section><section><h2>Granica zastosowania</h2><p>Próbka pokazuje warsztat animacji i zgodność gestów z narracją. Zlecenie 50–60 s wymaga przed umową uzgodnienia scenariusza, praw do postaci, lektora, liczby scen i formatu przekazania. Jeśli potrzebny jest natywny projekt Roblox Studio lub animacja działająca w grze, ten plik nie potwierdza takiej kompetencji.</p><p>Nie jest to płatny case ani realizacja dla autora ogłoszenia. Bez gwarancji wyników lub zasięgów.</p></section><p class="tag">Próbka własna · nieopublikowana przez generator · 15.10.2026</p></main></body></html>'''
(OUT/'index.html').write_text(page,encoding='utf-8');(OUT/'README.txt').write_text('Własna postać blokowa i natywny Blender. Otwórz index.html. Plik.blend zawiera rig, wagi i klatki kluczowe. MP4 zawiera systemową syntezę Microsoft Paulina Desktop z autorskim tekstem, nie ludzki głos ani lektora klienta. Brak Roblox Studio/.rbxl, marketplace assets lub cudzych postaci. Próbka nie dowodzi kompetencji wdrożenia animacji w grze Roblox.\n',encoding='utf-8')
archive=OUT.parent/'block-animation-zrodla.zip'
for backup in OUT.glob('*.blend1'):
 assert backup.resolve().parent==OUT.resolve();backup.unlink()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.iterdir():
  if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
assert all(p.stat().st_size<30*1024*1024 for p in OUT.iterdir() if p.is_file())
(HERE/'validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('BLOCK_ANIMATION_COMPLETE',N,position,archive.stat().st_size)
