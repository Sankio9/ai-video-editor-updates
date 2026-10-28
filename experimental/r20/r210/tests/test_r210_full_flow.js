/* R2.1.0 realistic CEP 2-step synthetic integration.
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
   module:'02',generatorVersion:scenario==='stale'?'R2.0.7-strike-option-candidate':'R2.1.0-two-phase-preflight',
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
 const analyze=el('r210AnalyzeSubs'),preview=el('r210SubtitlePreview');
 mode.value='independent';mode.onchange();strike.checked=true;strike.onchange();
 assert.equal(btn.disabled,true);
 btn.onclick();
 assert.equal(cepCommands.length,0,'NO Premiere commands before analysis');
 assert.equal(spawnCount,0,'Insert action may not start Python');
 scenario='zero';analyze.onclick();await tick();
 assert.equal(btn.disabled,true,'0 removal must fail before insert');
 assert.match(el('r20Status_subs').textContent,/STRIKETHROUGH_NOT_DETECTED/);
 assert.equal(cepCommands.length,0);
 scenario='stale';analyze.onclick();await tick();
 assert.equal(btn.disabled,true,'old Python engine must fail protocol handshake');
 assert.match(el('r20Status_subs').textContent,/ENGINE_VERSION_MISMATCH/);
 scenario='good';analyze.onclick();await tick();
 assert.equal(btn.disabled,false,'verified plan should unlock insertion');
 assert.match(preview.textContent,/ÎNAINTE:/);
 assert.match(preview.textContent,/DUPĂ:/);
 assert.match(preview.textContent,/Vreau să mă dezvolt/);
 assert.match(preview.textContent,/Unde ai vrea să muncești/);
 assert.equal(cepCommands.length,0,'Preview must never call Premiere');
 const prior=cepCommands.length;
 docBuffer=Buffer.from('synthetic-docx-changed');
 btn.onclick();
 assert.equal(cepCommands.length,prior,'changed DOCX cancels without Premiere');
 assert.equal(btn.disabled,false,'DOM disable state may remain; checked policy must block');
 docBuffer=Buffer.from('synthetic-docx-v1');
 analyze.onclick();await tick();
 btn.onclick();
 assert(cepCommands.length>prior,'Approved plan may enter Premiere validate');
 assert.equal(cepCommands.filter(s=>s.includes('.buildOne(')).length,0,
             'Failed mock preflight must never insert MOGRTs');
 assert.match(el('r20Status_subs').textContent,/OPRIT/);
 strike.checked=false;strike.onchange();
 assert.equal(btn.disabled,true,'Checkbox changes invalidate preview');
 const after=cepCommands.length;btn.onclick();assert.equal(cepCommands.length,after);
 console.log('PASS: 2-step 02 mock, no Premiere before preview, 0-removal and stale engine block, changed DOCX blocks, safe preflight failure, checkbox invalidation');
})().catch(e=>{console.error(e);process.exitCode=1});
