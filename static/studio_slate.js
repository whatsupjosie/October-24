/* One shared floor slate per top-level PubCast screen. No synthetic director voice. */
(() => {
  'use strict';
  if (window !== window.top || window.PubCastSlate) return;
  const nativeFetch = window.ReachAuth?.nativeFetch || window.fetch.bind(window);
  let connecting=false;
  let snapshot = null, socket = null, timer, closed = false, pending = false;
  let offset = 0, bestRTT = Infinity, scheduled = '', clockUncertainty = Infinity;
  let context, micContext, micStream, micNode, micSource, muteSink, voiceUntil = 0;
  let takeRecorder=null, takeResult=null, takeBusy=false;
  let crewDirty=false;
  let listening = false, microphone = false, micStarting = false, dirty = false;
  const root = document.createElement('section');
  root.id = 'pubcast-slate-floor'; root.hidden = true; root.setAttribute('aria-label','Production slate and roll call');
  root.innerHTML = `<div class="slate-wrap"><h1>Production floor · <span data-phase>standby</span></h1>
    <p>The director is calling departments. Check in at your assigned station.</p>
    <div class="clacker" aria-label="Raised clacker"></div><div class="board"><div class="fields"></div><div class="roll"></div></div>
    <p class="status" role="status"></p><div data-take-result role="status"></div><p class="sync">Clock measuring · recorded audio/video alignment unverified</p>
    <div class="actions"><button data-action="listen">Enable director audio</button><button data-action="mic" hidden>Start director microphone</button>
    <button data-action="record-take" hidden>Arm stage take recorder</button><button data-action="save" hidden>Save slate</button><button data-action="standby" hidden>Call stations / roll call</button>
    <button data-action="clap" hidden>Clap / begin take</button><button data-action="hide" hidden>Dismiss on every screen</button>
    <button data-action="close">Close my editor</button></div>
    <details data-editor hidden><summary>Departments and assistant permissions</summary>
    <label>Departments: one “department = account ID” per line<textarea data-departments></textarea></label><button data-action="departments">Assign departments</button>
    <label>Assistant account IDs, one per line<textarea data-editors></textarea></label><button data-action="delegate">Grant / revoke editing</button></details>
    <details data-editor hidden><summary>AI crew for this production only</summary><p>These assignments stay in this session. AI execution is not enabled by saving them.</p>
    <div class="crew-brain" aria-label="Session AI crew reference"></div><div data-crew></div><button data-action="add-crew">Add crew assignment</button><button data-action="crew">Save crew assignments</button></details>
    <button data-action="end" hidden>End production</button></div>`;
  const launcher = document.createElement('button'); launcher.id='pubcast-slate-open'; launcher.textContent='Production slate'; launcher.hidden=true;
  const stopTake=document.createElement('button');stopTake.id='pubcast-stop-take';stopTake.textContent='Stop take / save';stopTake.hidden=true;
  stopTake.style.cssText='position:fixed;left:14px;bottom:14px;z-index:2147483001;background:#a32d28;color:white;padding:14px;border:0;border-radius:6px';
  stopTake.onclick=()=>takeRecorder?.stop();
  document.body.append(root, launcher, stopTake);
  const $ = s => root.querySelector(s);
  const status = message => $('.status').textContent = message;
  const fields = {};
  for (const name of ['production','scene','take','actors','notes']) {
    const label=document.createElement('label'); label.textContent=name[0].toUpperCase()+name.slice(1);
    const input=document.createElement(name==='notes'?'textarea':'input'); input.name=name;
    input.addEventListener('input',()=>{dirty=true;}); label.append(input); $('.fields').append(label); fields[name]=input;
  }
  function token() { try{return sessionStorage.getItem('pubcast_token')||'';}catch(_){return '';}}
  async function request(method='GET', body) {
    const headers={'Content-Type':'application/json'}; if(token())headers.Authorization='Bearer '+token();
    const response=await nativeFetch('/api/studio/slate',{method,headers,body:body?JSON.stringify(body):undefined});
    if(!response.ok) { let d;try{d=await response.json();}catch(_){} throw Error(d?.detail||'Slate HTTP '+response.status); }
    return response.json();
  }
  function addCrew(item={label:'',role:'camera operator',profile:'',instructions:'',flight_pattern:'',enabled:false}){
    const row=document.createElement('fieldset');row.className='crew-entry';
    for(const [key,title]of [['label','Crew name'],['role','Department / job'],['profile','Configured AI profile'],['instructions','Instructions for this scene'],['flight_pattern','Flight path / movement instructions']]){
      const label=document.createElement('label');label.textContent=title;
      const input=document.createElement(['instructions','flight_pattern'].includes(key)?'textarea':'input');input.dataset.crewField=key;input.value=item[key]||'';input.oninput=()=>{crewDirty=true;};label.append(input);row.append(label);
    }
    const label=document.createElement('label'),enabled=document.createElement('input');enabled.type='checkbox';enabled.dataset.crewField='enabled';enabled.checked=!!item.enabled;enabled.onchange=()=>crewDirty=true;label.append(enabled,document.createTextNode('Enabled for this session'));row.append(label);
    const remove=document.createElement('button');remove.type='button';remove.textContent='Remove assignment';remove.onclick=()=>{row.remove();crewDirty=true;};row.append(remove);$('[data-crew]').append(row);
  }
  async function command(action,data={}) {
    if(pending)return;
    pending=true;
    try{snapshot=await request('POST',{action,data,revision:snapshot?.slate?.revision??null});dirty=false;if(action==='crew')crewDirty=false;render();status('Saved / delivered to production screens');}
    catch(error){status(error.message);await refresh();}
    finally{pending=false;}
  }
  function render() {
    if(!snapshot)return;
    const s=snapshot.slate, editor=snapshot.can_edit, director=snapshot.is_director;
    launcher.hidden=false;
    if(!s||s.phase==='ended'){if(takeRecorder?.active)takeRecorder.stop();root.hidden=true;launcher.textContent='Open production slate';stopMic();return;}
    launcher.textContent='Production slate · '+s.phase;
    if(s.visible)root.hidden=false;
    else if(root.dataset.forced!=='yes')root.hidden=true;
    $('[data-phase]').textContent=s.phase==='standby'?'STATIONS / ROLL CALL':s.phase.toUpperCase();
    for(const [name,input]of Object.entries(fields)){input.readOnly=!editor;if(!dirty)input.value=s.fields[name]||'';}
    for(const a of ['save','standby','clap','hide','record-take'])$(`[data-action="${a}"]`).hidden=!editor;
    for(const a of ['mic','delegate','end'])$(`[data-action="${a}"]`).hidden=!director;
    root.querySelectorAll('[data-editor]').forEach(e=>e.hidden=!editor);
    $('[data-action="clap"]').disabled=s.phase!=='standby'||Object.values(s.departments).some(e=>!e.ready);
    $('[data-editors]').readOnly=!director;
    if(!root.contains(document.activeElement)||!['TEXTAREA','INPUT'].includes(document.activeElement.tagName)){
      $('[data-departments]').value=Object.entries(s.departments).map(([d,e])=>d+' = '+e.user_id).join('\n');
      $('[data-editors]').value=s.editors.join('\n');if(!crewDirty){$('[data-crew]').replaceChildren();s.crew.forEach(addCrew);crewDirty=false;}
    }
    $('.roll').replaceChildren();
    for(const [department,e]of Object.entries(s.departments)){
      const row=document.createElement('div');row.className='roll-row';row.textContent=`${department} · ${e.user_id} · ${e.ready?'READY':'awaiting check-in'}`;
      if(e.user_id===snapshot.user_id&&s.phase==='standby'){const b=document.createElement('button');b.textContent=e.ready?'Not ready':'At station / ready';b.onclick=()=>command('ready',{department,ready:!e.ready});row.append(b);}
      $('.roll').append(row);
    }
    if(!editor&&takeRecorder?.active)takeRecorder.stop();
    if(!director)stopMic();
    if(s.phase==='ended'||!s.visible)stopMic();
    const clacker=$('.clacker');clacker.classList.toggle('closed',s.phase==='take'&&Date.now()/1000+offset>=s.clap_at);
    clacker.setAttribute('aria-label',clacker.classList.contains('closed')?'Closed clacker':'Raised clacker');
    if(s.clap_at&&scheduled!==String(s.clap_at))scheduleClap(s.clap_at);
    if(!s.clap_at){scheduled='';clearTimeout(timer);}
    $('.sync').textContent=`Clock uncertainty approximately ${Number.isFinite(clockUncertainty)?Math.round(clockUncertainty*1000)+' ms':'unmeasured'} · `+(takeResult?.slate_id===s.id&&takeResult.status==='verified_recorded_cue'?`Latest saved take cue verified: ${takeResult.after.audio_minus_video_ms} ms residual.`:'Recorded take awaits encoded-file verification.');
  }
  function scheduleClap(at){
    scheduled=String(at);clearTimeout(timer);
    const delay=at-Date.now()/1000-offset;
    // A late join sees the closed board; never replays an old synchronization cue.
    if(delay<=0){$('.clacker').classList.add('closed');return;}
    timer=setTimeout(()=>{$('.clacker').classList.add('closed');$('.clacker').setAttribute('aria-label','Closed clacker');},delay*1000);
    if((listening||takeRecorder?.active)&&context?.state==='running'){
      const oscillator=context.createOscillator(),gain=context.createGain(),start=context.currentTime+delay;
      oscillator.frequency.value=1500;gain.gain.setValueAtTime(.3,start);gain.gain.exponentialRampToValueAtTime(.001,start+.025);
      oscillator.connect(gain);if(listening)gain.connect(context.destination);
      if(takeRecorder?.active){takeRecorder.markClap(start);gain.connect(takeRecorder.destination);}
      oscillator.start(start);oscillator.stop(start+.03);
    }
  }
  async function refresh(){
    if(!token())return;
    const t0=Date.now()/1000;
    try{const data=await request();const t1=Date.now()/1000,rtt=t1-t0;
      if(rtt<bestRTT){bestRTT=rtt;offset=data.server_time-(t0+t1)/2;clockUncertainty=rtt/2;}
      if(!snapshot||data.slate?.revision!==snapshot.slate?.revision||!snapshot.slate){snapshot=data;render();}
      connect();
    }catch(error){if(snapshot?.slate?.visible)status('Connection lost. Last known slate shown; readiness and voice are not confirmed.');}
  }
  async function connect(){
    if(socket||closed||connecting)return;
    connecting=true;
    try{
    // Session imports can have a bearer without the HttpOnly socket cookie.
    // Verify through Reach before opening the browser's cookie-authenticated socket.
    const verified=await nativeFetch('/api/auth/verify',{headers:{Authorization:'Bearer '+token()}});
    if(!verified.ok)throw Error('Sign in again to join floor voice');
    if(closed)return;
    const url=new URL('/studio/slate/live',location.href);url.protocol=location.protocol==='https:'?'wss:':'ws:';
    socket=new WebSocket(url);
    socket.onmessage=e=>{let p;try{p=JSON.parse(e.data);}catch(_){return;}
      if(p.type==='slate_changed')refresh();
      if(p.type==='director_voice'&&listening&&context?.state==='running'&&p.slate_id===snapshot?.slate?.id){
        const buffer=context.createBuffer(1,p.samples.length,16000);buffer.copyToChannel(Float32Array.from(p.samples),0);
        const source=context.createBufferSource();source.buffer=buffer;source.connect(context.destination);
        if(voiceUntil>context.currentTime+.5)voiceUntil=context.currentTime;
        const at=Math.max(context.currentTime+.025,voiceUntil);source.start(at);voiceUntil=at+buffer.duration;
      }
    };
    socket.onclose=()=>{socket=null;stopMic();};socket.onerror=()=>status('Floor voice connection unavailable');
    }catch(error){status(error.message);}finally{connecting=false;}
  }
  async function enableAudio(){context ||= new AudioContext();await context.resume();listening=true;$('[data-action="listen"]').textContent='Director audio enabled';}
  async function startMic(){
    if(!snapshot?.is_director||!snapshot.slate.visible)throw Error('Call stations before opening the floor microphone');
    if(socket?.readyState!==WebSocket.OPEN)throw Error('Floor voice connection unavailable');
    // Browser permission is requested only from this explicit director button.
    if(!navigator.mediaDevices?.getUserMedia)throw Error('Microphone access needs HTTPS or localhost in this browser');
    micStream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true},video:false});
    if(!snapshot?.is_director||!snapshot.slate.visible||closed){stopMic();return;}
    micContext=new AudioContext({sampleRate:16000});await micContext.resume();
    if(micContext.sampleRate!==16000){stopMic();throw Error('This browser does not support the required 16 kHz microphone context');}
    micSource=micContext.createMediaStreamSource(micStream);micNode=micContext.createScriptProcessor(1024,1,1);
    muteSink=micContext.createGain();muteSink.gain.value=0;micSource.connect(micNode);micNode.connect(muteSink).connect(micContext.destination);
    micNode.onaudioprocess=e=>{if(socket?.readyState===WebSocket.OPEN&&socket.bufferedAmount<64000)socket.send(JSON.stringify({samples:Array.from(e.inputBuffer.getChannelData(0),v=>Math.round(Math.max(-1,Math.min(1,v))*10000)/10000)}));};
    takeRecorder?.attachMicrophone(micStream);
    microphone=true;$('[data-action="mic"]').textContent='Stop director microphone';status('Director microphone LIVE to listeners who enabled audio');
  }
  function stopMic(){takeRecorder?.attachMicrophone(null);micNode?.disconnect();micSource?.disconnect();muteSink?.disconnect();micStream?.getTracks().forEach(t=>t.stop());micContext?.close().catch(()=>{});micContext=null;micStream=null;micNode=null;micSource=null;muteSink=null;microphone=false;$('[data-action="mic"]').textContent='Start director microphone';}
  function findStage(win=window){
    if(win.PubCastStageCamera&&win.document.querySelector('canvas'))return win;
    for(const frame of win.document.querySelectorAll('iframe')){try{const found=findStage(frame.contentWindow);if(found)return found;}catch(_){}}
    return null;
  }
  function localDownload(blob,name){
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.textContent='Save '+name;
    $('[data-take-result]').append(a);a.click();setTimeout(()=>{a.remove();URL.revokeObjectURL(url);},300000);
  }
  async function saveTake(blob,slateId,timing,sourceRecorder){
    stopTake.hidden=true;takeBusy=true;root.dataset.forced='yes';root.hidden=false;
    const result=$('[data-take-result]');result.textContent='Original recorded locally. Measuring encoded clap timing… ';
    localDownload(blob,'PubCast-take-'+Date.now()+'.webm');
    try{
      const response=await nativeFetch('/api/studio/slate/takes/'+encodeURIComponent(slateId),{method:'POST',headers:{Authorization:'Bearer '+token(),'Content-Type':blob.type},body:blob});
      if(!response.ok)throw Error('Take upload HTTP '+response.status);
      takeResult=await response.json();
      const markers=await nativeFetch('/api/studio/slate/takes/'+encodeURIComponent(slateId)+'/'+takeResult.take_id+'/timing',{method:'POST',headers:{Authorization:'Bearer '+token(),'Content-Type':'application/json'},body:JSON.stringify({...timing,original_sha256:takeResult.original_sha256})});
      if(!markers.ok)throw Error('Video preserved; timing-marker save HTTP '+markers.status);
      const markerResult=await markers.json();
      for(const [label,url,extension]of [['Save edit copy · separate sync track',markerResult.editing_url,'-editing.mp4'],['Save Sync Reference audio',markerResult.reference_url,'-sync-reference.wav']]){
        if(!url)continue;const b=document.createElement('button');b.disabled=true;b.textContent=label;b.onclick=async()=>{try{const r=await nativeFetch(url,{headers:{Authorization:'Bearer '+token()}});if(!r.ok)throw Error('Download HTTP '+r.status);localDownload(await r.blob(),takeResult.take_id+extension);}catch(e){status(e.message);}};result.append(b);
      }
      if(markerResult.reference_track_error){const warning=document.createElement('p');warning.textContent='Clean aligned take saved; separate reference track unavailable: '+markerResult.reference_track_error;result.append(warning);}
      const saveMarkers=document.createElement('button');saveMarkers.textContent='Save silent edit markers';saveMarkers.onclick=()=>localDownload(new Blob([JSON.stringify(timing,null,2)],{type:'application/json'}),takeResult.take_id+'-timing.json');result.append(saveMarkers);
      for(let i=0;i<sourceRecorder.stemNames.length;i++){
        const name=sourceRecorder.stemNames[i];status('Saving separate audio track: '+name);
        const saved=await nativeFetch('/api/studio/slate/takes/'+slateId+'/'+takeResult.take_id+'/stem/'+name,{method:'POST',headers:{Authorization:'Bearer '+token(),'Content-Type':'audio/wav'},body:sourceRecorder.stemBlob(i)});
        if(!saved.ok)throw Error('Stem '+name+' save HTTP '+saved.status);
      }
      const stemResponse=await nativeFetch('/api/studio/slate/takes/'+slateId+'/'+takeResult.take_id+'/stems',{method:'POST',headers:{Authorization:'Bearer '+token()}});
      if(!stemResponse.ok)throw Error('Audio stem alignment HTTP '+stemResponse.status);
      const stemReport=await stemResponse.json();sourceRecorder.stemBlocks=[];result.querySelectorAll('button').forEach(b=>b.disabled=false);
      for(const stem of stemReport.tracks){const b=document.createElement('button');b.textContent='Save '+(stem.name==='dialogue'?'Vocals / Dialogue':stem.name)+' track';b.onclick=async()=>{try{const r=await nativeFetch(stem.url,{headers:{Authorization:'Bearer '+token()}});if(!r.ok)throw Error('Download HTTP '+r.status);localDownload(await r.blob(),takeResult.take_id+'-'+stem.name+'.wav');}catch(e){status(e.message);}};result.append(b);}
      const timeline=document.createElement('a');timeline.href='/static/take_editor.html?slate='+slateId+'&take='+takeResult.take_id;timeline.textContent='Open take timeline';timeline.target='_self';result.append(timeline);
      const message=document.createElement('p');message.textContent=takeResult.status==='verified_recorded_cue'?
        `Recorded cue verified: ${takeResult.after.audio_minus_video_ms} ms residual (tolerance ${takeResult.after.tolerance_ms} ms).`:
        'Original preserved. Sync not verified: '+takeResult.reason;
      result.append(message);
      for(const [label,url]of [['Save aligned take',takeResult.aligned_url],['Save sync report',takeResult.original_url?.replace(/original$/,'report')]]){
        if(!url)continue;const b=document.createElement('button');b.textContent=label;b.onclick=async()=>{try{const r=await nativeFetch(url,{headers:{Authorization:'Bearer '+token()}});if(!r.ok)throw Error('Download HTTP '+r.status);localDownload(await r.blob(),takeResult.take_id+(label.includes('report')?'-sync.json':'-aligned.mp4'));}catch(e){status(e.message);}};result.append(b);
      }
    }catch(error){const p=document.createElement('p');p.textContent=error.message+' · local recovery files remain available.';result.append(p);
      for(let i=0;i<sourceRecorder.stemNames.length;i++){const b=document.createElement('button');b.textContent='Save local '+sourceRecorder.stemNames[i]+' track';b.onclick=()=>localDownload(sourceRecorder.stemBlob(i),'PubCast-local-'+sourceRecorder.stemNames[i]+'.wav');result.append(b);}
    }
    finally{takeBusy=false;takeRecorder=null;render();}
  }
  async function armTake(){
    if(takeBusy||takeRecorder?.active)throw Error('A take is already recording or being saved');
    if(!snapshot?.can_edit)throw Error('Director or delegated assistant required');
    if(snapshot.slate.phase!=='standby')throw Error('Call stations before arming a take');
    const stage=findStage();if(!stage)throw Error('Open the director console or a 3D stage to record real stage pixels');
    context ||= new AudioContext();await context.resume();
    takeBusy=true;
    try{
      if(!window.PubCastTakeRecorder)await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/static/studio_take_recorder.js';script.onload=resolve;script.onerror=()=>reject(Error('Take recorder could not load'));document.head.append(script);});
      const slateId=snapshot.slate.id;
      takeRecorder=new window.PubCastTakeRecorder({canvas:stage.document.querySelector('canvas'),audioContext:context,programRuntime:stage.PubcastProgramAudio,microphone:micStream,getSlate:()=>snapshot});
      await takeRecorder.start();stopTake.hidden=false;takeBusy=false;
      takeRecorder.finished.then(blob=>saveTake(blob,slateId,takeRecorder.timing(),takeRecorder)).catch(error=>{status(error.message);stopTake.hidden=true;takeRecorder=null;takeBusy=false;});
      status('Recording actual stage + program audio. Clap once within two minutes, then dismiss the slate and film the take.');
    }catch(error){takeRecorder?.release();takeRecorder=null;takeBusy=false;throw error;}
  }
  launcher.onclick=async()=>{if(!snapshot?.slate||snapshot.slate.phase==='ended'){await command('create');}root.dataset.forced='yes';root.hidden=false;};
  root.addEventListener('click',async e=>{
    const action=e.target.closest('[data-action]')?.dataset.action;if(!action)return;
    try{
      if(action==='record-take')return await armTake();
      if(action==='listen')return await enableAudio();
      if(action==='mic'){if(micStarting)return;micStarting=true;try{return microphone?stopMic():await startMic();}catch(error){stopMic();throw error;}finally{micStarting=false;}}
      if(action==='close'){if(snapshot.slate.visible)return status('The shared board stays on screen until the director dismisses it.');root.dataset.forced='';root.hidden=true;return;}
      if(action==='save')return await command('edit',{fields:Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.value]))});
      if(action==='departments'){const entries={};for(const line of $('[data-departments]').value.split('\n').filter(v=>v.trim())){const i=line.indexOf('=');if(i<1)throw Error('Use department = account ID');entries[line.slice(0,i).trim()]=line.slice(i+1).trim();}return await command(action,{departments:entries});}
      if(action==='delegate')return await command(action,{editors:$('[data-editors]').value.split('\n').map(v=>v.trim()).filter(Boolean)});
      if(action==='add-crew'){addCrew();crewDirty=true;return;}
      if(action==='crew')return await command(action,{crew:Array.from(root.querySelectorAll('.crew-entry'),row=>Object.fromEntries(Array.from(row.querySelectorAll('[data-crew-field]'),e=>[e.dataset.crewField,e.type==='checkbox'?e.checked:e.value])))});
      if(action==='end'&&!confirm('End this production and release the shared floor?'))return;
      if(dirty&&['standby','clap'].includes(action))throw Error('Save the slate fields first');
      root.dataset.forced='';await command(action);
    }catch(error){status(error.message);}
  });
  window.addEventListener('pagehide',()=>{closed=true;takeRecorder?.stop();stopMic();socket?.close();context?.close();clearTimeout(timer);});
  window.PubCastSlate={refresh,open:()=>launcher.click(),getTiming:()=>takeRecorder?.timing(),getTakeResult:()=>takeResult};
  async function poll(){if(closed)return;await refresh();if(!closed)setTimeout(poll,1500);}poll();
})();
