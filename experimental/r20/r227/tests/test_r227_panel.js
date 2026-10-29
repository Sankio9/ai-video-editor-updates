'use strict';
const fs=require('fs'),path=require('path').win32,vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const script=fs.readFileSync(require('path').join(__dirname,'../../r226/cep/r226_partial_subtitles_panel.js'),'utf8');
const hash=v=>crypto.createHash('sha256').update(v).digest('hex');
function setup(ops={}){
 let legacy=0,called=0;
 const doc='Bubuieci.docx',raw=Buffer.from('synthetic DOCX'),docSHA=hash(raw),seqID='SEQ-TEST-77';
 const base='montage_'+docSHA.slice(0,12)+'_'+hash(seqID).slice(0,12);
 const root='D:\\AI-Video-Editor',dir=path.join(root,'Temp','R220'),last=path.join(dir,'last_report.json');
 const planPath=path.join(dir,base+'.plan.json'),reportPath=path.join(dir,base+'.report.json');
 const identity={docxSHA256:docSHA,sequenceId:seqID,diagnosticSHA256:'f'.repeat(64)};
 const cuts=[
  {cutId:'CUT-01',sourceCode:'9981',sourceName:'Source.mov',sourceNodeId:'N1',
    timelineStart:0,timelineEnd:5,state:'CONFIRMED'},
  {cutId:'CUT-02',sourceCode:'9931',timelineStart:5,timelineEnd:11,state:'PLACEHOLDER'}
 ];
 const plan={schema:'aive-r220-montage-plan-v1',phase:'ANALYSIS_ONLY',
   identity,planSHA256:'a'.repeat(64),confirmedCount:1,placeholderCount:1,totalCuts:2,cuts};
 const analysis={schema:'aive-r220-missing-cuts-v1',phase:'ANALYSIS_ONLY',
   identity,planSHA256:plan.planSHA256,items:[{cutId:'CUT-02',sourceCode:'9931'}]};
 const files={[doc]:raw};
 if(!ops.missingPlan){files[planPath]=JSON.stringify(plan);files[reportPath]=JSON.stringify(analysis);}
 const fakefs={
  existsSync:p=>Object.prototype.hasOwnProperty.call(files,p),
  readFileSync:(p,encoding)=>{if(!(p in files))throw Error('not found '+p);return files[p];},
  writeFileSync:(p,v)=>{files[p]=v;},
  renameSync:(a,b)=>{files[b]=files[a];delete files[a];},
 };
 const elem={subsR193Start:{onclick(){legacy++},disabled:false},
   r20Mode_subs:{value:'synced'},subsR193Status:{textContent:''},
   r207OmitStruck:{checked:false}};
 const cep={getSystemPath:()=>root,evalScript(code,callback){
   called++;
   if(code.indexOf('$.evalFile')===0){callback('true');return;}
   if(code.indexOf('AIVE_R227_RECOVERY.identity()')===0){
    callback(JSON.stringify({ok:true,sequenceId:seqID,name:'Bubuieci [AIVE TEST]',
       r220Markers:ops.noMarkers?0:1}));return;
   }
   if(code.indexOf('AIVE_R227_RECOVERY.recover(')===0){
    callback(JSON.stringify(ops.failure?
       {ok:false,message:'R220_LIVE_CLIP_READBACK_FAIL CUT-01'}:
       {ok:true,planSHA256:plan.planSHA256,sequenceId:seqID,
        confirmedClipIds:['CUT-01'],placeholderMarkerIds:['CUT-02']}));return;
   }
   throw Error('Unexpected Premiere eval '+code.slice(0,80));
 }};
 const req=name=>({'fs':fakefs,'path':path,'crypto':crypto,
    'child_process':{spawn(){throw Error('should not launch Python in this fixture')}}})[name];
 const window={cep_node:{require:req},__adobe_cep__:cep,
    AIVE_CONTEXT_R184:{getDocx:()=>doc}};
 vm.runInNewContext(script,{window,document:{getElementById:n=>elem[n]||null},
   process:{env:{}},JSON,Buffer,Object,String,Error});
 return {click(){elem.subsR193Start.onclick()},last,files,elem,
    legacy:()=>legacy,called:()=>called};
}
function test(name,fn){try{fn();console.log('PASS '+name)}
catch(e){console.error('FAIL '+name,e);process.exitCode=1}}
test('recover missing report from exact readback without calling R143',()=>{
 const x=setup();x.click();
 assert.equal(x.legacy(),0);assert.ok(x.files[x.last]);
 const report=JSON.parse(x.files[x.last]);
 assert.equal(report.phase,'POST_READBACK');
 assert.equal(report.confirmedInsertedCount,1);
 assert.equal(report.placeholderReservedCount,1);
 assert.equal(report.readbackKind,'RECOVERED_FROM_VERIFIED_PREMIERE_TIMELINE');
 assert.match(x.elem.subsR193Status.textContent,/incomplet/);
});
test('do not mark incomplete Premiere state as success',()=>{
 const x=setup({failure:true});x.click();
 assert.equal(x.legacy(),0);assert.equal(x.files[x.last],undefined);
 assert.match(x.elem.subsR193Status.textContent,/LIVE_CLIP_READBACK_FAIL/);
});
test('missing R220 plan with Premiere markers never falls back to R143',()=>{
 const x=setup({missingPlan:true});x.click();
 assert.equal(x.legacy(),0);assert.match(x.elem.subsR193Status.textContent,/planul său lipsește/);
});
test('no R220 plan and no markers allows legacy route',()=>{
 const x=setup({missingPlan:true,noMarkers:true});x.click();
 assert.equal(x.legacy(),1);assert.equal(x.files[x.last],undefined);
});
test('R220 plan but lost markers stops before writes',()=>{
 const x=setup({noMarkers:true});x.click();
 assert.equal(x.legacy(),0);assert.match(x.elem.subsR193Status.textContent,/markerele lipsesc/);
});
console.log('R227 panel recovery suite: no write without full live readback');
