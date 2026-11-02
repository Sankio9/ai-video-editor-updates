
/* R2.2.6: one-click R220 partial montage subtitle bridge. If no readback
 * R220 report exists, preserve the original R2.1 synced subtitle handler.
 * The new cue timings are explicitly ESTIMATED WITHIN confirmed CUTs.
 */
(function(){
'use strict';
// Startup order is async: R20 may create selectors after this script executes.
// The click listener must be delegated, not tied to a button that may not exist yet.
if(!window.__adobe_cep__)return;
var btn=null,mode=null,statusNode=null;
// Match the approved R20 CEP loader: production may expose Node through
// global require rather than window.cep_node.require. Never silently disable 02.
var requireNode=null;
try{requireNode=(window.cep_node&&window.cep_node.require)||require;}catch(e){}
if(!requireNode){return;}
var fs=requireNode('fs'),path=requireNode('path'),cp=requireNode('child_process'),
 crypto=requireNode('crypto'),cep=window.__adobe_cep__;
var ROOT='D:\\AI-Video-Editor',PY=path.join(ROOT,'.venv','Scripts','python.exe');
var GENERATOR=path.join(ROOT,'tools','r226_partial_subtitles.py');
var last=path.join(ROOT,'Temp','R220','last_report.json');
var busy=false;
function currentButton(){return document.getElementById('subsR193Start');}
function currentMode(){return document.getElementById('r20Mode_subs');}
function bind(){
 btn=currentButton();mode=currentMode();statusNode=document.getElementById('subsR193Status');
 var header=document.querySelector('#moduleSubs summary .small');
 if(btn&&mode&&header&&header.textContent!=='R2.2.9 BETA')header.textContent='R2.2.9 BETA';
 return !!(btn&&mode);
}
function status(s){var target=document.getElementById('subsR193Status')||statusNode;if(target)target.textContent=s;}
function digest(s){return crypto.createHash('sha256').update(s).digest('hex');}
function docx(){var ctx=window.AIVE_CONTEXT_R184;
 return String((ctx&&ctx.getDocx&&ctx.getDocx())||
   (document.getElementById('globalDocx')&&document.getElementById('globalDocx').value)||'').trim();}
function reset(){busy=false;var b=currentButton();if(b)b.disabled=false;}
function currentReport(){
 if(!fs.existsSync(last))return null;
 var obj=JSON.parse(fs.readFileSync(last,'utf8'));
 if(!obj||obj.schema!=='aive-r220-missing-cuts-v1'||obj.phase!=='POST_READBACK')
  return null;
 return obj;
}
function runEval(script,cb){cep.evalScript(script,function(x){
 if(String(x).indexOf('EvalScript error')>=0)cb(Error('Premiere EvalScript '+String(x)));
 else cb(null,String(x));
});}
function callJS(method,args,cb){
 runEval('$._AIVE_R226_.'+method+'('+args.map(JSON.stringify).join(',')+')',
 function(err,data){if(err){cb(err);return;}try{cb(null,JSON.parse(data));}
  catch(e){cb(Error('Răspuns Premiere invalid: '+String(data).slice(0,120)));}});
}
// Read-only recovery of the already-inserted R220 montage if the previous
// panel could not persist POST_READBACK (legacy variable actual vs actualC).
// Never run the legacy 19/19 ASR gate on an R220 timeline.
// R2.2.9: do not trust the old R220 .report.json sidecar. The initial
// montage may have inserted on V1/A1 before report persistence crashed.
// Instead authenticate ORIGINAL .plan.json via exact Python R220 SHA
// and check every clip and marker AGAIN against the active Premiere timeline.
function verifyR220Plan(doc,planFile,sequenceId,callback){
 var validator=path.join(ROOT,'tools','r229_validate_r220.py');
 if(!fs.existsSync(PY)||!fs.existsSync(validator)){
   callback(Error('R2.2.9 instalare incompletă: verificator R220 lipsește.'));return;
 }
 var before;
 try{before=digest(fs.readFileSync(planFile));}
 catch(e){callback(Error('PLAN_UNREADABLE '+e.message));return;}
 var stdout='',stderr='',finished=false;
 var args=['-X','utf8','-u',validator,'--docx',doc,'--plan',planFile,'--sequence-id',sequenceId];
 var env=Object.assign({},process.env,{PYTHONUTF8:'1',PYTHONIOENCODING:'utf8'});
 var proc;
 try{proc=cp.spawn(PY,args,{cwd:ROOT,env:env,windowsHide:true});}
 catch(e){callback(Error('PYTHON_SPAWN_FAILED '+e.message));return;}
 proc.stdout.on('data',function(b){stdout+=String(b);
   if(stdout.length>3000000){try{proc.kill();}catch(e){}}
 });
 proc.stderr.on('data',function(b){stderr=(stderr+String(b)).slice(-2500);});
 proc.on('error',function(e){if(!finished){finished=true;callback(Error('PYTHON_ERROR '+e.message));}});
 proc.on('close',function(code){
   if(finished)return;finished=true;
   try{
     var at=stdout.lastIndexOf('AIVE_R229_RESULT ');
     if(at<0)throw Error('VALIDATOR_NO_JSON '+stderr.slice(-450));
     var line=stdout.substring(at+17).split(/\r?\n/)[0].trim();
     var verdict=JSON.parse(line);
     if(code!==0||!verdict.ok)throw Error(verdict.message||stderr.slice(-450)||'PLAN_NOT_VALIDATED');
     if(verdict.planFileSHA256!==before||digest(fs.readFileSync(planFile))!==before||
        verdict.sequenceId!==sequenceId||verdict.docxSHA256!==digest(fs.readFileSync(doc)))
        throw Error('PLAN_OR_DOCX_CHANGED_DURING_VALIDATION');
     callback(null,verdict);
   }catch(e){callback(e);}
 });
}
function recoverOrFallback(done){
 var doc=docx();
 if(!doc||!/\.docx$/i.test(doc)||!fs.existsSync(doc)){
   done(Error('Selectează DOCX în modulul 00.'));return;
 }
 var docSHA=digest(fs.readFileSync(doc));
 var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\/g,'/');
 runEval('$.evalFile(new File('+JSON.stringify(ext+'/jsx/r227_montage_recovery.jsx')+'))',
 function(loading){
   if(loading){done(loading);return;}
   runEval('AIVE_R227_RECOVERY.identity()',function(error,raw){
     if(error){done(error);return;}
     var seq,planPath;
     try{
       seq=JSON.parse(raw);
       if(!seq.ok||!seq.sequenceId)throw Error('Secvența Premiere nu poate fi verificată.');
       var basename='montage_'+docSHA.slice(0,12)+'_'+digest(seq.sequenceId).slice(0,12);
       planPath=path.join(ROOT,'Temp','R220',basename+'.plan.json');
       if(!fs.existsSync(planPath)){
         if(seq.r220Markers>0)
           throw Error('R220_MARKERS_WITHOUT_MATCHING_PLAN: DOCX/sequence check.');
         done(null,null,true);return;
       }
       if(seq.r220Markers===0)throw Error('R220_PLAN_WITHOUT_MARKERS');
     }catch(e){done(e);return;}
     // This source plan must be authenticated by the ORIGINAL R220 Python
     // digest (Python float canonicalization differs from JSON.stringify).
     verifyR220Plan(doc,planPath,seq.sequenceId,function(problem,validated){
       if(problem){done(Error('PLAN_R220: '+problem.message));return;}
       var plan;
       try{
         plan=JSON.parse(fs.readFileSync(planPath,'utf8'));
         if(plan.planSHA256!==validated.planSHA256||
            plan.identity.docxSHA256!==docSHA||
            plan.identity.sequenceId!==seq.sequenceId)
            throw Error('VALIDATED_PLAN_IDENTITY_CHANGED');
       }catch(e){done(e);return;}
       runEval('AIVE_R227_RECOVERY.recover('+JSON.stringify(plan)+')',
       function(ex,readback){
         if(ex){done(ex);return;}
         try{
           var result=JSON.parse(readback);
           if(!result.ok)throw Error(result.message||'LIVE_READBACK_FAILED');
           var expected=plan.cuts.filter(function(x){return x.state==='CONFIRMED';})
                .map(function(x){return x.cutId;});
           var missing=plan.cuts.filter(function(x){return x.state==='PLACEHOLDER';})
                .map(function(x){return x.cutId;});
           if(result.planSHA256!==validated.planSHA256||
              result.sequenceId!==seq.sequenceId||
              result.confirmedClipIds.join('|')!==expected.join('|')||
              result.placeholderMarkerIds.join('|')!==missing.join('|')||
              validated.confirmedCount!==expected.length||
              validated.placeholderCount!==missing.length||
              digest(fs.readFileSync(planPath))!==validated.planFileSHA256||
              digest(fs.readFileSync(doc))!==docSHA)
              throw Error('LIVE_READBACK_PLAN_IDENTITY_MISMATCH');
           // Derive an immutable template from authenticated plan, NOT
           // from the untrusted/stale .report.json sidecar.
           var report=validated.reportTemplate;
           if(!report||report.planSHA256!==plan.planSHA256||
              report.items.length!==missing.length)
              throw Error('VALIDATED_REPORT_TEMPLATE_INVALID');
           var recovered=JSON.parse(JSON.stringify(report));
           recovered.phase='POST_READBACK';
           recovered.readbackKind='RECOVERED_FROM_VERIFIED_PREMIERE_TIMELINE_R229';
           recovered.confirmedInsertedCount=expected.length;
           recovered.placeholderReservedCount=missing.length;
           recovered.message='Montaj R220 verificat: '+expected.length+
             ' inserate / '+missing.length+' rezervate.';
           var tmp=last+'.tmp';
           fs.writeFileSync(tmp,JSON.stringify(recovered,null,2),'utf8');
           fs.renameSync(tmp,last);
           var finalReport=JSON.parse(fs.readFileSync(last,'utf8'));
           if(finalReport.phase!=='POST_READBACK'||
              finalReport.planSHA256!==validated.planSHA256)
              throw Error('POST_READBACK_PERSISTENCE_FAILED');
           status(recovered.message+' Generez V3 numai pe CUT-uri confirmate...');
           done(null,recovered,false);
         }catch(e){done(e);}
       });
     });
   });
 });
}
function main(){
 if(busy)return;
 if(!bind())return;
 busy=true;btn.disabled=true;
 // ALWAYS verify ACTIVE sequence from Premiere; cached last_report may
 // refer to another cut or sequence and must never drive V3 blindly.
 recoverOrFallback(function(error,recovered,legacy){
   if(error){status('OPRIT R220 READBACK: '+error.message+' — fără modificări V3.');reset();return;}
   if(legacy){
     // Preserve original, APPROVED legacy synced workflow only when both
     // R220 plan and R220 markers are absent. Call onclick directly to avoid
     // recapturing a synthetic click and keep its existing safety preflight.
     reset();
     var b=currentButton();
     if(b&&typeof b.onclick==='function')b.onclick.call(b);
     else status('Nu există montaj R220 și handlerul legacy 02 lipsește.');
     return;
   }
   startWithReport(recovered);
 });
}
function startWithReport(report){
 var doc=docx();
 try{
  if(!doc||!fs.existsSync(doc)||!/\.docx$/i.test(doc))throw Error('Selectează DOCX în 00.');
  if(!fs.existsSync(GENERATOR)||!fs.existsSync(PY))
   throw Error('Update R2.2.6 incomplet: motor subtitrări lipsă.');
  if(!report.identity||report.identity.docxSHA256!==digest(fs.readFileSync(doc)))
   throw Error('DOCX nu corespunde montajului deja inserat.');
  if(!report.confirmedInsertedCount||report.placeholderReservedCount!==report.items.length)
   throw Error('Readback R220 incomplet. V3 neatinsă.');
 }catch(e){status('OPRIT: '+e.message);reset();return;}
 busy=true;btn.disabled=true;
 status('02: pregătesc numai CUT-urile inserate din montajul R220...');
 var id=report.identity.sequenceId;
 var folder=path.join(ROOT,'Temp','R220');
 var montage=path.join(folder,'montage_'+report.identity.docxSHA256.slice(0,12)+'_'+digest(id).slice(0,12)+'.plan.json');
 var outDir=path.join(ROOT,'Temp','R226');try{fs.mkdirSync(outDir,{recursive:true});}
 catch(e){status('OPRIT: '+e.message);reset();return;}
 var planfile=path.join(outDir,'subtitle_'+report.identity.docxSHA256.slice(0,12)+'_'+digest(id).slice(0,12)+'.json');
 var omit=document.getElementById('r207OmitStruck'),
 omitStruck=!!omit&&omit.checked===true,expectedDocSHA=report.identity.docxSHA256;
 var args=['-X','utf8','-u',GENERATOR,'--docx',doc,'--montage',montage,
  '--report',last,'--output',planfile];
 if(omitStruck)args.push('--omit-struck');
 var child=cp.spawn(PY,args,{cwd:ROOT,windowsHide:true,
    env:Object.assign({},process.env,{PYTHONUTF8:'1',PYTHONIOENCODING:'utf8'})});
 var stdout='',stderr='',finished=false;
 child.stdout.on('data',function(b){stdout+=String(b).slice(0,500000);});
 child.stderr.on('data',function(b){stderr+=String(b).slice(-1000);});
 child.on('error',function(e){if(!finished){finished=true;status('OPRIT: '+e.message);reset();}});
 child.on('close',function(code){
  if(finished)return;finished=true;
  var summary,plan;
  try{
   summary=JSON.parse(stdout.trim());
   if(code!==0||!summary.ok)throw Error(summary.message||stderr.slice(-200));
   if(summary.plan!==planfile||!fs.existsSync(planfile)||
      summary.fileSHA256!==digest(fs.readFileSync(planfile)))throw Error('Plan R226 modificat');
   plan=JSON.parse(fs.readFileSync(planfile,'utf8'));
   if(summary.docxSHA256!==expectedDocSHA||plan.docx_sha256!==expectedDocSHA||
      plan.montagePlanSHA256!==report.planSHA256||plan.sequenceId!==id||
      plan.reservedCount!==report.placeholderReservedCount)throw Error('Planul nu corespunde montajului');
   if(mode.value!=='synced'||(omit&&omit.checked!==omitStruck))
    throw Error('Modul sau bifa s-a schimbat în timpul analizei');
  }catch(e){status('OPRIT: '+e.message+' — V3 neatinsă.');reset();return;}
  var msg='Montaj parțial R220: '+summary.subtitledCuts+' CUT-uri validate, '+
      summary.items+' subtitrări propuse pe V3.\n'+summary.reservedCuts+
      ' CUT-uri rezervate NU vor avea subtitrări.\n'+
      'Timpii fiecărei subtitrări sunt ESTIMAȚI în limitele CUT-ului audio validat, '+
      'nu ancorați cuvânt-cu-cuvânt prin ASR. Verifică-le la redare.\n\n'+
      'Continui pe V3 liberă, fără să modific V1/A1?';
  if(!window.confirm(msg)){
    status('Oprit la alegerea editorului: V3 neatinsă.');reset();return;
  }
  function unchanged(){
   return mode.value==='synced'&&docx()===doc&&
     digest(fs.readFileSync(doc))===expectedDocSHA&&
     digest(fs.readFileSync(planfile))===summary.fileSHA256&&
     (!omit||omit.checked===omitStruck);
  }
  function finishError(problem,n,token){
   if(!n){status('OPRIT: '+problem+' — fără subtitrări inserate.');reset();return;}
   callJS('rollback',[planfile,token],function(err,v){
     status('OPRIT: '+problem+' | '+
       (err?'ROLLBACK NECONFIRMAT: '+err.message:
         (v&&v.ok?v.message:'ROLLBACK NECONFIRMAT: '+(v&&v.message||'eroare'))));
     reset();
   });
  }
  var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\/g,'/');
  runEval('$.evalFile(new File('+JSON.stringify(ext+'/jsx/r226_partial_subtitles.jsx')+'))',
    function(error){
     if(error){status('OPRIT: '+error.message);reset();return;}
     callJS('preflight',[planfile],function(err,valid){
      if(err||!valid||!valid.ok){
       status('OPRIT PREFLIGHT: '+(err?err.message:valid&&valid.message||'eroare')+
         ' — V3 neatinsă.');reset();return;
      }
      var token=valid.token,n=0;
      function next(){
       if(!unchanged()){finishError('DOCX/plan/opțiuni schimbate',n,token);return;}
       if(n>=plan.totalItems){
        callJS('verify',[planfile,token],function(ex,r){
         if(ex||!r||!r.ok){finishError('READBACK: '+(ex?ex.message:r&&r.message||'eroare'),n,token);return;}
         status('[PREMIERE READBACK] '+r.message+' | '+r.sourceCuts+
           ' CUT-uri cu subtitrări, '+r.omitted+' CUT-uri fără audio confirmat.');
         reset();
        });return;
       }
       status('02: inserez V3 '+(n+1)+'/'+plan.totalItems+' · CUT-ALIGNED ESTIMAT');
       callJS('buildOne',[planfile,token,n],function(ex,r){
        if(ex||!r||!r.ok){finishError('MOGRT '+(n+1)+': '+(ex?ex.message:r&&r.message||'eroare'),n,token);return;}
        n++;token=r.token;next();
       });
      }
      next();
     });
    });
 });
}
// Capture before any old onclick/onClick registration. This survives delayed
// R193/R20 initialization, DOM replacement, and legacy handlers assigned later.
function onClickCapture(event){
 var b=currentButton(),m=currentMode();
 if(!b||!m||m.value!=='synced')return;
 if(event.target!==b&&!(b.contains&&b.contains(event.target)))return;
 if(event.preventDefault)event.preventDefault();
 if(event.stopImmediatePropagation)event.stopImmediatePropagation();
 if(event.stopPropagation)event.stopPropagation();
 bind();
 if(!busy)main();
}
document.addEventListener('click',onClickCapture,true);
bind();
if(typeof MutationObserver!=='undefined'){
 var observer=new MutationObserver(function(){bind();});
 if(document.body)observer.observe(document.body,{childList:true,subtree:true});
}
window.AIVE_R228_SUBS={version:'2.2.9',ready:function(){return bind();}};
})();
