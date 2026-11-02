/* R226 isolated JSX host mock. No actual Premiere calls. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const code=fs.readFileSync(path.join(__dirname,'../cep/jsx/r226_partial_subtitles.jsx'),'utf8');
function collection(values){Object.defineProperty(values,'numItems',{get(){return values.length}});return values;}
function fakeComp(){
 const props={};
 for(const k of ['Text'])props[k]=value(JSON.stringify({textEditValue:'',fontTextRunLength:[0]}));
 for(const k of ['Font Style','Aspect Ratio'])props[k]=value(0);
 return {properties:{getParamForDisplayName(k){return props[k]||null;}}};
}
function value(v){let stored=v;return {getValue:()=>stored,setValue(x){stored=x;return true}};}
function setup(opts={}){
 const video=Array.from({length:6},()=>({clips:collection([]),isLocked(){return false}}));
 const audio=Array.from({length:2},()=>({clips:collection([]),isLocked(){return false}}));
 video.numTracks=6;audio.numTracks=2;
 const cuts=[
  {cutId:'CUT-01',sourceCode:'9981',sourceName:'Original_9981.mov',sourceNodeId:'N1',timelineStart:2,timelineEnd:7},
  {cutId:'CUT-03',sourceCode:'9981',sourceName:'Original_9981.mov',sourceNodeId:'N1',timelineStart:14,timelineEnd:19}];
 const slots=[{cutId:'CUT-02',sourceCode:'9931',timelineStart:7,timelineEnd:14}];
 const one={name:'Original_9981.mov',projectItem:{name:'Original_9981.mov',nodeId:'N1'}};
 for(const c of cuts)for(const track of [video[0],audio[0]])
   track.clips.push({...one,start:{seconds:c.timelineStart},end:{seconds:c.timelineEnd}});
 const ms=[{name:'AIVE-R220 CUT-02 9931',start:{seconds:7},end:{seconds:14}}];
 const markers={getFirstMarker:()=>ms[0]||null,getNextMarker:(m)=>ms[ms.indexOf(m)+1]||null};
 const seq={name:'Copy [AIVE TEST]',sequenceID:'ABC_SEQ',videoTracks:video,audioTracks:audio,markers,
  importMGT(p,ticks,index){
   const st=Number(ticks)/254016000000,comp=fakeComp();
   const clip={name:'Graphic',projectItem:null,start:{seconds:st},end:{seconds:st+5},
    getMGTComponent:()=>comp,
    remove(){const arr=video[index].clips,idx=arr.indexOf(clip);if(idx>=0)arr.splice(idx,1);return true;}};
   video[index].clips.push(clip);
   return clip;
  }};
 const p={schema:'aive-r226-partial-subs-v1',module:'02',mode:'montage_partial',
  timing:'CUT_ALIGNED_ESTIMATED',docx_sha256:'a'.repeat(64),
  montagePlanSHA256:'b'.repeat(64),contentSHA256:'c'.repeat(64),
  sequenceId:'ABC_SEQ',confirmedCount:2,reservedCount:1,confirmedCuts:cuts,
  reservedCuts:slots,totalItems:2,subtitledCuts:['CUT-01','CUT-03'],
  items:[{id:'R226-0001',groupId:'CUT-01',sourceCode:'9981',text:'Salutare.',
           fontStyle:'Regular',timingKind:'CUT_ALIGNED_ESTIMATED',startSeconds:2,durationSeconds:5},
         {id:'R226-0002',groupId:'CUT-03',sourceCode:'9981',text:'Bună ziua.',
           fontStyle:'Italic',timingKind:'CUT_ALIGNED_ESTIMATED',startSeconds:14,durationSeconds:5}]};
 const files={'R226_PLAN.json':JSON.stringify(p)};
 function File(s){if(!(this instanceof File))return new File(s);this.exists=s in files||s.includes('Templates/');
   this.fsName=s;this.modified='2026-10-29';this.encoding='UTF-8';
   this.open=()=>true;this.read=()=>files[s];this.close=()=>true;}
 function Time(){let sec=0;Object.defineProperty(this,'seconds',{set(v){sec=v},get(){return sec}});
   Object.defineProperty(this,'ticks',{get(){return String(sec*254016000000)}});}
 const context={app:{project:{activeSequence:seq}},JSON,File,Time,String,Number,Math,Error,RegExp,Object,
  isFinite,Array};
 vm.runInNewContext(code,context,{timeout:2000});
 const api=context.$._AIVE_R226_;
 return {video,audio,seq,markers,ms,files,p,api,call:(fn,...args)=>JSON.parse(api[fn](...args))};
}
let count=0;
function test(label,fn){try{fn();console.log('PASS',label);count++}catch(e){console.error('FAIL',label,e);process.exitCode=1}}
test('Full preflight, two captions readback with ten-second gap',()=>{
 const s=setup(),pre=s.call('preflight','R226_PLAN.json');assert.equal(pre.ok,true,JSON.stringify(pre));
 let tok=pre.token;
 tok=s.call('buildOne','R226_PLAN.json',tok,0).token;
 tok=s.call('buildOne','R226_PLAN.json',tok,1).token;
 const end=s.call('verify','R226_PLAN.json',tok);assert.equal(end.ok,true,JSON.stringify(end));
 assert.equal(s.video[2].clips.length,2);assert.equal(s.video[0].clips.length,2);
 assert.equal(s.audio[0].clips.length,2);
 assert.equal(s.video[2].clips[0].start.seconds,2);
 assert.equal(s.video[2].clips[1].start.seconds,14);
});
test('No V3 overwrite if occupied',()=>{const s=setup();s.video[2].clips.push({});
 assert.equal(s.call('preflight','R226_PLAN.json').ok,false);});
test('Missing placeholder marker blocks',()=>{const s=setup();s.ms[0].end.seconds=16;
 assert.match(s.call('preflight','R226_PLAN.json').message,/R220_MARKER_CHANGED/);});
test('Changed V1 clip blocks',()=>{const s=setup();s.video[0].clips[0].start.seconds=3;
 assert.match(s.call('preflight','R226_PLAN.json').message,/R220_CLIP_READBACK_CHANGED/);});
test('Changed V1 after preflight blocks insert',()=>{const s=setup(),p=s.call('preflight','R226_PLAN.json');
 s.video[0].clips[0].name='mutated';
 assert.equal(s.call('buildOne','R226_PLAN.json',p.token,0).ok,false);
 assert.equal(s.video[2].clips.length,0);});
test('Wrong sequence blocks',()=>{const s=setup();s.seq.sequenceID='ABC_OTHER';
 assert.equal(s.call('preflight','R226_PLAN.json').ok,false);});
test('Unconfirmed CUT outside bound blocks',()=>{const s=setup();
 s.p.items[0].groupId='CUT-02';s.files['R226_PLAN.json']=JSON.stringify(s.p);
 assert.equal(s.call('preflight','R226_PLAN.json').ok,false);});
test('No pretend full speech sync',()=>{const s=setup();s.p.timing='SYNCED';
 s.files['R226_PLAN.json']=JSON.stringify(s.p);assert.equal(s.call('preflight','R226_PLAN.json').ok,false);});
test('Partial own rollback clears V3 only',()=>{const s=setup();let t=s.call('preflight','R226_PLAN.json').token;
 t=s.call('buildOne','R226_PLAN.json',t,0).token;
 const r=s.call('rollback','R226_PLAN.json',t);assert.equal(r.ok,true,JSON.stringify(r));
 assert.equal(s.video[2].clips.length,0);assert.equal(s.video[0].clips.length,2);});
test('Mutation before rollback refuses unsafe deletion',()=>{const s=setup();let t=s.call('preflight','R226_PLAN.json').token;
 t=s.call('buildOne','R226_PLAN.json',t,0).token;
 s.video[0].clips[0].start.seconds=2.3;
 assert.equal(s.call('rollback','R226_PLAN.json',t).ok,false);});
console.log('R226 mock tests',count,'PASS; LIVE Premiere still required');
