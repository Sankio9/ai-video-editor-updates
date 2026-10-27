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
 function finish(){busy=false;var bar=E('r20Progress');if(bar)bar.style.display='none';}
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
 function generate(module,doc,callback){try{
   if(!fs.existsSync(PY)||!fs.existsSync(PLANNER))throw Error('Motor R2.0 lipsă — nu modific timeline-ul.');
   var docHash=sha(doc),folder=path.join(root,'Temp','R20',docHash.slice(0,24));
   if(!fs.existsSync(folder))fs.mkdirSync(folder,{recursive:true});
   var outfile=path.join(folder,'R20_'+module+'.json');
   var args=['-X','utf8','-u',PLANNER,'--docx',doc,'--module',module,'--output',outfile];
   var env=Object.assign({},process.env,{PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8'});
   var child=cp.spawn(PY,args,{cwd:root,windowsHide:true,env:env}),std='',err='',ended=false;
   child.stdout.on('data',function(b){std+=String(b);});child.stderr.on('data',function(b){err+=String(b);});
   child.on('error',function(e){if(ended)return;ended=true;callback(e);});
   child.on('close',function(code){if(ended)return;ended=true;
     try{if(code!==0)throw Error(err.slice(-500)||'Generatorul DOCX a eșuat');
       var r=JSON.parse(std.trim());if(!r.ok||r.docx_sha256!==docHash||r.plan!==outfile)throw Error('Rezultatul Python / DOCX SHA nu corespunde');
       var plan=JSON.parse(fs.readFileSync(outfile,'utf8'));
       if(plan.docx_sha256!==docHash||plan.module!==module||plan.totalItems!==r.count)throw Error('Planul R2.0 este inconsistent');
       callback(null,{path:outfile,sha:docHash,items:r.count,groups:r.groups,timing:r.timing});
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
 function run(key){if(busy)return;var cfg=settings[key],doc=docx();
   if(!fileValid(doc)){status(key,'Alege un scenariu DOCX valid în modulul 00.');return;}
   var seqPolicy=E('r20Position_'+key).value;if(seqPolicy!=='zero'&&seqPolicy!=='append')return;
   busy=true;E('r20Conflict_'+key).style.display='none';progress('Pregătesc '+cfg.num+' din DOCX',0,0);
   generate(cfg.num,doc,function(err,plan){if(err){status(key,'OPRIT: '+err.message);finish();return;}
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
           evalR20('verify',[plan.path,tok],function(ex,done){status(key,ex?'READBACK EROARE: '+ex.message:
              ((done.ok?'[PREMIERE READBACK] ':'EROARE: ')+done.message));finish();});return;}
         if(sha(doc)!==plan.sha){abort('DOCX schimbat în timpul inserării');return;}
         progress('Inserez '+cfg.track+' · '+plan.timing,n,plan.items);
         evalR20('buildOne',[plan.path,tok,n],function(ex,out){if(ex||!out||!out.ok){abort('Inserarea '+(n+1)+'/'+plan.items+': '+(ex?ex.message:out&&out.message||'răspuns invalid'));return;}
           tok=out.token;n++;next();});
       }next();
     });
   });
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
     var btn=E(k+'R193Start'),old=btn.onclick,config=settings[k],content=E('module'+(k==='subs'?'Subs':k==='name'?'Name':'Caps')).querySelector('.content');
     var wrap=document.createElement('div');wrap.className='r20-options';
     var mode=document.createElement('select');mode.id='r20Mode_'+k;
     [['synced','Pe montajul existent'],['independent','Independent din scenariu']].forEach(function(v){var o=document.createElement('option');o.value=v[0];o.textContent=v[1];mode.appendChild(o);});
     var position=document.createElement('select');position.id='r20Position_'+k;
     [['zero','De la începutul pistei (00:00)'],['append','După ultimul element de pe pistă']].forEach(function(v){var o=document.createElement('option');o.value=v[0];o.textContent=v[1];position.appendChild(o);});
     var hint=document.createElement('div');hint.id='r20Status_'+k;hint.className='r192-message';hint.textContent='Alege modul de lucru. 05 VO rămâne HOLD.';
     var conflictBox=document.createElement('div');conflictBox.id='r20Conflict_'+k;conflictBox.style.display='none';
     wrap.appendChild(mode);wrap.appendChild(position);position.style.display='none';
     content.insertBefore(wrap,btn);content.insertBefore(conflictBox,btn.nextSibling);content.insertBefore(hint,btn.nextSibling);
     mode.onchange=function(){var independent=mode.value==='independent';position.style.display=independent?'block':'none';
       btn.textContent=independent?'Generează '+config.track+' din DOCX':({'subs':'Adaugă subtitrările','name':'Adaugă NameTag','caps':'Adaugă cartoanele'})[k];
       conflictBox.style.display='none';hint.textContent=independent?(k==='subs'?'PREVIEW TIMING — fără sincronism audio.':'Banda grafică editorială — fără montaj V1/A1.'):'Pe montajul deja validat.';};
     btn.onclick=function(){if(mode.value==='independent')run(k);else if(old)old.call(btn);};mode.onchange();
   })(key);
   safeCapsLegacy();
 }
 // 00 and 02 are open in some old panel builds. All sections MUST start closed.
 var all=document.querySelectorAll('details.module');for(var a=0;a<all.length;a++)all[a].open=false;
 install();var observer=new MutationObserver(function(){if(!installed)install();});
 observer.observe(document.body,{childList:true,subtree:true});
})();
