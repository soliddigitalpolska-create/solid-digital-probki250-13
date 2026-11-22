from pathlib import Path
import numpy as np, wave, subprocess, json
from PIL import ImageFont
p=Path(__file__).parent/'render'
sr=44100;duration=15; track=np.zeros(sr*duration,dtype=np.float64)
# Original procedural motif, no samples or third-party recording.
notes=[48,55,60,64,48,55,62,67,45,52,60,64,43,50,59,62]
beat=.375
for i in range(40):
 midi=notes[i%len(notes)];freq=440*2**((midi-69)/12);t=np.arange(int(sr*.7))/sr
 env=np.minimum(t/.012,1)*np.exp(-t*6)
 tone=(np.sin(2*np.pi*freq*t)+.24*np.sin(2*np.pi*freq*2*t)+.08*np.sin(2*np.pi*freq*3*t))*env*.18
 start=int(i*beat*sr);n=min(len(tone),len(track)-start)
 if n>0:track[start:start+n]+=tone[:n]
rng=np.random.default_rng(22)
for startsec in [0,4,8,11]:
 n=int(.35*sr);tt=np.linspace(0,1,n);noise=rng.normal(size=n);smoothed=np.convolve(noise,np.ones(20)/20,mode='same')
 start=int(startsec*sr);track[start:start+n]+=smoothed*np.sin(np.pi*tt)**2*.2
track*=np.minimum(np.arange(len(track))/sr/0.1,1)*np.minimum((len(track)-np.arange(len(track)))/sr/.5,1)
track=np.clip(track,-.9,.9)
with wave.open(str(p/'original-audio.wav'),'wb') as out:
 out.setnchannels(1);out.setsampwidth(2);out.setframerate(sr);out.writeframes((track*32767).astype('<i2').tobytes())
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
blocks=[('Ruch zamiast slajdu',0,4,48),('Przestrzeń na zabawę',4,8,44),('Produkt w roli głównej',8,11,42),('Sprawdź szczegóły',11,15,44)]
f=['hqdn3d=3:3:4:4','fps=24',"drawbox=x=0:y=0:w=iw:h=185:color=0xF5F0E5:t=fill", "drawbox=x=0:y=810:w=iw:h=150:color=0x15372D:t=fill"]
for text,a,b,size in blocks:
 while ImageFont.truetype(bold,size).getlength(text)>460:size-=1
 f.append(f"drawtext=fontfile={bold}:text='{text}':fontcolor=0x163B2D:fontsize={size}:x=(w-text_w)/2:y=72:enable='gte(t,{a})*lt(t,{b})'")
f.append(f"drawtext=fontfile={regular}:text='AUTORSKA ANIMACJA 3D / DEMO':fontcolor=0xEFF3E9:fontsize=21:x=(w-text_w)/2:y=847")
f.append(f"drawtext=fontfile={regular}:text='CloudCode Studio':fontcolor=0xBCCD9A:fontsize=22:x=(w-text_w)/2:y=886")
cmd=['ffmpeg','-y','-framerate','10','-i',str(p/'frame_%04d.png'),'-i',str(p/'original-audio.wav'),'-vf',','.join(f),'-c:v','libx264','-preset','medium','-crf','26','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-af','loudnorm=I=-18:TP=-2:LRA=7','-t','15','-movflags','+faststart',str(p/'product-motion-demo.mp4')]
subprocess.run(cmd,check=True,capture_output=True)
subprocess.run(['ffmpeg','-y','-ss','5','-i',str(p/'product-motion-demo.mp4'),'-frames:v','1',str(p/'poster.jpg')],check=True,capture_output=True)
result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p/'product-motion-demo.mp4')],check=True,capture_output=True,text=True)
(p/'media-check.json').write_text(result.stdout)
meta=json.loads(result.stdout)
print(json.dumps({'duration':meta['format']['duration'],'size':meta['format']['size'],'streams':[(s['codec_type'],s['codec_name'],s.get('width'),s.get('height')) for s in meta['streams']]},ensure_ascii=False))
