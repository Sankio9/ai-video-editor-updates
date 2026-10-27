/* Mocked Premiere API regression: not a claim of live Adobe validation. */
const fs=require('fs'), vm=require('vm'),assert=require('assert');
const SCRIPT=fs.readFileSync(require('path').join(__dirname,'../cep/jsx/r20_graphics.jsx'),'utf8');
const SHA='a'.repeat(64);
function item(id,group,start,dur,text,extras={}){return Object.assign({id,groupId:group,startSeconds:start,durationSeconds:dur,text},extras);}
function plan(module,items){return {schema:'aive-r20-graphics-v1',module,mode:'independent',timing:module==='02'?'SCRIPT_PREVIEW':'EDITORIAL_PREVIEW',docx_sha256:SHA,separatorSeconds:.75,totalItems:items.length,items};}
function track(locked=false){const clips=[];Object.defineProperty(clips,'numItems',{get(){return clips.length}});return {clips,isLocked(){return locked}};}
function pref(v){let value=v;return {getValue(){return value},setValue(x){value=x;return true}};}
function fakeComp(){const dictionary={};for(const p of ['Text','Name','2 LINES TITLE','Text Line 0','Text Line 1,2,3','Line 0 Bold Words','Line 1 Bold Words','Line 2 Bold Words','Line 3 Bold Words'])dictionary[p]=pref(JSON.stringify({textEditValue:'',fontTextRunLength:[0]}));
 for(const p of ['Font Style','Aspect Ratio','SubsShift','Color Scheme'])dictionary[p]=pref(0);
 return {properties:{getParamForDisplayName(p){return dictionary[p]||null;}}};}
function createRunner(data,opts={}){
  let target=opts.target||({02:2,03:3,04:4})[data.module];
  const video=Array.from({length:opts.trackCount===undefined?6:opts.trackCount},()=>track());video.numTracks=video.length;
  const audio=Array.from({length:2},()=>track());audio.numTracks=audio.length;
  const seq={name:'UnitTest',sequenceID:'sequence-a',videoTracks:video,audioTracks:audio,
    importMGT(path,ticks,index){let start=Number(ticks)/254016000000;
      const comp=fakeComp(),clip={name:'Mock MOGRT',projectItem:null,start:{seconds:start},end:{seconds:start+5},
        getMGTComponent(){return comp},remove(){const a=video[index].clips,ix=a.indexOf(clip);if(ix>=0)a.splice(ix,1);return true}};
      video[index].clips.push(clip);return clip;
    }
  };
  function File(p){if(!(this instanceof File))return new File(p);this.fsName=p;this.exists=(p in files)||p.includes('Templates/');this.modified=new Date('2026-10-27T12:00:00Z').toString();this.open=()=>true;this.read=()=>files[p];this.close=()=>true;}
  const files={'R20_PLAN.json':JSON.stringify(data)};
  function Time(){let secs=0;Object.defineProperty(this,'seconds',{set(x){secs=x},get(){return secs}});Object.defineProperty(this,'ticks',{get(){return ''+(secs*254016000000)}});}
  const context={$:{},app:{project:{activeSequence:seq}},File,Time,JSON,Array,String,Number,Math,isFinite,Error,RegExp};
  vm.runInNewContext(SCRIPT,context);
  const api=context.$._AIVE_R20_;
  function call(method,...args){const out=JSON.parse(api[method](...args));return out;}
  return {seq,call,video,audio,files,api,target};
}
function foreign(start,end,name='Existing video'){const component=fakeComp();return {name,start:{seconds:start},end:{seconds:end},getMGTComponent(){return null}};}
function ok(r){assert.equal(r.ok,true,JSON.stringify(r));return r;}
let passed=0;
function test(name,fn){try{fn();passed++;console.log('LOCAL PASS',name)}catch(e){console.error('FAIL',name,e);process.exitCode=1}}
function subPlan(){return plan('02',[item('s1','a',0,2,'Școala Ștefănești',{fontStyle:'Regular'}),item('s2','b',2.75,3,'Elevi și profesori',{fontStyle:'Italic'})]);}
function capsPlan(){let slots=['','TEST','CARTON','ȘCOALĂ'];return plan('04',[item('c1','vo1',0,3,'TEST CARTON ȘCOALĂ',
  {physicalLines:slots,textLine0:slots[0],textLines123:slots.slice(1).join('\r'),boldWords:{'0':'','1':'','2':'1','3':''},colorScheme:'Orange'})]);}
test('02 standalone inserts, token refresh, MOGRT readback, no V1/A1',()=>{
 const r=createRunner(subPlan()),start=ok(r.call('validate','R20_PLAN.json','zero'));
 let tok=start.token;for(let i=0;i<2;i++)tok=ok(r.call('buildOne','R20_PLAN.json',tok,i)).token;
 assert.match(ok(r.call('verify','R20_PLAN.json',tok)).message,/SCRIPT_PREVIEW/);
 assert.equal(r.video[0].clips.numItems,0);assert.equal(r.audio[0].clips.numItems,0);
});
test('03 standalone name + Unicode readback',()=>{
 const p=plan('03',[item('n1','new',0,4,'Ștefan', {name:'Ștefan Țurcanu',title:'Director de școală'})]);
 const r=createRunner(p);let tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,0)).token;ok(r.call('verify','R20_PLAN.json',tok));
});
test('04 standalone carton Orange/Bold readback',()=>{
 const r=createRunner(capsPlan());let tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,0)).token;ok(r.call('verify','R20_PLAN.json',tok));
});
test('V5 occupied even outside interval: full inventory and exactly two choices, non-destructive',()=>{
 const r=createRunner(capsPlan());r.video[4].clips.push(foreign(100,120,'Photo.png'));const a=r.call('validate','R20_PLAN.json','zero');
 assert.equal(a.ok,false);assert.equal(a.needsChoice,true);assert.equal(a.inventory.length,1);
 assert.equal(a.inventory[0].name,'Photo.png');assert.equal(a.choices.length,2);assert.equal(r.video[4].clips.numItems,1);
});
test('Locked target track: fail-closed',()=>{
 const r=createRunner(subPlan());r.video[2].isLocked=()=>true;assert.equal(r.call('validate','R20_PLAN.json','zero').ok,false);
});
test('Missing target track: fail-closed',()=>{
 const r=createRunner(capsPlan(),{trackCount:4});assert.equal(r.call('validate','R20_PLAN.json','zero').ok,false);
});
test('Sequence changed after validate: no writes',()=>{
 const r=createRunner(subPlan()),tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 r.seq.sequenceID='sequence-b';assert.equal(r.call('buildOne','R20_PLAN.json',tok,0).ok,false);assert.equal(r.video[2].clips.numItems,0);
});
test('V1 changed after validate: no writes',()=>{
 const r=createRunner(subPlan()),tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 r.video[0].clips.push(foreign(0,1));assert.equal(r.call('buildOne','R20_PLAN.json',tok,0).ok,false);assert.equal(r.video[2].clips.numItems,0);
});
test('Plan changed after validate: no writes',()=>{
 const r=createRunner(subPlan()),tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 r.files['R20_PLAN.json']=JSON.stringify({...subPlan(),docx_sha256:'b'.repeat(64)});
 assert.equal(r.call('buildOne','R20_PLAN.json',tok,0).ok,false);assert.equal(r.video[2].clips.numItems,0);
});
test('Target changed after validate: no writes',()=>{
 const r=createRunner(subPlan()),tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 r.video[2].clips.push(foreign(200,210));assert.equal(r.call('buildOne','R20_PLAN.json',tok,0).ok,false);
});
test('Append after existing clip without overwriting',()=>{
 const r=createRunner(subPlan());r.video[2].clips.push(foreign(0,10,'Old'));
 let tok=ok(r.call('validate','R20_PLAN.json','append')).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,0)).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,1)).token;
 assert.equal(r.video[2].clips.numItems,3);assert.equal(r.video[2].clips[0].name,'Old');
 ok(r.call('verify','R20_PLAN.json',tok));
});
test('Zero on occupied track blocks',()=>{
 const r=createRunner(subPlan());r.video[2].clips.push(foreign(100,110));assert.equal(r.call('validate','R20_PLAN.json','zero').ok,false);
});
test('Rollback on MOGRT missing parameter',()=>{
 const r=createRunner(subPlan()),tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 r.seq.importMGT=(path,ticks,index)=>{const clip=foreign(0,5,'Failing MOGRT');r.video[index].clips.push(clip);
    clip.getMGTComponent=()=>({properties:{getParamForDisplayName:()=>null}});
    clip.remove=()=>{const a=r.video[index].clips;a.splice(a.indexOf(clip),1);return true};return clip;};
 const res=r.call('buildOne','R20_PLAN.json',tok,0);assert.equal(res.ok,false);assert.equal(r.video[2].clips.numItems,0);
});
test('Reject subtitle pretending audio sync',()=>{
 const p=subPlan();p.timing='SYNCED';const r=createRunner(p);assert.equal(r.call('validate','R20_PLAN.json','zero').ok,false);
});
test('Reject oversized subtitle',()=>{
 const p=subPlan();p.items[0].text='x'.repeat(75);const r=createRunner(p);assert.equal(r.call('validate','R20_PLAN.json','zero').ok,false);
});
test('Reject montage-sized gap',()=>{
 const p=subPlan();p.items[1].startSeconds=30;const r=createRunner(p);assert.equal(r.call('validate','R20_PLAN.json','zero').ok,false);
});
test('Rollback all own MOGRTs and preserve previous timeline',()=>{
 const r=createRunner(subPlan());r.video[2].clips.push(foreign(0,9,'Before'));
 let tok=ok(r.call('validate','R20_PLAN.json','append')).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,0)).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,1)).token;
 ok(r.call('rollback','R20_PLAN.json',tok,2));
 assert.equal(r.video[2].clips.numItems,1);assert.equal(r.video[2].clips[0].name,'Before');
});
test('Rollback refuses foreign mutation to target',()=>{
 const r=createRunner(subPlan());let tok=ok(r.call('validate','R20_PLAN.json','zero')).token;
 tok=ok(r.call('buildOne','R20_PLAN.json',tok,0)).token;
 r.video[2].clips.push(foreign(80,85,'External'));
 assert.equal(r.call('rollback','R20_PLAN.json',tok,1).ok,false);assert.equal(r.video[2].clips.numItems,2);
});
console.log('Mock tests:',passed,'passed; Adobe LIVE not tested.');
