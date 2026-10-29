/* R2.2.6 experimental V3 subtitles on already-readback R220 partial montage.
 * Only confirmed audio CUTs. Cue distribution WITHIN each CUT is an estimate,
 * not a claim of word-level ASR sync. No QE, no V1/A1 writes.
 */
if(typeof $==="undefined"){$={};}
$._AIVE_R226_=(function(){
 var TEMPLATE="D:/AI-Video-Editor/Templates/RFERL_Subtitles.mogrt";
 function fail(message){throw Error(String(message));}
 function safe(fn){try{return fn();}catch(e){return JSON.stringify({ok:false,message:String(e&&e.message||e)});}}
 function ok(message,more){var result={ok:true,message:message};
   if(more)for(var k in more)if(more.hasOwnProperty(k))result[k]=more[k];
   return JSON.stringify(result);}
 function numeric(n){return typeof n==="number"&&isFinite(n);}
 function near(a,b){return Math.abs(Number(a)-Number(b))<=.13;}
 function text(x){return String(x===undefined||x===null?"":x);}
 function tm(seconds){var t=new Time();t.seconds=seconds;return t;}
 function load(file){var f=File(file);if(!f.exists)fail("PLAN_FILE_MISSING");
   f.encoding="UTF-8";if(!f.open("r"))fail("PLAN_CANNOT_OPEN");
   var p;try{p=JSON.parse(f.read());}finally{f.close();}
   if(p.schema!=="aive-r226-partial-subs-v1"||p.module!=="02"||
      p.mode!=="montage_partial"||p.timing!=="CUT_ALIGNED_ESTIMATED"||
      !/^[a-f0-9]{64}$/.test(text(p.docx_sha256))||
      !/^[a-f0-9]{64}$/.test(text(p.montagePlanSHA256))||
      !/^[a-f0-9]{64}$/.test(text(p.contentSHA256))||
      !p.sequenceId||!p.items||p.items.length<1||
      p.totalItems!==p.items.length||p.items.length>2000)fail("PLAN_R226_INVALID");
   var group={};var previous=-1;
   for(var i=0;i<p.items.length;i++){
     var c=p.items[i];
     if(!/^CUT-[0-9]{1,4}$/.test(c.groupId)||!c.text||c.text.length>74||
        c.timingKind!=="CUT_ALIGNED_ESTIMATED"||
        (c.fontStyle!=="Italic"&&c.fontStyle!=="Regular")||
        !numeric(c.startSeconds)||!numeric(c.durationSeconds)||
        c.startSeconds<0||c.durationSeconds<.8||
        c.startSeconds<previous-.001)fail("CAPTION_DATA_INVALID");
     group[c.groupId]=true;previous=c.startSeconds+c.durationSeconds;
   }
   if(!p.confirmedCuts||p.confirmedCuts.length!==p.confirmedCount||
      !p.reservedCuts||p.reservedCuts.length!==p.reservedCount||
      p.confirmedCount<1)fail("PLAN_COUNTS_INVALID");
   var present={},missing={};
   for(var j=0;j<p.confirmedCuts.length;j++){
     var v=p.confirmedCuts[j];if(present[v.cutId]||!v.sourceName||!v.sourceNodeId)fail("CONFIRMED_INVALID");
     present[v.cutId]=v;
   }
   for(var q=0;q<p.reservedCuts.length;q++){
     var r=p.reservedCuts[q];if(present[r.cutId]||missing[r.cutId])fail("RESERVED_INVALID");
     missing[r.cutId]=true;
   }
   for(var n=0;n<p.items.length;n++){
     var a=p.items[n],m=present[a.groupId];
     if(!m||missing[a.groupId]||a.startSeconds<m.timelineStart-.14||
        a.startSeconds+a.durationSeconds>m.timelineEnd+.14)
         fail("SUBTITLE_OUTSIDE_VERIFIED_CUT "+a.groupId);
   }
   return {file:f,plan:p};
 }
 function active(){if(!app||!app.project||!app.project.activeSequence)fail("NO_ACTIVE_SEQUENCE");
   return app.project.activeSequence;}
 function seqId(s){return text(s.sequenceID||s.id);}
 function clipSignature(track){var rows=[];
   for(var i=0;i<track.clips.numItems;i++){
     var c=track.clips[i];rows.push([text(c.name),text(c.projectItem&&c.projectItem.name),
       text(c.projectItem&&c.projectItem.nodeId),
       Number(c.start.seconds).toFixed(4),Number(c.end.seconds).toFixed(4)].join("|"));
   }return rows.join("\n");}
 function markersSignature(s){var a=[],m=s.markers&&s.markers.getFirstMarker();
   while(m){a.push([text(m.name),Number(m.start.seconds).toFixed(4),
       Number(m.end&&m.end.seconds).toFixed(4)].join("|"));
     if(a.length>2500)fail("MARKER_LOOP");
     m=s.markers.getNextMarker(m);
   }return a.join("\n");}
 function otherSignature(s){var a=[];
   for(var i=0;i<s.videoTracks.numTracks;i++)if(i!==2)
     a.push("V"+i+":"+clipSignature(s.videoTracks[i]));
   for(var j=0;j<s.audioTracks.numTracks;j++)
     a.push("A"+j+":"+clipSignature(s.audioTracks[j]));
   return a.join("\n#\n")+"#markers\n"+markersSignature(s);
 }
 function checkMontage(s,p){
   if(seqId(s)!==p.sequenceId||text(s.name).indexOf("[AIVE TEST]")<0)
     fail("SEQUENCE_CHANGED_OR_NOT_TEST_COPY");
   if(s.videoTracks.numTracks<3||s.audioTracks.numTracks<1)fail("TRACK_MISSING");
   var v=s.videoTracks[0],a=s.audioTracks[0],target=s.videoTracks[2];
   if(!v||!a||!target||target.isLocked())fail("V3_LOCKED_OR_MISSING");
   if(v.clips.numItems!==p.confirmedCount||a.clips.numItems!==p.confirmedCount)
     fail("R220_MONTAGE_CLIP_COUNT_CHANGED");
   var usedV={},usedA={};
   for(var i=0;i<p.confirmedCuts.length;i++){
     var row=p.confirmedCuts[i],hitsV=0,hitsA=0;
     for(var j=0;j<v.clips.numItems;j++){
       var vc=v.clips[j],nm=text(vc.name),nm2=text(vc.projectItem&&vc.projectItem.name);
       if(near(vc.start.seconds,row.timelineStart)&&near(vc.end.seconds,row.timelineEnd)&&
          (nm===row.sourceName||nm2===row.sourceName)){
         hitsV++;usedV[j]=true;
       }
     }
     for(var k=0;k<a.clips.numItems;k++){
       var ac=a.clips[k],an=text(ac.name),an2=text(ac.projectItem&&ac.projectItem.name);
       if(near(ac.start.seconds,row.timelineStart)&&near(ac.end.seconds,row.timelineEnd)&&
          (an===row.sourceName||an2===row.sourceName)){
         hitsA++;usedA[k]=true;
       }
     }
     if(hitsV!==1||hitsA!==1)fail("R220_CLIP_READBACK_CHANGED "+row.cutId);
   }
   var countV=0,countA=0;
   for(var vk in usedV)if(usedV.hasOwnProperty(vk))countV++;
   for(var ak in usedA)if(usedA.hasOwnProperty(ak))countA++;
   if(countV!==p.confirmedCount||countA!==p.confirmedCount)fail("R220_CLIP_DUPLICATE");
   var markerCount=0,first=s.markers&&s.markers.getFirstMarker();
   while(first){if(text(first.name).indexOf("AIVE-R220 ")===0)markerCount++;
     first=s.markers.getNextMarker(first);if(markerCount>2500)fail("MARKER_LOOP");}
   if(markerCount!==p.reservedCount)fail("R220_PLACEHOLDER_MARKERS_CHANGED");
   for(var z=0;z<p.reservedCuts.length;z++){
     var slot=p.reservedCuts[z],count=0,m=s.markers&&s.markers.getFirstMarker();
     while(m){if(text(m.name).indexOf("AIVE-R220 "+slot.cutId+" "+slot.sourceCode)===0 &&
         near(m.start.seconds,slot.timelineStart)&&m.end&&near(m.end.seconds,slot.timelineEnd))count++;
       m=s.markers.getNextMarker(m);}
     if(count!==1)fail("R220_MARKER_CHANGED "+slot.cutId);
   }
   return target;
 }
 function ctx(file){var loaded=load(file),s=active(),target=checkMontage(s,loaded.plan);
   return {plan:loaded.plan,seq:s,target:target,file:loaded.file};}
 function token(c,step,base){
   return JSON.stringify({sequence:c.plan.sequenceId,hash:c.plan.contentSHA256,
      stamp:text(c.file.modified),path:text(c.file.fsName),count:step,
      other:otherSignature(c.seq),target:clipSignature(c.target),base:base});
 }
 function verifiedToken(c,raw){
   var t;try{t=JSON.parse(raw);}catch(e){fail("TOKEN_INVALID");}
   if(!t||t.sequence!==c.plan.sequenceId||t.hash!==c.plan.contentSHA256||
      t.stamp!==text(c.file.modified)||t.path!==text(c.file.fsName)||
      t.other!==otherSignature(c.seq)||t.target!==clipSignature(c.target)||
      !numeric(t.count)||t.count<0||t.count>c.plan.totalItems)
      fail("SEQUENCE_OR_TRACK_CHANGED_STOP");
   if(c.target.clips.numItems!==t.count||t.base!=="")fail("V3_NOT_OWNED");
   return t;
 }
 function param(comp,key){
   if(!comp||!comp.properties)fail("MOGRT_COMPONENT_MISSING");
   var x=comp.properties.getParamForDisplayName(key);
   if(!x)fail("MOGRT_PARAM_MISSING "+key);return x;
 }
 function payload(value){
   var s=text(value),idx=s.indexOf("{");if(idx<0||idx>8)fail("UNKNOWN_MOGRT_PAYLOAD");
   var obj=JSON.parse(s.substring(idx)),f=[];
   function walk(x,d){if(!x||typeof x!=="object"||d>15)return;
     if(typeof x.textEditValue==="string")f.push({obj:x,key:"textEditValue"});
     if(x.mTextParam&&x.mTextParam.mStyleSheet&&
        typeof x.mTextParam.mStyleSheet.mText==="string")
       f.push({obj:x.mTextParam.mStyleSheet,key:"mText"});
     for(var key in x)if(x.hasOwnProperty(key)&&typeof x[key]==="object")walk(x[key],d+1);
   }walk(obj,0);if(!f.length)fail("TEXT_NOT_EDITABLE");
   return {prefix:s.substring(0,idx),obj:obj,fields:f};
 }
 function readText(p){var x=payload(p.getValue());return x.fields[0].obj[x.fields[0].key];}
 function writeText(p,value){
   var x=payload(p.getValue());
   for(var i=0;i<x.fields.length;i++){
     var y=x.fields[i];y.obj[y.key]=value;
     if(y.key==="textEditValue"&&y.obj.fontTextRunLength instanceof Array &&
        y.obj.fontTextRunLength.length===1)y.obj.fontTextRunLength=[value.length];
   }
   if(p.setValue(x.prefix+JSON.stringify(x.obj),true)===false ||
      readText(p)!==value)fail("SUBTITLE_MOGRT_TEXT_READBACK_FAIL");
 }
 function writeNum(p,n){
   if(p.setValue(n,true)===false||text(p.getValue())!==text(n))
     fail("SUBTITLE_MOGRT_STYLE_READBACK_FAIL");
 }
 function matches(clip,item){
   if(!near(clip.start.seconds,item.startSeconds)||
      !near(clip.end.seconds,item.startSeconds+item.durationSeconds))return false;
   try{var comp=clip.getMGTComponent();
     return readText(param(comp,"Text"))===item.text &&
       text(param(comp,"Font Style").getValue())===(item.fontStyle==="Italic"?"0":"1") &&
       text(param(comp,"Aspect Ratio").getValue())==="1";
   }catch(e){return false;}
 }
 function preflight(file){return safe(function(){
   var c=ctx(file);if(c.target.clips.numItems!==0)fail("V3_OCCUPIED_NO_OVERWRITE");
   if(!File(TEMPLATE).exists)fail("SUBTITLE_TEMPLATE_MISSING");
   return ok("V3 pregătită: "+c.plan.totalItems+" subtitrări, "+c.plan.reservedCount+
      " CUT-uri fără audio confirmat.",{token:token(c,0,""),
      items:c.plan.totalItems,omitted:c.plan.reservedCount,
      timing:c.plan.timing});
 });}
 function buildOne(file,raw,n){return safe(function(){
   var c=ctx(file),t=verifiedToken(c,raw),i=Number(n);
   if(!numeric(i)||i!==Math.floor(i)||i!==t.count||i>=c.plan.totalItems)
     fail("INSERT_ORDER_CHANGED");
   var a=c.plan.items[i],start=a.startSeconds,ending=start+a.durationSeconds;
   if(c.target.clips.numItems!==i)fail("V3_OCCUPIED");
   var originalOther=otherSignature(c.seq),inserted=null;
   try{
     inserted=c.seq.importMGT(File(TEMPLATE).fsName,text(tm(start).ticks),2,0);
     if(!inserted||!near(inserted.start.seconds,start))fail("MOGRT_IMPORT_FAILED");
     var component=inserted.getMGTComponent();
     writeText(param(component,"Text"),a.text);
     writeNum(param(component,"Font Style"),a.fontStyle==="Italic"?0:1);
     writeNum(param(component,"Aspect Ratio"),1);
     inserted.end=tm(ending);
     if(!matches(inserted,a))fail("MOGRT_READBACK_FAILED");
     if(otherSignature(c.seq)!==originalOther)fail("V1_A1_OR_OTHER_CHANGED");
     if(c.target.clips.numItems!==i+1)fail("V3_INSERT_COUNT_MISMATCH");
   }catch(e){
     var problems=[];
     if(inserted)try{inserted.remove(false,false);}catch(z){problems.push("OWN_CLIP_REMOVE_FAILED");}
     if(otherSignature(c.seq)!==originalOther)problems.push("OTHER_TRACK_CHANGED");
     if(c.target.clips.numItems!==i)problems.push("V3_NOT_RESTORED");
     fail("STOP "+a.id+": "+String(e)+
       (problems.length?" ROLLBACK_UNCERTAIN "+problems.join(","):""));
   }
   return ok("SUBTITLE_READBACK "+(i+1)+"/"+c.plan.totalItems,
     {token:token(c,i+1,t.base),done:i+1});
 });}
 function verify(file,raw){return safe(function(){
   var c=ctx(file),t=verifiedToken(c,raw);
   if(t.count!==c.plan.totalItems)fail("PARTIAL_CAPTION_SET");
   for(var i=0;i<c.plan.totalItems;i++)if(!matches(c.target.clips[i],c.plan.items[i]))
     fail("FINAL_CAPTION_READBACK "+c.plan.items[i].id);
   return ok("V3 CONFIRMAT: "+c.plan.totalItems+" subtitrări. Timing în CUT estimativ.",
     {count:c.plan.totalItems,sourceCuts:c.plan.subtitledCuts.length,
      omitted:c.plan.reservedCount,timing:c.plan.timing});
 });}
 function rollback(file,raw){return safe(function(){
   var c=ctx(file),t=verifiedToken(c,raw);
   for(var i=t.count-1;i>=0;i--){
     if(!matches(c.target.clips[i],c.plan.items[i]))fail("ROLLBACK_CLIP_IDENTITY_UNKNOWN");
     if(c.target.clips[i].remove(false,false)===false)fail("ROLLBACK_REMOVE_FAILED");
   }
   if(c.target.clips.numItems!==0)fail("ROLLBACK_V3_NOT_EMPTY");
   return ok("ROLLBACK PASS: propriile subtitrări eliminate; V1/A1 intacte.");
 }); }
 return {preflight:preflight,buildOne:buildOne,verify:verify,rollback:rollback};
})();
