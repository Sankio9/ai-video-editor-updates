/* R2.1.1 single-click CEP with mandatory internal 2-phase integration.
   Controls only local mock Python / Premiere -- NEVER accesses private DOCX.
*/
'use strict';
const assert=require('assert'),fsNative=require('fs'),path=require('path');
const vm=require('vm'),crypto=require('crypto');
const EventEmitter=require('events');
const script=fsNative.readFileSync(path.join(__dirname,'../candidate/cep/r20_panel.js'),'utf8');
const DOC='D:\\AIVE_TEST\\sample.docx';
let docBuffer=Buffer.from('synthetic-docx-v1'), scenario='good', cepCommands=[],spawnCount=0;
function digest(v){return crypto.createHash('sha256').update(v).digest('hex');}
function mockPlan() {
 const valid=scenario==='good';
 return {
   module:'02',generatorVersion:scenario==='stale'?'R2.0.7-strike-option-candidate':'R2.1.1-auto-preflight-readable',
   docx_sha256:digest(docBuffer),totalItems:1,groups:1,timing:'SCRIPT_PREVIEW',
   skipped:[],reviewRequired:false,reviewPolicy:'NONE',strikeAnalysisReady:true,
   strikePolicy:'OMIT_STRUCK',removedStrikeCharacters:valid?38:0,
   strikeCutsChanged:valid?1:0,omittedStrikeCuts:[],
   strikeAudit:valid?[{cutId:'CUT-02',paragraph:0,
     before:'Vreau să mă dezvolt în profesia dată. Unde ai vrea să muncești?',
     after:'Unde ai vrea să muncești?'}]:[]
 };
}
const fakeFs={
 existsSync:()=>true,statSync:()=>({isFile:()=>true}),mkdirSync:()=>{},
 readFileSync:(p)=>{
   if(String(p).endsWith('.docx'))return docBuffer;
   if(String(p).endsWith('.json'))return Buffer.from(JSON.stringify(mockPlan()));
   throw Error('Unexpected fake file '+p);
 }
};
const fakeCp={
 spawn:(exe,args)=>{
   spawnCount++;
   assert(args.includes('--omit-struck'), 'Checked policy should reach Python');
   const child=new EventEmitter();child.stdout=new EventEmitter();child.stderr=new EventEmitter();
   const out=args[args.indexOf('--output')+1];
   process.nextTick(()=>{
     const plan=mockPlan();
     child.stdout.emit('data',Buffer.from(JSON.stringify({
       ok:true,plan:out,count:1,groups:1,docx_sha256:plan.docx_sha256,timing:plan.timing,
       skipped:[],reviewRequired:false,strikePolicy:'OMIT_STRUCK',
       omittedStrikeCuts:plan.omittedStrikeCuts,removedStrikeCharacters:plan.removedStrikeCharacters,
       strikeCutsChanged:plan.strikeCutsChanged,strikeAuditCount:plan.strikeAudit.length,
       strikeAnalysisReady:true,generatorVersion:plan.generatorVersion
     })));
     child.emit('close',0);
   });
   return child;
 }
};
function Node(tag,id){
 this.tagName=tag;this.id=id||'';this.style={display:''};this.children=[];
 this.parentNode=null;this.attrs={};this.value='';this.textContent='';this.onclick=null;
 this.disabled=false;this.checked=false;
}
Node.prototype.appendChild=function(n){
 if(n.parentNode){let i=n.parentNode.children.indexOf(n);if(i>=0)n.parentNode.children.splice(i,1);}
 this.children.push(n);n.parentNode=this;
 if(this.tagName==='select'&&n.tagName==='option'&&!this.value)this.value=n.value;
 return n;
};
Node.prototype.insertBefore=function(n,ref){
 if(n.parentNode){let i=n.parentNode.children.indexOf(n);if(i>=0)n.parentNode.children.splice(i,1);}
 let i=ref?this.children.indexOf(ref):-1;
 if(i<0)this.children.push(n);else this.children.splice(i,0,n);
 n.parentNode=this;return n;
};
Node.prototype.setAttribute=function(k,v){this.attrs[k]=String(v);};
Node.prototype.getAttribute=function(k){return this.attrs[k]===undefined?null:this.attrs[k];};
Object.defineProperty(Node.prototype,'nextSibling',{get(){
 if(!this.parentNode)return null;let arr=this.parentNode.children;return arr[arr.indexOf(this)+1]||null;
}});
Object.defineProperty(Node.prototype,'firstChild',{get(){return this.children[0]||null;}});
const body=new Node('body'),main=new Node('main');body.appendChild(main);
const modules={};
['subs','name','caps'].forEach(k=>{
 const m=new Node('details','module'+({subs:'Subs',name:'Name',caps:'Caps'}[k]));
 const c=new Node('div');const tag=new Node('span');tag.textContent='R1.7 · V5';
 m.querySelector=q=>q==='.content'?c:q==='summary .small'?tag:null;
 m.appendChild(c);main.appendChild(m);modules[k]=m;
 for(let i=0;i<3;i++)c.appendChild(new Node('div'));
 const btn=new Node('button',k+'R193Start');btn.onclick=()=>{};c.appendChild(btn);
});
const find=(n,id)=>n.id===id?n:n.children.map(x=>find(x,id)).find(Boolean);
const document={
 body,createElement:tag=>new Node(tag),
 getElementById:id=>find(body,id),
 querySelector:selector=>selector==='main'?main:null,
 querySelectorAll:selector=>selector==='details.module'?Object.values(modules):[]
};
const cep={
 getSystemPath:()=>'/fake/extension',
 evalScript:(command,callback)=>{
   cepCommands.push(command);
   if(command.indexOf('$.evalFile')>=0)callback('LOADED');
   else callback(JSON.stringify({ok:false,message:'TEST SAFE: V3 blocked'}));
 }
};
const win={__adobe_cep__:cep,AIVE_CONTEXT_R184:{getDocx:()=>DOC},
 cep_node:{require:name=>({fs:fakeFs,path,crypto,child_process:fakeCp})[name]}};
class FakeMutationObserver{observe(){}}
vm.runInNewContext(script,{window:win,document,MutationObserver:FakeMutationObserver,
 process:{env:{}},console,Error,JSON,String,Array,Object,decodeURIComponent}, {timeout:2000});
function el(x){return document.getElementById(x);}
function tick(){return new Promise(resolve=>setImmediate(resolve));}
(async()=>{
 const mode=el('r20Mode_subs'),strike=el('r207OmitStruck'),btn=el('subsR193Start');
 mode.value='independent';mode.onchange();strike.checked=true;strike.onchange();
 assert.equal(btn.textContent,'Inserează subtitrările');
 assert.equal(el('r210AnalyzeSubs'),null,'No manual analysis button');
 assert.equal(el('r210SubtitlePreview'),null,'No extra preview UI');
 assert.notEqual(btn.disabled,true);

 scenario='zero';btn.onclick();
 assert.equal(cepCommands.length,0,'No Premiere command during Word analysis');
 await tick();
 assert.match(el('r20Status_subs').textContent,/STRIKETHROUGH_NOT_DETECTED/);
 assert.equal(cepCommands.length,0,'0 removals must STOP');
 assert.notEqual(btn.disabled,true);

 scenario='stale';btn.onclick();
 assert.equal(cepCommands.length,0);
 await tick();
 assert.match(el('r20Status_subs').textContent,/ENGINE_VERSION_MISMATCH/);
 assert.equal(cepCommands.length,0,'Old Python engine must STOP before V3');

 scenario='good';btn.onclick();
 assert.equal(cepCommands.length,0,'Analyze phase has NO Premiere actions');
 await tick();
 assert(cepCommands.length>0,'Successful analysis triggers Premiere preflight automatically');
 assert.equal(cepCommands.filter(x=>x.includes('.buildOne(')).length,0,
              'Premiere preflight fails in mock, so no clip inserted');
 assert.match(el('r20Status_subs').textContent,/OPRIT/);
 const afterValid=cepCommands.length;

 scenario='good';btn.onclick();docBuffer=Buffer.from('synthetic-docx-changed');
 await tick();
 assert.equal(cepCommands.length,afterValid,'Changed DOCX must block before Premiere');
 assert.match(el('r20Status_subs').textContent,/OPRIT/);
 docBuffer=Buffer.from('synthetic-docx-v1');
 const afterDoc=cepCommands.length;

 scenario='good';btn.onclick();strike.checked=false;
 await tick();
 assert.equal(cepCommands.length,afterDoc,'Changed checkbox must stop before Premiere');
 assert.match(el('r20Status_subs').textContent,/OPRIT/);
 strike.checked=true;strike.onchange();
 assert.notEqual(btn.disabled,true);
 console.log('PASS: one-click 02 auto DOCX preflight, 0-removal block, stale engine block, valid plan Premiere preflight, changed Word/checkbox abort, no manual preview');
})().catch(e=>{console.error(e);process.exitCode=1});
