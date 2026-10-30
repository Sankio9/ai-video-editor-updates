/* R2.3.5 guarded V5 replacement ONLY inside a verified CLONE of the
   current Premiere sequence. NEVER delete material on the source sequence.
   ExtendScript ES3/CEP; no QE or track creation. The approved independent
   MOGRT writer performs insertion and readback after clone preparation.
*/
if (typeof $ === 'undefined') {$={};}
$._AIVE_R235_V5_=(function(){
 function fail(s){throw Error(String(s));}
 function out(ok,msg,extra){var a={ok:!!ok,message:String(msg)};if(extra)for(var k in extra)if(extra.hasOwnProperty(k))a[k]=extra[k];return JSON.stringify(a);}
 function guarded(f){try{return f();}catch(e){return out(false,String(e&&e.message||e));}}
 function str(x){return String(x===undefined||x===null?'':x);}
 function id(s){return str(s&&s.sequenceID);}
 function clips(track){var a=[];for(var i=0;i<track.clips.numItems;i++){
   var c=track.clips[i];a.push([str(c.name),str(c.projectItem&&c.projectItem.name),
      Number(c.start.seconds).toFixed(5),Number(c.end.seconds).toFixed(5),
      str(c.projectItem&&c.projectItem.nodeId)].join('#'));
 }return a.join('|');}
 function external(s){var a=[];for(var i=0;i<s.videoTracks.numTracks;i++)if(i!==4)a.push('V'+i+'='+clips(s.videoTracks[i]));
   if(s.audioTracks)for(var j=0;j<s.audioTracks.numTracks;j++)a.push('A'+j+'='+clips(s.audioTracks[j]));
   return a.join('||');}
 function inv(t){var a=[];for(var i=0;i<t.clips.numItems;i++){
   var c=t.clips[i],v='';try{v=c.getMGTComponent&&c.getMGTComponent()?'MOGRT/GRAFICĂ':'';}catch(e){}
   a.push({kind:v||'ALT MATERIAL',name:str(c.name||(c.projectItem&&c.projectItem.name)||'fără nume'),
     start:Number(c.start.seconds),end:Number(c.end.seconds)});
 }return a;}
 function validatePlan(p){
   if(!/\.json$/i.test(str(p)))fail('Plan JSON invalid');
   var f=File(p);if(!f.exists)fail('Planul DOCX nu mai există');
   f.encoding='UTF-8';if(!f.open('r'))fail('Nu pot citi planul DOCX');
   var data;try{data=JSON.parse(f.read());}finally{f.close();}
   if(data.schema!=='aive-r20-graphics-v1'||data.mode!=='independent'||data.module!=='04'||
      !data.items||!data.items.length||data.items.length!==data.totalItems)
      fail('Planul nu este Cartoane independent sau nu are cartoane');
 }
 function assertOther(original,sourceFingerprint){
   if(external(original)!==sourceFingerprint)fail('Pistele originale au fost schimbate; oprit');
 }
 function prepare(p,expectedInventory){
   return guarded(function(){
     validatePlan(p);
     if(!app.project||!app.project.activeSequence)fail('Secvența Premiere nu este activă');
     var source=app.project.activeSequence,originalId=id(source),project=app.project;
     if(!originalId)fail('Nu există un sequenceID sigur');
     if(!source.videoTracks||source.videoTracks.numTracks<=4)fail('Pista V5 lipsește');
     var target=source.videoTracks[4],sourceOther=external(source),sourceV5=clips(target);
     if(typeof target.isLocked!=='function'||target.isLocked())fail('V5 este blocată');
     var visible=inv(target),wanted=JSON.parse(expectedInventory);
     if(JSON.stringify(visible)!==JSON.stringify(wanted))fail('Inventarul V5 diferă; reia verificarea');
     if(visible.length<1||visible.length>150)fail('Număr neașteptat de materiale V5');
     // The first live implementation is MOGRT-only. Refuse mixed video/photo
     // rather than risk removing footage or linked audio from a cloned sequence.
     for(var i=0;i<visible.length;i++)if(visible[i].kind!=='MOGRT/GRAFICĂ')
       fail('V5 conține material nemarcat MOGRT: '+visible[i].name+'. Oprește și verifică manual.');
     if(typeof source.clone!=='function')fail('Premiere nu oferă Sequence.clone(); V5 originală neatinsă');
     var existing={},before=project.sequences.numSequences;
     for(i=0;i<before;i++)existing[id(project.sequences[i])]=true;
     if(source.clone()!==true)fail('Premiere nu a confirmat duplicarea secvenței');
     var added=[];
     for(i=0;i<project.sequences.numSequences;i++){
       var q=project.sequences[i];if(!existing[id(q)])added.push(q);
     }
     if(added.length!==1||project.sequences.numSequences!==before+1)
       fail('După clonare nu pot identifica UNIC noua secvență. Nu șterg nimic.');
     var copy=added[0],copyId=id(copy);
     if(!copyId||copyId===originalId)fail('Identitatea copiei este invalidă');
     if(copy.videoTracks.numTracks!==source.videoTracks.numTracks||
        clips(copy.videoTracks[4])!==sourceV5||external(copy)!==sourceOther)
       fail('Copia nu este identică cu originalul; nu șterg nimic');
     assertOther(source,sourceOther);
     if(clips(source.videoTracks[4])!==sourceV5)fail('Originalul V5 a fost modificat');
     if(typeof project.openSequence!=='function'||project.openSequence(copyId)===false)
       fail('Nu am putut deschide copia; niciun material nu a fost șters.');
     if(!project.activeSequence||id(project.activeSequence)!==copyId)
       fail('Nu s-a activat copia verificată; nu șterg nimic');
     copy=project.activeSequence;
     var ctrack=copy.videoTracks[4];
     if(typeof ctrack.isLocked!=='function'||ctrack.isLocked()||
        clips(ctrack)!==sourceV5||external(copy)!==sourceOther)
       fail('Copie V5 indisponibilă; nicio ștergere');
     var names=[];
     for(i=0;i<visible.length;i++)names.push(visible[i].name);
     // Non-ripple deletion, reverse order. Only the CLONE is ever modified.
     for(i=ctrack.clips.numItems-1;i>=0;i--){
       if(id(project.activeSequence)!==copyId||id(source)!==originalId)
         fail('Secvența activă s-a schimbat. Originalul rămâne protejat.');
       assertOther(source,sourceOther);
       if(clips(source.videoTracks[4])!==sourceV5)
         fail('ALERTĂ: V5 originală s-a schimbat; STOP.');
       var numBefore=ctrack.clips.numItems;
       var item=ctrack.clips[i];
       var removed=item.remove(false,false);
       // Premiere docs return 0 on success. Enforce actual count readback,
       // never trust only this return value.
       if(removed!==0&&removed!==true)
         fail('Ștergerea din copia secvenței nu a fost confirmată');
       if(ctrack.clips.numItems!==numBefore-1)
         fail('READBACK: nu s-a redus numărul de elemente V5 pe copie');
       if(external(copy)!==sourceOther)
         fail('O altă pistă de pe copie s-a modificat — nu continua!');
     }
     if(ctrack.clips.numItems!==0||clips(ctrack)!==''||external(copy)!==sourceOther)
       fail('V5 copiată nu este complet liberă după ștergere');
     assertOther(source,sourceOther);
     if(clips(source.videoTracks[4])!==sourceV5)
       fail('V5 sursă nu mai corespunde inventarului inițial');
     // Name is advisory; do not fail if a Premiere installation restricts it.
     try{copy.name=str(source.name)+' [AIVE V5 REPLACE]';}catch(rename){}
     return out(true,'V5 eliberată doar în copia secvenței. Originalul este intact.',
       {copySequence:id(copy),copyName:str(copy.name),originalSequence:originalId,
        originalName:str(source.name),removed:visible.length});
   });
 }
 return {prepare:prepare};
})();
