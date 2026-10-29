'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const SCRIPT=fs.readFileSync(path.join(__dirname,'../cep/r226_partial_subtitles_panel.js'),'utf8');
function start(report,docHash){
 let calls=0,button={disabled:false,onclick(){calls++}},
 mode={value:'independent'},stat={textContent:''},omit={checked:false};
 const elements={subsR193Start:button,r20Mode_subs:mode,subsR193Status:stat,r207OmitStruck:omit};
 const doc='case.docx';
 const bytes=Buffer.from('test DOCX');
 const files={'D:\\AI-Video-Editor\\Temp\\R220\\last_report.json':report,'case.docx':bytes};
 const fss={existsSync(p){return Object.prototype.hasOwnProperty.call(files,p);},
   readFileSync(p,enc){const obj=files[p];
     if(typeof obj==='object'&&!Buffer.isBuffer(obj))return JSON.stringify(obj);
     return obj;}};
 const req=x=>({'fs':fss,'path':require('path').win32,'crypto':require('crypto'),
 'child_process':{spawn(){throw Error('Should never spawn during stale/missing report');}}})[x];
 const w={cep_node:{require:req},__adobe_cep__:{},
   AIVE_CONTEXT_R184:{getDocx(){return doc;}}};
 const ctx={document:{getElementById:key=>elements[key]||null},window:w,
   Object,Buffer,process:{env:{}},JSON,Error,String};
 vm.runInNewContext(SCRIPT,ctx);
 return {button,mode,stat,omit,calls:()=>calls,files};
}
function suite(){
 const a=start(null);a.mode.value='independent';a.button.onclick();assert.equal(a.calls(),1);
 a.mode.value='synced';a.button.onclick();assert.equal(a.calls(),2);
 const b=start({schema:'aive-r220-missing-cuts-v1',phase:'POST_READBACK',
    identity:{docxSHA256:'0'.repeat(64),sequenceId:'SEQ_0'},
    confirmedInsertedCount:9,placeholderReservedCount:10,items:Array.from({length:10},(_,i)=>({cutId:'CUT-'+i}))});
 b.mode.value='synced';b.button.onclick();assert.equal(b.calls(),0);
 assert.match(b.stat.textContent,/DOCX nu corespunde/);
 console.log('PASS R226 panel interception: independent unchanged, legacy fallback without R220, stale report blocked');
}
suite();
