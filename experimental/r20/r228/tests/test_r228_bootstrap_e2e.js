'use strict';
const assert=require('assert'),crypto=require('crypto'),path=require('path').win32,EventEmitter=require('events'),fs=require('fs'),vm=require('vm');
const code=fs.readFileSync(require('path').join(__dirname,'../cep/r228_subtitles_panel.js'),'utf8');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function startScenario({late=false,withPlan=false,legacyAssignedLater=false,mode='synced',failRecovery=false}={}){
 const document={listeners:{},body:{},elements:{},header:{textContent:'R1.5.15'},
  addEventListener(type,fn,capture){assert.equal(type,'click');assert.equal(capture,true);
    this.listeners.click=fn;},
  getElementById(id){return this.elements[id]||null;},
  querySelector(sel){return sel==='#moduleSubs summary .small'?this.header:null;}};
 let originalCalls=0,spawnCalls=0,writerCalls=0,jsCalls=0;
 const runBtn={disabled:false,contains(n){return n===this},onclick(){originalCalls++;}};
 const selector={value:mode},status={textContent:''},struck={checked:false};
 function place(){document.elements.subsR193Start=runBtn;
   document.elements.r20Mode_subs=selector;
   document.elements.subsR193Status=status;
   document.elements.r207OmitStruck=struck;}
 if(!late)place();
 const doc='D:\\Docs\\Bubuieci.docx',rawDoc=Buffer.from('SAMPLE_DOCX_BYTES');
 const docSHA=sha(rawDoc),id='R220_SEQ_A';
 const folder=path.join('D:\\AI-Video-Editor','Temp','R220');
 const base='montage_'+docSHA.slice(0,12)+'_'+sha(id).slice(0,12);
 const planPath=path.join(folder,base+'.plan.json'),reportPath=path.join(folder,base+'.report.json');
 const last=path.join(folder,'last_report.json');
 const identity={docxSHA256:docSHA,sequenceId:id,diagnosticSHA256:'c'.repeat(64)};
 const cuts=[{cutId:'CUT-01',sourceCode:'9981',sourceName:'ANMR_REL9981.MP4',sourceNodeId:'NODE-1',
   timelineStart:0,timelineEnd:4,state:'CONFIRMED'},
   {cutId:'CUT-02',sourceCode:'9931',sourceName:'ANMR_REL9931.MP4',
    timelineStart:4,timelineEnd:10,state:'PLACEHOLDER'}];
 const montage={schema:'aive-r220-montage-plan-v1',phase:'ANALYSIS_ONLY',identity,
   planSHA256:'d'.repeat(64),totalCuts:2,confirmedCount:1,placeholderCount:1,cuts};
 const report={schema:'aive-r220-missing-cuts-v1',phase:'ANALYSIS_ONLY',identity,
   planSHA256:montage.planSHA256,items:[{cutId:'CUT-02',sourceCode:'9931'}]};
 const files={[doc]:rawDoc};
 if(withPlan){files[planPath]=JSON.stringify(montage);files[reportPath]=JSON.stringify(report);}
 const generator=path.join('D:\\AI-Video-Editor','tools','r226_partial_subtitles.py');
 const py=path.join('D:\\AI-Video-Editor','.venv','Scripts','python.exe');
 const mockfs={
  existsSync:p=>p===generator||p===py||Object.prototype.hasOwnProperty.call(files,p),
  readFileSync:(p,encoding)=>{if(!(p in files))throw Error('Missing '+p);
    const x=files[p];return encoding==='utf8'?String(x):Buffer.from(x);},
  writeFileSync:(p,data)=>{files[p]=data;},
  renameSync:(from,to)=>{files[to]=files[from];delete files[from];},
  mkdirSync:()=>{}
 };
 const spawn=(python,args)=>{
   spawnCalls++;const proc=new EventEmitter();proc.stdout=new EventEmitter();proc.stderr=new EventEmitter();
   setImmediate(()=>{
     const out=args[args.indexOf('--output')+1];
     const plan={schema:'aive-r226-partial-subs-v1',module:'02',mode:'montage_partial',
       timing:'CUT_ALIGNED_ESTIMATED',docx_sha256:docSHA,montagePlanSHA256:montage.planSHA256,
       sequenceId:id,reservedCount:1,totalItems:1,items:[{id:'R226-0001',groupId:'CUT-01',
        sourceCode:'9981',startSeconds:0,durationSeconds:4,text:'Bubuieci',fontStyle:'Regular'}]};
     const bytes=Buffer.from(JSON.stringify(plan));files[out]=bytes;
     const output={ok:true,plan:out,fileSHA256:sha(bytes),docxSHA256:docSHA,
       montagePlanSHA256:montage.planSHA256,sequenceId:id,reservedCuts:1,items:1,subtitledCuts:1};
     proc.stdout.emit('data',Buffer.from(JSON.stringify(output)));proc.emit('close',0);
   });
   return proc;
 };
 const cep={
   getSystemPath:()=>path.join('D:\\AI-Video-Editor','cep'),
   evalScript(script,cb){
     jsCalls++;
     if(script.includes('$.evalFile(')){cb('true');return;}
     if(script.includes('RECOVERY.identity()')){cb(JSON.stringify({ok:true,sequenceId:id,
       name:'Bubuieci [AIVE TEST]',r220Markers:withPlan?1:0}));return;}
     if(script.includes('RECOVERY.recover(')){
       cb(JSON.stringify(failRecovery?{ok:false,message:'R220_LIVE_CLIP_READBACK_FAIL CUT-01'}:{
         ok:true,planSHA256:montage.planSHA256,sequenceId:id,
         confirmedClipIds:['CUT-01'],placeholderMarkerIds:['CUT-02']}));return;
     }
     if(script.includes('$._AIVE_R226_.preflight(')){cb(JSON.stringify({ok:true,token:'token0'}));return;}
     if(script.includes('$._AIVE_R226_.buildOne(')){
       writerCalls++;cb(JSON.stringify({ok:true,token:'token1',done:1}));return;}
     if(script.includes('$._AIVE_R226_.verify(')){
       cb(JSON.stringify({ok:true,message:'1 MOGRT verificat',sourceCuts:1,omitted:1}));return;}
     throw Error('UNEXPECTED_EVAL '+script.slice(0,80));
   }};
 const req=name=>({'fs':mockfs,'path':path,'crypto':crypto,'child_process':{spawn}})[name];
 const win={cep_node:{require:req},__adobe_cep__:cep,
   AIVE_CONTEXT_R184:{getDocx(){return doc}},confirm(){return true;}};
 const ctx={window:win,document,console,MutationObserver:class{
     observe(){/* reactive DOM is delivered on actual click via delegation */}},
     JSON,String,Number,Error,Object,Buffer,process:{env:{}},decodeURIComponent};
 vm.runInNewContext(code,ctx,{timeout:2500});
 assert.equal(typeof document.listeners.click,'function','R228 must capture events even before R20 selector exists');
 if(late)place();
 if(legacyAssignedLater)runBtn.onclick=()=>originalCalls++;
 const click=()=>{
   const e={target:runBtn,stopped:false,
     preventDefault(){this.stopped=true;},
     stopImmediatePropagation(){this.stopped=true;},
     stopPropagation(){this.stopped=true;}};
   document.listeners.click(e);
   if(!e.stopped&&runBtn.onclick)runBtn.onclick();
   return e.stopped;
 };
 return {click,win,status,document,files,last,runBtn,selector,
  originalCalls:()=>originalCalls,spawnCalls:()=>spawnCalls,
  writerCalls:()=>writerCalls,jsCalls:()=>jsCalls};
}
const run=async()=>{
 const tests=[
  ['async DOM arrival + legacy onclick assigned after script; capture always intercepts',async()=>{
    const x=startScenario({late:true,legacyAssignedLater:true,withPlan:true});
    assert.equal(x.document.header.textContent,'R1.5.15');
    assert.equal(x.click(),true);
    await new Promise(r=>setTimeout(r,30));
    assert.equal(x.originalCalls(),0);
    assert.equal(x.writerCalls(),1);
    assert.equal(x.document.header.textContent,'R2.2.8 BETA');
    assert.match(x.status.textContent,/PREMIERE READBACK/);
    const report=JSON.parse(String(x.files[x.last]));
    assert.equal(report.confirmedInsertedCount,1);
  }],
  ['early DOM event: exact same full V3 flow, no old R143 handler',async()=>{
    const x=startScenario({withPlan:true});
    assert.equal(x.click(),true);
    await new Promise(r=>setTimeout(r,30));
    assert.equal(x.originalCalls(),0);assert.equal(x.writerCalls(),1);
    assert.match(x.status.textContent,/1 CUT-uri fără audio confirmat/);
  }],
  ['independent 02 preserves original handler',async()=>{
    const x=startScenario({late:true,mode:'independent'});
    assert.equal(x.click(),false);assert.equal(x.originalCalls(),1);
    assert.equal(x.spawnCalls(),0);
  }],
  ['Montage metadata missing: no fallback to old 19/19 engine',async()=>{
    const x=startScenario();
    assert.equal(x.click(),true);await new Promise(r=>setTimeout(r,10));
    assert.equal(x.originalCalls(),0);assert.equal(x.writerCalls(),0);
    assert.match(x.status.textContent,/Nu există montaj R220/);
  }],
  ['Premiere refused verified readback: V3 untouched, button re-enabled',async()=>{
    const x=startScenario({withPlan:true,failRecovery:true});
    assert.equal(x.click(),true);await new Promise(r=>setTimeout(r,10));
    assert.equal(x.writerCalls(),0);assert.equal(x.originalCalls(),0);
    assert.equal(x.runBtn.disabled,false);
    assert.match(x.status.textContent,/R220_LIVE_CLIP_READBACK_FAIL/);
  }]
 ];
 for(const [name,fn] of tests){
   try{await fn();console.log('PASS '+name);}catch(e){console.error('FAIL '+name,e);process.exitCode=1;}
 }
};
run();
