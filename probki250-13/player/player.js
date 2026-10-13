(async function(){
 'use strict';
 const ui=id=>document.getElementById(id);
 const catalog=await fetch('catalog.json').then(r=>r.json());
 const token=new URLSearchParams(location.hash.slice(1)).get('token');
 const isLocal=['127.0.0.1','localhost'].includes(location.hostname);
 let backend=Boolean(token&&isLocal),profile=catalog.profiles[0].id;
 let ctx,gain,buffers=new Map(),deck=[],last=null,queuedEnd=null,running=false,paused=false,busy=false;
 let nodes=new Set(),scheduled=[],heard=0,cycles=0,underruns=0,heartbeat,generation=0;
 const existing=localStorage.getItem('ownPlayerDevice');
 const device=existing||crypto.randomUUID();localStorage.setItem('ownPlayerDevice',device);
 async function api(route,payload){
   const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,device,...payload})});
   const result=await response.json();if(!response.ok)throw new Error(result.error||'Dostęp nieaktywny');return result;
 }
 function status(text){ui('status').textContent=text;}
 function diagnostic(){const cycleInfo=backend?'kolejność cykli: zarządzana przez backend':`cykle: ${cycles}`;ui('technical').textContent=`Web Audio: ${ctx?.state||'nieutworzony'} · rozpoczęte próbki: ${heard} · ${cycleInfo} · wykryte opóźnienia kolejki: ${underruns}`;}
 async function next(){
   if(backend){const track=await api('/api/next',{profile});return track.track;}
   if(!deck.length){deck=PlayerScheduling.shuffleCycle(catalog.tracks.map(t=>t.id),last);cycles++;}
   const id=deck.shift();last=id;return id;
 }
 function clearAudio(){
   generation++;
   for(const source of nodes){try{source.stop();}catch{}}nodes.clear();scheduled=[];queuedEnd=null;
   ui('visualizer').classList.remove('playing');
 }
 async function stop(release=true){
   running=false;paused=false;clearAudio();clearInterval(heartbeat);heartbeat=null;
   if(ctx&&ctx.state==='running'){try{await ctx.suspend();}catch{}}
   if(backend&&release){try{const result=await api('/api/release',{});ui('security').textContent=result.released?'Lokalny backend: rezerwacja urządzenia zwolniona.':'Lokalny backend: brak potwierdzenia zwolnienia rezerwacji.';}catch{ui('security').textContent='Lokalny backend: dostęp nieaktywny lub brak potwierdzenia zwolnienia; rezerwacja wygasa automatycznie.';}}
   ui('play').textContent='Odtwarzaj';ui('stop').disabled=true;ui('now-playing').textContent='Gotowy do odtwarzania';status('Odtwarzanie zatrzymane.');diagnostic();
 }
 async function schedule(){
   if(!running||paused||busy)return;busy=true;
   const scheduledGeneration=generation;
   try{
     while(running&&!paused&&(queuedEnd===null||queuedEnd-ctx.currentTime<1.2)){
       const id=await next(),buffer=buffers.get(id);
       if(!running||paused||generation!==scheduledGeneration)break;
       const plan=PlayerScheduling.planNext(queuedEnd,ctx.currentTime,buffer.duration);
       if(plan.underrun)underruns++;
       const source=ctx.createBufferSource();source.buffer=buffer;source.connect(gain);source.start(plan.start);nodes.add(source);
       source.onended=()=>nodes.delete(source);scheduled.push({id,start:plan.start,end:plan.end,announced:false});queuedEnd=plan.end;
     }
   }catch(error){await stop();status(error.message);ui('security').textContent='Dostęp nieaktywny: odtwarzanie przerwane.';}
   finally{busy=false;diagnostic();}
 }
 async function loadBuffers(){
   const AudioClass=window.AudioContext||window.webkitAudioContext;
   if(!AudioClass)throw new Error('Przeglądarka nie obsługuje Web Audio.');
   ctx=new AudioClass();gain=ctx.createGain();gain.gain.value=Number(ui('volume').value);gain.connect(ctx.destination);
   if(backend){
     await api('/api/lease',{});ui('mode').textContent='Backend lokalny / prototyp';
     ui('security').textContent='Lokalny backend: podpisany link i aktywna rezerwacja urządzenia. Płatności są symulacją.';
     const allocations=[];
     for(let i=0;i<catalog.tracks.length;i++)allocations.push(await api('/api/next',{profile}));
     for(const item of allocations){const response=await fetch(item.url);if(!response.ok)throw new Error('Dostęp do próbki nieaktywny.');buffers.set(item.track,await ctx.decodeAudioData(await response.arrayBuffer()));}
     // The first complete cycle was allocated for secure source loading. Playback has its next independent complete cycle.
     await api('/api/release',{});
     ui('security').textContent='Lokalny backend: podpisany link, rezerwacja zwolniona po przygotowaniu próbek. Play przyzna ją ponownie.';
   }else{
     for(const track of catalog.tracks){const response=await fetch(track.file);if(!response.ok)throw new Error('Nie udało się pobrać próbki.');buffers.set(track.id,await ctx.decodeAudioData(await response.arrayBuffer()));}
   }
 }
 for(const item of catalog.profiles){
   const button=document.createElement('button');button.textContent=item.name;button.setAttribute('aria-pressed',String(item.id===profile));
   const hint=document.createElement('small');hint.textContent='Własne syntetyczne próbki';button.append(hint);
   button.addEventListener('click',async()=>{
     const active=running;if(active)await stop();profile=item.id;deck=[];last=null;cycles=0;
     for(const child of ui('profiles').children)child.setAttribute('aria-pressed',String(child===button));
     ui('selected').textContent='Profil: '+item.name;if(active)await begin();
   });ui('profiles').append(button);
 }
 async function begin(){
   try{
     await ctx.resume();
     if(paused){paused=false;running=true;ui('play').textContent='Pauza';ui('visualizer').classList.add('playing');status('Odtwarzanie wznowione.');diagnostic();return;}
     if(backend){await api('/api/lease',{});const heartbeatGeneration=generation;ui('security').textContent='Lokalny backend: rezerwacja urządzenia aktywna.';heartbeat=setInterval(async()=>{try{await api('/api/heartbeat',{});if(running&&generation===heartbeatGeneration)ui('security').textContent='Lokalny backend: urządzenie aktywne, heartbeat potwierdzony.';}catch(error){if(running&&generation===heartbeatGeneration){await stop(false);status(error.message);ui('security').textContent='Link cofnięty, wygasł lub rezerwacja nieaktywna.';}}},10000);}
     running=true;ui('play').textContent='Pauza';ui('stop').disabled=false;ui('visualizer').classList.add('playing');status('Odtwarzanie własnych próbek.');await schedule();
   }catch(error){status(error.message);}
 }
 ui('play').addEventListener('click',async()=>{
   if(running&&!paused){paused=true;await ctx.suspend();ui('play').textContent='Wznów';ui('visualizer').classList.remove('playing');status('Pauza.');diagnostic();}
   else await begin();
 });
 ui('stop').addEventListener('click',()=>stop());
 ui('volume').addEventListener('input',()=>{if(gain)gain.gain.setValueAtTime(Number(ui('volume').value),ctx.currentTime);});
 setInterval(()=>{
   if(running&&!paused&&ctx){
     for(const item of scheduled)if(!item.announced&&ctx.currentTime>=item.start){item.announced=true;heard++;ui('now-playing').textContent=catalog.tracks.find(t=>t.id===item.id).name;diagnostic();}
     scheduled=scheduled.filter(item=>item.end>ctx.currentTime-.1);schedule();
   }
 },100);
 try{await loadBuffers();ui('play').disabled=false;ui('play').textContent='Odtwarzaj';status('Próbki gotowe. Kliknięcie uruchomi dźwięk.');diagnostic();}
 catch(error){status(error.message);ui('play').textContent='Brak aktywnego dostępu';}
})();
