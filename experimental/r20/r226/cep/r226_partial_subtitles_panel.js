
/* R2.2.6: one-click R220 partial montage subtitle bridge. If no readback
 * R220 report exists, preserve the original R2.1 synced subtitle handler.
 * The new cue timings are explicitly ESTIMATED WITHIN confirmed CUTs.
 */
(function(){
'use strict';
var btn=document.getElementById('subsR193Start');
var mode=document.getElementById('r20Mode_subs');
if(!btn||!mode||!window.__adobe_cep__)return;
var requireNode=(window.cep_node&&window.cep_node.require)||null;
if(!requireNode)return;
var fs=requireNode('fs'),path=requireNode('path'),cp=requireNode('child_process'),
 crypto=requireNode('crypto'),cep=window.__adobe_cep__;
var ROOT='D:\\AI-Video-Editor',PY=path.join(ROOT,'.venv','Scripts','python.exe');
var GENERATOR=path.join(ROOT,'tools','r226_partial_subtitles.py');
var last=path.join(ROOT,'Temp','R220','last_report.json');
var oldClick=btn.onclick,busy=false;
var statusNode=document.getElementById('subsR193Status');
function status(s){if(statusNode)statusNode.textContent=s;}
function digest(s){return crypto.createHash('sha256').update(s).digest('hex');}
function docx(){var ctx=window.AIVE_CONTEXT_R184;
 return String((ctx&&ctx.getDocx&&ctx.getDocx())||
   (document.getElementById('globalDocx')&&document.getElementById('globalDocx').value)||'').trim();}
function reset(){busy=false;btn.disabled=false;}
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
function main(){
 if(busy)return;
 var report;
 try{report=currentReport();}catch(e){status('OPRIT: raport R220 corupt: '+e.message);return;}
 if(!report){if(oldClick)oldClick.call(btn);return;}
 var doc=docx();
 try{
  if(!doc||!fs.existsSync(doc)||!/\.docx$/i.test(doc))throw Error('Selectează DOCX în 00.');
  if(!fs.existsSync(GENERATOR)||!fs.existsSync(PY))
   throw Error('Update R2.2.6 incomplet: motor subtitrări lipsă.');
  if(!report.identity||report.identity.docxSHA256!==digest(fs.readFileSync(doc)))
   throw Error('DOCX nu corespunde montajului deja inserat.');
  if(!report.confirmedInsertedCount||report.placeholderReservedCount!==report.items.length)
   throw Error('Readback R220 incomplet. V3 neatinsă.');
 }catch(e){status('OPRIT: '+e.message);return;}
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
btn.onclick=function(){if(mode.value!=='synced'){if(oldClick)oldClick.call(btn);return;}main();};
})();
