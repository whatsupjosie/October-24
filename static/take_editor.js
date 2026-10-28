(async()=>{
 'use strict';const $=id=>document.getElementById(id),video=$('video'),params=new URLSearchParams(location.search),slate=params.get('slate'),take=params.get('take');
 const prefix='/api/studio/slate/takes/'+encodeURIComponent(slate)+'/'+encodeURIComponent(take)+'/';
 let manifest,context,objects=[],nodes=[],buffers=new Map(),selected=new Set(['dialogue','music','sfx','ui','vtr','room','floor']),edits={},playing=false,segment=-1,urls=[];
 const labels={dialogue:'Vocals / Dialogue',music:'Music',sfx:'Sound Effects',floor:'Director / floor',reference:'Sync Reference',ui:'UI',vtr:'VTR',room:'Room'};
 const say=s=>$('status').textContent=s;
 async function get(suffix){const r=await fetch(prefix+suffix);if(!r.ok)throw Error('Take HTTP '+r.status);return r;}
 function section(){return Math.max(0,Math.floor((video.currentTime-(manifest?.timeline_origin_seconds||0))/15));}
 function offset(name){return Number(edits[section()]?.[name]||0);}
 function stop(){nodes.forEach(n=>{try{n.stop();}catch(_){}});nodes=[];playing=false;}
 async function load(name){if(buffers.has(name))return buffers.get(name);const response=await get('stem-'+name),buffer=await context.decodeAudioData(await response.arrayBuffer());buffers.set(name,buffer);return buffer;}
 async function start(){
  stop();context ||= new AudioContext();await context.resume();const names=[...selected];await Promise.all(names.map(load));
  await video.play();const at=context.currentTime+.03;segment=section();
  for(const name of names){const buffer=buffers.get(name),position=video.currentTime-manifest.audio_to_video_offset_seconds-offset(name);if(position>=buffer.duration)continue;const node=context.createBufferSource();node.buffer=buffer;node.connect(context.destination);node.start(at+Math.max(0,-position),Math.max(0,position));nodes.push(node);}
  playing=true;say('Playing selected tracks · section '+(segment+1));
 }
 function rows(){
  $('section').textContent='Section '+(section()+1)+' · '+(section()*15)+'–'+((section()+1)*15)+' seconds';$('tracks').replaceChildren();
  for(const track of manifest.tracks){const row=document.createElement('div');row.className='track';const check=document.createElement('input');check.type='checkbox';check.checked=selected.has(track.name);check.setAttribute('aria-label','Enable '+labels[track.name]);check.onchange=()=>{if(check.checked)selected.add(track.name);else selected.delete(track.name);if(playing)start().catch(e=>say(e.message));};const title=document.createElement('strong');title.textContent=labels[track.name];row.append(check,title);
   for(const [label,delta]of [['−5 ms',-.005],['+5 ms',.005]]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{edits[section()] ||= {};edits[section()][track.name]=Math.max(-2,Math.min(2,offset(track.name)+delta));rows();if(playing)start().catch(e=>say(e.message));};row.append(b);}
   const value=document.createElement('span');value.textContent=(offset(track.name)*1000).toFixed(0)+' ms';row.append(value);$('tracks').append(row);
  }
 }
 function timeline(){
  const lanes=$('lanes');lanes.replaceChildren();for(const name of ['Video',...manifest.tracks.map(t=>labels[t.name])]){const row=document.createElement('div');row.className='lane';row.textContent=name;lanes.append(row);}
  const duration=video.duration;if(!Number.isFinite(duration)||duration<=0)return;
  for(let at=manifest.timeline_origin_seconds||0;at<=duration;at+=15){const tick=document.createElement('div');tick.className='tick';tick.style.left=(at/duration*100)+'%';const label=document.createElement('span');const target=Math.round((at-(manifest.timeline_origin_seconds||0))/15)*15;label.textContent=String(Math.floor(target/60)).padStart(2,'0')+':'+String(target%60).padStart(2,'0');tick.append(label);lanes.append(tick);}
 }
 $('play').onclick=()=>start().catch(e=>say(e.message));video.onpause=stop;video.onseeking=stop;video.onseeked=rows;video.onloadedmetadata=timeline;
 video.ontimeupdate=()=>{const s=section();if(s!==segment){segment=s;rows();if(playing)start().catch(e=>say(e.message));}};
 $('previous').onclick=()=>{video.pause();video.currentTime=Math.max(0,(Math.ceil((video.currentTime-(manifest.timeline_origin_seconds||0))/15)-1)*15+(manifest.timeline_origin_seconds||0));rows();};$('next').onclick=()=>{video.pause();video.currentTime=Math.min(video.duration,(Math.floor((video.currentTime-(manifest?.timeline_origin_seconds||0))/15)+1)*15+(manifest.timeline_origin_seconds||0));rows();};
 async function saveEdits(){try{const r=await fetch(prefix+'edits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'pubcast.take-edits.v1',cadence_seconds:15,sections:edits,enabled_tracks:[...selected].filter(n=>n!=='reference')})});if(!r.ok)throw Error('Edit save HTTP '+r.status);say('Edit decisions saved. Original media preserved.');return true;}catch(e){say(e.message);return false;}}
 $('save').onclick=saveEdits;
 $('render').onclick=async()=>{if(!await saveEdits())return;const button=$('render');button.disabled=true;try{say('Rendering saved section offsets…');const r=await fetch(prefix+'render',{method:'POST'});if(!r.ok)throw Error('Render HTTP '+r.status);const result=await r.json();const file=await fetch(result.final_url);if(!file.ok)throw Error('Final download HTTP '+file.status);const url=URL.createObjectURL(await file.blob());urls.push(url);const a=document.createElement('a');a.href=url;a.download=take+'-final.mp4';a.click();say('Final take rendered. Sync Reference stays out of the program mix.');}catch(e){say(e.message);}finally{button.disabled=false;}};
 try{
  if(!slate||!take)throw Error('Open a saved take from the director’s slate');
  await ReachAuth.requireSession();manifest=await(await get('stems')).json();
  const response=await get('preview'),url=URL.createObjectURL(await response.blob());urls.push(url);video.src=url;
  try{edits=(await(await get('edits')).json()).sections||{};}catch(_){}
  rows();say('Ready · Sync Reference muted');
 }catch(e){say(e.message);}
 window.addEventListener('pagehide',()=>{stop();context?.close();urls.forEach(URL.revokeObjectURL);});
})();
