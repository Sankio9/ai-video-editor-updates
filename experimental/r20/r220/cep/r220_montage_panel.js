/* R2.2 experimental Montage 01 one-click bridge. Loaded AFTER R193 workflow.
 * All non-cut modules retain existing workflow unchanged.
 * No automatic partial insertion; approval is contextual only.
 */
(function(){
'use strict';
function E(x){return document.getElementById(x);}
var req=(window.cep_node&&window.cep_node.require)||null;
var cep=window.__adobe_cep__;
if(!req||!cep||!E('moduleCut'))return;
var fs=req('fs'),cp=req('child_process'),path=req('path'),crypto=req('crypto');
var ROOT='D:\\AI-Video-Editor',PY=path.join(ROOT,'.venv','Scripts','python.exe');
var RUN=path.join(ROOT,'tools','r220_montage_runner.py');
var busy=false,mainButton=E('cutR193Start');
var container=E('moduleCut').querySelector('.content');
var pane=document.createElement('div');pane.id='r220Results';
pane.style.cssText='display:none;max-height:330px;overflow:auto;margin:8px 0;padding:9px;border:1px solid #6a7786;border-radius:6px;font-size:12px;line-height:1.5';
if(mainButton)container.insertBefore(pane,mainButton.nextSibling);
var stat=E('cutR193Status'),lastDoc=null;
function status(t){if(stat)stat.textContent=t;}
function hide(){pane.style.display='none';pane.textContent='';}
function textBlock(tag,t){var n=document.createElement(tag);n.textContent=t;return n;}
function sha(bytes){return crypto.createHash('sha256').update(bytes).digest('hex');}
function docx(){var ctx=window.AIVE_CONTEXT_R184;return String((ctx&&ctx.getDocx&&ctx.getDocx())||
 (E('globalDocx')&&E('globalDocx').value)||'').trim();}
function exit(){busy=false;if(mainButton)mainButton.disabled=false;}
function ensureReady(){
 var d=docx();
 if(!d||!/\.docx$/i.test(d)||!fs.existsSync(d))throw Error('Selectează DOCX valid în 00.');
 if(!fs.existsSync(PY)||!fs.existsSync(RUN))throw Error('R2.2 nu este instalat complet (Python/runner).');
 return d;
}
function evalJS(code,cb){cep.evalScript(code,function(raw){
 if(String(raw).indexOf('EvalScript error')>=0){cb(Error('Premiere JSX error '+String(raw)));return;}
 cb(null,String(raw));
});}
function probe(cb){
 var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\/g,'/');
 var filename=ext+'/jsx/r220_media_probe.jsx';
 evalJS('$.evalFile(new File('+JSON.stringify(filename)+'))',function(e){
  if(e){cb(e);return;}
  evalJS('$._AIVE_R220_.scan()',function(err,result){
   if(err){cb(err);return;}
   try{var v=JSON.parse(result);
    if(!v.ok||!v.sequenceId||!v.media)throw Error(v.message||'Project Panel invalid');
    if(v.sequence.indexOf('[AIVE TEST]')<0)throw Error('Creează o COPIE a secvenței și adaugă [AIVE TEST] în nume.');
    cb(null,v);
   }catch(x){cb(x);}
  });
 });
}
function runner(media,d,cb){
 try{
  var w=path.join(ROOT,'Temp','R220');fs.mkdirSync(w,{recursive:true});
  var filename=path.join(w,'project_media_'+media.sequenceId.replace(/[^a-zA-Z0-9_-]/g,'_')+'.json');
  fs.writeFileSync(filename,JSON.stringify(media),'utf8');
  var args=['-X','utf8','-u',RUN,'--docx',d,'--project-media',filename,'--sequence-id',String(media.sequenceId)];
  var env=Object.assign({},process.env,{PYTHONUTF8:'1',PYTHONIOENCODING:'utf8'});
  var p=cp.spawn(PY,args,{cwd:ROOT,windowsHide:true,env:env}),buffer='',error='',finished=false;
  p.stdout.on('data',function(b){
   buffer+=String(b);
   if(buffer.length>2e6){p.kill();return;}
   var lines=String(b).split(/\r?\n/);
   var last=lines.filter(function(x){return x.length&&x.indexOf('AIVE_RESULT_JSON ')!==0;}).slice(-1)[0];
   if(last)status('Analizez ASR: '+last.slice(0,130));
  });
  p.stderr.on('data',function(b){error+=String(b).slice(0,1000);});
  p.on('error',function(e){if(!finished){finished=true;cb(e);}});
  p.on('close',function(code){
   if(finished)return;finished=true;
   try{
    var at=buffer.lastIndexOf('AIVE_RESULT_JSON ');
    if(at<0)throw Error('Motorul R2.2 nu a returnat un rezultat. '+error.slice(-140));
    var result=JSON.parse(buffer.slice(at+17).trim());
    if(code!==0||!result.ok)throw Error(result.message||error||'Analiza R2.2 a eșuat');
    cb(null,result);
   }catch(x){cb(x);}
  });
 }catch(x){cb(x);}
}
function loadLocked(response,cb){
 try{
  if(!fs.existsSync(response.plan)||!fs.existsSync(response.report))throw Error('Lipsește planul de analiză.');
  var bytes=fs.readFileSync(response.plan);
  if(sha(bytes)!==response.planFileSHA256)throw Error('SHA_PLAN_FILE_CHANGED');
  var plan=JSON.parse(String(bytes));
  var report=JSON.parse(fs.readFileSync(response.report,'utf8'));
  if(plan.planSHA256!==response.planSHA256 || plan.identity.sequenceId!==response.sequenceId ||
     report.planSHA256!==plan.planSHA256 || report.phase!=='ANALYSIS_ONLY')throw Error('PLAN_OR_REPORT_INVALID');
  cb(null,{plan:plan,report:report,response:response});
 }catch(e){cb(e);}
}
function list(report){
 hide();pane.style.display='block';
 pane.appendChild(textBlock('strong','Materiale de verificat: '+report.items.length+' CUT-uri'));
 var ul=document.createElement('div');
 for(var i=0;i<report.items.length;i++){
  var x=report.items[i];
  var node=textBlock('div',x.cutId+' · '+x.sourceCode+' · '+(x.sourceName||'Sursa negăsită')+
    ' | '+x.reason+' | '+x.durationSeconds+'s estimat');
  node.style.cssText='margin-top:6px;border-top:1px solid #66727d;padding-top:5px;';
  ul.appendChild(node);
 }
 pane.appendChild(ul);
}
function verifyState(state,source,cb){
 try{
  if(docx()!==state.doc || sha(fs.readFileSync(state.doc))!==state.docSHA ||
    sha(fs.readFileSync(state.lock.response.plan))!==state.lock.response.planFileSHA256)
    throw Error('DOCX/plan modificat după analiză. Reanalizează.');
 }catch(e){cb(e);return;}
 probe(function(err,current){
  if(err){cb(err);return;}
  if(current.sequenceId!==source.sequenceId)cb(Error('Secvența a fost schimbată.'));
  else cb(null,current);
 });
}
function saveReport(state,result){
 var report=state.lock.report,plan=state.lock.plan;
 var actualC=result.confirmedClipIds||[],marks=result.placeholderMarkerIds||[];
 var expected=plan.cuts.filter(function(v){return v.state==='CONFIRMED';}).map(function(v){return v.cutId;});
 var reserved=plan.cuts.filter(function(v){return v.state==='PLACEHOLDER';}).map(function(v){return v.cutId;});
 if(actualC.join('|')!==expected.join('|')||marks.join('|')!==reserved.join('|')||
    result.planSHA256!==plan.planSHA256 || result.sequenceId!==plan.identity.sequenceId)
   throw Error('READBACK_CUT_COUNT_MISMATCH');
 report.phase='POST_READBACK';
 report.readbackKind='LIVE_PREMIERE_CONFIRMED';
 report.confirmedInsertedCount=actualC.length;
 report.placeholderReservedCount=marks.length;
 report.message=marks.length?'Montaj parțial. Au rămas '+marks.length+' sincronuri de verificat.':'Montaj complet confirmat.';
 var target=path.join(ROOT,'Temp','R220','last_report.json'),temp=target+'.tmp';
 fs.writeFileSync(temp,JSON.stringify(report,null,2),'utf8');fs.renameSync(temp,target);
 return report;
}
function commit(state,choice,media){
 if(busy)return;busy=true;if(mainButton)mainButton.disabled=true;
 status('Verific identitatea și pistele înainte de inserare...');
 verifyState(state,media,function(err){
  if(err){status('OPRIT: '+err.message);exit();return;}
  var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\/g,'/');
  evalJS('$.evalFile(new File('+JSON.stringify(ext+'/jsx/r220_montage_writer.jsx')+'))',function(e){
   if(e){status('OPRIT: '+e.message);exit();return;}
   var params=JSON.stringify(state.lock.plan)+','+JSON.stringify(choice)+','+
       JSON.stringify(state.lock.plan.planSHA256);
   evalJS('AIVE_R220.commit('+params+')',function(error,result){
    if(error){status('OPRIT: '+error.message);exit();return;}
    try{
     var r=JSON.parse(result);
     if(!r.ok)throw Error(r.error||'Inserarea a eșuat. '+(r.rollbackIssues||[]).join(','));
     var report=saveReport(state,r);
     status(report.message);
     if(report.items.length)list(report);
     else hide();
    }catch(x){status('NECESITĂ VERIFICARE: '+x.message);}
    exit();
   });
  });
 });
}
function offer(state,media){
 var r=state.lock.report,p=state.lock.plan;
 if(!r.items.length){exit();commit(state,'COMPLETE_AFTER_PREFLIGHT',media);return;}
 list(r);
 var controls=document.createElement('div');controls.style.cssText='display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;';
 var yes=textBlock('button','Continuă cu spații rezervate');yes.className='secondary';
 var no=textBlock('button','Oprește');no.className='secondary';
 controls.appendChild(yes);controls.appendChild(no);pane.appendChild(controls);
 status('ANALIZĂ: '+p.confirmedCount+'/'+p.totalCuts+' confirmate, '+r.items.length+' de verificat. V1/A1 neschimbate.');
 no.onclick=function(){hide();status('Oprit la alegerea editorului. Timeline nemodificat.');exit();};
 yes.onclick=function(){controls.style.display='none';commit(state,'CONTINUE_WITH_PLACEHOLDERS',media);};
 exit();
}
function start(){
 if(busy)return;var d;
 try{d=ensureReady();}catch(e){status('OPRIT: '+e.message);return;}
 busy=true;if(mainButton)mainButton.disabled=true;
 hide();status('01 Montaj: verific sursele Premiere...');
 var docHash=sha(fs.readFileSync(d));
 probe(function(err,media){
  if(err){status('OPRIT: '+err.message);exit();return;}
  status('01 Montaj: analizez integral DOCX și ASR...');
  runner(media,d,function(error,response){
   if(error){status('OPRIT: '+error.message);exit();return;}
   loadLocked(response,function(problem,lock){
    if(problem){status('OPRIT: '+problem.message);exit();return;}
    if(docx()!==d || sha(fs.readFileSync(d))!==docHash){
      status('OPRIT: DOCX modificat în timpul analizei.');exit();return;
    }
    offer({doc:d,docSHA:docHash,lock:lock},media);
   });
  });
 });
}
window.AIVE_R220_UI={start:start};
})();
