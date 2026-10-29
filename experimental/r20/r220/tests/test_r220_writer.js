/* R2.2: synthetic Premiere ExtendScript writer dry-run, no real video or user data. */
'use strict';
const assert=require('assert');
const fs=require('fs'),vm=require('vm'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../cep/jsx/r220_montage_writer.jsx'),'utf8');
function mock(opts={}){

  const video=[],audio=[],markers=[],events=[];
  function collection(items){return new Proxy(items,{get(target,key){
    if(key==='numItems')return target.length;
    return target[key];
  }});}
  function markerCollection(){return {
    createMarker(sec){
      const m={start:{seconds:sec},name:'',comments:''};
      let endSec=sec;
      Object.defineProperty(m,'end',{get(){return {seconds:endSec}},
        set(v){endSec=Number(v)}});
      markers.push(m);events.push('marker-create');return m;
    },deleteMarker(m){let i=markers.indexOf(m);if(i<0)return false;markers.splice(i,1);events.push('marker-remove');return true;},
    getFirstMarker(){return markers[0]||null;},
    getNextMarker(m){return markers[markers.indexOf(m)+1]||null;}
  };}
  const item={
    name:'Original_9981.mov',nodeId:'NODE_9981',_in:opts.originalIn||0,_out:opts.originalOut||100,
    getInPoint(){return {seconds:this._in}},
    getOutPoint(){return {seconds:this._out}},
    setInPoint(n){
      if(typeof n!=='string' || !/^\d+$/.test(n))return -1;
      const value=Number(n)/254016000000;
      if(value>=this._out)return -1;
      if(opts.failIn && Math.abs(value-20)<.1)return -1;
      this._in=value;events.push('setIn');return opts.returnUndefined?undefined:0;
    },
    setOutPoint(n){
      if(typeof n!=='string' || !/^\d+$/.test(n))return -1;
      const value=Number(n)/254016000000;
      if(value<=this._in)return -1;
      this._out=value;events.push('setOut');return opts.returnUndefined?undefined:0;
    },
    clearInPoint(){this._in=0;events.push('clearIn');return 0},
    clearOutPoint(){this._out=100;events.push('clearOut');return 0},
    isOffline(){return false},isSequence(){return false},
  };
  const v={clips:collection(video),isLocked(){return false}},
        a={clips:collection(audio),isLocked(){return false}};
  let failure=false;
  let insertIndex=0;
  const seq={
    name:'Sequence copy [AIVE TEST]',sequenceID:'TEST_SEQ_03',
    videoTracks:collection([v]),audioTracks:collection([a]),markers:markerCollection(),
    overwriteClip(projectItem,start,vTrack,aTrack){
      insertIndex++;events.push('overwrite');
      if(failure && insertIndex===2)return false;
      const duration=projectItem._out-projectItem._in;
      for(const [tracks,type] of [[video,'video'],[audio,'audio']]){
        const clip={name:projectItem.name,start:{seconds:start},end:{seconds:start+duration},
          remove(ripple){assert.equal(ripple,false);events.push(type+'-remove');
            const ix=tracks.indexOf(clip);if(ix>=0)tracks.splice(ix,1);return 0;}};
        tracks.push(clip);
      }
      return true;
    }
  };
  const root={children:collection([item])};
  const app={project:{activeSequence:seq,rootItem:root}};
  const context=vm.createContext({app,Error,isFinite,Number,String,Object,JSON,Math});
  vm.runInContext(source,context,{timeout:2500});
  const api=context.AIVE_R220;
  const hash='a'.repeat(64);
  const plan={schema:'aive-r220-montage-plan-v1',phase:'ANALYSIS_ONLY',
     identity:{sequenceId:'TEST_SEQ_03',docxSHA256:'b'.repeat(64),diagnosticSHA256:'c'.repeat(64)},
     planSHA256:hash,approvalRequired:true,totalCuts:3,confirmedCount:2,placeholderCount:1,
     cuts:[
       {cutId:'CUT-01',sourceCode:'9981',sourceNodeId:'NODE_9981',
        sourceName:'Original_9981.mov',state:'CONFIRMED',
        sourceIn:10,sourceOut:15,timelineStart:0,timelineEnd:5,durationSeconds:5},
       {cutId:'CUT-02',sourceCode:'9931',state:'PLACEHOLDER',estimated:true,
        reason:'AUDIO_NOT_FOUND',timelineStart:5,timelineEnd:8,durationSeconds:3},
       {cutId:'CUT-03',sourceCode:'9981',sourceNodeId:'NODE_9981',
        sourceName:'Original_9981.mov',state:'CONFIRMED',
        sourceIn:20,sourceOut:24,timelineStart:8,timelineEnd:12,durationSeconds:4}
     ]};
  return {plan,api,seq,item,video,audio,markers,events,failSecond:()=>failure=true};
}
(function testSuccess(){
 const m=mock();
 const pre=m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS');
 assert.equal(pre.ok,true);assert.equal(pre.phase,'PREFLIGHT_ONLY');
 assert.equal(m.events.length,0,'preflight must never write');
 const actual=JSON.parse(m.api.commit(m.plan,'CONTINUE_WITH_PLACEHOLDERS',m.plan.planSHA256));
 assert.equal(actual.ok,true,JSON.stringify(actual));
 assert.deepEqual([...actual.confirmedClipIds],['CUT-01','CUT-03']);
 assert.deepEqual([...actual.placeholderMarkerIds],['CUT-02']);
 assert.equal(m.video.length,2);assert.equal(m.audio.length,2);assert.equal(m.markers.length,1);
 assert.equal(m.markers[0].name,'AIVE-R220 CUT-02 9931');
 assert.equal(m.markers[0].end.seconds,8);
 assert.equal(m.item._in,0);assert.equal(m.item._out,100);
})();
(function testApprovalAndOccupiedTracks(){
 const m=mock();
 assert.throws(()=>m.api.preflight(m.plan,'COMPLETE_AFTER_PREFLIGHT'),/EXPLICIT_APPROVAL_REQUIRED/);
 m.seq.name='Original Sequence';assert.throws(()=>m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS'),/COPY_REQUIRED/);
 m.seq.name='Sequence [AIVE TEST]';m.video.push({name:'Editor content'});
 assert.throws(()=>m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS'),/V1_A1_NOT_EMPTY/);
})();
(function testWrongIdentity(){
 const m=mock();m.plan.identity.sequenceId='NOT_THIS';
 assert.throws(()=>m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS'),/SEQUENCE_CHANGED/);
})();
(function testSourceMismatch(){
 const m=mock();m.plan.cuts[0].sourceNodeId='WRONG';
 assert.throws(()=>m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS'),/SOURCE_IDENTITY_INVALID/);
})();
(function testPlaceholderNeverUsesSourceInOut(){
 const m=mock();m.plan.cuts[1].sourceIn=2;
 assert.throws(()=>m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS'),/PLACEHOLDER_CANNOT_HAVE_SOURCE_IN_OUT/);
})();
(function testRollbackWhenSecondInsertFails(){
 const m=mock();m.failSecond();
 const output=JSON.parse(m.api.commit(m.plan,'CONTINUE_WITH_PLACEHOLDERS',m.plan.planSHA256));
 assert.equal(output.ok,false,JSON.stringify(output));
 assert.equal(output.phase,'ROLLED_BACK_OR_REVIEW');
 assert.equal(m.video.length,0);assert.equal(m.audio.length,0);assert.equal(m.markers.length,0);
 assert.equal(m.item._in,0);assert.equal(m.item._out,100);
 assert.equal(output.rollbackIssues.length,0);
})();
(function testPremiereNotTouchedAfterHashChanged(){
 const m=mock();
 assert.throws(()=>m.api.commit(m.plan,'CONTINUE_WITH_PLACEHOLDERS','WRONG'),/PLAN_HASH_NOT_APPROVED/);
 assert.equal(m.events.length,0);
})();
(function testRepeatedInvocationBlocked(){
 const m=mock();
 assert.equal(JSON.parse(m.api.commit(m.plan,'CONTINUE_WITH_PLACEHOLDERS',m.plan.planSHA256)).ok,true);
 assert.throws(()=>m.api.preflight(m.plan,'CONTINUE_WITH_PLACEHOLDERS'),/V1_A1_NOT_EMPTY/);
})();

// Premiere 2025 live reports SET_IN_FAILED CUT-03 (first confirmed CUT).
// Assert tick-string setters, original source trims, and readback, not just
// a setter return code. A failed readback must prevent any timeline write.
(function testRealPremiereTickStringsAndUndefinedSetterReturn(){
 const m=mock({returnUndefined:true,originalOut:11});
 const result=JSON.parse(m.api.commit(m.plan,'CONTINUE_WITH_PLACEHOLDERS',m.plan.planSHA256));
 assert.equal(result.ok,true,JSON.stringify(result));
 assert.equal(m.item._in,0);
 assert.equal(m.item._out,11,'restore original source out after a later cut');
 assert.equal(m.video.length,2);
 assert.equal(m.audio.length,2);
})();
(function testRealSetInFailureIsNotMistakenForSuccess(){
 const m=mock({failIn:true});
 const result=JSON.parse(m.api.commit(m.plan,'CONTINUE_WITH_PLACEHOLDERS',m.plan.planSHA256));
 assert.equal(result.ok,false,JSON.stringify(result));
 assert.match(result.error,/SET_IN_FAILED CUT-03/);
 assert.equal(m.video.length,0);
 assert.equal(m.audio.length,0);
 assert.equal(m.markers.length,0);
 assert.equal(m.item._in,0);
 assert.equal(m.item._out,100);
 assert.equal(result.rollbackIssues.length,0);
})();
console.log('PASS R2.2.5: 10 Premiere API mock tests, tick-string In/Out, source restoration, safe abort/readback');
