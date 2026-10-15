import sys,json,math,subprocess,hashlib,zipfile,html,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'proof-145002-deps'))
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=ROOT/'outputs/probki-plus28-2026-10-15/logo-tracking';OUT.mkdir(exist_ok=True,parents=True)
frames=HERE/'source-frames';dest=HERE/'after-frames';dest.mkdir(exist_ok=True)
gt=json.loads((HERE/'ground-truth.json').read_text());W,H=gt['width'],gt['height']
reference=cv2.imread(str(frames/'0000.png'));gray0=cv2.cvtColor(reference,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(nfeatures=4000,contrastThreshold=.006,edgeThreshold=20)
refs=[]
for i,quad in enumerate(gt['frames'][0]['label_quads']):
 q=np.float32(quad);mask=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(mask,np.int32(q),255)
 kp,des=sift.detectAndCompute(gray0,mask)
 assert des is not None and len(kp)>=6,(i,'too few initial keypoints',len(kp))
 im=Image.new('RGB',(640,300),'#e8e9e4');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',92);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',29)
 d.rounded_rectangle((20,20,620,280),radius=18,outline='#285750',width=8)
 d.text((85,67),'SDP' if i==0 else 'LAB',font=font,fill='#26564e');d.text((85,196),'AUTORSKI ZNAK / DEMO',font=small,fill='#57756b')
 im.save(OUT/f'new-logo-{i}.png')
 patch=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR)
 M=cv2.getPerspectiveTransform(np.float32([[0,0],[639,0],[639,299],[0,299]]),q)
 overlay=cv2.warpPerspective(patch,M,(W,H));alpha=cv2.warpPerspective(np.full((300,640),255,np.uint8),M,(W,H))
 refs.append({'kp':kp,'des':des,'quad':q,'overlay':overlay,'alpha':alpha})
log=[]
bf=cv2.BFMatcher(cv2.NORM_L2)
for row in gt['frames']:
 f=row['frame'];source=cv2.imread(str(frames/f'{f:04d}.png'));gray=cv2.cvtColor(source,cv2.COLOR_BGR2GRAY);kp,des=sift.detectAndCompute(gray,None);result=source.copy();info=[]
 occlusion=np.zeros((H,W),np.uint8);hull=cv2.convexHull(np.int32(row['occluder_projected_vertices']));cv2.fillConvexPoly(occlusion,hull,255)
 for i,r in enumerate(refs):
  if f==0:hom=np.eye(3);good=[];inliers=len(r['kp'])
  else:
   matches=bf.knnMatch(r['des'],des,k=2);good=[a for a,b in matches if a.distance<.78*b.distance]
   assert len(good)>=4,(f,i,'insufficient matches',len(good))
   src=np.float32([r['kp'][m.queryIdx].pt for m in good]);dst=np.float32([kp[m.trainIdx].pt for m in good]);hom,ok=cv2.findHomography(src,dst,cv2.RANSAC,2.5)
   assert hom is not None,(f,i,'homography failed');inliers=int(ok.sum())
  estimated=cv2.perspectiveTransform(r['quad'][None,:,:],hom)[0];truth=np.float32(row['label_quads'][i]);error=float(np.sqrt(np.mean(np.sum((estimated-truth)**2,axis=1))))
  assert error<100,(f,i,'tracking error over 100px',error)
  patch=cv2.warpPerspective(r['overlay'],hom,(W,H));alpha=cv2.warpPerspective(r['alpha'],hom,(W,H))
  alpha=cv2.erode(alpha,np.ones((2,2),np.uint8));alpha=cv2.GaussianBlur(alpha,(3,3),.5);alpha[occlusion>0]=0
  # Estimate illumination from the observed label paper, independent of motion ground truth.
  sample=gray[alpha>230];level=float(np.percentile(sample,85))/238 if len(sample) else 1
  patch=np.uint8(np.clip(patch.astype(float)*min(1.15,max(.55,level)),0,255))
  a=(alpha.astype(float)/255)[:,:,None];result=np.uint8(patch*a+result*(1-a))
  info.append({'surface':i,'reference_keypoints':len(r['kp']),'matches':len(good),'inliers':inliers,'raw_corner_rmse_px':round(error,3),'observed_quad':estimated.tolist(),'illumination_scale':round(level,3),'occlusion_mask':'Own geometry projection, not an automatic segmentation claim'})
 cv2.imwrite(str(dest/f'{f:04d}.png'),result)
 log.append({'frame':f,'surfaces':info})
# A five-frame temporal median suppresses isolated feature-matching jitter.
# It uses only image-derived quadrilaterals, never the source motion transforms.
observed=np.array([[r['observed_quad'] for r in f['surfaces']] for f in log])
filtered=observed.copy()
for f in range(2,len(log)-2):filtered[f]=np.median(observed[f-2:f+3],axis=0)
for row,entry in zip(gt['frames'],log):
 f=row['frame'];source=cv2.imread(str(frames/f'{f:04d}.png'));gray=cv2.cvtColor(source,cv2.COLOR_BGR2GRAY);result=source.copy();occlusion=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(occlusion,cv2.convexHull(np.int32(row['occluder_projected_vertices'])),255)
 for i,r in enumerate(refs):
  hom=cv2.getPerspectiveTransform(r['quad'],np.float32(filtered[f,i]));patch=cv2.warpPerspective(r['overlay'],hom,(W,H));alpha=cv2.warpPerspective(r['alpha'],hom,(W,H));alpha=cv2.erode(alpha,np.ones((2,2),np.uint8));alpha=cv2.GaussianBlur(alpha,(3,3),.5);alpha[occlusion>0]=0
  sample=gray[alpha>230];level=float(np.percentile(sample,85))/238 if len(sample) else 1;patch=np.uint8(np.clip(patch.astype(float)*min(1.15,max(.55,level)),0,255));a=(alpha.astype(float)/255)[:,:,None];result=np.uint8(patch*a+result*(1-a))
  error=float(np.sqrt(np.mean(np.sum((filtered[f,i]-np.float32(row['label_quads'][i]))**2,axis=1))));entry['surfaces'][i]['corner_rmse_px']=round(error,3)
 cv2.imwrite(str(dest/f'{f:04d}.png'),result)
ffmpeg=ROOT/'work/useme-pakiet35-2026-10-11/vendor/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
for folder,name in [(frames,'before.mp4'),(dest,'after.mp4')]:
 subprocess.run([str(ffmpeg),'-y','-loglevel','error','-framerate',str(gt['fps']),'-i',str(folder/'%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/name)],check=True)
subprocess.run([str(ffmpeg),'-y','-loglevel','error','-i',str(OUT/'before.mp4'),'-i',str(OUT/'after.mp4'),'-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'before-after.mp4')],check=True)
maxerror=max(r['corner_rmse_px'] for f in log for r in f['surfaces']);medianerror=statistics.median(r['corner_rmse_px'] for f in log for r in f['surfaces'])
assert maxerror<=3.5 and medianerror<=1,('Controlled test tracking tolerance failed',maxerror,medianerror)
assert (frames/'0000.png').read_bytes()!=(frames/'0024.png').read_bytes(),'Source motion must be real, not a repeated frame'
evidence={'frame_count':len(log),'fps':gt['fps'],'resolution':[W,H],'motion':'Two independent 3D label surfaces with perspective changes, rendered in Blender','tracker':'OpenCV SIFT features, ratio test, RANSAC homography and five-frame temporal median; no ground-truth transforms used for placement','max_corner_rmse_px':maxerror,'median_corner_rmse_px':medianerror,'raw_max_corner_rmse_px':max(r['raw_corner_rmse_px'] for f in log for r in f['surfaces']),'occlusion':'Own opaque foreground beam. Mask computed from own source geometry, analogous to supplied holdout/rotoscope; not proof of automatic mask extraction from arbitrary client footage.','sample_status':'Own controlled test; not client footage, no commercial case, no promise that 16 client shots can be automatically processed.','client_scope':'Approx.16 shots,2–10sec each, two logos, perspective and occlusion. Each client shot requires manual review and masks as needed.','software':{'OpenCV':cv2.__version__,'Blender':'5.2.2'},'log':log}
(OUT/'tracking-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['render_source.py','track_and_package.py']:(OUT/name).write_text((HERE/name).read_text(encoding='utf-8'),encoding='utf-8')
for i in [0,24,35,59]:
 a=Image.open(frames/f'{i:04d}.png');b=Image.open(dest/f'{i:04d}.png');im=Image.new('RGB',(W*2,H));im.paste(a,(0,0));im.paste(b,(W,0));im.resize((1000,281)).save(OUT/f'comparison-{i:02d}.jpg',quality=90)
page=f'''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Podmiana logo — rzeczywisty tracking perspektywiczny</title><style>body{{background:#eef0e9;color:#1c3430;font:16px/1.7 Arial,sans-serif;margin:0}}main{{max-width:1100px;padding:35px 24px;margin:auto}}h1{{font-size:clamp(36px,6vw,65px);line-height:1.05;letter-spacing:-2px}}h2{{font-size:27px}}.tag{{font-size:11px;letter-spacing:2px;text-transform:uppercase}}video,img{{max-width:100%;height:auto;border-radius:8px}}section{{margin:40px 0;padding:28px;background:white;border-radius:12px}}a{{color:#236154}}.note{{font-size:13px;padding:20px;background:#e2e8d7}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}@media(max-width:700px){{.grid{{grid-template-columns:1fr}}section{{padding:20px}}}}</style></head><body><main><p class="tag">Autorski test / niewdrożony</p><h1>Dwa znaki.<br>Ruch, perspektywa i przesłonięcie.</h1><p>Rzeczywiste śledzenie dwóch powierzchni po wyrenderowaniu własnego materiału. Nowe logo jest nakładane w postprodukcji; ruchu nie kopiujemy z animacji 3D.</p><p class="note">To kontrolowany test na własnym modelu i własnych znakach. Nie jest materiałem klienta, realizacją komercyjną ani dowodem automatycznego usunięcia logo z dowolnego filmu.</p><section><h2>Przed / po</h2><video controls preload="metadata" src="before-after.mp4" poster="comparison-00.jpg"></video><p>Po lewej materiał źródłowy, po prawej wynik. Dwie powierzchnie poruszają się niezależnie i zmieniają perspektywę; belka przechodzi przed obiektem.</p></section><section><h2>Co faktycznie sprawdzono</h2><ul><li>{len(log)} klatek × 2 śledzone powierzchnie, {gt['fps']} kl./s, {W} × {H}.</li><li>SIFT → dopasowanie cech → RANSAC → homografia. Dane geometrii nie sterują położeniem nowego znaku.</li><li>Kontrola porównuje wynik śledzenia z osobną geometrią wzorcową: maks. błąd narożników {maxerror:.2f}px, mediana {medianerror:.2f}px przy tej rozdzielczości.</li><li>Rzeczywiste przesłonięcie nowego znaku przez obiekt pierwszego planu.</li><li>Maska pochodzi z własnej sceny, nie z automatycznego wycinania dowolnego filmu. W zleceniu odpowiednie maski trzeba przygotować dla rzeczywistych ujęć.</li><li>Jasność znaku dopasowana na podstawie obrazu; krawędzie wygładzone.</li></ul></section><section><h2>Zbliżenie kontroli klatek</h2>{''.join(f'<img src="comparison-{i:02d}.jpg" alt="Klatka {i}, oryginał i wynik">' for i in [0,24,35,59])}</section><section><h2>Źródła i granice</h2><p>Model, tekstury, znaki i animacja są własne. Plik .blend zawiera spakowane własne tekstury. Źródła Python i log pozwalają sprawdzić wykonanie. Ten przykład nie obejmuje cudzych znaków ani modeli.</p><p>Naturalność retuszu, rozmycie ruchu i maski ocenia się osobno w każdym ujęciu klienta. Brakujący materiał źródłowy trzeba obejrzeć przed potwierdzeniem ostatecznej realizacji.</p><p><a href="../logo-tracking-zrodla.zip">Pobierz komplet źródeł ZIP</a> · <a href="own-source-robot.blend">Natywny plik Blender</a> · <a href="tracking-evidence.json">Dane kontroli</a> · <a href="before.mp4">Oryginał MP4</a> · <a href="after.mp4">Wynik MP4</a></p></section><p class="tag">Autorska próbka · bez publikacji i wysyłki z tego pliku</p></main></body></html>'''
(OUT/'index.html').write_text(page,encoding='utf-8')
(OUT/'README.txt').write_text('Autorski kontrolowany test. Otwórz index.html. Przed/po w MP4. Własny model .blend i znaki, brak materiału klienta. Ruch logo po wyrenderowaniu filmu wyznacza SIFT/RANSAC, nie gotowe krzywe 3D. Maska okluzji pochodzi z własnej sceny; nie jest dowodem automatycznej segmentacji obcej surówki. Log błędów w tracking-evidence.json. Żadnej oferty nie wysłano przez te pliki.\n',encoding='utf-8')
archive=OUT.parent/'logo-tracking-zrodla.zip'
for backup in OUT.glob('*.blend1'):
 assert backup.resolve().parent==OUT.resolve();backup.unlink()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.iterdir():
  if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
assert all(p.stat().st_size<30*1024*1024 for p in OUT.iterdir() if p.is_file())
(HERE/'validation.json').write_text(json.dumps({k:v for k,v in evidence.items() if k!='log'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('TRACKING_PASS',maxerror,medianerror,'ZIP',archive.stat().st_size)
