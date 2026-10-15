"""Local product-media workflow. Inputs -> preset -> MP4 + captions + manifest.
The original image is only resized proportionally. No model generates/repaints it.
Narration is supplied as an audio file. No network/provider call is implemented.
"""
import argparse,hashlib,json,math,re,subprocess,sys,wave
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

PRESETS={
 'product-focus':{'bg':'#f4f1e9','fg':'#173b37','accent':'#ad764d','eyebrow':'PRODUKT / JEDEN ZAPIS','layout':'centered'},
 'editorial':{'bg':'#163d38','fg':'#fff9e9','accent':'#e4ba77','eyebrow':'DETAL MA ZNACZENIE','layout':'offset'},
}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',size)
def wrap(draw,text,face,max_width):
    result=[];line=''
    for word in text.split():
        new=(line+' '+word).strip()
        if line and draw.textbbox((0,0),new,font=face)[2]>max_width:result.append(line);line=word
        else:line=new
    if line:result.append(line)
    return result
def block(draw,text,xy,face,color,width,line_height,max_lines=4):
    lines=wrap(draw,text,face,width)
    if len(lines)>max_lines:raise ValueError('Text too long for layout; shorten the supplied copy')
    x,y=xy
    for line in lines:draw.text((x,y),line,font=face,fill=color);y+=line_height
    return y
def srt_time(sec):
    ms=round(sec*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
def run(job_path,output,preset,ratio,size,ffmpeg):
    job_path=Path(job_path).resolve();job=json.loads(job_path.read_text(encoding='utf-8'))
    assets={key:(job_path.parent/job[key]).resolve() for key in ('image','audio')}
    if job.get('video'):assets['video']=(job_path.parent/job['video']).resolve()
    for key,path in assets.items():
        if not path.is_file():raise ValueError(f'Missing source {key}: {path.name}')
    if not Path(ffmpeg).is_file():raise ValueError('Missing source ffmpeg executable')
    duration=float(job['duration'])
    if not 0<duration<=30:raise ValueError('Duration must be greater than zero and at most 30 seconds')
    if ratio=='9:16':w,h=size,round(size*16/9)
    else:w,h=round(size*16/9),size
    w+=w%2;h+=h%2
    captions=job.get('captions',[{'start':0,'end':duration,'text':job['caption']}])
    for cap in captions:
        if not 0<=float(cap['start'])<float(cap['end'])<=duration+.001:raise ValueError('Invalid caption timing')
    # Preflight all layouts before creating the output directory.
    style=PRESETS[preset];base=Image.new('RGB',(w,h),style['bg']);draw=ImageDraw.Draw(base)
    margin=round(w*.065);portrait=h>w;unit=min(w,h)
    headline=font(round(unit*.073),True);small=font(round(unit*.026),True)
    eyebrow=font(round(unit*.023),True);capface=font(round(unit*.044),True)
    draw.text((margin,round(h*.045)),style['eyebrow'],font=eyebrow,fill=style['accent'])
    text_width=round(w*.85) if portrait else round(w*.40)
    block(draw,job['headline'],(margin,round(h*.09)),headline,style['fg'],text_width,round(unit*.085),max_lines=3)
    box=(margin,round(h*.26),w-margin,round(h*.735)) if portrait else (round(w*.50),round(h*.08),w-margin,round(h*.74))
    if preset=='editorial' and portrait:box=(round(w*.12),round(h*.27),round(w*.94),round(h*.75))
    source=Image.open(assets['image']).convert('RGB')
    if 'video' in assets:
        info=subprocess.run([str(ffmpeg),'-hide_banner','-i',str(assets['video'])],capture_output=True,text=True)
        video_line=next((line for line in info.stderr.splitlines() if 'Video:' in line),'')
        dimensions=re.search(r'[, ](\d{2,5})x(\d{2,5})[, ]',video_line)
        if not dimensions:raise ValueError('Cannot decode source video dimensions')
        source=Image.new('RGB',(int(dimensions.group(1)),int(dimensions.group(2))),'white')
    factor=min((box[2]-box[0])/source.width,(box[3]-box[1])/source.height)
    sw,sh=round(source.width*factor),round(source.height*factor)
    px=box[0]+(box[2]-box[0]-sw)//2;py=box[1]+(box[3]-box[1]-sh)//2
    resized=source.resize((sw,sh),Image.Resampling.LANCZOS)
    draw.rounded_rectangle((box[0]-8,box[1]-8,box[2]+8,box[3]+8),radius=round(unit*.024),fill='white')
    base.paste(resized,(px,py))
    footer_y=round(h*.91)
    draw.text((margin,footer_y),'PRÓBKA AUTORSKA / WŁASNY MODEL 3D',font=font(round(unit*.019),True),fill=style['accent'])
    draw.text((margin,round(h*.95)),'Źródło bez generatywnej modyfikacji produktu',font=font(round(unit*.018)),fill=style['fg'])
    # Check caption length before encoding as well.
    for cap in captions:
        if len(wrap(draw,cap['text'],capface,w-2*margin-30))>3:raise ValueError('Caption too long')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    (output/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}" for i,c in enumerate(captions))+'\n',encoding='utf-8')
    fps=24;frames=math.ceil(duration*fps)
    command=[str(ffmpeg),'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','pipe:0','-i',str(assets['audio']),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-af','apad','-t',str(duration),'-movflags','+faststart',str(output/'video.mp4')]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    decoder=None;decoded_frames=0
    if 'video' in assets:
        decoder=subprocess.Popen([str(ffmpeg),'-hide_banner','-loglevel','error','-i',str(assets['video']),'-an','-vf',f'fps={fps},scale={sw}:{sh},tpad=stop_mode=clone:stop_duration={duration}','-t',str(duration),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for number in range(frames):
            t=number/fps;frame=base.copy();d=ImageDraw.Draw(frame)
            if decoder:
                raw=decoder.stdout.read(sw*sh*3)
                if len(raw)!=sw*sh*3:raise RuntimeError('Source video ended before the planned output')
                frame.paste(Image.frombytes('RGB',(sw,sh),raw),(px,py));decoded_frames+=1
            active=next((c for c in captions if float(c['start'])<=t<float(c['end'])),None)
            if active:
                y=round(h*.785);d.rounded_rectangle((margin-14,y-12,w-margin+14,round(h*.89)),radius=round(unit*.017),fill='#102f2c')
                block(d,active['text'],(margin,y),capface,'#ffffff',w-2*margin,round(unit*.053),max_lines=3)
            d.rectangle((margin,round(h*.765),margin+round((w-2*margin)*(number+1)/frames),round(h*.769)),fill=style['accent'])
            process.stdin.write(frame.tobytes())
            if number==0:frame.save(output/'poster.jpg',quality=92)
        process.stdin.close();stderr=process.stderr.read().decode('utf-8','replace');code=process.wait()
    except Exception:
        process.kill();process.wait();raise
    finally:
        if decoder:
            decoder.stdout.close()
            try:decoder.wait(timeout=5)
            except subprocess.TimeoutExpired:decoder.kill();decoder.wait()
    if code:raise RuntimeError(f'Encoder failed: {stderr}')
    # Decoder inspection: catches corrupt output and absent/mismatched tracks.
    inspect=subprocess.run([str(ffmpeg),'-hide_banner','-i',str(output/'video.mp4'),'-f','null','-'],capture_output=True,text=True)
    if inspect.returncode:raise RuntimeError('Output did not decode: '+inspect.stderr)
    audio_present='Audio: aac' in inspect.stderr
    if not audio_present:raise RuntimeError('Encoded output is missing narration')
    (output/'decode.log').write_text(inspect.stderr,encoding='utf-8')
    manifest={'preset':preset,'ratio':ratio,'source':{key:{'filename':path.name,'sha256':digest(path)} for key,path in assets.items()},'source_kind':job.get('source_kind','client-supplied'),'audio_kind':job.get('audio_kind','client-supplied'),'source_video_frames_decoded':decoded_frames,'video_input_processing':'Original decoded frames; proportional fit, 24fps resampling and final-frame hold if narration is longer. No generated motion.','product_geometry':{'source_dimensions':list(source.size),'source_aspect_ratio':source.width/source.height,'image_box':[px,py,sw,sh],'operation':'proportional resize + original source pixels; no crop, inpaint or image generation'},'output':{'filename':'video.mp4','sha256':digest(output/'video.mp4'),'dimensions':[w,h],'fps':fps,'frames':frames,'duration_seconds':duration,'audio_present':audio_present,'codec':'H264/AAC','caption_count':len(captions),'captions_burned_in':True},'network_calls':0,'llm_called':False,'generative_video_called':False,'commercial_voice_licence_claimed':False,'production_voice_requirement':'Client-provided audio or a licensed provider agreed before financing. Local TTS is only a technical demo.'}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(output),'dimensions':[w,h],'frames':frames,'audio_present':audio_present}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);p.add_argument('--output',required=True);p.add_argument('--preset',choices=PRESETS,required=True);p.add_argument('--ratio',choices=['9:16','16:9'],required=True);p.add_argument('--size',type=int,default=1080);p.add_argument('--ffmpeg',required=True)
    args=p.parse_args()
    try:run(args.job,args.output,args.preset,args.ratio,args.size,args.ffmpeg)
    except Exception as exc:print(f'{type(exc).__name__}: {exc}',file=sys.stderr);sys.exit(1)
