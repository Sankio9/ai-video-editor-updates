/* R2.3.7 BETA candidate — synced 04 VO graphics from verified R220 audio montage.
   Read-only identity/provenance -> optional approved V5 import. Does not call
   legacy R143 "all audio CUTs matched" gate. No QE/track creation/overwrite.
*/
(function(){
 'use strict';
 var req=null;try{req=(window.cep_node&&window.cep_node.require)||require;}catch(e){}
 var cep=window.__adobe_cep__;
 if(!req||!cep)return;
 var fs=req('fs'),path=req('path'),cp=req('child_process'),crypto=req('crypto'),
     ROOT='D:\\AI-Video-Editor',PY=path.join(ROOT,'.venv','Scripts','python.exe'),
     ENGINE=path.join(ROOT,'tools','r237_vo_plan.py'),busy=false;
 function E(x){return document.getElementById(x);}
 function button(){return E('capsR193Start');}
 function mode(){return E('r20Mode_caps');}
 function digest(bytes){return crypto.createHash('sha256').update(bytes).digest('hex');}
 function docx(){var ctx=window.AIVE_CONTEXT_R184;
   return String((ctx&&ctx.getDocx&&ctx.getDocx())||(E('globalDocx')&&E('globalDocx').value)||'').trim();}
 function msg(x){var el=E('r20Status_caps')||E('capsR193Status');if(el)el.textContent=String(x);
   var log=E('log');if(log){log.textContent+='\nR237 V5: '+x;log.scrollTop=log.scrollHeight;}}
 function done(){busy=false;var b=button();if(b)b.disabled=false;}
 function evalJs(script,cb){cep.evalScript(script,function(raw){
   if(String(raw).indexOf('EvalScript error')>=0){cb(Error('Premiere JS '+String(raw)));return;}
   cb(null,String(raw));
 });}
 function loadJs(filename,cb){
   var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\/g,'/');
   evalJs('$.evalFile(new File('+JSON.stringify(ext+'/jsx/'+filename)+'))',cb);
 }
 function call(symbol,method,args,cb){
   evalJs(symbol+'.'+method+'('+args.map(JSON.stringify).join(',')+')',function(err,raw){
     if(err){cb(err);return;}
     try{cb(null,JSON.parse(raw));}catch(e){cb(Error('Premiere JSON invalid: '+String(raw).slice(0,120)));}
   });
 }
 function py(args,cb){
   var c=null;try{c=cp.spawn(PY,['-X','utf8','-u'].concat(args),{
      cwd:ROOT,windowsHide:true,env:Object.assign({},process.env,{PYTHONUTF8:'1',PYTHONIOENCODING:'utf8'})
   });}catch(err){cb(err);return;}
   var stdout='',stderr='',complete=false;
   c.stdout.on('data',function(b){stdout+=String(b);if(stdout.length>3000000)c.kill();});
   c.stderr.on('data',function(b){stderr=(stderr+String(b)).slice(-1700);});
   c.on('error',function(err){if(!complete){complete=true;cb(err);}});
   c.on('close',function(code){if(complete)return;complete=true;cb(null,{code:code,stdout:stdout,stderr:stderr});});
 }
 function oneState(doc,wordSHA,seqId,planPath,planFileSHA,planSha){
   if(docx()!==doc||!fs.existsSync(doc)||digest(fs.readFileSync(doc))!==wordSHA||
      !fs.existsSync(planPath)||digest(fs.readFileSync(planPath))!==planFileSHA)
     throw Error('DOCX/plan schimbat; nicio inserare');
   if(!seqId||!planSha)return false;return true;
 }
 function buildReport(doc,seq,cb){
   try{
     var wordSHA=digest(fs.readFileSync(doc));
     var base='montage_'+wordSHA.slice(0,12)+'_'+digest(Buffer.from(seq.sequenceId,'utf8')).slice(0,12);
     var planfile=path.join(ROOT,'Temp','R220',base+'.plan.json');
     if(!fs.existsSync(planfile))throw Error('Nu există plan R220 pentru DOCX/sequence active. Folosește Independent din scenariu.');
     var fileSHA=digest(fs.readFileSync(planfile));
     var original=JSON.parse(fs.readFileSync(planfile,'utf8'));
     if(original.identity.docxSHA256!==wordSHA||original.identity.sequenceId!==seq.sequenceId)
       throw Error('Planul R220 aparține altui DOCX/secvență');
     py([path.join(ROOT,'tools','r229_validate_r220.py'),
         '--docx',doc,'--plan',planfile,'--sequence-id',seq.sequenceId],function(e,r){
       if(e){cb(e);return;}
       var v;
       try{
         var pos=r.stdout.lastIndexOf('AIVE_R229_RESULT ');
         if(pos<0)throw Error('Validatorul R220 nu a returnat un rezultat');
         v=JSON.parse(r.stdout.slice(pos+18).trim());
         if(r.code!==0||!v.ok||v.planFileSHA256!==fileSHA||
            v.docxSHA256!==wordSHA||v.planSHA256!==original.planSHA256||
            v.sequenceId!==seq.sequenceId)throw Error(v&&v.message||'Validarea planului R220 a eșuat');
         if(original.cuts.filter(function(x){return x.state==='VO_RESERVE';}).length<1)
           throw Error('Montajul nu are spații VO. Folosește Independent din scenariu.');
       }catch(err){cb(err);return;}
       call('AIVE_R227_RECOVERY','recover',[original],function(problem,checked){
         if(problem||!checked||!checked.ok){cb(problem||Error(checked&&checked.message||'READBACK R220 eșuat'));return;}
         try{
           var confirmed=original.cuts.filter(function(x){return x.state==='CONFIRMED';}).map(function(x){return x.cutId;});
           var reserved=original.cuts.filter(function(x){return x.state==='PLACEHOLDER';}).map(function(x){return x.cutId;});
           if(checked.sequenceId!==seq.sequenceId||checked.planSHA256!==original.planSHA256||
              checked.confirmedClipIds.join('|')!==confirmed.join('|')||
              checked.placeholderMarkerIds.join('|')!==reserved.join('|'))
             throw Error('READBACK clipuri/markere neconforme cu planul');
           oneState(doc,wordSHA,seq.sequenceId,planfile,fileSHA,original.planSHA256);
           var report=v.reportTemplate;
           if(!report||report.planSHA256!==original.planSHA256)throw Error('Raport R220 invalid');
           report.phase='POST_READBACK';report.identity=original.identity;
           report.confirmedInsertedCount=confirmed.length;
           report.placeholderReservedCount=reserved.length;
           report.items=original.cuts.filter(function(x){return x.state==='PLACEHOLDER';});
           report.readbackKind='RECOVERED_FROM_LIVE_PREMIERE_READBACK';
           var folder=path.join(ROOT,'Temp','R237');
           fs.mkdirSync(folder,{recursive:true});
           var prefix=base+'_vo';
           var reportfile=path.join(folder,prefix+'.readback.json');
           fs.writeFileSync(reportfile+'.tmp',JSON.stringify(report,null,2),'utf8');
           fs.renameSync(reportfile+'.tmp',reportfile);
           cb(null,{doc:doc,wordSHA:wordSHA,sequenceId:seq.sequenceId,
                    montage:planfile,montageFileSHA:fileSHA,
                    montageSHA:original.planSHA256,report:reportfile,
                    confirmed:confirmed.length,reserved:reserved.length,
                    vo:original.cuts.filter(function(x){return x.state==='VO_RESERVE';}).length});
         }catch(err){cb(err);}
       });
     });
   }catch(e){cb(e);}
 }
 function generate(state,cb){
   if(!fs.existsSync(ENGINE)||!fs.existsSync(PY)){cb(Error('R237 VO planner/Python lipsește; instalare incompletă'));return;}
   var f=path.join(ROOT,'Temp','R237','vo_'+state.wordSHA.slice(0,12)+'_'+digest(Buffer.from(state.sequenceId)).slice(0,12)+'.json');
   py([ENGINE,'--docx',state.doc,'--montage',state.montage,
       '--report',state.report,'--output',f],function(err,r){
     if(err){cb(err);return;}
     try{
       var a=JSON.parse(r.stdout.trim());
       if(r.code!==0||!a.ok||a.path!==f||!fs.existsSync(f))
         throw Error(a.message||r.stderr||'Generator V5 nu a returnat plan');
       if(digest(fs.readFileSync(f))!==a.sha256)throw Error('SHA plan V5 schimbat');
       var p=JSON.parse(fs.readFileSync(f,'utf8'));
       if(p.module!=='04'||p.mode!=='montage_vo'||p.r237Schema!=='aive-r237-vo-montage-v1'||
          p.timing!=='VO_RESERVE_ESTIMATED'||p.sequenceId!==state.sequenceId||
          p.montagePlanSHA256!==state.montageSHA||p.docx_sha256!==state.wordSHA||
          p.totalVO!==state.vo||p.totalItems!==a.items)
         throw Error('Schema/identitatea VO V5 invalidă');
       cb(null,{path:f,sha:a.sha256,plan:p});
     }catch(e){cb(e);}
   });
 }
 function insert(state,vo){
   var count=0,token='';
   function unchanged(){
     return mode()&&mode().value==='synced'&&oneState(state.doc,state.wordSHA,
       state.sequenceId,state.montage,state.montageFileSHA,state.montageSHA)&&
       digest(fs.readFileSync(vo.path))===vo.sha;
   }
   function aborted(reason){
     if(count<1){msg('OPRIT V5: '+reason+' — nicio inserare.');done();return;}
     call('$._AIVE_R237_VO_','rollback',[vo.path,token,count],function(err,r){
       msg('OPRIT V5: '+reason+' | '+(err?'ROLLBACK NECONFIRMAT: '+err.message:
           r&&r.ok?r.message:'ROLLBACK NECONFIRMAT: '+(r&&r.message||'necunoscut')));
       done();
     });
   }
   loadJs('r237_vo_graphics.jsx',function(e){
     if(e){msg('OPRIT: '+e.message);done();return;}
     try{if(!unchanged())throw Error('DOCX/montaj/generator schimbat');}
     catch(x){msg('OPRIT: '+x.message);done();return;}
     call('$._AIVE_R237_VO_','validate',[vo.path,'zero'],function(e,r){
       if(e||!r||!r.ok){msg('OPRIT PREFLIGHT V5: '+(e?e.message:r&&r.message||'necunoscut')+' — V5 neatinsă.');done();return;}
       token=r.token;
       function next(){
         try{if(!unchanged()){aborted('DOCX, opțiune sau plan modificat');return;}}
         catch(x){aborted(x.message);return;}
         if(count>=vo.plan.totalItems){
           call('$._AIVE_R237_VO_','verify',[vo.path,token],function(err,r){
             if(err||!r||!r.ok){aborted('READBACK: '+(err?err.message:r&&r.message||'invalid'));return;}
             msg('[PREMIERE READBACK] '+r.message+' | '+vo.plan.totalVO+
                 ' blocuri VO, '+vo.plan.totalItems+' MOGRT pe V5, '+state.reserved+
                 ' CUT-uri audio lipsă au rămas rezervate. Timpii VO sunt estimați.');
             done();
           });return;
         }
         msg('Inserez V5 '+(count+1)+'/'+vo.plan.totalItems+' · VO editorial estimat.');
         call('$._AIVE_R237_VO_','buildOne',[vo.path,token,count],function(err,r){
           if(err||!r||!r.ok){aborted('MOGRT '+(count+1)+': '+(err?err.message:r&&r.message||'invalid'));return;}
           count++;token=r.token;next();
         });
       }
       next();
     });
   });
 }
 function start(){
   if(busy)return;
   var doc=docx(),b=button(),m=mode();
   if(!doc||!/\.docx$/i.test(doc)||!fs.existsSync(doc)){msg('Alege DOCX valid în 00.');return;}
   if(!m||m.value!=='synced')return;
   busy=true;if(b)b.disabled=true;
   msg('Verific planul R220 și starea reală V1/A1, markerele și spațiile VO...');
   loadJs('r227_montage_recovery.jsx',function(e){
     if(e){msg('OPRIT: '+e.message);done();return;}
     call('AIVE_R227_RECOVERY','identity',[],function(err,seq){
       if(err||!seq||!seq.ok){msg('OPRIT: '+(err?err.message:seq&&seq.message||'Secvență inaccesibilă'));done();return;}
       if(!seq.sequenceId||!seq.name||seq.name.indexOf('[AIVE TEST]')<0){
         msg('OPRIT: activează o secvență COPIE [AIVE TEST]; nu inserez în montajul original.');done();return;
       }
       buildReport(doc,seq,function(err,state){
         if(err){msg('OPRIT R220 READBACK: '+err.message+' — V5 neatinsă.');done();return;}
         msg('Plan R220 valid: '+state.confirmed+' confirmate, '+state.reserved+' rezervate, '+
             state.vo+' blocuri VO. Generez textul cartoanelor.');
         generate(state,function(err,vo){
           if(err){msg('OPRIT VO: '+err.message+' — V5 neatinsă.');done();return;}
           if(!window.confirm('Generez '+vo.plan.totalItems+' cartoane pe V5 în '+
              state.vo+' spații VO R220, cu temporizare EDITORIALĂ estimată. '+
              'Sincronurile audio rezervate rămân nemodificate. V5 trebuie să fie liberă. Continui?')){
             msg('Oprit la alegerea editorului. V5 neatinsă.');done();return;
           }
           insert(state,vo);
         });
       });
     });
   });
 }
 function captured(event){
   var b=button(),m=mode();
   if(!b||!m||m.value!=='synced')return;
   if(event.target!==b&&!(b.contains&&b.contains(event.target)))return;
   if(event.preventDefault)event.preventDefault();
   if(event.stopImmediatePropagation)event.stopImmediatePropagation();
   if(event.stopPropagation)event.stopPropagation();
   start();
 }
 document.addEventListener('click',captured,true);
 window.AIVE_R237_VO_UI={ready:true};
})();
