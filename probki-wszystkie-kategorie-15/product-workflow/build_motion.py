import hashlib,json,shutil,subprocess,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKSPACE=HERE.parents[3]
FFMPEG=WORKSPACE/'work/useme-pakiet35-2026-10-11/vendor/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
assets=HERE/'inputs'
for i in (1,2):
    shutil.copyfile(WORKSPACE/f'outputs/probki-plus28-2026-10-15/raw-cut/sources/shot-{i:02}.mp4',assets/f'own-shot-{i}.mp4')
(assets/'concat.txt').write_text("file 'own-shot-1.mp4'\nfile 'own-shot-2.mp4'\n",encoding='utf-8')
subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(assets/'concat.txt'),'-c','copy',str(assets/'own-lamp-footage.mp4')],check=True)
job=json.loads((assets/'job.json').read_text(encoding='utf-8'));job['video']='own-lamp-footage.mp4';job['source_kind']='Own actual Blender camera-orbit footage, two source clips, 540x960; not physical client footage. Original frames decoded; no generated video.'
(assets/'motion-job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
results=[]
for preset in ['product-focus','editorial']:
    for ratio in ['9:16','16:9']:
        name='motion-'+preset+'-'+ratio.replace(':','x');output=HERE/name
        subprocess.run([sys.executable,str(HERE/'workflow.py'),'--job',str(assets/'motion-job.json'),'--output',str(output),'--preset',preset,'--ratio',ratio,'--size','1080','--ffmpeg',str(FFMPEG)],check=True)
        results.append({'name':name,**json.loads((output/'manifest.json').read_text(encoding='utf-8'))})
tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_workflow.py','-v'],capture_output=True,text=True)
(HERE/'tests.log').write_text(tests.stdout+'\n'+tests.stderr,encoding='utf-8');assert tests.returncode==0
qa=json.loads((HERE/'qa.json').read_text(encoding='utf-8'));qa['still_output_count']=4;qa['motion_output_count']=4;qa['output_count']=8;qa['tests_passed']=3;qa['test_return_code']=0;qa['motion_results']=results;qa['source_clips']=[{'file':f'inputs/own-shot-{i}.mp4','sha256':hashlib.sha256((assets/f'own-shot-{i}.mp4').read_bytes()).hexdigest(),'same_as_existing_frozen_source':(assets/f'own-shot-{i}.mp4').read_bytes()==(WORKSPACE/f'outputs/probki-plus28-2026-10-15/raw-cut/sources/shot-{i:02}.mp4').read_bytes()} for i in (1,2)]
qa['motion_frames_decoded']=sum(r['source_video_frames_decoded'] for r in results);qa['rendered_frames']=sum(r['output']['frames'] for r in qa['results']+results)
(HERE/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
cards=''.join(f'<article><h3>Wideo wejściowe / {r["preset"]} / {r["ratio"]}</h3><video controls preload="metadata" playsinline poster="{r["name"]}/poster.jpg" src="{r["name"]}/video.mp4"></video><p><a href="{r["name"]}/video.mp4">MP4</a> · <a href="{r["name"]}/captions.srt">Napisy</a> · <a href="{r["name"]}/manifest.json">Źródła i metadane</a></p></article>' for r in results)
html=(HERE/'index.html').read_text(encoding='utf-8')
html=html.replace('cztery rzeczywiste eksporty','osiem rzeczywistych eksportów').replace('<b>4</b>gotowe MP4','<b>8</b>gotowe MP4').replace('<b>2 / 2</b>testy','<b>3 / 3</b>testy').replace('Dekoder sprawdził cztery pełne filmy.','Dekoder sprawdził osiem pełnych filmów.')
html=html.replace('<section><h2>Porównaj rzeczywiste pliki</h2>','<section><h2>Rzeczywisty klip wejściowy → gotowa rolka</h2><p>Oryginalne ruchome klatki z dwóch własnych ujęć kamery Blender (pełna lampa i detal podstawy), wejście 540×960. To nie są fizyczne nagrania klienta. Workflow dekoduje klatki, dopasowuje proporcje i dodaje audio/layout/napisy. Gdy narracja jest dłuższa, zatrzymuje ostatnią klatkę; nie tworzy nowego ruchu. Pliki wyjściowe mają rozdzielczość 1080p, bez twierdzenia o odzyskaniu szczegółów ponad źródło.</p><p><a href="inputs/own-lamp-footage.mp4">Dokładny ruchomy plik wejściowy</a> · <a href="inputs/motion-job.json">Dane scenariusza</a></p><div class="grid">'+cards+'</div></section><section><h2>Drugi rodzaj wejścia: obraz PNG</h2>')
html=html.replace('Jeden folder źródeł, dwa presety','Ruchomy klip albo obraz PNG, dwa presety').replace('Źródłem jest własny render natywnego modelu Blender, a nie fotografia fizycznego produktu klienta.','Źródłami są własny render i rzeczywiste ruchome ujęcia kamery z natywnego modelu Blender, a nie fotografia ani nagranie fizycznego produktu klienta.')
html=html.replace('Własny obraz PNG i plik WAV','Własny obraz PNG lub klip MP4 i plik WAV').replace('Powtarzalny workflow lokalny z plikiem danych, dwoma presetami','Powtarzalny workflow lokalny dla obrazu i rzeczywistych klatek wideo z plikiem danych, dwoma presetami')
(HERE/'index.html').write_text(html,encoding='utf-8')
readme=(HERE/'README.txt').read_text(encoding='utf-8');readme+='\nWideo wejściowe: użyj inputs/motion-job.json. Workflow zachowuje oryginalne klatki, zmienia proporcjonalnie rozmiar i może trzymać ostatnią klatkę, jeśli audio jest dłuższe. Źródło demo 540x960, eksport 1080p bez twierdzenia o dodanej jakości.\nFFmpeg dla testów: ustaw zmienną FFMPEG_EXE na lokalny plik binarny albo dodaj ffmpeg do PATH.\n';(HERE/'README.txt').write_text(readme,encoding='utf-8')
with zipfile.ZipFile(HERE/'workflow-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in [HERE/'workflow.py',HERE/'test_workflow.py',HERE/'README.txt',HERE/'qa.json',HERE/'tests.log']+list(assets.glob('*')):
        if path.is_file():archive.write(path,path.relative_to(HERE))
print(json.dumps({'outputs':8,'motion_frames_decoded':qa['motion_frames_decoded'],'total_rendered_frames':qa['rendered_frames'],'tests_passed':3,'all_motion_audio':all(r['output']['audio_present'] for r in results)},indent=2))
