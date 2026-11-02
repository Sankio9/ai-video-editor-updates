'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(__dirname+'/../cep/jsx/r235_v5_clone.jsx','utf8');
function makeRuntime(opts={}){
  const calls={removedSource:0,removedClone:0,cloned:0};
  let active;
  function mkClip(name,start,end,kind='MOGRT',original=false){
    return {name,start:{seconds:start},end:{seconds:end},projectItem:{name,nodeId:'node_'+name},
      getMGTComponent(){return kind==='MOGRT'?{}:null},
      remove(){
        if(original){calls.removedSource++;throw Error('SOURCE_SHOULD_NEVER_BE_REMOVED');}
        calls.removedClone++;
        const a=this._owner;
        const k=a.indexOf(this);
        if(k<0)return false;
        a.splice(k,1);return 0;
      }};
  }
  function mkTrack(entries,isOriginal){
    const data=entries.map(x=>mkClip(...x,isOriginal));
    data.forEach(x=>x._owner=data);
    const clips={get numItems(){return data.length}};
    Object.defineProperty(clips,'_data',{value:data});
    for(let k=0;k<200;k++)Object.defineProperty(clips,k,{get:()=>data[k]});
    return {clips,isLocked(){return opts.locked===true}};
  }
  function mkSeq(id,name,orig){
    const video=[mkTrack([['scene',0,14,'VIDEO']],orig)];
    for(let i=1;i<4;i++)video.push(mkTrack([],orig));
    const originals=[['card1',0,6.52,'MOGRT'],['card2',6.52,12.90,'MOGRT'],
      ['card3',20.84,27.53,'MOGRT'],['card4',28.28,36.44,'MOGRT'],
      ['card5',37.20,43.19,'MOGRT'],['card6',43.20,49.05,opts.nonMogrt?'VIDEO':'MOGRT']];
    video.push(mkTrack(originals,orig));
    const audio=[mkTrack([['audio',0,14,'VIDEO']],orig)];
    video.numTracks=5;audio.numTracks=1;
    return {sequenceID:id,name,videoTracks:video,audioTracks:audio};
  }
  const original=mkSeq('ORIGINAL-01','Premiere Reportaj',true);
  const sequences=[original];
  const project={
    activeSequence:original,sequences:{get numSequences(){return sequences.length}},
    openSequence(id){
      const next=sequences.find(x=>x.sequenceID===id);
      if(!next)return false;
      active=next;this.activeSequence=next;return true;
    }};
  for(let i=0;i<100;i++)Object.defineProperty(project.sequences,i,{get:()=>sequences[i]});
  original.clone=function(){
    calls.cloned++;
    if(opts.noClone)return false;
    const copy=mkSeq('COPY-'+calls.cloned,original.name+' Copy',false);
    if(opts.mismatch)copy.videoTracks[4].clips[0].name='different';
    if(opts.externalMismatch)copy.videoTracks[0].clips[0].name='unexpected';
    sequences.push(copy);
    return true;
  };
  const F=function(p){
    return {exists:/.json$/i.test(p),encoding:'',open(mode){return mode==='r'},read(){
      return JSON.stringify({schema:'aive-r20-graphics-v1',mode:'independent',module:'04',
         items:[{id:'CAP-01'}],totalItems:1});},close(){}};
  };
  const ctx={app:{project},File:F,JSON,Error,Math,Number,String,isFinite,Array,$:{}};
  vm.runInNewContext(source,ctx);
  const inventory=original.videoTracks[4].clips._data.map(x=>({
      kind:x.getMGTComponent()?'MOGRT/GRAFICĂ':'ALT MATERIAL',
      name:x.name,start:x.start.seconds,end:x.end.seconds
  }));
  return {fn:ctx.$._AIVE_R235_V5_.prepare,calls,inventory,project,sequences,original};
}
function test(name,fn){fn();console.log('PASS '+name);}
test('explicit clone, 6 non-ripple removals on clone, original V5 and other tracks untouched',()=>{
  const r=makeRuntime();
  const before=r.original.videoTracks[4].clips.numItems;
  const beforeV1=r.original.videoTracks[0].clips[0].name;
  const out=JSON.parse(r.fn('D:/AI/plan.json',JSON.stringify(r.inventory)));
  assert(out.ok,out.message);
  assert.strictEqual(out.removed,6);
  assert.strictEqual(r.original.videoTracks[4].clips.numItems,before);
  assert.strictEqual(r.original.videoTracks[0].clips[0].name,beforeV1);
  assert.strictEqual(r.project.activeSequence.sequenceID,'COPY-1');
  assert.strictEqual(r.project.activeSequence.videoTracks[4].clips.numItems,0);
  assert.strictEqual(r.project.activeSequence.audioTracks[0].clips.numItems,1);
  assert.strictEqual(r.calls.removedSource,0);
  assert.strictEqual(r.calls.removedClone,6);
});
test('reject changed source inventory without touching sequence or making a clone',()=>{
  const r=makeRuntime();r.inventory[0].name='mismatched';
  const out=JSON.parse(r.fn('D:/AI/plan.json',JSON.stringify(r.inventory)));
  assert(!out.ok);assert.strictEqual(r.calls.cloned,0);
  assert.strictEqual(r.calls.removedSource,0);
});
test('refuse non-MOGRT material on V5 even on clone',()=>{
  const r=makeRuntime({nonMogrt:true});
  const out=JSON.parse(r.fn('D:/AI/plan.json',JSON.stringify(r.inventory)));
  assert(!out.ok);assert.strictEqual(r.calls.cloned,0);assert.strictEqual(r.calls.removedSource,0);
});
test('clone data mismatch fails closed before any clip removal',()=>{
  const r=makeRuntime({mismatch:true});
  const out=JSON.parse(r.fn('D:/AI/plan.json',JSON.stringify(r.inventory)));
  assert(!out.ok);assert.strictEqual(r.calls.removedClone,0);assert.strictEqual(r.calls.removedSource,0);
  assert.strictEqual(r.original.videoTracks[4].clips.numItems,6);
});
test('cannot duplicate source: no deletion or sequence switching',()=>{
  const r=makeRuntime({noClone:true});
  const out=JSON.parse(r.fn('D:/AI/plan.json',JSON.stringify(r.inventory)));
  assert(!out.ok);assert.strictEqual(r.calls.removedClone,0);assert.strictEqual(r.calls.removedSource,0);
  assert.strictEqual(r.project.activeSequence.sequenceID,'ORIGINAL-01');
});
test('other tracks on clone changed: abort before delete',()=>{
  const r=makeRuntime({externalMismatch:true});
  const out=JSON.parse(r.fn('D:/AI/plan.json',JSON.stringify(r.inventory)));
  assert(!out.ok);assert.strictEqual(r.calls.removedClone,0);
});
console.log('R235 mock Premiere tests: guarded clone-only V5 replace PASS');
