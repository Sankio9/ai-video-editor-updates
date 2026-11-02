/* R2 beta updater channel. Stable updater remains unchanged and remains default.
   Uses existing official runner.prepare() SHA-256, backup and rollback engine. */
(function(){'use strict';
 var stable=document.getElementById('aiveUpdateButton');
 var status=document.getElementById('aiveUpdateStatus');
 if(!stable||!status)return;
 var req=(window.cep_node&&window.cep_node.require)||(typeof require==='function'?require:null);
 if(!req)return;
 var cp=req('child_process'),fs=req('fs'),path=req('path');
 var root='D:\\AI-Video-Editor';
 var python=path.join(root,'.venv','Scripts','python.exe');
 var bridge=path.join(root,'updater','beta.py');
 var select=document.createElement('select');select.id='aiveUpdateChannel';
 select.style.cssText='width:100%;padding:8px;margin:6px 0;background:#21262a;color:#f4f6f8;border:1px solid #66717b;border-radius:4px;';
 [['stable','Stable (recomandat)'],['beta','Beta — doar pentru teste']].forEach(function(x){
   var option=document.createElement('option');option.value=x[0];option.textContent=x[1];select.appendChild(option);
 });
 var beta=document.createElement('button');beta.type='button';beta.id='aiveBetaUpdate';
 beta.className='secondary';beta.textContent='Verifică actualizări Beta';beta.style.display='none';
 stable.parentNode.insertBefore(select,stable);
 stable.parentNode.insertBefore(beta,stable.nextSibling);
 var busy=false,state='check';
 function say(m){status.textContent=String(m);}
 select.onchange=function(){if(busy||state==='waiting')return;
   var selected=select.value==='beta';stable.style.display=selected?'none':'';beta.style.display=selected?'':'none';
   state='check';beta.textContent='Verifică actualizări Beta';
   say(selected?'Canal Beta: funcții experimentale, numai proiecte TEST.':'Canal Stable (recomandat).');};
 function call(cmd,callback){
   if(!fs.existsSync(bridge)||!fs.existsSync(python)){
     callback({ok:false,message:'Lipsește modulul Beta sau Python local.'});return;}
   var args=[bridge,'--root',root,cmd];
   var ps=cp.spawn(python,args,{cwd:root,windowsHide:true}),stdout='',stderr='',done=false;
   ps.stdout.on('data',function(b){stdout+=String(b);});
   ps.stderr.on('data',function(b){stderr+=String(b);});
   ps.on('error',function(e){if(done)return;done=true;callback({ok:false,message:e.message});});
   ps.on('close',function(){if(done)return;done=true;try{callback(JSON.parse(stdout.trim()));}
       catch(e){callback({ok:false,message:'Răspuns Beta invalid: '+stderr.slice(-200)});}});
 }
 beta.onclick=function(){if(busy||state==='waiting')return;
   busy=true;select.disabled=true;beta.disabled=true;
   var command=state==='check'?'--check-beta':'--prepare-beta';
   say(state==='check'?'Verific GitHub Beta…':'Verific SHA-256 și pregătesc Beta…');
   call(command,function(response){busy=false;beta.disabled=false;select.disabled=false;
     if(!response||!response.ok){state='check';beta.textContent='Verifică actualizări Beta';say(response&&response.message||'Eroare Beta.');return;}
     if(command==='--check-beta'){
       if(!response.new){say('Nicio versiune Beta nouă ('+response.current+').');return;}
       say('Beta '+response.latest+' disponibilă (instalat '+response.current+'). Pentru test, apasă pregătirea.');
       state='prepare';beta.textContent='Descarcă și pregătește Beta';return;
     }
     state='waiting';select.disabled=true;beta.textContent='Actualizare în așteptarea închiderii';beta.disabled=true;
     say('Beta pregătită și verificată. Salvează proiectul de test și închide Premiere. Instalarea se finalizează automat.');
     window.alert('Beta pregătită și verificată cu SHA-256.\nSalvează proiectul (Ctrl+S), apoi închide complet Premiere.\nActualizarea se aplică automat și creează backup.');
   });
 };
})();
