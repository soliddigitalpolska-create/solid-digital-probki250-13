import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import crypto from 'node:crypto';
const require=createRequire(import.meta.url);
const sharp=require(process.env.FASHION_SHARP_MODULE || 'sharp');
const R=path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1'));
const P=path.join(R,'publishable');await fs.mkdir(P,{recursive:true});
const originals=['01-editorial-outfit.png','02-knit-detail.png','03-capsule-flatlay.png'];
const photos=await Promise.all(originals.map(async name=>{const bytes=await fs.readFile(path.join(R,'originals',name));return {name,bytes,uri:'data:image/png;base64,'+bytes.toString('base64'),sha256:crypto.createHash('sha256').update(bytes).digest('hex'),...(await sharp(bytes).metadata())};}));
const bg='#F3EFE7',ink='#292D29',muted='#615D53';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const text=(x,y,s,size=24,col=ink,serif=false,bold=false,spacing=0)=>`<text x="${x}" y="${y}" font-family="${serif?'Georgia':'Segoe UI'}" font-size="${size}" fill="${col}" font-weight="${bold?700:400}" letter-spacing="${spacing}">${esc(s)}</text>`;
const rect=(x,y,w,h,fill,r=0)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" rx="${r}"/>`;
const line=(x1,y1,x2,y2,col=ink,sw=1)=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="${sw}"/>`;
const photo=(i,x,y,w,h,opacity=1)=>`<image href="${photos[i].uri}" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="xMidYMid meet" opacity="${opacity}"/>`;
const start=(w,h,title)=>`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">Własna demonstracja fikcyjnej marki FORMA. Oryginalna wizualizacja AI, bez prawdziwego produktu klienta lub historii prowadzenia kont.</desc>`;
const end='</svg>';
const label=(y=1312)=>rect(49,y-17,607,29,'#F3EFE7',3)+text(61,y+2,'DEMO / FIKCYJNA MARKA / WIZUALIZACJA AI',13,muted,false,false,1.1);
const header=()=>text(63,79,'FORMA',28,ink,false,false,8)+text(858,75,'STUDY / 01',12,ink,false,false,1.5);
const posts=[
 {name:'01-editorial-post',title:'Styl bez pośpiechu.',svg:start(1080,1350,'Forma - własny post fashion: editorial')+photo(0,0,0,1080,1350)+header()+text(64,273,'Styl bez',76,ink,true)+text(64,361,'pośpiechu.',76,ink,true)+text(68,414,'JEDNA STYLIZACJA. WŁASNY RYTM.',13,ink,false,false,1.5)+rect(64,1114,310,57,'#F3EFE7',28)+text(87,1151,'Zapisz tę inspirację',19,ink,false,true)+label()+end},
 {name:'02-detail-post',title:'Detal robi różnicę.',svg:start(1080,1350,'Forma - własny post fashion: detal')+rect(0,0,1080,1350,bg)+header()+text(64,183,'Detal robi',77,ink,true)+text(64,272,'różnicę.',77,ink,true)+photo(1,298,350,719,898.75)+line(66,374,228,374,muted)+text(65,446,'FAKTURA',15,muted,false,false,2)+text(65,480,'ŚWIATŁO',15,muted,false,false,2)+text(65,514,'FORMA',15,muted,false,false,2)+text(62,1135,'02',94,ink,true)+label()+end},
 {name:'03-capsule-post',title:'Jedna paleta. Wiele możliwości.',svg:start(1080,1350,'Forma - własny post fashion: capsule flat lay')+photo(2,0,0,1080,1350)+header()+text(64,177,'Jedna paleta.',73,ink,true)+text(64,262,'Wiele możliwości.',73,ink,true)+text(68,318,'ZESTAW ZBUDOWANY WOKÓŁ KONTRASTU.',13,ink,false,false,1.5)+rect(715,1237,303,51,'#F3EFE7',25)+text(743,1269,'Który detal wybierasz?',16,ink,false,true)+label()+end}
];
for(const p of posts){await fs.writeFile(path.join(P,p.name+'.svg'),p.svg);await sharp(Buffer.from(p.svg)).png().toFile(path.join(P,p.name+'.png'));await sharp(Buffer.from(p.svg)).resize({width:864}).png().toFile(path.join(P,p.name+'-preview.png'));}

const chapters=[['Jak zbudować','spójny look?'],['Zacznij od','jednej palety.'],['Dodaj kontrast.','Zostaw oddech.']];
function reelFrame(t){
 const i=Math.min(2,Math.floor(t/4));const local=t-i*4;
 const u=Math.min(1,Math.max(0,local/0.65));const ease=1-Math.pow(1-u,3);const shift=28*(1-ease);
 const progress=Math.min(1,t/12);const imageShift=10*Math.sin(local*Math.PI/8);
 let s=start(1080,1920,'Forma - własna rolka 2D fashion')+rect(0,0,1080,1920,bg);
 s+=text(61,98,'FORMA',31,ink,false,false,9)+text(855,94,`0${i+1} / 03`,14,muted,false,false,1.4)+line(60,136,1020,136,'#B2AA9D');
 s+=`<g opacity="${ease.toFixed(4)}">`+text(60,248+shift,chapters[i][0],71,ink,true)+text(60,333+shift,chapters[i][1],71,ink,true)+'</g>';
 s+=photo(i,48,408+imageShift,984,1230);
 s+=text(61,1712,i===0?'OUTFIT STUDY':i===1?'DETAIL STUDY':'CAPSULE STUDY',14,muted,false,false,2);
 s+=line(60,1750,1020,1750,'#CEC7BA',2)+line(60,1750,60+960*progress,1750,ink,3);
 s+=text(61,1825,i===2?'Zapisz. Wróć po inspirację.':'Spójność zaczyna się od prostych decyzji.',25,ink,false,false);
 s+=text(61,1880,'DEMO / FIKCYJNA MARKA / OBRAZY AI / MOTION 2D',12,muted,false,false,1);
 return s+end;
}
for(const t of [1,5,9]){const svg=reelFrame(t);await fs.writeFile(path.join(P,'reel-chapter-'+(1+Math.floor(t/4))+'.svg'),svg);await sharp(Buffer.from(svg)).png().toFile(path.join(R,'reel-qa-'+t+'.png'));}
const ffmpeg=process.env.FASHION_FFMPEG || 'ffmpeg';
const video=path.join(P,'forma-fashion-motion-12s.mp4');
const proc=spawn(ffmpeg,['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','png','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',video],{stdio:['pipe','ignore','pipe'],windowsHide:true});
let errors='';proc.stderr.on('data',b=>errors+=b.toString());
for(let f=0;f<288;f++){
 const png=await sharp(Buffer.from(reelFrame(f/24))).png({compressionLevel:1}).toBuffer();
 if(!proc.stdin.write(png))await once(proc.stdin,'drain');
 if(f%72===0)console.log(JSON.stringify({frames:f,total:288}));
}
proc.stdin.end();const [code]=await once(proc,'close');if(code!==0)throw new Error(errors||'FFmpeg '+code);
await sharp(Buffer.from(reelFrame(1))).resize({width:540}).png().toFile(path.join(P,'forma-motion-poster.png'));
await fs.mkdir(path.join(P,'originals'),{recursive:true});for(const p of photos)await fs.writeFile(path.join(P,'originals',p.name),p.bytes);
await fs.copyFile(path.join(R,'build-fashion.mjs'),path.join(P,'build-fashion-source.mjs'));
await fs.writeFile(path.join(R,'fashion-render-manifest.json'),JSON.stringify({status:'PREPARED_OWN_FICTIONAL_DEMONSTRATION',brand:'FORMA - fictional concept',image_method:'Built-in image_gen; images embedded unchanged and proportionally scaled as separate SVG layers',photos:photos.map(({name,sha256,width,height})=>({name,sha256,width,height})),posts:posts.map(({name,title})=>({name,title,width:1080,height:1350})),video:{file:path.basename(video),width:1080,height:1920,fps:24,duration_seconds:12,frames:288,audio:false,technique:'2D image-layer translation, native vector typography entrance and animated progress; no generated human motion or real shoot'},published_by_this_agent:false},null,2));
console.log(JSON.stringify({posts:3,video:12,publishable:P}));
