(() => {
 'use strict';const client=window.PubCastControlRoom.client,$=id=>document.getElementById('mini-'+id),camera=$('camera'),mode=$('mode');
 let sources='', busy=false, axes=null, interval=null;
 const say=s=>$('status').textContent=s;
 const selected=()=>client.state?.cameras.find(c=>c.source_id===camera.value);
 function preview(){const c=selected();$('screen').hidden=!c||!['virtual','voxel_3d'].includes(c.transport);if(!$('screen').hidden)$('screen').src='/static/stage_3d.html?camera_id='+encodeURIComponent(c.source_id);}
 camera.onchange=()=>{stop();preview();};mode.onchange=()=>stop();
 client.addEventListener('state',e=>{const s=e.detail,signature=JSON.stringify(s.cameras.map(c=>[c.source_id,c.name,c.transport]));if(signature!==sources){const value=camera.value;camera.replaceChildren();for(const c of s.cameras){const o=document.createElement('option');o.value=c.source_id;o.textContent=c.name;camera.append(o);}camera.value=s.cameras.some(c=>c.source_id===value)?value:(s.preview||s.program);sources=signature;preview();}});
 async function nudge(x,y,z=0){if(busy)return;busy=true;try{if(!['virtual','voxel_3d'].includes(selected()?.transport))throw Error('No motion driver connected for this camera');const r=await client.command('camera.nudge',{source_id:camera.value,mode:mode.value,x,y,z});say('Camera pose confirmed · '+JSON.stringify(r.result));}catch(e){stop();say(e.message);}finally{busy=false;}}
 function stop(){axes=null;clearInterval(interval);interval=null;$('stick').style.transform='';}
 function start(x,y){axes=[x,y];if(!interval){nudge(...axes);interval=setInterval(()=>{if(axes)nudge(...axes);},150);}}
 const stick=$('stick');stick.addEventListener('pointerdown',e=>{e.preventDefault();stick.setPointerCapture(e.pointerId);move(e);});
 function move(e){if(!stick.hasPointerCapture(e.pointerId))return;const r=stick.getBoundingClientRect(),x=Math.max(-1,Math.min(1,(e.clientX-r.left-r.width/2)/(r.width/2))),y=Math.max(-1,Math.min(1,(e.clientY-r.top-r.height/2)/(r.height/2)));start(x,y);}
 stick.addEventListener('pointermove',move);for(const name of ['pointerup','pointercancel','lostpointercapture','blur'])stick.addEventListener(name,stop);
 stick.addEventListener('keydown',e=>{const a={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];if(a){e.preventDefault();start(...a);}});stick.addEventListener('keyup',stop);
 for(const [id,z]of [['up',1],['down',-1]])$(id).onclick=()=>mode.value==='truck'?nudge(0,0,z):say('Select Move mode to lift or lower');
 async function action(id,payload){try{await client.command(id,payload);say('Confirmed: '+id);}catch(e){say(e.message);}}
 $('preview').onclick=()=>action('camera.switch.preview',{source_id:camera.value});$('cut').onclick=()=>action('camera.cut',{});$('auto').onclick=()=>{const host=window.top;host.PubCastSlate?.open();};
 window.addEventListener('pagehide',stop);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
})();
