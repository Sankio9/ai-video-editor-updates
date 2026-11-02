/* R2.0 guard unit tests. node experimental/r20/tests/guard.test.js */
const assert=require('assert');
const G=require('../cep/jsx/r20_graphics_guard.jsx');
const sha='a'.repeat(64);
function plan(module, items, timing='SCRIPT_PREVIEW'){return {schema:'aive-r20-graphics-v1',module,mode:'independent',docx_sha256:sha,sequenceId:'seq-1',separatorSeconds:.75,timing,items};}
function item(id,groupId,startSeconds,durationSeconds,text){return {id,groupId,startSeconds,durationSeconds,text};}
function snap(track,clips=[]){return {sequenceId:'seq-1',targetTrack:track,trackCount:6,lockState:false,clips};}
function rejects(fn,pattern){assert.throws(fn,pattern);}
const sub=plan('02',[item('s1','g1',0,2,'Școală, învățământ și educație.'),item('s2','g2',2.75,2,'Bună ziua!')]);
assert.strictEqual(G.inspect(sub,snap(2)).ok,true);
assert.strictEqual(G.inspect(sub,snap(2)).timing,'SCRIPT_PREVIEW');
assert.strictEqual(G.inspect(sub,snap(2,[{name:'owned',start:10,end:12}])).ok,true);
assert.strictEqual(G.inspect(sub,snap(2,[{name:'foreign',start:1,end:3}])).ok,false);
rejects(()=>G.checkPlan({...sub,timing:'SYNCED'}),/SCRIPT_PREVIEW/);
rejects(()=>G.checkPlan({...sub,mode:'synced'}),/synced/);
rejects(()=>G.checkPlan({...sub,items:[item('1','g1',0,1,'A'),item('2','g2',7,1,'B')]}),/montage-sized/);
rejects(()=>G.checkPlan({...sub,items:[item('1','g1',0,1,'A'),item('2','g1',1.2,1,'B')]}),/space within/);
rejects(()=>G.checkPlan({...sub,items:[item('1','g1',0,1,'x'.repeat(75))]}),/74/);
rejects(()=>G.inspect(sub,snap(4)),/target track/);
rejects(()=>G.inspect(sub,{...snap(2),lockState:true}),/locked/);
rejects(()=>G.inspect(sub,{...snap(2),sequenceId:'changed'}),/sequence changed/);
const names=plan('03',[item('n1','a',0,2,'Ion Popescu\nDirector'),item('n2','b',2.75,2,'Ion Popescu\nDirector')]);
assert.strictEqual(G.inspect(names,snap(3)).ok,true);
rejects(()=>G.checkPlan(plan('03',[item('n1','a',0,1,'Ion'),item('n2','a',1,1,'Ion')])),/multiple nametags/);
const cartons=plan('04',[item('v1','g1',0,2,'CARTON\nEDUCAȚIE'),item('v2','g2',2.75,2,'TEXT NOU')],'EDITORIAL_PREVIEW');
assert.strictEqual(G.inspect(cartons,snap(4)).ok,true);
const occupied=G.inspect(cartons,snap(4,[{name:'some photo',kind:'photo',start:100,end:110}]));
assert.strictEqual(occupied.ok,false);
assert.strictEqual(occupied.reason,'V5_OCCUPIED');
assert.deepStrictEqual(occupied.choices,['Suprascrie materialele de pe V5','Oprește, eliberez V5']);
rejects(()=>G.checkPlan(plan('04',[item('x','g',0,1,'a'.repeat(34))],'EDITORIAL_PREVIEW')),/33/);
rejects(()=>G.checkPlan(plan('04',[item('x','g',0,1,'1\n2\n3\n4\n5')],'EDITORIAL_PREVIEW')),/4 lines/);
console.log('LOCAL PASS: R2.0 guard mock assertions (not Premiere LIVE validation)');
