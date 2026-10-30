'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const path=process.argv[2];
if(!path)throw Error('Provide extracted release panel path');
const source=fs.readFileSync(path,'utf8');
const start=source.indexOf('  function showNameTagReview(');
const end=source.indexOf(' function conflict(key,inventory)',start);
assert(start>=0&&end>start,'Missing review modal in installed CEP panel');
const code=source.slice(start,end)+'\nthis.showNameTagReview=showNameTagReview;';
function node(tag){
 return {
  tagName:tag,children:[],style:{cssText:''},textContent:'',attributes:{},
  parentNode:null,setAttribute(k,v){this.attributes[k]=v;},
  appendChild(item){item.parentNode=this;this.children.push(item);return item;},
  removeChild(item){this.children.splice(this.children.indexOf(item),1);item.parentNode=null;},
  focus(){this.focused=true;}
 };
}
const body=node('body');
const events={};
const doc={body,createElement:node};
const win={addEventListener(n,cb){events[n]=cb;},
 removeEventListener(n,cb){if(events[n]===cb)delete events[n];}};
const context={window:win,document:doc,String};
vm.runInNewContext(code,context);
const review=Array.from({length:26},(_,i)=>({
 cutId:'CUT-'+String(i+1).padStart(2,'0'),
 sourceCode:'0651',paragraph:i+11,
 reason:'Nume și funcție neconfirmate — sursă pentru verificare editorială'
}));
let response;
context.showNameTagReview(review,5,value=>{response=value;});
assert.equal(body.children.length,1);
const overlay=body.children[0],panel=overlay.children[0];
const title=panel.children[0],summary=panel.children[1],scroll=panel.children[2];
assert(title.textContent.includes('26 identificări'));
assert(summary.textContent.includes('5 burtiere confirmate'));
assert.equal(scroll.children.length,26);
assert(scroll.style.cssText.includes('overflow-y:auto'));
assert(scroll.style.cssText.includes('max-height:56vh'));
assert(scroll.children[25].textContent.includes('CUT-26'));
assert(scroll.children[25].textContent.includes('0651'));
assert.equal(response,undefined,'Must not approve without user action');
const actions=panel.children[4];
assert.equal(actions.children.length,2);
actions.children[1].onclick();
assert.equal(response,true);
assert.equal(body.children.length,0);
assert.equal(events.keydown,undefined);
response=undefined;
context.showNameTagReview(review,0,value=>response=value);
const second=body.children[0];
second.children[0].children[4].children[0].onclick();
assert.equal(response,false,'Cancel must stop before touching Premiere');
response=undefined;
context.showNameTagReview(review,4,value=>response=value);
events.keydown({key:'Escape',preventDefault(){}});
assert.equal(response,false);
assert.equal(body.children.length,0);
assert(!source.includes('if(!window.confirm(question))'));
console.log('PASS R232 full scrollable 26 CUT modal, explicit approve/cancel/Escape, no truncated native confirm');
