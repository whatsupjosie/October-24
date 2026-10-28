/* Shared, server-authoritative control room client and operator strip. */
(function (root) {
  'use strict';
  class ControlRoomClient extends EventTarget {
    constructor(adapter) {
      super();
      this.adapter = adapter || new root.PubCastStudioConsoleHotspots.StudioConsoleHotspots();
      this.state = null;
      this.pending = null;
      this.timer = null;
      this.closed = false;
      this.recordingBusy = false;
    }
    async refresh(force) {
      if (this.pending) {
        if (!force) return this.pending;
        await this.pending.catch(() => {});
      }
      const task = this.adapter._fetch('/api/studio/console-state', {method:'GET'});
      this.pending = task;
      try {
        const state = await task;
        if (!this.closed) {
          this.state = state;
          this.dispatchEvent(new CustomEvent('state', {detail:state}));
          root.dispatchEvent(new CustomEvent('pubcast:console-state', {detail:state}));
        }
        return state;
      } finally { if (this.pending === task) this.pending = null; }
    }
    async command(action, payload, context) {
      const recording = action.startsWith('recording.');
      if (recording && this.recordingBusy) throw Error('A recording command is already in progress');
      if (recording) this.recordingBusy = true;
      try {
        const result = await this.adapter.executeConfirmed(action, payload || {}, context || {});
        if (!result.canceled) await this.refresh(true);
        return result;
      } finally { if (recording) this.recordingBusy = false; }
    }
    async start() {
      if (root.ReachAuth && await root.ReachAuth.requireSession(location.pathname + location.search) === null) return;
      const poll = async () => {
        if (this.closed) return;
        try { await this.refresh(); }
        catch (error) { this.dispatchEvent(new CustomEvent('error', {detail:error})); }
        if (!this.closed) this.timer = setTimeout(poll, 1500);
      };
      await poll();
    }
    stop() { this.closed = true; clearTimeout(this.timer); }
  }
  function element(tag, label, attrs) {
    const node = document.createElement(tag);
    if (label !== undefined) node.textContent = label;
    for (const [key,value] of Object.entries(attrs || {})) node.setAttribute(key, value);
    return node;
  }
  const client = new ControlRoomClient();
  function mountPanel(mount) {
    const status = element('p', 'Connecting to the control room…', {role:'status','data-control-status':''});
    mount.append(status);
    const say = (text, error) => { status.textContent=text; status.dataset.level=error?'error':'ok'; };
    const act = async (action, payload, context) => {
      try {
        const result = await client.command(action, payload, context);
        if (result.canceled) { say('Canceled.'); return result; }
        if (action === 'recording.preflight') {
          const r=result.result;
          say(r.ready ? 'Recording checks passed.' : (r.issues || []).map(i=>i.message).join(' · '), !r.ready);
        } else say(result.delivery === 'queued_for_players' ? 'Sent to audio players.' : 'Confirmed by the host.');
        return result;
      } catch(error) { say(error.message+' · Refresh state before retrying an unconfirmed command.', true); return null; }
    };
    const readout=element('p','',{'data-control-readout':''});mount.append(readout);
    const switcher=element('div',undefined,{class:'pc-control-row'});
    const camera=element('select',undefined,{'aria-label':'Camera source'});
    switcher.append(camera);
    const button=(text,fn,parent=switcher)=>{const b=element('button',text,{type:'button'});b.onclick=fn;parent.append(b);return b;};
    button('Set preview',()=>act('camera.switch.preview',{source_id:camera.value}));
    button('Take selected',()=>act('camera.switch.program',{source_id:camera.value}));
    button('Cut program / preview',()=>act('camera.cut',{}));
    for (const [name,url] of [['Stage','/stage'],['Director','/director-console'],['Audio','/audio-console'],['Production tools','/static/control_room.html']]) {
      switcher.append(element('a',name,{href:url,target:'_blank',rel:'noopener'}));
    }
    mount.append(switcher);
    const rec=element('details');rec.open=mount.dataset.consoleKind!=='audio';
    rec.append(element('summary','Recording'));
    const row=element('div',undefined,{class:'pc-control-row'});
    const profile=element('select',undefined,{'aria-label':'Recording profile'});
    const session=element('select',undefined,{'aria-label':'Recording session'});
    row.append(profile,session);rec.append(row);
    const sources=()=>({sources:client.state?.program?[client.state.program]:[],profile_id:profile.value||'broadcast_mp4'});
    button('Check recording',()=>act('recording.preflight',sources()),row);
    const start=button('Start capture',async()=>{
      const pre=await act('recording.preflight',sources());
      if(!pre?.result.ready)return;
      await act('recording.start',{...sources(),countdown_seconds:0});
    },row);
    const stop=button('Stop capture',()=>act('recording.stop',{session_id:session.value}),row);
    const recInfo=element('p','No recording state yet.',{'data-recording-info':''});rec.append(recInfo);mount.append(rec);
    const mixer=element('details');mixer.open=mount.dataset.consoleKind==='audio';
    mixer.append(element('summary','Program audio'));
    const controls = new Map();
    for (const bus of ['dialogue','music','sfx','ui','vtr','room']) {
      const line=element('label',undefined,{class:'pc-control-row'});
      line.append(element('span',bus));
      const range=element('input',undefined,{type:'range',min:'0',max:'100','aria-label':bus+' volume'});
      range.onchange=()=>act('audio.event',{action:'set_volume',bus,volume:Number(range.value)/100});
      const mute=element('button','Mute',{type:'button','aria-label':'Mute '+bus});
      mute.onclick=()=>act('audio.event',{action:client.state?.audio.buses[bus].muted?'unmute':'mute',bus});
      line.append(range,mute);mixer.append(line);controls.set(bus,{range,mute});
    }
    const cue=element('div',undefined,{class:'pc-control-row'});
    const url=element('input',undefined,{type:'url',placeholder:'/static/audio/clip.ogg','aria-label':'Audio cue URL'});
    const bus=element('select',undefined,{'aria-label':'Audio cue bus'});
    ['music','dialogue','sfx','vtr','room','ui'].forEach(b=>bus.append(element('option',b,{value:b})));
    cue.append(url,bus);
    button('Send cue',()=>{
      try {
        const value=url.value.trim();if(!value)throw Error('Choose an audio cue URL first');
        const address=new URL(value,location.origin);
        if(!['http:','https:'].includes(address.protocol))throw Error('Use a host media path or an HTTP audio URL');
        return act('audio.event',{action:'play',bus:bus.value,url:address.href});
      }catch(error){say(error.message,true);}
    },cue);
    button('Stop all sounds',()=>act('audio.stop_all',{}),cue);
    mixer.append(cue);mixer.append(element('p','Players may need audio permission. Mixer settings are not microphone signal meters.'));mount.append(mixer);
    const emergency=element('button','Emergency stop',{type:'button'});
    emergency.onclick=async()=>{
      const ok=await client.adapter.confirmImpl({title:'Emergency stop',message:'Stop captures and program audio, and take production off air?',details:[],confirmText:'Stop',cancelText:'Cancel'});
      if(!ok)return;
      try{await client.adapter._fetch('/api/production/panic',{method:'POST'});await client.refresh(true);say('Emergency stop confirmed.');}
      catch(error){say(error.message,true);}
    };mount.append(emergency);
    let lastSources='',lastProfiles='',lastSessions='';
    client.addEventListener('state',event=>{
      const s=event.detail;
      const signature=JSON.stringify(s.cameras);
      if(signature!==lastSources){
        const selected=camera.value;camera.replaceChildren();
        s.cameras.forEach(c=>camera.append(element('option',c.name+' · '+c.transport,{value:c.source_id})));
        camera.value=s.cameras.some(c=>c.source_id===selected)?selected:(s.preview||s.program||'');lastSources=signature;
      }
      const names=id=>s.cameras.find(c=>c.source_id===id)?.name||id||'None';
      readout.textContent='Program: '+names(s.program)+' · Preview: '+names(s.preview);
      const p=JSON.stringify(s.profiles);
      if(p!==lastProfiles){profile.replaceChildren();s.profiles.forEach(id=>profile.append(element('option',id,{value:id})));profile.value='broadcast_mp4';lastProfiles=p;}
      const active=s.sessions.filter(x=>['active','countdown','paused','requested'].includes(x.state));
      const ids=JSON.stringify(active.map(x=>[x.session_id,x.state]));
      if(ids!==lastSessions){const selected=session.value;session.replaceChildren();active.forEach(x=>session.append(element('option',x.session_id+' · '+x.state,{value:x.session_id})));if(active.some(x=>x.session_id===selected))session.value=selected;lastSessions=ids;}
      start.disabled=active.length>0;stop.disabled=!active.length;
      recInfo.textContent=active.map(x=>x.session_id+' · '+x.state+' · '+(x.capture.running?'encoder running':'no running encoder')).join(' | ')||'No active capture session.';
      if(s.cameras.find(c=>c.source_id===s.program)?.transport==='virtual')recInfo.textContent+=' Selected virtual source records a test pattern.';
      for(const [name,c] of controls){const b=s.audio.buses[name];if(document.activeElement!==c.range)c.range.value=Math.round(b.volume*100);c.mute.textContent=b.muted?'Unmute':'Mute';c.mute.setAttribute('aria-pressed',String(b.muted));}
    });
    client.addEventListener('error',event=>say('Control room unavailable: '+event.detail.message,true));
    client.refresh().then(()=>say('Connected to the host.')).catch(e=>say(e.message,true));
  }
  root.PubCastControlRoom={ControlRoomClient,client,mountPanel};
  document.addEventListener('DOMContentLoaded',async()=>{
    document.querySelectorAll('[data-control-room-panel]').forEach(mountPanel);
    await client.start();
  });
  root.addEventListener('pagehide',()=>client.stop());
})(window);
