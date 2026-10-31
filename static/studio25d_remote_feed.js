/* PubCast real video confidence monitor for existing Director Switcher.
 * Displays ONLY acknowledged, fresh JPEGs published by the actual 2.5D stage.
 * No guessed video sources or simulated animation/meter. This is a lower-rate
 * operator confidence path, not a full broadcast video decoder.
 */
(function(root,factory){
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 else root.PubCast25DRemoteFeed=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 const sourcePattern=/^p25d_[a-z0-9_]{2,100}$/;
 function create(options={}) {
   const fetcher=options.fetch||globalThis.fetch?.bind(globalThis);
   const urlAPI=options.urlAPI||(typeof URL!=="undefined"?URL:null);
   const targets=options.targets||{};
   if(!fetcher||!urlAPI)throw Error("Remote confidence preview requires Fetch and URL");
   const entries={program:{source:null,url:null,busy:false,generation:0},preview:{source:null,url:null,busy:false,generation:0}};
   let stopped=false;
   function setStatus(role,label,visible=false) {
     const target=targets[role];if(!target?.status)return;
     target.status.textContent=label;target.status.style.position="relative";
     target.status.style.zIndex="3";
     target.status.style.color=visible?"#86e4b4":"#ff9393";
   }
   function clear(role,reason) {
     const entry=entries[role],target=targets[role];
     if(entry.url){urlAPI.revokeObjectURL(entry.url);entry.url=null;}
     if(target?.image){target.image.removeAttribute("src");target.image.hidden=true;}
     setStatus(role,reason||"VIDEO FEED UNBOUND");
   }
   function setSources(program,preview) {
     for(const [role,source] of [["program",program],["preview",preview]]){
       const entry=entries[role];
       if(entry.source===source)continue;
       entry.source=source||null;entry.generation++;
       clear(role,sourcePattern.test(source||"")?"AWAITING REAL 2.5D FRAME":"VIDEO FEED UNBOUND");
     }
   }
   async function update(role) {
     const entry=entries[role],source=entry.source,target=targets[role];
     if(stopped||entry.busy||!target?.image||!sourcePattern.test(source||""))return false;
     entry.busy=true;const gen=entry.generation;
     try{
       const response=await fetcher("/api/studio25d/media/frames/"+encodeURIComponent(source),{
         cache:"no-store",credentials:"same-origin"
       });
       if(!response.ok)throw Error("HTTP "+response.status);
       if(!String(response.headers?.get?.("content-type")||"").startsWith("image/jpeg"))
         throw Error("Non-JPEG response");
       const age=Number(response.headers.get("x-studio-frame-age-ms"));
       if(!Number.isFinite(age)||age>5000)throw Error("Frame is stale");
       const blob=await response.blob();
       if(!blob||!blob.size||blob.size>240000)throw Error("Invalid frame size");
       // A transport ACK alone does not prove a JPEG can be decoded.
       // Decode *before* marking the monitor as carrying a real frame.
       const decode=options.decode||(typeof createImageBitmap==="function"?async b=>{
         const image=await createImageBitmap(b);image.close();
       }:null);
       if(decode)await decode(blob);
       if(stopped||gen!==entry.generation||entry.source!==source)return false;
       const newURL=urlAPI.createObjectURL(blob),old=entry.url;
       entry.url=newURL;target.image.src=newURL;target.image.hidden=false;
       if(old)urlAPI.revokeObjectURL(old);
       setStatus(role,"REAL 2.5D FRAME · "+Math.round(age)+"ms OLD · LOW-RATE CONFIDENCE",true);
       return true;
     }catch(e){
       if(gen===entry.generation&&!stopped)clear(role,"NO FRESH VIDEO FRAME ("+e.message+")");
       return false;
     }finally{entry.busy=false;}
   }
   async function refresh(){
     if(stopped)return;
     await Promise.all([update("program"),update("preview")]);
   }
   function stop(){
     if(stopped)return;stopped=true;
     clear("program");clear("preview");
   }
   return {setSources,refresh,stop,status:()=>({stopped,program:entries.program.source,preview:entries.preview.source})};
 }
 return {create};
});
