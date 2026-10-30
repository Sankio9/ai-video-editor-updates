/* R2.0.5: isolated CEP DOM regression. No Adobe Premiere required. */
'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const vm=require('vm');

function Node(tag, id) {
  this.tagName=tag; this.id=id||''; this.style={display:''}; this.children=[];
  this.parentNode=null; this.attrs={}; this.value=''; this.textContent=''; this.onclick=null;
}
Node.prototype.appendChild=function(n){
  if(n.parentNode){let i=n.parentNode.children.indexOf(n);if(i>=0)n.parentNode.children.splice(i,1);}
  this.children.push(n);n.parentNode=this;
  if(this.tagName==='select'&&n.tagName==='option'&&!this.value)this.value=n.value;
  return n;
};
Node.prototype.insertBefore=function(n, ref) {
  if(n.parentNode){let i=n.parentNode.children.indexOf(n);if(i>=0)n.parentNode.children.splice(i,1);}
  let i=ref?this.children.indexOf(ref):-1;
  if(i<0)this.children.push(n);else this.children.splice(i,0,n);
  n.parentNode=this;return n;
};
Node.prototype.setAttribute=function(k,v){this.attrs[k]=String(v);};
Node.prototype.getAttribute=function(k){return this.attrs[k]===undefined?null:this.attrs[k];};
Object.defineProperty(Node.prototype,'nextSibling',{get:function(){
  if(!this.parentNode)return null;let a=this.parentNode.children;return a[a.indexOf(this)+1]||null;
}});
Object.defineProperty(Node.prototype,'firstChild',{get:function(){return this.children[0]||null;}});

const main=new Node('main'),body=new Node('body');
body.appendChild(main);
const modules={},triggers={},legacy={},states={};
['subs','name','caps'].forEach(k=>{
  const m=new Node('details','module'+({subs:'Subs',name:'Name',caps:'Caps'}[k]));
  const content=new Node('div');
  const legacyTag=new Node('span');legacyTag.textContent='R1.7 · V5';
  m.content=content;m.legacyTag=legacyTag;m.querySelector=q=>q==='.content'?content:q==='summary .small'?legacyTag:null;m.appendChild(content);
  main.appendChild(m);modules[k]=m;
  const desc=new Node('div');desc.textContent='LEGACY R17 / R143 description';
  const check=new Node('button');check.textContent='Verifică rezultatul';
  const status=new Node('div');status.style.display='none';status.textContent='Generează planul R17';
  let counter=0;
  const btn=new Node('button',k+'R193Start');
  btn.onclick=()=>counter++;
  [desc,check,status,btn].forEach(x=>content.appendChild(x));
  legacy[k]=[desc,check,status];triggers[k]=btn;
  states[k]={read:()=>counter};
});
const nodes=(n,id)=>n.id===id?n:n.children.map(c=>nodes(c,id)).find(Boolean);
const document={
  body:body,
  getElementById:id=>nodes(body,id),
  querySelector:selector=>selector==='main'?main:null,
  querySelectorAll:selector=>selector==='details.module'?Object.values(modules):[],
  createElement:tag=>new Node(tag)
};
const window={
  __adobe_cep__:{},
  cep_node:{require:require},
  AIVE_CONTEXT_R184:{}
};
class FakeMutationObserver {observe(){}}
const source=fs.readFileSync(path.join(__dirname,'../candidate/cep/r20_panel.js'),'utf8');
vm.runInNewContext(source,{window,document,MutationObserver:FakeMutationObserver,
  require:()=>({}),console,Error,JSON,String,Array,Object},{timeout:1000});
for(const k of ['subs','name','caps']){
  const mode=document.getElementById('r20Mode_'+k);
  const pos=document.getElementById('r20Position_'+k);
  const hint=document.getElementById('r20Status_'+k);
  assert(mode&&pos&&hint);
  assert.equal(mode.value,'synced');
  assert.equal(pos.style.display,'none');
  assert.equal(legacy[k][0].style.display,'');
  assert.equal(legacy[k][2].style.display,'none');
  // Independent mode hides ALL old instructions and controls, not R20 action/status.
  mode.value='independent';mode.onchange();
  assert.equal(modules[k].legacyTag.textContent,'R2.0 Beta · '+({subs:'V3',name:'V4',caps:'V5'}[k]));
  assert.equal(pos.style.display,'block');
  legacy[k].forEach(x=>assert.equal(x.style.display,'none'));
  assert.notEqual(triggers[k].style.display,'none');
  assert.notEqual(hint.style.display,'none');
  assert(hint.textContent.indexOf('EDITORIAL_PREVIEW')>=0 || k==='subs');
  // Toggling to synchronized must restore original visual styles + click handler.
  mode.value='synced';mode.onchange();
  assert.equal(modules[k].legacyTag.textContent,'R1.7 · V5');
  assert.equal(pos.style.display,'none');
  assert.equal(legacy[k][0].style.display,'');
  assert.equal(legacy[k][1].style.display,'');
  assert.equal(legacy[k][2].style.display,'none');
  triggers[k].onclick();
  assert.equal(states[k].read(),1);
  mode.value='independent';mode.onchange();
  legacy[k].forEach(x=>assert.equal(x.style.display,'none'));
}
assert(Object.values(modules).every(m=>m.open===false));
console.log('PASS: 3 independent/synced legacy isolation, restore, click, status and closed sections');
