'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(path.join(__dirname,'../cep/jsx/r227_montage_recovery.jsx'),'utf8');
function mock(){
 const clip=(name,start,end)=>({name,projectItem:{name,nodeId:'N1'},
   start:{seconds:start},end:{seconds:end}});
 const video=[clip('Original.mov',4,9),clip('Original.mov',17,22)];
 const audio=[clip('Original.mov',4,9),clip('Original.mov',17,22)];
 const raw=[
  {name:'AIVE-R220 CUT-02 9931',start:{seconds:9},end:{seconds:17}}
 ];
 function coll(items){Object.defineProperty(items,'numItems',{get:()=>items.length});return items;}
 const marks={getFirstMarker:()=>raw[0]||null,getNextMarker:m=>raw[raw.indexOf(m)+1]||null};
 const seq={name:'Bubuieci [AIVE TEST]',sequenceID:'SEQ-READBACK',
   markers:marks,videoTracks:coll([{clips:coll(video)}]),
   audioTracks:coll([{clips:coll(audio)}])};
 seq.videoTracks.numTracks=1;seq.audioTracks.numTracks=1;
 const plan={schema:'aive-r220-montage-plan-v1',phase:'ANALYSIS_ONLY',
   identity:{sequenceId:'SEQ-READBACK',docxSHA256:'a'.repeat(64)},
   planSHA256:'b'.repeat(64),totalCuts:3,confirmedCount:2,placeholderCount:1,
   cuts:[
    {cutId:'CUT-01',sourceName:'Original.mov',sourceNodeId:'N1',sourceCode:'9981',
      state:'CONFIRMED',timelineStart:4,timelineEnd:9,sourceIn:12,sourceOut:17},
    {cutId:'CUT-02',sourceCode:'9931',state:'PLACEHOLDER',
      timelineStart:9,timelineEnd:17,estimated:true,reason:'ASR_WEAK_BOUNDARY'},
    {cutId:'CUT-03',sourceName:'Original.mov',sourceNodeId:'N1',sourceCode:'9981',
      state:'CONFIRMED',timelineStart:17,timelineEnd:22,sourceIn:30,sourceOut:35}
   ]};
 const context={app:{project:{activeSequence:seq}},Error,JSON,String,Number,Math,isFinite};
 vm.runInNewContext(source,context,{timeout:2500});
 const api=context.AIVE_R227_RECOVERY;
 return {seq,plan,raw,video,audio,api,check:()=>JSON.parse(api.recover(plan))};
}
function test(name,fn){try{fn();console.log('PASS '+name)}
catch(e){console.error('FAIL '+name,e);process.exitCode=1}}
test('read-only recovered 2 confirmed plus 1 reserved',()=>{
 const x=mock(),before=JSON.stringify({v:x.video,a:x.audio,m:x.raw});
 const result=x.check();
 assert.equal(result.ok,true,JSON.stringify(result));
 assert.deepEqual(Array.from(result.confirmedClipIds),['CUT-01','CUT-03']);
 assert.deepEqual(Array.from(result.placeholderMarkerIds),['CUT-02']);
 assert.equal(x.api.identity().indexOf('"r220Markers":1')>0,true);
 assert.equal(JSON.stringify({v:x.video,a:x.audio,m:x.raw}),before);
});
test('changed V1 clip stops',()=>{const x=mock();x.video[0].start.seconds=5;
 assert.match(x.check().message,/LIVE_CLIP_READBACK_FAIL/);});
test('changed A1 clip stops',()=>{const x=mock();x.audio[0].end.seconds=8;
 assert.match(x.check().message,/LIVE_CLIP_READBACK_FAIL/);});
test('missing marker stops',()=>{const x=mock();x.raw.pop();
 assert.match(x.check().message,/MISSING_INTERVAL_MARKER/);});
test('changed marker duration stops',()=>{const x=mock();x.raw[0].end.seconds=18;
 assert.match(x.check().message,/MISSING_INTERVAL_MARKER/);});
test('extra marker stops',()=>{const x=mock();x.raw.push({
 name:'AIVE-R220 CUT-44 9974',start:{seconds:55},end:{seconds:60}});
 assert.match(x.check().message,/EXTRA_MARKER/);});
test('wrong sequence stops',()=>{const x=mock();x.seq.sequenceID='OTHER';
 assert.match(x.check().message,/SEQUENCE_IDENTITY_MISMATCH/);});
test('source nodeId conflict stops',()=>{const x=mock();x.video[0].projectItem.nodeId='DIFFERENT';
 assert.match(x.check().message,/LIVE_CLIP_READBACK_FAIL/);});
test('no reporter timecode fallback ever used',()=>{const x=mock();
 x.plan.cuts[1].sourceIn=10;
 assert.match(x.check().message,/PLACEHOLDER_SOURCE_BOUNDS_FORBIDDEN/);});
test('V1 extra clip stops, no deletion',()=>{const x=mock();x.video.push({});
 assert.match(x.check().message,/CLIP_COUNT_MISMATCH/);assert.equal(x.video.length,3);});
console.log('R227 recovery mocks done, LIVE Premiere verification pending.');
