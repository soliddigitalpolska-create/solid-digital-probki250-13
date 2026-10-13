"""Generate7 original synthetic4-second demonstrations. No client music."""
from pathlib import Path
import json
import subprocess
import sys
import wave
import numpy as np

BASE=Path(__file__).resolve().parent
(BASE/'audio').mkdir(exist_ok=True)
SR=48000
profiles=['Spokojne wejście','Ciepłe popołudnie','Lekki ruch','Przestrzeń','Wieczorny spokój','Jasny poranek','Neutralne tło']
tracks=[]
for number,base_note in enumerate([48,50,52,53,55,57,59],1):
    t=np.arange(4*SR)/SR
    values=np.zeros(len(t))
    for step,note in enumerate([base_note,base_note+7,base_note+4,base_note+12]):
        selected=(t>=step)&(t<step+1)
        local=t[selected]-step
        frequency=440*2**((note-69)/12)
        envelope=np.sin(np.pi*local)**2
        values[selected]=.15*envelope*(np.sin(2*np.pi*frequency*local)+.22*np.sin(2*np.pi*frequency*2*local))
    path=BASE/'audio'/f't{number:02d}.wav'
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(SR);out.writeframes(np.rint(values*32767).astype('<i2').tobytes())
    target=path.with_suffix('.mp3')
    result=subprocess.run([sys.argv[1],'-hide_banner','-nostdin','-y','-i',str(path),'-c:a','libmp3lame','-b:a','128k',str(target)],capture_output=True,timeout=30)
    if result.returncode:raise RuntimeError('Synthetic audio encode failed')
    tracks.append({'id':f't{number:02d}','name':f'Własna próbka {number:02d}','file':f'audio/t{number:02d}.mp3','source_duration':4,'kind':'own synthetic test; not client catalog'})
catalog={'kind':'own synthetic engineering demo','tracks':tracks,'profiles':[{'id':f'p{index:02d}','name':name,'demo_library':'Shared7 original synthetic tracks, not75+ client tracks'} for index,name in enumerate(profiles,1)]}
(BASE/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'own_tracks':7,'own_profiles':7,'source_seconds_each':4,'client_tracks':0}))
