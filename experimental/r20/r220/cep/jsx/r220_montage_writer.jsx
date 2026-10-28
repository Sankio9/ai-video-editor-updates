/* R2.2 experimental Premiere ExtendScript writer, ES3-compatible.
 * NEVER call directly from an unverified plan. Initial live gate:
 * only an explicitly named [AIVE TEST] sequence with empty V1/A1.
 * No QE, no track creation, no ripple, no default overwrite on user clips.
 */
var AIVE_R220 = (function(){
  function number(x){return typeof x==="number" && isFinite(x);}
  function fail(message){throw Error(message);}
  function close(a,b){return Math.abs(Number(a)-Number(b))<=0.08;}
  function seq(){
    if(!app||!app.project||!app.project.activeSequence)fail("SEQUENCE_NOT_ACTIVE");
    return app.project.activeSequence;
  }
  function identity(s){return String(s.sequenceID||s.id||"");}
  function trackOK(s){
    if(s.videoTracks.numTracks<1||s.audioTracks.numTracks<1)fail("V1_A1_TRACK_MISSING");
    var v=s.videoTracks[0],a=s.audioTracks[0];
    if(v.isLocked()||a.isLocked())fail("V1_A1_LOCKED");
    if(v.clips.numItems!==0||a.clips.numItems!==0)fail("V1_A1_NOT_EMPTY");
  }
  function scan(item,found){
    if(!item)return;
    if(item.type===2 || item.type==="Bin"){
      var children=item.children||[];
      for(var i=0;i<children.numItems;i++)scan(children[i],found);
      return;
    }
    if(item.nodeId)found[String(item.nodeId)]=item;
  }
  function index(){
    var found={};scan(app.project.rootItem,found);return found;
  }
  function checkPlan(s,plan,choice){
    if(!plan||plan.schema!=="aive-r220-montage-plan-v1"||
       plan.phase!=="ANALYSIS_ONLY"||!plan.identity||
       !plan.planSHA256||String(plan.planSHA256).length!==64)fail("PLAN_INVALID");
    if(identity(s)!==plan.identity.sequenceId)fail("SEQUENCE_CHANGED");
    if(String(s.name).indexOf("[AIVE TEST]")<0)fail("COPY_REQUIRED: rename a separate TEST sequence to [AIVE TEST]");
    if(!plan.cuts||plan.cuts.length!==plan.totalCuts ||
       plan.totalCuts>2000||!plan.totalCuts)fail("CUT_COUNT_INVALID");
    if(choice!==(plan.approvalRequired?"CONTINUE_WITH_PLACEHOLDERS":"COMPLETE_AFTER_PREFLIGHT"))
       fail("EXPLICIT_APPROVAL_REQUIRED");
    trackOK(s);
    if(s.markers){
      var m=s.markers.getFirstMarker();
      while(m){if(String(m.name).indexOf("AIVE-R220")>=0)fail("AIVE_MARKERS_ALREADY_PRESENT");
        m=s.markers.getNextMarker(m);}
    }
  }
  function validateSources(plan,byId){
    var seen={},previous=0,clipCount=0,slotCount=0,selected={};
    for(var i=0;i<plan.cuts.length;i++){
      var c=plan.cuts[i];
      if(!c||!/^CUT-[0-9]{1,4}$/.test(c.cutId)||seen[c.cutId])fail("CUT_DUPLICATE");
      seen[c.cutId]=1;
      if(!number(c.timelineStart)||!number(c.timelineEnd)||
         !number(c.durationSeconds)||c.timelineEnd<=c.timelineStart||
         c.durationSeconds<=0||!close(c.timelineStart,previous) ||
         !close(c.timelineEnd-c.timelineStart,c.durationSeconds))
          fail("TIMELINE_RANGE_INVALID "+c.cutId);
      previous=c.timelineEnd;
      if(c.state==="PLACEHOLDER"){
        if(c.sourceIn!==undefined||c.sourceOut!==undefined||
           !c.reason||!c.estimated)fail("PLACEHOLDER_CANNOT_HAVE_SOURCE_IN_OUT");
        slotCount++;
      }else if(c.state==="CONFIRMED"){
        if(!number(c.sourceIn)||!number(c.sourceOut)||c.sourceIn<0||
           c.sourceOut<=c.sourceIn||!close(c.sourceOut-c.sourceIn,c.durationSeconds))
            fail("SOURCE_RANGE_INVALID");
        var item=byId[String(c.sourceNodeId||"")];
        if(!item || String(item.name)!==String(c.sourceName)||
           item.isOffline() || item.isSequence())fail("SOURCE_IDENTITY_INVALID "+c.cutId);
        if(selected[c.cutId])fail("SOURCE_CONFLICT");selected[c.cutId]=item;clipCount++;
      }else fail("UNKNOWN_CUT_STATE");
    }
    if(clipCount!==plan.confirmedCount||slotCount!==plan.placeholderCount)
       fail("COUNT_INTEGRITY_ERROR");
    return selected;
  }
  function preflight(planJson,choice){
    var plan=typeof planJson==="string"?JSON.parse(planJson):planJson;
    var s=seq();checkPlan(s,plan,choice);
    var selected=validateSources(plan,index());
    return {ok:true,phase:"PREFLIGHT_ONLY",sequenceId:identity(s),
            totalCuts:plan.totalCuts,confirmed:plan.confirmedCount,
            placeholders:plan.placeholderCount,planSHA256:plan.planSHA256,
            targetCount:Object.keys?Object.keys(selected).length:plan.confirmedCount};
  }
  function findClip(track,start,name){
    var matches=[];
    for(var i=0;i<track.clips.numItems;i++){
      var c=track.clips[i];
      if(close(c.start.seconds,start) && String(c.name)===String(name))matches.push(c);
    }
    return matches.length===1?matches[0]:null;
  }
  function restoreItem(item,oldIn,oldOut){
    try {
      if(oldIn!==null)item.setInPoint(oldIn,4);
      else item.clearInPoint();
      if(oldOut!==null)item.setOutPoint(oldOut,4);
      else item.clearOutPoint();
    }catch(e){fail("SOURCE_IN_OUT_RESTORE_FAILED "+String(e));}
  }
  function insert(s,item,c){
    // Source In/Out is modified temporarily; restore it in all paths.
    var previousIn=item.getInPoint(),previousOut=item.getOutPoint();
    var oldIn=previousIn&&number(previousIn.seconds)?previousIn.seconds:null;
    var oldOut=previousOut&&number(previousOut.seconds)?previousOut.seconds:null;
    try{
      if(item.setInPoint(c.sourceIn,4)!==0)fail("SET_IN_FAILED "+c.cutId);
      if(item.setOutPoint(c.sourceOut,4)!==0)fail("SET_OUT_FAILED "+c.cutId);
      if(s.overwriteClip(item,c.timelineStart,0,0)!==true)
         fail("OVERWRITE_FAILED "+c.cutId);
    }finally{restoreItem(item,oldIn,oldOut);}
    var v=findClip(s.videoTracks[0],c.timelineStart,c.sourceName);
    var a=findClip(s.audioTracks[0],c.timelineStart,c.sourceName);
    if(!v||!a||!close(v.end.seconds,c.timelineEnd)||
       !close(a.end.seconds,c.timelineEnd))fail("CLIP_READBACK_FAIL "+c.cutId);
    return {video:v,audio:a,cutId:c.cutId};
  }
  function marker(s,c){
    if(!s.markers)fail("MARKERS_NOT_SUPPORTED");
    var created=s.markers.createMarker(c.timelineStart);
    if(!created)fail("MARKER_CREATE_FAILED "+c.cutId);
    created.name="AIVE-R220 "+c.cutId+" "+c.sourceCode;
    created.comments="AUDIO NECONFIRMAT | "+c.reason+" | DURATA ESTIMATA "+c.durationSeconds+"s";
    created.end=c.timelineEnd; // documented marker.end: assign seconds, not Time object
    if(!close(created.start.seconds,c.timelineStart) ||
       String(created.name).indexOf(c.cutId)<0)
       fail("MARKER_READBACK_FAIL "+c.cutId);
    return created;
  }
  function rollback(s,inserts,markers){
    var errors=[];
    for(var i=markers.length-1;i>=0;i--){
      try{if(!s.markers.deleteMarker(markers[i]))errors.push("marker");}
      catch(e){errors.push("marker:"+String(e));}
    }
    for(var j=inserts.length-1;j>=0;j--){
      var c=inserts[j];
      try{if(c.audio)c.audio.remove(false,false);}catch(e){errors.push("audio:"+c.cutId);}
      try{if(c.video)c.video.remove(false,false);}catch(e){errors.push("video:"+c.cutId);}
    }
    return errors;
  }
  function commit(planJson,choice,explicitPlanSHA){
    var plan=typeof planJson==="string"?JSON.parse(planJson):planJson;
    if(plan.planSHA256!==explicitPlanSHA)fail("PLAN_HASH_NOT_APPROVED");
    var verified=preflight(plan,choice),s=seq(),byId=index(),sources=validateSources(plan,byId);
    var added=[],markers=[],resultIds=[],markerIds=[];
    try{
      for(var i=0;i<plan.cuts.length;i++){
        if(identity(seq())!==verified.sequenceId)fail("SEQUENCE_SWITCHED_DURING_INSERT");
        var row=plan.cuts[i];
        if(row.state==="CONFIRMED"){
          var item=insert(s,sources[row.cutId],row);added.push(item);
          resultIds.push(row.cutId);
        }else{
          var m=marker(s,row);markers.push(m);markerIds.push(row.cutId);
        }
      }
      if(s.videoTracks[0].clips.numItems!==plan.confirmedCount||
         s.audioTracks[0].clips.numItems!==plan.confirmedCount ||
         markers.length!==plan.placeholderCount)
         fail("FINAL_READBACK_COUNT_MISMATCH");
      return JSON.stringify({ok:true,phase:"PREMIERE_READBACK",sequenceId:verified.sequenceId,
        planSHA256:plan.planSHA256,confirmedClipIds:resultIds,placeholderMarkerIds:markerIds,
        confirmedCount:resultIds.length,placeholderCount:markerIds.length});
    }catch(e){
      var problems=rollback(s,added,markers);
      return JSON.stringify({ok:false,phase:"ROLLED_BACK_OR_REVIEW",error:String(e),
        rollbackIssues:problems,planSHA256:plan.planSHA256});
    }
  }
  return {preflight:preflight,commit:commit};
})();
