/* R2.2.7: read-only LIVE Premiere R220 montage recovery.
 * Recovers POST_READBACK only when every approved CONFIRMED clip
 * and every PLACEHOLDER marker is still exactly at the planned range.
 * Does not write to Premiere or use QE; never infers match from TC.
 */
var AIVE_R227_RECOVERY=(function(){
 function fail(s){throw Error(s);}
 function str(x){return String(x===null||x===undefined?"":x);}
 function finite(x){return typeof x==="number"&&isFinite(x);}
 function close(a,b){return finite(Number(a))&&finite(Number(b))&&Math.abs(Number(a)-Number(b))<=0.08;}
 function active(){if(!app||!app.project||!app.project.activeSequence)fail("SEQUENCE_NOT_ACTIVE");
   return app.project.activeSequence;}
 function identity(){
  var s=active(),count=0,marker=s.markers&&s.markers.getFirstMarker();
  while(marker){
   if(str(marker.name).indexOf("AIVE-R220 ")===0)count++;
   if(count>2500)fail("R220_MARKER_LOOP");
   marker=s.markers.getNextMarker(marker);
  }
  return JSON.stringify({ok:true,sequenceId:str(s.sequenceID||s.id),
    name:str(s.name),r220Markers:count});
 }
 function clipMatch(clip,row){
  if(!close(clip.start.seconds,row.timelineStart)||
     !close(clip.end.seconds,row.timelineEnd))return false;
  var original=clip.projectItem;
  if(str(clip.name)!==str(row.sourceName) &&
     str(original&&original.name)!==str(row.sourceName))return false;
  if(original&&original.nodeId&&str(original.nodeId)!==str(row.sourceNodeId))return false;
  return true;
 }
 function check(plan){
  var s=active();
  if(!plan||plan.schema!=="aive-r220-montage-plan-v1"||
     plan.phase!=="ANALYSIS_ONLY"||!plan.identity||
     !/^[a-f0-9]{64}$/.test(str(plan.planSHA256))||
     !plan.cuts||!plan.cuts.length)fail("R220_PLAN_INVALID");
  if(str(s.sequenceID||s.id)!==str(plan.identity.sequenceId)||
     str(s.name).indexOf("[AIVE TEST]")<0)fail("R220_SEQUENCE_IDENTITY_MISMATCH");
  if(!s.videoTracks||!s.audioTracks||s.videoTracks.numTracks<1||
     s.audioTracks.numTracks<1)fail("R220_TRACK_MISSING");
  var v=s.videoTracks[0],a=s.audioTracks[0],matched=[],reserved=[];
  if(v.clips.numItems!==plan.confirmedCount||a.clips.numItems!==plan.confirmedCount)
     fail("R220_READBACK_CLIP_COUNT_MISMATCH");
  var seen={},vIdx={},aIdx={},markIDs={};
  for(var i=0;i<plan.cuts.length;i++){
    var row=plan.cuts[i],id=str(row.cutId);
    if(seen[id])fail("R220_DUPLICATE_CUT");seen[id]=true;
    if(!finite(row.timelineStart)||!finite(row.timelineEnd)||
       row.timelineEnd<=row.timelineStart)fail("R220_RANGE_INVALID");
    if(row.state==="CONFIRMED"){
      if(!row.sourceName||!row.sourceNodeId)fail("R220_SOURCE_ID_MISSING "+id);
      var vHit=-1,aHit=-1;
      for(var j=0;j<v.clips.numItems;j++)if(clipMatch(v.clips[j],row)){
        if(vHit!==-1)fail("R220_MULTIPLE_VIDEO_CLIPS "+id);vHit=j;
      }
      for(var k=0;k<a.clips.numItems;k++)if(clipMatch(a.clips[k],row)){
        if(aHit!==-1)fail("R220_MULTIPLE_AUDIO_CLIPS "+id);aHit=k;
      }
      if(vHit<0||aHit<0||vIdx[vHit]||aIdx[aHit])
        fail("R220_LIVE_CLIP_READBACK_FAIL "+id);
      vIdx[vHit]=1;aIdx[aHit]=1;matched.push(id);
    }else if(row.state==="PLACEHOLDER"){
      if(row.sourceIn!==undefined||row.sourceOut!==undefined)
        fail("R220_PLACEHOLDER_SOURCE_BOUNDS_FORBIDDEN "+id);
      var marker=s.markers&&s.markers.getFirstMarker(),found=0;
      while(marker){
        if(str(marker.name).indexOf("AIVE-R220 "+id+" "+str(row.sourceCode))===0 &&
           close(marker.start.seconds,row.timelineStart)&&marker.end &&
           close(marker.end.seconds,row.timelineEnd)){found++;}
        marker=s.markers.getNextMarker(marker);
      }
      if(found!==1)fail("R220_MISSING_INTERVAL_MARKER "+id);
      markIDs[id]=true;reserved.push(id);
    }else if(row.state!=="VO_RESERVE")fail("R220_UNKNOWN_STATE "+id);
  }
  if(matched.length!==plan.confirmedCount||reserved.length!==plan.placeholderCount||
     plan.totalCuts!==plan.confirmedCount+plan.placeholderCount)
     fail("R220_PLAN_TOTALS_INVALID");
  // No extra R220 markers: an old/partial run must not be accepted.
  var m=s.markers&&s.markers.getFirstMarker(),n=0;
  while(m){if(str(m.name).indexOf("AIVE-R220 ")===0)n++;
    if(n>2500)fail("R220_TOO_MANY_MARKERS");
    m=s.markers.getNextMarker(m);
  }
  if(n!==reserved.length)fail("R220_EXTRA_MARKER_OR_COUNT_CHANGED");
  return {ok:true,phase:"RECOVERED_FROM_LIVE_PREMIERE_READBACK",
    sequenceId:str(s.sequenceID||s.id),planSHA256:plan.planSHA256,
    confirmedClipIds:matched,placeholderMarkerIds:reserved};
 }
 function recover(json){
  try{var p=typeof json==="string"?JSON.parse(json):json;return JSON.stringify(check(p));}
  catch(e){return JSON.stringify({ok:false,message:str(e&&e.message||e)});}
 }
 return {identity:identity,recover:recover};
})();