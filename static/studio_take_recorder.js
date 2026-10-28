/* Capture actual stage pixels and mixed audio; encoded-file verification is server-side. */
(() => {
 'use strict';
 class TakeRecorder {
  constructor({canvas,audioContext,programRuntime,microphone,getSlate}){
   this.source=canvas;this.context=audioContext;this.program=programRuntime;this.microphone=microphone;this.getSlate=getSlate;
   this.checkpoints=[];this.nextCheckpoint=0;this.frameCount=0;
   this.chunks=[];this.bytes=0;this.cueAt=null;this.nodes=[];this.active=false;
  }
  async start(){
   if(!window.MediaRecorder||!this.source?.width)throw Error('A running 3D stage is required for this take recorder');
   await this.context.resume();if(this.context.state!=='running')throw Error('Enable browser audio before recording');
   this.destination=this.context.createMediaStreamDestination();
   if(this.program){
    const sourceContext=this.program.ensureContext();await sourceContext.resume();
    this.programTap=sourceContext.createMediaStreamDestination();this.program.master.connect(this.programTap);
    const bridge=this.context.createMediaStreamSource(this.programTap.stream);bridge.connect(this.destination);this.nodes.push(bridge);
   }
   this.startStems();
   this.attachMicrophone(this.microphone);
   this.canvas=document.createElement('canvas');this.canvas.width=1280;this.canvas.height=720;
   this.startedAt=this.context.currentTime;
   this.paint=this.canvas.getContext('2d',{alpha:false});this.active=true;this.draw();
   this.video=this.canvas.captureStream(30);
   this.stream=new MediaStream([...this.video.getVideoTracks(),...this.destination.stream.getAudioTracks()]);
   const mime=['video/webm;codecs=vp8,opus','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));
   if(!mime){this.release();throw Error('This browser cannot encode WebM with audio');}
   this.recorder=new MediaRecorder(this.stream,{mimeType:mime,videoBitsPerSecond:4000000});
   this.finished=new Promise((resolve,reject)=>{
    this.recorder.ondataavailable=e=>{if(e.data.size){this.chunks.push(e.data);this.bytes+=e.data.size;if(this.bytes>120*1024*1024&&this.recorder.state==='recording')this.recorder.stop();}};
    this.recorder.onerror=e=>{this.release();reject(e.error||Error('Take recording failed'));};
    this.recorder.onstop=()=>{const blob=new Blob(this.chunks,{type:mime});this.release();resolve(blob);};
   });
   this.recorder.start(1000);this.scheduleReference();return this;
  }
  attachMicrophone(stream){
   this.micNode?.disconnect();this.micNode=null;
   if(stream?.active&&this.destination){this.micNode=this.context.createMediaStreamSource(stream);this.micNode.connect(this.destination);if(this.stemMerger)this.micNode.connect(this.stemMerger,0,12);}
  }
  draw(){
   if(!this.active)return;const c=this.paint,w=this.canvas.width,h=this.canvas.height,s=this.getSlate()?.slate;
   c.fillStyle='#071014';c.fillRect(0,0,w,h);c.drawImage(this.source,0,0,w,h);
   const clapping=this.cueAt!==null&&this.context.currentTime>=this.cueAt&&this.context.currentTime<this.cueAt+.16;
   if(s?.visible||clapping){
    c.fillStyle='#10242aee';c.fillRect(160,190,960,340);c.fillStyle='#f8e7bb';c.font='bold 40px sans-serif';
    c.fillText(`SCENE ${s.fields.scene}   TAKE ${s.fields.take}`,200,300,860);
    c.font='24px sans-serif';c.fillText(s.fields.production||'PubCast',200,350,860);c.fillText(s.fields.actors||'',200,400,860);
    c.save();c.translate(180,195);if(this.cueAt===null||this.context.currentTime<this.cueAt)c.rotate(-.1);
    c.fillStyle='#e7d3a3';c.fillRect(0,-30,920,28);c.restore();
   }
   const elapsed=this.context.currentTime-this.startedAt;this.frameCount++;
   if(elapsed>=this.nextCheckpoint){this.checkpoints.push({target_seconds:this.nextCheckpoint,audio_seconds:elapsed,audio_sample:Math.round(elapsed*this.context.sampleRate),compositor_frame:this.frameCount,performance_ms:performance.now(),late_ms:Math.max(0,(elapsed-this.nextCheckpoint)*1000)});this.nextCheckpoint+=15;}
   // A reserved corner provides an unambiguous, machine-readable visual clap.
   if(s?.visible||clapping){c.fillStyle=this.cueAt!==null&&this.context.currentTime>=this.cueAt&&this.context.currentTime<this.cueAt+.12?'#fff':'#000';c.fillRect(0,0,64,64);}
   this.frame=requestAnimationFrame(()=>this.draw());
  }
  startStems(){
   this.stemNames=['dialogue','music','sfx','ui','vtr','room','floor','reference'];this.stemBlocks=[];this.stemFrames=0;this.pcmBytes=0;this.captureStems=true;
   this.stemMerger=this.context.createChannelMerger(14);this.referenceInput=this.context.createGain();this.referenceInput.connect(this.stemMerger,0,13);
   this.stemProcessor=this.context.createScriptProcessor(4096,14,1);this.stemSink=this.context.createGain();this.stemSink.gain.value=0;
   this.stemMerger.connect(this.stemProcessor);this.stemProcessor.connect(this.stemSink).connect(this.context.destination);
   this.stemProcessor.onaudioprocess=e=>{
    if(!this.captureStems)return;const n=e.inputBuffer.length,block=[];
    for(let track=0;track<8;track++){
     const channels=track<6?2:1,left=e.inputBuffer.getChannelData(track<6?track*2:track+6),right=channels===2?e.inputBuffer.getChannelData(track*2+1):left;
     let nonzero=false;for(let i=0;i<n;i++)if(Math.abs(left[i])+Math.abs(right[i])>.00003){nonzero=true;break;}
     let pcm=null;if(nonzero){pcm=new Int16Array(n*channels);for(let i=0;i<n;i++){pcm[i*channels]=Math.round(Math.max(-1,Math.min(1,left[i]))*32767);if(channels===2)pcm[i*2+1]=Math.round(Math.max(-1,Math.min(1,right[i]))*32767);}this.pcmBytes+=pcm.byteLength;}
     block.push(pcm);
    }
    this.stemBlocks.push({frames:n,tracks:block});this.stemFrames+=n;
    if(this.pcmBytes>100*1024*1024||this.stemFrames/this.context.sampleRate>600)this.stop();
   };
   this.stemTaps=[];
   if(this.program)for(let i=0;i<6;i++){
    const bus=this.program.buses.get(this.stemNames[i]);if(!bus)continue;
    const tap=this.program.context.createMediaStreamDestination();bus.gain.connect(tap);
    const bridge=this.context.createMediaStreamSource(tap.stream),split=this.context.createChannelSplitter(2);bridge.connect(split);split.connect(this.stemMerger,0,i*2);split.connect(this.stemMerger,1,i*2+1);
    this.stemTaps.push({bus,tap,bridge,split});
   }
  }
  scheduleReference(){
   if(this.referenceScheduled)return;this.referenceScheduled=true;let index=1;
   const schedule=()=>{if(!this.active)return;while(this.startedAt+index*15<this.context.currentTime+20){this.referencePulse(this.startedAt+index*15);index++;}};
   schedule();this.syncScheduler=setInterval(schedule,5000);
  }
  referencePulse(at){
   const oscillator=this.context.createOscillator(),gain=this.context.createGain();oscillator.frequency.value=1500;
   gain.gain.setValueAtTime(.3,at);gain.gain.exponentialRampToValueAtTime(.001,at+.03);oscillator.connect(gain).connect(this.referenceInput);oscillator.start(at);oscillator.stop(at+.03);
  }
  stemBlob(index){
   const channels=index<6?2:1,bytes=this.stemFrames*channels*2,header=new ArrayBuffer(44),v=new DataView(header);
   const text=(at,s)=>[...s].forEach((c,i)=>v.setUint8(at+i,c.charCodeAt(0)));text(0,'RIFF');v.setUint32(4,36+bytes,true);text(8,'WAVE');text(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,channels,true);v.setUint32(24,this.context.sampleRate,true);v.setUint32(28,this.context.sampleRate*channels*2,true);v.setUint16(32,channels*2,true);v.setUint16(34,16,true);text(36,'data');v.setUint32(40,bytes,true);
   return new Blob([header,...this.stemBlocks.map(b=>b.tracks[index]||new Int16Array(b.frames*channels))],{type:'audio/wav'});
  }
  markClap(audioTime){this.cueAt=audioTime;this.referencePulse(audioTime);}

  timing(){return {schema:'pubcast.timing.v1',cadence_seconds:15,sample_rate:this.context.sampleRate,clock:'browser_audio_context',clap_audio_seconds:this.cueAt===null?null:this.cueAt-this.startedAt,checkpoints:this.checkpoints,periodic_audio_added:false};}
  stop(){if(this.recorder?.state==='recording')this.recorder.stop();return this.finished;}
  release(){
   if(this.released)return;this.released=true;
   this.captureStems=false;this.stemProcessor?.disconnect();this.stemMerger?.disconnect();this.stemSink?.disconnect();clearInterval(this.syncScheduler);
   this.stemTaps?.forEach(({bus,tap,bridge,split})=>{bus.gain.disconnect(tap);bridge.disconnect();split.disconnect();tap.stream.getTracks().forEach(t=>t.stop());});
   this.active=false;cancelAnimationFrame(this.frame);this.micNode?.disconnect();this.nodes.forEach(n=>n.disconnect());
   if(this.programTap){this.program.master.disconnect(this.programTap);this.programTap.stream.getTracks().forEach(t=>t.stop());}
   this.destination?.stream.getTracks().forEach(t=>t.stop());
   this.stream?.getTracks().forEach(t=>t.stop());this.video?.getTracks().forEach(t=>t.stop());
  }
 }
 window.PubCastTakeRecorder=TakeRecorder;
})();
