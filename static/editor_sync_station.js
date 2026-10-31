/* PubCast simple shoot assembler.
 * Original UI built around broadly familiar NLE concepts: bin, viewer,
 * track sync and selects. No branded Resolve assets or copyrighted UI.
 * Does not render, transform or overwrite source media.
 */
(function(){
"use strict";
const Core=window.PubCastEditorSync, Store=window.PubCastEditorSyncStore;
const $=id=>document.getElementById(id);
if(!Core||!Store||!$("station-editor"))return;
const ui={
 title:$("ed-project-title"),projects:$("ed-projects"),newProject:$("ed-new-project"),
 save:$("ed-save"),export:$("ed-export"),import:$("ed-import"),cache:$("ed-cache"),
 sidecar:$("ed-sidecar"),bin:$("ed-bin"),video:$("ed-view"),audio:$("ed-audio"),
 playhead:$("ed-playhead"),markIn:$("ed-mark-in"),markOut:$("ed-mark-out"),add:$("ed-add-subclip"),
 io:$("ed-io"),timeline:$("ed-timeline"),status:$("ed-status"),selected:$("ed-selected-track"),
 offset:$("ed-offset"),apply:$("ed-apply-offset"),reset:$("ed-reset-offset"),
 marker:$("ed-marker-number"),markClacker:$("ed-mark-clacker"),health:$("ed-sync-health"),
 menu:$("ed-sync-menu"),advance:$("ed-advance-30"),delay:$("ed-delay-30"),
 resetMenu:$("ed-reset-menu"),closeMenu:$("ed-close-sync")
};
let project=null,currentTrackId=null,playheadUs=0,markInUs=null,markOutUs=null,selectionToken=0;
let saveQueue=Promise.resolve(),lastSaved=-1,projectEpoch=0;
const fileByTrack=new Map(),objectURLByTrack=new Map();
const fail=err=>{const msg=String(err?.message||err);ui.status.textContent=msg;ui.status.style.color="#ff8585";console.error("PubCast assembly",err)};
const say=s=>{ui.status.textContent=s;ui.status.style.color="#91dfaf"};
const safe=fn=>Promise.resolve().then(fn).catch(fail);
const ensure=()=>{if(!project)throw Error("Create or open a shoot first");return project};
const selected=()=>{ensure();const t=project.tracks.find(x=>x.id===currentTrackId);if(!t)throw Error("Choose a camera or audio track");return t};
const timeText=us=>{const ms=Math.round(Math.max(0,us)/1000),h=Math.floor(ms/3600000),m=Math.floor(ms%3600000/60000),s=Math.floor(ms%60000/1000);
 return [h,m,s].map(n=>String(n).padStart(2,"0")).join(":")+"."+String(ms%1000).padStart(3,"0")};
const clone=x=>JSON.parse(JSON.stringify(x));
const filenameSafe=s=>String(s).replace(/[^a-zA-Z0-9._-]+/g,"-").slice(0,90)||"pubcast-shoot";
function stopPreview(){
 selectionToken++;for(const media of [ui.video,ui.audio]){media.pause();media.removeAttribute("src");media.load();media.hidden=true;}
}
function releaseURLs(){stopPreview();for(const url of objectURLByTrack.values())URL.revokeObjectURL(url);
 objectURLByTrack.clear();fileByTrack.clear()}
async function save(){
 ensure();Core.validateProject(project);
 const saved=clone(project),epoch=projectEpoch,rev=saved.revision;
 saveQueue=saveQueue.catch(()=>{}).then(async()=>{
   if(epoch!==projectEpoch||rev<lastSaved)return;
   await Store.saveProject(saved);
   if(epoch===projectEpoch){lastSaved=rev;say("Saved project revision "+rev)}
 });
 await saveQueue;
}
function updated(){renderBin();renderSelected();renderTimeline();return save()}
function currentMedia(){const t=selected();return t.kind==="audio"?ui.audio:ui.video}
function shootPosition(){
 const t=selected(),media=currentMedia(),sourceUs=Math.round((Number(media.currentTime)||0)*1000000);
 return Math.max(0,Core.editTimeUs(project,t.id,sourceUs));
}
function updatePlayhead(){
 if(!project||!currentTrackId)return;
 try{playheadUs=shootPosition();ui.playhead.textContent="Shoot time: "+timeText(playheadUs)}
 catch(e){ui.health.textContent=String(e.message)}
}
async function resolveMedia(t){
 if(fileByTrack.has(t.id))return fileByTrack.get(t.id);
 if(t.mediaRef?.startsWith("local:"))return (await Store.readMedia(t.mediaRef.slice(6)))?.blob||null;
 if(t.mediaRef?.startsWith("studio:")){
   if(!window.PubCast25DStore)throw Error("Stage recording store unavailable");
   return (await window.PubCast25DStore.read(t.mediaRef.slice(7)))?.blob||null;
 }
 return null;
}
async function selectTrack(id){
 ensure();if(currentTrackId&&currentTrackId!==id)updatePlayhead();
 const t=project.tracks.find(x=>x.id===id);if(!t)throw Error("Track not found");
 currentTrackId=t.id;stopPreview();const token=selectionToken;
 renderBin();renderSelected();
 const blob=await resolveMedia(t);
 if(token!==selectionToken)return;
 if(!blob){say("Proxy not loaded. Relink "+t.label+" using Import; your edits are safe.");return}
 let url=objectURLByTrack.get(t.id);
 if(!url){url=URL.createObjectURL(blob);objectURLByTrack.set(t.id,url)}
 const media=t.kind==="audio"?ui.audio:ui.video;media.hidden=false;media.src=url;
 const desired=Core.sourceTimeUs(project,t.id,playheadUs);
 media.addEventListener("loadedmetadata",()=>{
   if(token!==selectionToken)return;
   const sec=Math.max(0,desired/1000000);
   try{media.currentTime=Number.isFinite(media.duration)&&media.duration>0?Math.min(sec,Math.max(0,media.duration-.001)):sec}
   catch(e){fail(e)}
 },{once:true});
 media.load();say("Viewing "+t.label+" — source is unchanged");
}
function renderBin(){
 ui.bin.replaceChildren();
 if(!project){ui.bin.textContent="No shoot open";return}
 if(!project.tracks.length){ui.bin.textContent="Add camera/audio proxy files, then mark clacker sync points";return}
 for(const t of project.tracks){
   const row=document.createElement("div");row.style.cssText="display:flex;gap:6px;align-items:center;padding:6px;border-bottom:1px solid #8885";
   if(t.id===currentTrackId)row.style.background="rgba(140,150,255,.16)";
   const choose=document.createElement("button");choose.type="button";choose.style.flex="1";choose.textContent=(t.kind==="audio"?"♫ ":"▣ ")+t.label;
   choose.addEventListener("click",()=>safe(()=>selectTrack(t.id)));
   choose.addEventListener("contextmenu",e=>{e.preventDefault();currentTrackId=t.id;renderSelected();renderBin();ui.menu.hidden=false});
   const offset=document.createElement("span");offset.className="muted small";offset.textContent=(t.manualOffsetUs>=0?"+":"")+Core.formatSeconds(t.manualOffsetUs)+"s";
   const adjust=document.createElement("button");adjust.type="button";adjust.textContent="Sync / Offset";
   adjust.addEventListener("click",()=>{currentTrackId=t.id;renderSelected();renderBin();ui.menu.hidden=false;ui.offset.focus()});
   row.append(choose,offset,adjust);ui.bin.append(row);
 }
}
function renderSelected(){
 if(!project||!currentTrackId){ui.selected.textContent="Select a track";ui.offset.value="0.000000";ui.health.textContent="Unanchored";return}
 const t=selected(),a=Core.alignment(project,t);
 ui.selected.textContent=t.label;ui.offset.value=Core.formatSeconds(t.manualOffsetUs);
 ui.health.textContent=a.origin==="clacker"
   ?("Clacker "+a.markers+" marker(s); drift "+a.driftPpm.toFixed(1)+" ppm; residual "+a.residualUs+" µs")
   :a.origin==="wallclock"?"Wall-clock estimate; set clacker markers for precision"
   :"UNANCHORED — mark clacker before trusting sync";
}
function renderTimeline(){
 ui.timeline.replaceChildren();if(!project)return;
 if(!project.selections.length){ui.timeline.textContent="No selected shots yet";return}
 for(const s of project.selections){
   const row=document.createElement("div");row.style.cssText="display:flex;gap:8px;padding:6px;align-items:center;border-bottom:1px solid #8885";
   const track=project.tracks.find(t=>t.id===s.trackId);
   const label=document.createElement("span");label.style.flex="1";label.textContent=(track?.label||s.trackId)+" · "+timeText(s.inUs)+" – "+timeText(s.outUs);
   const open=document.createElement("button");open.type="button";open.textContent="Review";
   open.addEventListener("click",()=>safe(async()=>{playheadUs=s.inUs;await selectTrack(s.trackId)}));
   const remove=document.createElement("button");remove.type="button";remove.textContent="Remove";remove.title="Remove select, not original footage";
   remove.addEventListener("click",()=>safe(async()=>{project.selections=project.selections.filter(x=>x.id!==s.id);project.revision++;project.updatedAt=new Date().toISOString();await updated()}));
   row.append(label,open,remove);ui.timeline.append(row);
 }
}
function renderIO(){ui.io.textContent="In: "+(markInUs==null?"—":timeText(markInUs))+"  Out: "+(markOutUs==null?"—":timeText(markOutUs))}
async function openProject(id){
 if(project&&project.revision!==lastSaved)await save();
 const result=await Store.readProject(id);if(!result)throw Error("Shoot project missing");
 Core.validateProject(result);releaseURLs();project=result;projectEpoch++;lastSaved=result.revision;
 currentTrackId=null;markInUs=null;markOutUs=null;playheadUs=0;ui.title.value=result.title;
 renderBin();renderTimeline();renderSelected();renderIO();say("Opened "+result.title+"; relink un-cached files as needed");
}
async function refreshProjects(){
 const projects=await Store.listProjects();ui.projects.replaceChildren();
 const placeholder=document.createElement("option");placeholder.value="";placeholder.textContent="Saved shoots…";ui.projects.append(placeholder);
 for(const item of projects){const option=document.createElement("option");option.value=item.id;option.textContent=item.title+" · "+new Date(item.updatedAt).toLocaleDateString();ui.projects.append(option)}
}
function createShoot(){
 releaseURLs();project=Core.createProject(ui.title.value||"Untitled shoot",Date.now(),"edit-"+Date.now()+"-"+Math.random().toString(36).slice(2,8));
 projectEpoch++;lastSaved=-1;currentTrackId=null;playheadUs=0;markInUs=null;markOutUs=null;
 ui.title.value=project.title;renderBin();renderSelected();renderTimeline();renderIO();
 return save().then(refreshProjects);
}
async function importFiles(){
 ensure();const files=[...ui.import.files];if(!files.length)return;
 let imported=0;
 for(const file of files){
   if(!file.type.startsWith("video/")&&!file.type.startsWith("audio/"))throw Error(file.name+" is not an audio/video proxy");
   const existing=project.tracks.find(t=>t.label===file.name);
   if(existing){
     fileByTrack.set(existing.id,file);
     if(ui.cache.checked){await Store.saveMedia(existing.id,file,file.name);existing.mediaRef="local:"+existing.id}
     imported++;continue;
   }
   const track=Core.addTrack(project,{id:"track-"+Date.now().toString(36)+"-"+(project.tracks.length+1),
     kind:file.type.startsWith("audio/")?"audio":"camera",label:file.name,
     mediaRef:"temporary:"+file.name,durationUs:null});
   fileByTrack.set(track.id,file);
   if(ui.cache.checked){await Store.saveMedia(track.id,file,file.name);track.mediaRef="local:"+track.id}
   imported++;
 }
 ui.import.value="";await updated();say(imported+" proxy file(s) imported/relinked; set clacker markers to establish sync");
 if(!currentTrackId&&project.tracks.length)await selectTrack(project.tracks[0].id);
}
async function importSidecar(){
 ensure();const f=ui.sidecar.files[0];if(!f)return;
 const data=JSON.parse(await f.text());
 if(data.schema!=="pubcast.clacker"||data.version!==1||!Array.isArray(data.markers)||data.markers.length>50000)
   throw Error("Unsupported clacker sidecar format");
 const staged=clone(project);
 for(const marker of data.markers){
   if(!marker||typeof marker.trackId!=="string"||!Number.isSafeInteger(marker.sequence)||!Number.isSafeInteger(marker.sourceUs))
     throw Error("Invalid clacker marker");
   Core.addClackerMark(staged,marker.trackId,marker.sequence,marker.sourceUs);
 }
 Core.validateProject(staged);project=staged;ui.sidecar.value="";await updated();say(data.markers.length+" clacker markers imported and saved");
}
function applyOffset(seconds){const t=selected();Core.setOffsetSeconds(project,t.id,seconds);return updated()}
async function noteClacker(){
 const t=selected(),sequence=Number(ui.marker.value);
 if(!Number.isSafeInteger(sequence)||sequence<0)throw Error("Invalid 15-second clacker number");
 Core.addClackerMark(project,t.id,sequence,Math.round(Number(currentMedia().currentTime||0)*1000000));
 await updated();say("Clacker #"+sequence+" placed on "+t.label+" at source "+timeText(Math.round(currentMedia().currentTime*1000000)));
}
function exportPlan(){
 ensure();Core.validateProject(project);
 const obj={format:"PubCast Rough-Cut Transfer",version:1,
   purpose:"Portable non-destructive sync, coverage selections and relink metadata; NOT a native Resolve project",
   project:clone(project),renderSelection:Core.exportManifest(project),
   integration:{preferredFinisher:"DaVinci Resolve",transferStatus:"interchange adapter required",
     note:"All timing is integer microseconds, clacker reference every 15 seconds; media files must be relinked by the finisher."}};
 const blob=new Blob([JSON.stringify(obj,null,2)],{type:"application/json"});
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=filenameSafe(project.title)+".pubcast-edit.json";
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
 say("Exported edit-plan JSON. Resolve-specific interchange requires a validated adapter.");
}
function changePlayhead(us){playheadUs=Math.max(0,us);if(currentTrackId)selectTrack(currentTrackId).catch(fail);ui.playhead.textContent="Shoot time: "+timeText(playheadUs)}
ui.newProject.addEventListener("click",()=>safe(createShoot));
ui.save.addEventListener("click",()=>safe(async()=>{await save();await refreshProjects()}));
ui.projects.addEventListener("change",()=>{if(ui.projects.value)safe(()=>openProject(ui.projects.value))});
ui.import.addEventListener("change",()=>safe(importFiles));
ui.sidecar.addEventListener("change",()=>safe(importSidecar));
ui.apply.addEventListener("click",()=>safe(()=>applyOffset(ui.offset.value)));
ui.reset.addEventListener("click",()=>safe(()=>applyOffset("0")));
ui.advance.addEventListener("click",()=>safe(()=>{const t=selected();Core.adjustOffsetSeconds(project,t.id,"0.030");return updated()}));
ui.delay.addEventListener("click",()=>safe(()=>{const t=selected();Core.adjustOffsetSeconds(project,t.id,"-0.030");return updated()}));
ui.resetMenu.addEventListener("click",()=>safe(()=>applyOffset("0")));
ui.closeMenu.addEventListener("click",()=>{ui.menu.hidden=true});
ui.markClacker.addEventListener("click",()=>safe(noteClacker));
ui.markIn.addEventListener("click",()=>safe(()=>{markInUs=shootPosition();renderIO()}));
ui.markOut.addEventListener("click",()=>safe(()=>{markOutUs=shootPosition();renderIO()}));
ui.add.addEventListener("click",()=>safe(async()=>{
 const t=selected();if(markInUs==null||markOutUs==null)throw Error("Mark an In and Out first");
 Core.addSelection(project,{id:"select-"+(project.selections.length+1)+"-"+Date.now(),trackId:t.id,inUs:markInUs,outUs:markOutUs});
 await updated();say("Selected coverage added — original take untouched");
}));
ui.export.addEventListener("click",()=>safe(exportPlan));
for(const media of [ui.video,ui.audio]){
 media.addEventListener("timeupdate",updatePlayhead);
 media.addEventListener("seeked",updatePlayhead);
}
document.addEventListener("keydown",e=>{
 if(!$("station-editor")||$("station-editor").classList.contains("hidden"))return;
 if(e.ctrlKey||e.metaKey||e.altKey)return;
 if(["INPUT","TEXTAREA","SELECT"].includes(e.target?.tagName)||e.target?.isContentEditable)return;
 if(e.key.toLowerCase()==="i"){e.preventDefault();ui.markIn.click()}
 if(e.key.toLowerCase()==="o"){e.preventDefault();ui.markOut.click()}
});
window.addEventListener("pagehide",releaseURLs);
refreshProjects().then(()=>{renderBin();renderTimeline()}).catch(fail);
window.PubCastShootAssembly={openProject,refreshProjects,exportPlan};
})();
