/* PubCast 2.5D real-frame confidence publisher.
 * The same browser that renders program/preview publishes downscaled JPEGs to
 * an authenticated bounded server endpoint. This is a monitor confidence feed,
 * not a replacement for full frame-rate local capture or future WebRTC ingest.
 * No response means no claim of live media.
 */
(function(root,factory){
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 else root.PubCast25DFramePublisher=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 function create(options={}) {
   const fetcher=options.fetch||(typeof fetch!=="undefined"?fetch.bind(globalThis):null);
   const session=String(options.session||"");
   const sourceId=options.sourceId;
   const onState=typeof options.onState==="function"?options.onState:()=>{};
   const onError=typeof options.onError==="function"?options.onError:()=>{};
   if(!/^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/.test(session))throw Error("Invalid publisher session");
   if(typeof sourceId!=="function")throw Error("Studio camera source mapping required");
   if(!fetcher)throw Error("Fetch unavailable");
   let stopped=false,acknowledged=0,errors=0;
   const busySources=new Set(),lastAtBySource=new Map();
   const size={width:640,height:360},minInterval=220;
   // Only constructed when a real browser canvas is available.
   let scratch=null,context=null;
   function toJpeg(canvas) {
     if(typeof options.encode==="function")return options.encode(canvas);
     if(!scratch){scratch=document.createElement("canvas");scratch.width=size.width;scratch.height=size.height;context=scratch.getContext("2d",{alpha:false});}
     if(!context||!canvas)throw Error("2.5D camera frame unavailable");
     context.drawImage(canvas,0,0,size.width,size.height);
     return new Promise((resolve,reject)=>{
       scratch.toBlob(blob=>blob&&blob.size?resolve(blob):reject(Error("JPEG confidence encoder returned no data")),"image/jpeg",.68);
     });
   }
   async function publish(cameraId,canvas,now=Date.now()){
     if(stopped||!cameraId||!canvas)return false;
     const id=sourceId(cameraId);
     if(busySources.has(id)||now-(lastAtBySource.get(id)||0)<minInterval)return false;
     busySources.add(id);lastAtBySource.set(id,now);
     try {
       const blob=await toJpeg(canvas);
       if(stopped)return false;
       if(!blob||blob.size>240000)throw Error("Confidence frame exceeds 240KB budget");
       const response=await fetcher("/api/studio25d/media/frames/"+encodeURIComponent(id),{
         method:"POST",credentials:"same-origin",headers:{"Content-Type":"image/jpeg","X-Studio-Session":session},body:blob
       });
       if(!response.ok)throw Error("Confidence upload HTTP "+response.status);
       const result=await response.json();
       if(!result?.ok||result.source_id!==id||!Number.isInteger(result.sequence))throw Error("Video frame acknowledgment malformed");
       acknowledged++;errors=0;onState({live:true,frames:acknowledged,source:id,sequence:result.sequence});
       return true;
     }catch(e){
       errors++;onError("Remote video confidence frame failed: "+e.message,errors);
       return false;
     }finally{busySources.delete(id);}
   }
   async function stop(){
     if(stopped)return;stopped=true;onState({live:false,frames:acknowledged});
     try{
       const response=await fetcher("/api/studio25d/media/sessions/"+encodeURIComponent(session),{
         method:"DELETE",credentials:"same-origin"
       });
       if(!response.ok)onError("Video publisher release HTTP "+response.status,errors);
     }catch(e){onError("Video publisher cleanup: "+e.message,errors);}
     if(scratch){scratch.width=0;scratch.height=0;scratch=null;context=null;}
   }
   return {publish,stop,status:()=>({stopped,busy:busySources.size>0,acknowledged,errors})};
 }
 return {create};
});
