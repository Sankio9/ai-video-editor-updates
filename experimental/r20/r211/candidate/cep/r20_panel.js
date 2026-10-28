/* R2.0 experimental: independent 02/03/04 workflow, without changing stable synced executors.
   CEP ES5 / Node enabled. Only one DOCX selected in 00; one button per category. */
(function(){'use strict';
 function E(id){return document.getElementById(id);}
 var req=null,cep=window.__adobe_cep__;
 try{req=(window.cep_node&&window.cep_node.require)||require;}catch(ignore){}
 if(!req||!cep)return;
 var fs=req('fs'),path=req('path'),crypto=req('crypto'),cp=req('child_process'),root='D:\\AI-Video-Editor';
 var PY=path.join(root,'.venv','Scripts','python.exe'),PLANNER=path.join(root,'tools','r20_graphics_plans.py');
 var settings={subs:{num:'02',track:'V3'},name:{num:'03',track:'V4'},caps:{num:'04',track:'V5'}};
 var busy=false,installed=false;
 function status(key,message){var area=E('r20Status_'+key);if(area)area.textContent=message;
   var log=E('log');if(log){log.textContent+='\nR20 '+key+': '+message;log.scrollTop=log.scrollHeight;}}
 function progress(text,done,total){var bar=E('r20Progress'),line=E('r20ProgressText');
   if(!bar||!line)return;bar.style.display='block';line.textContent=text+(total?' ('+done+'/'+total+')':'');}
 function finish(){busy=false;var bar=E('r20Progress');if(bar)bar.style.display='none';var b=E('subsR193Start');if(b&&E('r20Mode_subs')&&E('r20Mode_subs').value==='independent')b.disabled=false;}
 function sha(p){return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');}
 function fileValid(doc){return !!doc && /\.docx$/i.test(doc)&&fs.existsSync(doc)&&fs.statSync(doc).isFile();}
 function docx(){var ctx=window.AIVE_CONTEXT_R184;return String((ctx&&ctx.getDocx&&ctx.getDocx())||(E('globalDocx')&&E('globalDocx').value)||'').trim();}
 function evalR20(method,args,cb){var ext=decodeURIComponent(cep.getSystemPath('extension')).replace(/\\/g,'/');
   var js='$.evalFile(new File('+JSON.stringify(ext+'/jsx/r20_graphics.jsx')+'))';
   cep.evalScript(js,function(loaded){if(String(loaded).indexOf('EvalScript error')!==-1){cb(Error('Nu s-a încărcat R2.0 JSX: '+loaded));return;}
     cep.evalScript('$._AIVE_R20_.'+method+'('+args.map(JSON.stringify).join(',')+')',function(raw){
       try{var r=JSON.parse(raw);cb(null,r);}catch(e){cb(Error('Răspuns invalid Premiere: '+String(raw).slice(0,250)));}
     });
   });
 }
 function generate(module,doc,callback,omitStruck){try{
   omitStruck=module==='02'&&omitStruck===true;
   if(!fs.existsSync(PY)||!fs.existsSync(PLANNER))throw Error('Motor R2.0 lipsă — nu modific timeline-ul.');
   var docHash=sha(doc),folder=path.join(root,'Temp','R20',docHash.slice(0,24));
   if(!fs.existsSync(folder))fs.mkdirSync(folder,{recursive:true});
   var outfile=path.join(folder,'R20_'+module+(module==='02'?(omitStruck?'_OMIT_STRUCK':'_INCLUDE_STRUCK'):'')+'.json');
   var args=['-X','utf8','-u',PLANNER,'--docx',doc,'--module',module,'--output',outfile];
   if(omitStruck)args.push('--omit-struck');
   var env=Object.assign({},process.env,{PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8'});
   var child=cp.spawn(PY,args,{cwd:root,windowsHide:true,env:env}),std='',err='',ended=false;
   child.stdout.on('data',function(b){std+=String(b);});child.stderr.on('data',function(b){err+=String(b);});
   child.on('error',function(e){if(ended)return;ended=true;callback(e);});
   child.on('close',function(code){if(ended)return;ended=true;
     try{if(code!==0)throw Error(err.slice(-500)||'Generatorul DOCX a eșuat');
       var r=JSON.parse(std.trim());if(!r.ok||r.docx_sha256!==docHash||r.plan!==outfile)throw Error('Rezultatul Python / DOCX SHA nu corespunde');
       var plan=JSON.parse(fs.readFileSync(outfile,'utf8'));
       if(plan.docx_sha256!==docHash||plan.module!==module||plan.totalItems!==r.count)throw Error('Planul R2.0 este inconsistent');
       if(!Array.isArray(plan.skipped)||!Array.isArray(r.skipped)
          ||JSON.stringify(plan.skipped)!==JSON.stringify(r.skipped)
          ||plan.reviewRequired!==plan.skipped.some(function(x){return x.kind==='REVIEW_MISSING_IDENTITY';})
          ||r.reviewRequired!==plan.reviewRequired
          ||plan.reviewPolicy!==(plan.reviewRequired?'EXPLICIT_SKIP_APPROVAL':(plan.skipped.length?'AUTO_AMBIENCE_SKIP':'NONE')))
         throw Error('Raportul de revizuire NameTag este inconsistent');
       if(module!=='03'&&plan.reviewRequired)throw Error('Omitere neașteptată în modul '+module);
       // Runtime handshake catches stale CEP/Python copies and old helpers:
       // a previous R2.0.9 helper must NEVER be used with the new 2-phase UI.
       if(plan.generatorVersion!=='R2.1.1-auto-preflight-readable'||
          r.generatorVersion!==plan.generatorVersion)
         throw Error('ENGINE_VERSION_MISMATCH: motorul DOCX nu este cel din update. Analiza este blocată.');
       if(module==='02' && (plan.strikeAnalysisReady!==true||
          r.strikeAnalysisReady!==true||!Array.isArray(plan.strikeAudit)||
          plan.strikeAudit.length!==r.strikeAuditCount))
         throw Error('STRIKE_ANALYSIS_INCOMPLETE: previzualizarea DOCX este invalidă.');
       if(module==='02'&&omitStruck &&
          (!(plan.removedStrikeCharacters>0)||!(plan.strikeCutsChanged>0)||
            plan.strikeAudit.length!==plan.strikeCutsChanged))
         throw Error('STRIKETHROUGH_NOT_DETECTED: bifa ON, dar analiza nu a identificat text de omis. V3 nu se modifică.');
       var expectedStrike=module==='02'?(omitStruck?'OMIT_STRUCK':'INCLUDE_STRUCK'):'NOT_APPLICABLE';
       if(plan.strikePolicy!==expectedStrike||r.strikePolicy!==expectedStrike||
          plan.removedStrikeCharacters!==r.removedStrikeCharacters||
          plan.strikeCutsChanged!==r.strikeCutsChanged||
          !Array.isArray(plan.omittedStrikeCuts)||JSON.stringify(plan.omittedStrikeCuts)!==JSON.stringify(r.omittedStrikeCuts))
         throw Error('Politica pentru text tăiat a fost modificată; opresc înainte de Premiere.');
       callback(null,{path:outfile,sha:docHash,planSha:sha(outfile),
         items:r.count,groups:r.groups,
         timing:r.timing,skipped:plan.skipped,reviewRequired:plan.reviewRequired,
         strikePolicy:plan.strikePolicy,omittedStrikeCuts:plan.omittedStrikeCuts,
         strikeCutsChanged:plan.strikeCutsChanged,removedStrikeCharacters:plan.removedStrikeCharacters,
         strikeAudit:plan.strikeAudit,strikeAnalysisReady:plan.strikeAnalysisReady});
     }catch(e){callback(e);}
   });
   }catch(e){callback(e);}}
 function conflict(key,inventory){var host=E('r20Conflict_'+key);if(!host)return;
   host.style.display='block';host.innerHTML='';
   var title=document.createElement('div');title.innerHTML='<strong>V5 este ocupată.</strong> Nicio ștergere automată.';host.appendChild(title);
   var info=document.createElement('pre');info.className='r20-inventory';info.textContent=inventory.map(function(x){return x.kind+' · '+x.name+' ['+x.start.toFixed(2)+'–'+x.end.toFixed(2)+' s]';}).join('\n');host.appendChild(info);
   var overwrite=document.createElement('button');overwrite.textContent='Suprascrie materialele de pe V5';host.appendChild(overwrite);
   overwrite.onclick=function(){if(!window.confirm('ATENȚIE: suprascrierea V5 este distructivă. Confirmi că ai făcut backup al proiectului de test?'))return;
     status(key,'OPRIT PREVENTIV: executarea suprascrierii distructive nu este certificată în Premiere. V5 rămâne neschimbată.');};
   var stop=document.createElement('button');stop.className='secondary';stop.textContent='Oprește, eliberez V5';host.appendChild(stop);
   stop.onclick=function(){host.style.display='none';status(key,'Oprit. Eliberează manual V5; nicio ștergere nu a fost executată.');};
 }
 function run(key,verified){if(busy)return;var cfg=settings[key],doc=docx();
   // 02 may insert only an immutable plan generated and verified by internal preflight.
   if(key==='subs'&&(!verified||!verified.plan||verified.doc!==doc)){
     status(key,'OPRIT: analiza DOCX obligatorie nu a fost finalizată. V3 neschimbată.');
     return;
   }
   var strikeOption=E('r207OmitStruck'),omitStruck=key==='subs'&&!!strikeOption&&strikeOption.checked===true;
   if(!fileValid(doc)){status(key,'Alege un scenariu DOCX valid în modulul 00.');return;}
   var seqPolicy=E('r20Position_'+key).value;if(seqPolicy!=='zero'&&seqPolicy!=='append')return;
   if(key==='subs'){
     if(verified.position!==seqPolicy||verified.omitStruck!==omitStruck || sha(doc)!==verified.plan.sha ||
        !fs.existsSync(verified.plan.path) || sha(verified.plan.path)!==verified.plan.planSha){
       status(key,'OPRIT: DOCX, bifa sau planul s-a schimbat. Nicio inserare pe V3.');return;
     }
     if(omitStruck && (!(verified.plan.removedStrikeCharacters>0) ||
          !verified.plan.strikeAudit || !verified.plan.strikeAudit.length)){
       status(key,'OPRIT: analiza NU confirmă eliminări Strikethrough. Fără inserare V3.');return;
     }
   }
   busy=true;E('r20Conflict_'+key).style.display='none';progress('Verific planul '+cfg.num+' pregătit',0,0);
   function withPlan(err,plan){if(err){status(key,'OPRIT: '+err.message);finish();return;}
     if(key==='subs'&&strikeOption&&strikeOption.checked!==omitStruck){status(key,'OPRIT: bifa de text tăiat s-a schimbat în timpul pregătirii. Nicio inserare.');finish();return;}
     var skipReport='';
     if(cfg.num==='03'&&plan.skipped.length){
       skipReport=plan.skipped.map(function(x){return String(x.kind)+' · '+String(x.cutId)+
         ' (paragraful '+String(x.paragraph)+', sursa '+String(x.sourceCode||'?')+') — '+String(x.reason);}).join('\n');
       if(plan.reviewRequired){
         var reviewItems=plan.skipped.filter(function(x){return x.kind==='REVIEW_MISSING_IDENTITY';});
         var question='REVIZUIRE EDITORIALĂ NAMETAG — '+reviewItems.length+' identificări NECONFIRMATE:\n'+
           reviewItems.map(function(x){return String(x.cutId)+' · sursa '+String(x.sourceCode||'?');}).join('\n')+
           '\n\nVor fi create numai '+plan.items+' NameTag-uri valide pe V4.'+
           '\nAMB marcate SKIP nu primesc burtieră. Nicio identitate nu va fi inventată.'+
           '\n\nAprobi OMITEREA identificărilor neconfirmate în proiectul TEST?';
         if(!window.confirm(question)){
           status(key,'OPRIT: omiterile SINCRON nu sunt aprobate. Nicio inserare V4.\n'+skipReport);
           finish();return;
         }
         status(key,'REVIEW APROBAT: '+reviewItems.length+' identificări fără burtieră.\n'+skipReport);
       }else{
         status(key,'SKIP_AMBIENCE: '+plan.skipped.length+' fragmente de ambianță fără NameTag.\n'+skipReport);
       }
     }
     var n=0,tok='';
     function abort(reason){
       if(n===0){status(key,'OPRIT: '+reason+' — fără inserări anterioare.');finish();return;}
       progress('Rollback grafică inserată',n,plan.items);
       evalR20('rollback',[plan.path,tok,n],function(ex,undo){
         status(key,'OPRIT: '+reason+' | '+(ex?'ROLLBACK NECONFIRMAT: '+ex.message:(undo&&undo.ok?undo.message:'ROLLBACK NECONFIRMAT: '+(undo&&undo.message||'eroare'))));finish();
       });
     }
     progress('Verific pista '+cfg.track+' în Premiere',0,plan.items);
     evalR20('validate',[plan.path,seqPolicy],function(error,r){
       if(error||!r||!r.ok){status(key,'OPRIT: '+(error?error.message:r&&r.message||'preflight eșuat'));
         if(r&&r.needsChoice)conflict(key,r.inventory||[]);finish();return;}
       tok=r.token;status(key,plan.timing+' — '+plan.items+' MOGRT / '+plan.groups+' grupuri. Inserare pe '+cfg.track+'.');
       function next(){if(n>=plan.items){progress('Verific readback MOGRT',n,plan.items);
           evalR20('verify',[plan.path,tok],function(ex,done){
             if(ex||!done||!done.ok){abort('READBACK FINAL: '+(ex?ex.message:done&&done.message||'răspuns invalid'));return;}
             status(key,'[PREMIERE READBACK] '+done.message+
               (key==='subs'&&omitStruck?'\n[DOCX STRIKETHROUGH] Omise '+plan.removedStrikeCharacters+
                ' caractere tăiate în '+plan.strikeCutsChanged+' CUT-uri; CUT-uri eliminate integral: '+
                plan.omittedStrikeCuts.length+'.':'')+
               (skipReport?'\n['+(plan.reviewRequired?'REVIEW APROBAT':'SKIP_AMBIENCE')+
               '] '+plan.skipped.length+' fragmente fără NameTag:\n'+skipReport:''));finish();});return;}
         if(sha(doc)!==plan.sha){abort('DOCX schimbat în timpul inserării');return;}
         if(!fs.existsSync(plan.path)||sha(plan.path)!==plan.planSha){
           abort('Planul DOCX s-a schimbat după analiză');return;
         }
         if(key==='subs'&&strikeOption&&strikeOption.checked!==omitStruck){abort('Bifa Strikethrough schimbată în timpul inserării');return;}
         progress('Inserez '+cfg.track+' · '+plan.timing,n,plan.items);
         evalR20('buildOne',[plan.path,tok,n],function(ex,out){if(ex||!out||!out.ok){abort('Inserarea '+(n+1)+'/'+plan.items+': '+(ex?ex.message:out&&out.message||'răspuns invalid'));return;}
           tok=out.token;n++;next();});
       }next();
     });
   }
   if(key==='subs')withPlan(null,verified.plan);
   else generate(cfg.num,doc,withPlan);
 }
 function runSubtitlesOneClick(){
   if(busy)return;
   var doc=docx(),option=E('r207OmitStruck'),mode=E('r20Mode_subs'),
       position=E('r20Position_subs');
   if(!fileValid(doc)){status('subs','OPRIT: selectează un DOCX valid în 00.');return;}
   if(!option||!mode||mode.value!=='independent'||!position ||
      (position.value!=='zero'&&position.value!=='append')){
     status('subs','OPRIT: modul și poziția V3 sunt invalide.');return;
   }
   var policy=option.checked===true,selectedPosition=position.value,docHash=sha(doc);
   busy=true;var btn=E('subsR193Start');if(btn)btn.disabled=true;
   progress('1/2 · Analizez DOCX și bifa Strikethrough',0,2);
   status('subs','Analizez Word, elimin textul tăiat doar dacă bifa este activă. V3 neatinsă.');
   generate('02',doc,function(error,plan){
     if(error){status('subs','OPRIT la analiza DOCX: '+error.message+' — V3 neatinsă.');finish();return;}
     if(doc!==docx()||!fs.existsSync(doc)||sha(doc)!==docHash||
       option.checked!==policy||mode.value!=='independent'||position.value!==selectedPosition){
       status('subs','OPRIT: DOCX, bifa, modul sau poziția s-au modificat. V3 neatinsă.');finish();return;
     }
     if(!plan.strikeAnalysisReady||!fs.existsSync(plan.path)||sha(plan.path)!==plan.planSha||
        (policy&&(!(plan.removedStrikeCharacters>0)||!plan.strikeAudit.length))){
       status('subs','OPRIT: verificarea textului tăiat a eșuat. V3 neatinsă.');finish();return;
     }
     // Only the second phase is allowed to access Premiere.
     busy=false;if(btn)btn.disabled=false;
     progress('2/2 · Verific V3 și inserez subtitrările',1,2);
     status('subs','DOCX verificat: '+plan.items+' subtitrări, '+
       plan.removedStrikeCharacters+' caractere tăiate omise în '+
       plan.strikeCutsChanged+' CUT-uri. Urmează inserarea pe V3.');
     run('subs',{doc:doc,omitStruck:policy,position:selectedPosition,plan:plan});
   },policy);
 }
 function safeCapsLegacy(){var a=E('capsProceed'),b=E('capsClear');
   if(!a||!b||a.getAttribute('data-r20-fixed'))return;
   a.setAttribute('data-r20-fixed','1');var old=a.onclick;
   a.textContent='Suprascrie materialele de pe V5';b.textContent='Oprește, eliberez V5';
   a.onclick=function(){if(window.confirm('Suprascrierea V5 poate șterge video/foto/MOGRT. Ai salvat o copie separată a proiectului și accepți pierderea materialelor V5?')){
     if(old)old.call(a);}};
   b.onclick=function(){E('capsConflict').style.display='none';if(E('capsStatus'))E('capsStatus').textContent='OPRIT: eliberează manual V5 și verifică din nou. Nicio ștergere executată.';};
 }
 function install(){if(installed)return;
   for(var k in settings)if(settings.hasOwnProperty(k)&&!E(k+'R193Start'))return;
   installed=true;
   var global=document.createElement('div');global.id='r20Progress';global.style.cssText='display:none;position:sticky;top:0;z-index:100;background:#1c3850;color:#fff;padding:9px;border:1px solid #5d94c1;border-radius:4px;';
   var line=document.createElement('div');line.id='r20ProgressText';global.appendChild(line);
   var main=document.querySelector('main');if(main)main.insertBefore(global,main.firstChild);
   for(var key in settings)if(settings.hasOwnProperty(key))(function(k){
     var btn=E(k+'R193Start'),old=btn.onclick,originalDisabled=btn.disabled,config=settings[k],module=E('module'+(k==='subs'?'Subs':k==='name'?'Name':'Caps')),content=module.querySelector('.content');
     var legacyTag=module.querySelector('summary .small'),originalTag=legacyTag?legacyTag.textContent:'';
     // Snapshot the untouched legacy UI before adding independent controls.
     // Hiding legacy elements must NOT remove or rewrite their event handlers,
     // styles, or state; switching back to Synced restores every original node.
     var legacy=[];
     for(var i=0;i<content.children.length;i++){
       var node=content.children[i];if(node!==btn)legacy.push({node:node,display:node.style.display});
     }
     function setLegacyVisible(independent){
       for(var j=0;j<legacy.length;j++)legacy[j].node.style.display=independent?'none':legacy[j].display;
     }
     var wrap=document.createElement('div');wrap.className='r20-options';
     var mode=document.createElement('select');mode.id='r20Mode_'+k;
     [['synced','Pe montajul existent'],['independent','Independent din scenariu']].forEach(function(v){var o=document.createElement('option');o.value=v[0];o.textContent=v[1];mode.appendChild(o);});
     var position=document.createElement('select');position.id='r20Position_'+k;
     [['zero','De la începutul pistei (00:00)'],['append','După ultimul element de pe pistă']].forEach(function(v){var o=document.createElement('option');o.value=v[0];o.textContent=v[1];position.appendChild(o);});
     var hint=document.createElement('div');hint.id='r20Status_'+k;hint.className='r192-message';hint.textContent='Alege modul de lucru. 05 VO rămâne HOLD.';
     var conflictBox=document.createElement('div');conflictBox.id='r20Conflict_'+k;conflictBox.style.display='none';
     wrap.appendChild(mode);wrap.appendChild(position);position.style.display='none';

     var strikeLabel=null,strikeInput=null;
     if(k==='subs'){
       strikeLabel=document.createElement('label');strikeLabel.className='r207-strike-policy';
       strikeLabel.style.display='block';
       strikeInput=document.createElement('input');strikeInput.type='checkbox';strikeInput.id='r207OmitStruck';
       strikeInput.checked=false;strikeLabel.appendChild(strikeInput);
       var strikeText=document.createElement('span');
       strikeText.textContent=' Omite textul tăiat (Strikethrough) din DOCX';
       strikeLabel.appendChild(strikeText);
       content.insertBefore(strikeLabel,btn);
       strikeInput.onchange=function(){
         status('subs','Opțiune actualizată. La inserare verific automat DOCX și apoi V3.');
       };
     }
     content.insertBefore(wrap,btn);content.insertBefore(conflictBox,btn.nextSibling);content.insertBefore(hint,btn.nextSibling);
     mode.onchange=function(){var independent=mode.value==='independent';position.style.display=independent?'block':'none';setLegacyVisible(independent);
       if(legacyTag)legacyTag.textContent=independent?'R2.0 Beta · '+config.track:originalTag;
       if(strikeInput){
         btn.disabled=originalDisabled;
         strikeInput.disabled=!independent;
         strikeLabel.style.opacity=independent?'1':'.55';
         strikeLabel.title=independent?'Analiza Word rulează automat înainte de inserare.':'Modul sincronizat nu acceptă încă filtrarea Strikethrough.';
       }
       btn.textContent=independent?(k==='subs'?'Inserează subtitrările':'Generează '+config.track+' din DOCX'):({'subs':'Adaugă subtitrările','name':'Adaugă NameTag','caps':'Adaugă cartoanele'})[k];
       conflictBox.style.display='none';hint.textContent=independent?(k==='subs'?'PREVIEW TIMING — fără sincronism audio.':(k==='caps'?'Cartoane din DOCX 00 · V5 · EDITORIAL_PREVIEW; fără goluri de montaj.':'Grafică din DOCX 00 · EDITORIAL_PREVIEW; fără V1/A1.')):'Pe montajul deja validat.';};
     btn.onclick=function(){if(mode.value==='independent'){if(k==='subs')runSubtitlesOneClick();else run(k,null);}else if(old)old.call(btn);};mode.onchange();
   })(key);
   safeCapsLegacy();
 }
 // 00 and 02 are open in some old panel builds. All sections MUST start closed.
 var all=document.querySelectorAll('details.module');for(var a=0;a<all.length;a++)all[a].open=false;
 install();var observer=new MutationObserver(function(){if(!installed)install();});
 observer.observe(document.body,{childList:true,subtree:true});
})();
