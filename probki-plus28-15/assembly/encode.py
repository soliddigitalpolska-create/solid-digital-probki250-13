import json,subprocess,time,textwrap,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/assembly';READY=WORK/'ready';READY.mkdir(exist_ok=True);FRAMES=WORK/'frames'
FF=ROOT/'work/useme-pakiet35-2026-10-11/vendor/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
points=json.loads((WORK/'projected-points.json').read_text(encoding='utf-8'));R=json.loads((WORK/'render-manifest.json').read_text(encoding='utf-8'));assert R['frames']==912
fonts={s:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',s) for s in [20,23,26,29,32,36,40]};bold={s:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',s) for s in [20,24,28,34,44]}
stages=[(0,3,'Elementy zestawu','6 elementów + 16 wkrętów','A1,A2,B1,B2,C1,C2'),(3,8,'Boki A1 + A2','Ustawienie obu boków','A1,A2'),(8,13,'Rygle C1 + C2','Dolny i górny rygiel','C1,C2'),(13,18,'Dolna półka B1','Wsuń półkę na poziom100 mm','B1'),(18,23,'Górna półka B2','Wsuń półkę na poziom550 mm','B2'),(23,32,'Połączenia','16 × wkręt4 ×40 mm',''),(32,38,'Kontrola końcowa','800 ×350 ×600 mm','')]
start=time.time()
for frame in range(1,913):
 t=(frame-1)/24;stage=next(i for i,row in enumerate(stages) if row[0]<=t<row[1]);a,b,title,desc,tags=stages[stage]
 im=Image.open(FRAMES/f'{frame:04d}.png').convert('RGB');dr=ImageDraw.Draw(im);dr.text((58,30),'WOOD 01 / INSTRUKCJA MONTAŻU',font=bold[28],fill='#1d2c25');dr.text((59,69),'Autorski model i animacja 3D • Solid Digital',font=fonts[23],fill='#657269')
 dr.rounded_rectangle((1360,180,1870,780),radius=12,fill='#f5f7f3',outline='#ced5cc',width=2);dr.text((1390,210),f'KROK {stage+1} / 7',font=bold[20],fill='#6a786e');dr.text((1390,256),title,font=bold[34],fill='#1d2c25')
 desc=desc.replace('poziom100','poziom 100').replace('poziom550','poziom 550').replace('wkręt4 ×40','wkręt 4 × 40').replace('800 ×350 ×600','800 × 350 × 600')
 dr.text((1390,312),desc,font=fonts[26],fill='#526256')
 if stage==0:
  dr.text((1390,355),'Wymiary w mm',font=fonts[20],fill='#6a786e')
  for j,txt in enumerate(['A • 2 boki600 ×350 ×18','B • 2 półki764 ×350 ×18','C • 2 rygle764 ×70 ×18','16 × wkręt4 ×40']):
   for x,y in [('boki600','boki 600'),('półki764','półki 764'),('rygle764','rygle 764'),('wkręt4','wkręt 4'),('×350','× 350'),('×18','× 18'),('×70','× 70'),('×40','× 40')]:txt=txt.replace(x,y)
   dr.text((1390,395+j*57),txt,font=fonts[23],fill='#34473b')
 elif stage in [1,2,3,4]:
  notes={1:['Boki zachowują rozstaw','764 mm pomiędzy powierzchniami','wewnętrznymi.'],2:['Dolny rygiel: z30–100 mm','Górny rygiel: z480–550 mm','Równoległe powierzchnie.'],3:['Spód półki:100 mm.','Półka opiera się na ryglu.','Sprawdź położenie przed łączeniem.'],4:['Spód półki:550 mm.','Prześwit pomiędzy półkami:432 mm.','Sprawdź krawędzie i kąty.']}[stage]
  for j,txt in enumerate(notes):
   for x,y in [('z30','z 30'),('z480','z 480'),(':100',': 100'),(':550',': 550'),(':432',': 432')]:txt=txt.replace(x,y)
   dr.text((1390,406+j*48),txt,font=fonts[23],fill='#34473b')
 elif stage==5:
  dr.rounded_rectangle((1400,395,1830,570),radius=5,fill='white',outline='#607263',width=2);dr.text((1420,410),'16×',font=bold[34],fill='#263b2e');dr.line((1505,503,1770,503),fill='#263b2e',width=10);dr.ellipse((1760,481,1787,525),fill='white',outline='#263b2e',width=3)
  for x in range(1520,1730,17):dr.line((x,490,x+10,516),fill='#263b2e',width=2)
  dr.text((1440,615),'Ruch osiowy + obrót łączników',font=fonts[23],fill='#34473b');dr.text((1440,655),'4 × 40 mm',font=bold[28],fill='#263b2e')
 else:
  for j,txt in enumerate(['Szerokość800 mm','Głębokość350 mm','Wysokość600 mm','6 elementów / 16 połączeń']):
   for x,y in [('Szerokość800','Szerokość 800'),('Głębokość350','Głębokość 350'),('Wysokość600','Wysokość 600')]:txt=txt.replace(x,y)
   dr.text((1390,405+j*53),txt,font=fonts[26],fill='#34473b')
 for tag in tags.split(',') if tags else []:
  x,y=points[str(frame)][tag];dr.ellipse((x-22,y-22,x+22,y+22),fill='white',outline='#263b2e',width=2);dr.text((x,y),tag,font=bold[20],fill='#263b2e',anchor='mm')
 # True timeline, without covering the native moving model.
 dr.line((58,1002,1870,1002),fill='#d6ddd4',width=5);dr.line((58,1002,58+1812*min(t/38,1),1002),fill='#3d6249',width=5);dr.text((58,1030),f'{t:04.1f}s / 38.0s',font=fonts[20],fill='#6b776c');dr.text((1580,1030),'1920 × 1080 / 24 fps',font=fonts[20],fill='#6b776c')
 im.save(READY/f'{frame:04d}.jpg',quality=96,subsampling=0)
 if frame in [1,132,252,372,492,660,840]:im.save(OUT/f'kadr-{frame:04d}.jpg',quality=96)
 if frame%120==0:print('OVERLAY',frame,flush=True)
args=[str(FF),'-hide_banner','-y','-framerate','24','-i',str(READY/'%04d.jpg'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'wood01-instrukcja-montazu.mp4')]
r=subprocess.run(args,capture_output=True,text=True);(WORK/'encode.log').write_text(r.stderr,encoding='utf-8');assert r.returncode==0
(WORK/'encoding-manifest.json').write_text(json.dumps({'status':'PASS','video':'wood01-instrukcja-montazu.mp4','duration_seconds':38,'frames':912,'fps':24,'dimensions':[1920,1080],'bytes':(OUT/'wood01-instrukcja-montazu.mp4').stat().st_size,'source_frames_actual_Blender':912,'overlay_seconds':round(time.time()-start,2),'external_music_or_TTS':False},indent=2),encoding='utf-8');print('ENCODED_PASS',flush=True)
