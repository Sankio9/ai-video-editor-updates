/* R2.0 experimental independent graphics MOGRT executor for Premiere Pro 25.6.4.
   ES3 ExtendScript. No V1/A1 prerequisites, no QE, no automatic overwrite.
   On failure remove only the MOGRT inserted by this invocation; preserve all other tracks.
*/
if(typeof $==='undefined'){$={};}
$._AIVE_R20_=(function(){
 var N={'02':2,'03':3,'04':4}, T={'02':'D:/AI-Video-Editor/Templates/RFERL_Subtitles.mogrt',
   '03':'D:/AI-Video-Editor/Templates/RFERL_NameTag_2LinesTitle.mogrt',
   '04':'D:/AI-Video-Editor/Templates/RFERL_Captions_STROKE_2_.mogrt'};
 function fail(x){throw Error(String(x));}
 function result(ok,message,extra){var r={ok:!!ok,message:String(message)};
   if(extra)for(var k in extra)if(extra.hasOwnProperty(k))r[k]=extra[k];return JSON.stringify(r);}
 function safe(cb){try{return cb();}catch(e){return result(false,String(e&&e.message?e.message:e));}}
 function num(x){return typeof x==='number'&&isFinite(x);}
 function near(a,b,d){return Math.abs(Number(a)-Number(b))<=d;}
 function tm(x){var v=new Time();v.seconds=Number(x);return v;}
 function text(x){return String(x||'');}
 function hashPlan(p){if(!p||p.schema!=='aive-r20-graphics-v1'||p.mode!=='independent'||!N.hasOwnProperty(p.module))fail('Plan independent incompatibil');
   if(!/^[a-f0-9]{64}$/.test(text(p.docx_sha256)))fail('DOCX hash invalid');
   if((p.module==='02'&&p.timing!=='SCRIPT_PREVIEW')||(p.module!=='02'&&p.timing!=='EDITORIAL_PREVIEW'))fail('TIMING preview obligatoriu');
   if(!p.items||!p.items.length||p.items.length>2000||p.totalItems!==p.items.length)fail('Număr MOGRT invalid');
   if(!num(p.separatorSeconds)||p.separatorSeconds<0||p.separatorSeconds>2)fail('Separator invalid');
   var prev=null,ids={},names={};
   for(var i=0;i<p.items.length;i++){
     var a=p.items[i];if(!a||!a.id||ids[a.id]||!a.groupId||typeof a.text!=='string'||!a.text)fail('Element invalid sau duplicat');
     ids[a.id]=true;
     if(!num(a.startSeconds)||!num(a.durationSeconds)||a.startSeconds<0||a.durationSeconds<.8||a.durationSeconds>15)fail('Timing preview invalid');
     if(prev){var gap=a.startSeconds-prev.startSeconds-prev.durationSeconds;
       if(gap<-.01||gap>(prev.groupId===a.groupId?.13:p.separatorSeconds+.13))fail('Gap/overlap nepermis');}
     if(p.module==='02'&&(a.text.length>74||a.fontStyle!=='Regular'&&a.fontStyle!=='Italic'))fail('Subtitle invalid');
     if(p.module==='03'){
       if(!a.name||!a.title||names[a.groupId])fail('NameTag invalid / grup duplicat');
       names[a.groupId]=1;
     }
     if(p.module==='04'){
       if(!a.physicalLines||a.physicalLines.length!==4||!a.boldWords||a.colorScheme!=='Orange')fail('Carton invalid');
       var lines=[];for(var j=0;j<4;j++){
         if(a.physicalLines[j].length>33)fail('Line carton >33');
         if(a.physicalLines[j])lines.push(a.physicalLines[j]);
       }
       if(lines.join(' ')!==a.text||a.textLine0!==a.physicalLines[0]||a.textLines123!==a.physicalLines.slice(1).join('\r'))fail('Text carton nu corespunde liniilor');
     }
     prev=a;
   }
   return N[p.module];
 }
 function load(path){if(!/\.json$/i.test(text(path)))fail('Planul trebuie să fie JSON');
   var f=File(path);if(!f.exists)fail('Plan R2.0 inexistent');f.encoding='UTF-8';
   if(!f.open('r'))fail('Nu pot citi planul R2.0');var p;try{p=JSON.parse(f.read());}finally{f.close();}
   var idx=hashPlan(p);return {plan:p,file:f,index:idx};}
 function sequence(idx){if(!app.project||!app.project.activeSequence)fail('Activează o secvență Premiere');
   var s=app.project.activeSequence;if(s.videoTracks.numTracks<=idx)fail('Pista V'+(idx+1)+' lipsește. Creeaz-o din Premiere (fără QE).');
   var track=s.videoTracks[idx];if(!track||!track.clips)fail('Pista inaccesibilă');
   if(typeof track.isLocked!=='function'||track.isLocked())fail('Pista este blocată sau lock-state indisponibil');
   return s;}
 function clipPrint(track){var out=[];for(var i=0;i<track.clips.numItems;i++){
   var c=track.clips[i];out.push([text(c.name),text(c.projectItem?c.projectItem.name:''),
     Number(c.start.seconds).toFixed(5),Number(c.end.seconds).toFixed(5),
     text(c.projectItem?c.projectItem.nodeId:'')].join('#'));}return out.join('|');}
 function otherPrint(s,idx){var out=[];for(var i=0;i<s.videoTracks.numTracks;i++)if(i!==idx)out.push('V'+i+'='+clipPrint(s.videoTracks[i]));
   if(s.audioTracks)for(var j=0;j<s.audioTracks.numTracks;j++)out.push('A'+j+'='+clipPrint(s.audioTracks[j]));
   return out.join('||');}
 function kind(c){var name=text(c.name)+' '+text(c.projectItem?c.projectItem.name:'');
   if(/\.(jpg|jpeg|png|bmp|psd|gif|tiff?)\b/i.test(name))return 'FOTO';
   if(/\.(mp4|mov|mxf|avi|mkv|mts)\b/i.test(name))return 'VIDEO';
   try{if(c.getMGTComponent&&c.getMGTComponent())return 'MOGRT/GRAFICĂ';}catch(e){}
   return 'ALT MATERIAL';}
 function inventory(track){var out=[];for(var i=0;i<track.clips.numItems;i++){
    var a=track.clips[i];out.push({kind:kind(a),name:text(a.name||(a.projectItem&&a.projectItem.name)||'fără nume'),
      start:Number(a.start.seconds),end:Number(a.end.seconds)});}return out;}
 function maxEnd(track){var end=0;for(var i=0;i<track.clips.numItems;i++)end=Math.max(end,Number(track.clips[i].end.seconds));return end;}
 function token(c,policy,offset){return JSON.stringify({sequence:String(c.seq.sequenceID||c.seq.name),
   plan:text(c.data.file.fsName),stamp:text(c.data.file.modified),docx:c.data.plan.docx_sha256,
   module:c.data.plan.module,policy:policy,offset:offset,
   initialCount:c.initialCount===undefined?c.track.clips.numItems:c.initialCount,
   baseTarget:c.baseTarget===undefined?clipPrint(c.track):c.baseTarget,
   other:otherPrint(c.seq,c.data.index),target:clipPrint(c.track)});}
 function loadContext(path){var d=load(path),s=sequence(d.index);return {data:d,seq:s,track:s.videoTracks[d.index]};}
 function parseToken(raw,c){var t;try{t=JSON.parse(raw);}catch(e){fail('Token preflight invalid');}
   if(!t||t.sequence!==String(c.seq.sequenceID||c.seq.name)||t.module!==c.data.plan.module||
     t.docx!==c.data.plan.docx_sha256||t.plan!==text(c.data.file.fsName)||t.stamp!==text(c.data.file.modified)||
     t.target!==clipPrint(c.track)||t.other!==otherPrint(c.seq,c.data.index)||typeof t.baseTarget!=='string'||!num(t.initialCount)||!num(t.offset)||t.offset<0||
     (t.policy!=='zero'&&t.policy!=='append'))fail('Secvența/planul/pistele s-au schimbat după verificare. Reia Verifică.');
   return t;}
 function param(comp,key){if(!comp||!comp.properties)fail('MOGRT fără Essential Graphics');
   var p=comp.properties.getParamForDisplayName(key);if(!p)fail('Parametrul MOGRT lipsește: '+key);return p;}
 function payload(value){var s=text(value),i=s.indexOf('{');if(i<0||i>8)fail('Text MOGRT cu structură necunoscută');
   var o=JSON.parse(s.substring(i)),fields=[];
   function walk(v,d){if(!v||typeof v!=='object'||d>15)return;
     if(typeof v.textEditValue==='string')fields.push({o:v,k:'textEditValue'});
     if(v.mTextParam&&v.mTextParam.mStyleSheet&&typeof v.mTextParam.mStyleSheet.mText==='string')fields.push({o:v.mTextParam.mStyleSheet,k:'mText'});
     for(var k in v)if(v.hasOwnProperty(k)&&typeof v[k]==='object')walk(v[k],d+1);
   }walk(o,0);if(!fields.length)fail('Text MOGRT needitabil');return {prefix:s.substring(0,i),object:o,fields:fields};}
 function getText(p){var o=payload(p.getValue());return o.fields[0].o[o.fields[0].k];}
 function setText(p,str){var v=payload(p.getValue());for(var i=0;i<v.fields.length;i++){
    var z=v.fields[i];z.o[z.k]=str;
    if(z.k==='textEditValue'&&z.o.fontTextRunLength instanceof Array&&z.o.fontTextRunLength.length===1)z.o.fontTextRunLength=[str.length];}
   if(p.setValue(v.prefix+JSON.stringify(v.object),true)===false)fail('Premiere a refuzat textul');
   v=payload(p.getValue());for(var j=0;j<v.fields.length;j++)if(v.fields[j].o[v.fields[j].k]!==str)fail('READBACK text eșuat');}
 function setNumber(p,n){if(p.setValue(n,true)===false||String(p.getValue())!==String(n))fail('READBACK numeric MOGRT eșuat');}
 function matches(x,a,st,ed,module){if(!near(x.start.seconds,st,.13)||!near(x.end.seconds,ed,.13))return false;
   try{var m=x.getMGTComponent();if(!m)return false;
     if(String(param(m,'Aspect Ratio').getValue())!=='1')return false;
     if(module==='02')return getText(param(m,'Text'))===a.text&&String(param(m,'Font Style').getValue())===(a.fontStyle==='Italic'?'0':'1');
     if(module==='03')return getText(param(m,'Name'))===a.name&&getText(param(m,'2 LINES TITLE'))===a.title&&String(param(m,'SubsShift').getValue())==='1';
     if(getText(param(m,'Text Line 0'))!==a.textLine0||getText(param(m,'Text Line 1,2,3'))!==a.textLines123||String(param(m,'Color Scheme').getValue())!=='0')return false;
     for(var k=0;k<4;k++)if(getText(param(m,'Line '+k+' Bold Words'))!==text(a.boldWords[String(k)]))return false;
     return true;
   }catch(e){return false;}}
 function collision(track,st,ed){for(var i=0;i<track.clips.numItems;i++){
   var x=track.clips[i];if(Number(x.start.seconds)<ed-.03&&Number(x.end.seconds)>st+.03)return true;}return false;}
 function allowedPosition(c,policy,offset){
   if(policy!=='zero'&&policy!=='append')fail('Alege poziția 0 sau după ultimul clip');
   if(c.data.plan.module==='04'&&c.track.clips.numItems>0)fail('V5_OCCUPIED: nu șterg materiale; suprascrierea necesită backup/consimțământ și test Premiere separat.');
   if(policy==='zero'&&c.track.clips.numItems>0)fail('Pista ocupată. Pentru 02/03 selectează după ultimul element sau eliberează pista manual.');
   if(policy==='append'&&offset<maxEnd(c.track)+.25)fail('Append anchor invalid sau pista modificată');
 }
 function validate(path,policy){return safe(function(){var c=loadContext(path),inven=inventory(c.track),offset=0;
   if(c.data.plan.module==='04'&&inven.length)return result(false,'V5 ocupată — operație oprită; nu s-a șters nimic.',
     {needsChoice:true,choices:['Suprascrie materialele de pe V5','Oprește, eliberez V5'],inventory:inven});
   if(policy==='append')offset=Number((maxEnd(c.track)+.75).toFixed(3));
   allowedPosition(c,policy,offset);
   if(!File(T[c.data.plan.module]).exists)fail('Template MOGRT lipsește: '+T[c.data.plan.module]);
   return result(true,c.data.plan.totalItems+' MOGRT pregătite pe V'+(c.data.index+1)+' — '+c.data.plan.timing,
     {token:token(c,policy,offset),count:c.data.plan.items.length,done:0,timing:c.data.plan.timing,inventory:inven});
 });}
 function buildOne(path,tok,index){return safe(function(){var c=loadContext(path),t=parseToken(tok,c),i=Number(index),items=c.data.plan.items;
   if(!num(i)||i<0||i>=items.length||Math.floor(i)!==i)fail('Index invalid');
   // V5 is strictly empty at start and thereafter contains only this session's newly inserted MOGRTs.
   if(c.track.clips.numItems!==t.initialCount+i)fail('Număr de clipuri modificat / rerulare incorectă');
   if(c.data.plan.module==='04'&&i===0&&c.track.clips.numItems>0)fail('V5 ocupată');
   var a=items[i],st=a.startSeconds+t.offset,ed=st+a.durationSeconds;
   if(collision(c.track,st,ed))fail('Coliziune cu material existent pe V'+(c.data.index+1));
   var beforeOther=otherPrint(c.seq,c.data.index),beforeTrack=clipPrint(c.track),inserted=null;
   try{
     inserted=c.seq.importMGT(File(T[c.data.plan.module]).fsName,String(tm(st).ticks),c.data.index,0);
     if(!inserted||!near(inserted.start.seconds,st,.13))fail('Premiere nu a inserat MOGRT la începutul așteptat');
     var m=inserted.getMGTComponent();if(!m)fail('Componenta MOGRT lipsește');
     if(c.data.plan.module==='02'){
       setText(param(m,'Text'),a.text);setNumber(param(m,'Font Style'),a.fontStyle==='Italic'?0:1);
     }else if(c.data.plan.module==='03'){
       setText(param(m,'Name'),a.name);setText(param(m,'2 LINES TITLE'),a.title);
       setNumber(param(m,'SubsShift'),1);
     }else{
       setText(param(m,'Text Line 1,2,3'),a.textLines123);setText(param(m,'Text Line 0'),a.textLine0);
       for(var k=0;k<4;k++)setText(param(m,'Line '+k+' Bold Words'),text(a.boldWords[String(k)]));
       setNumber(param(m,'Color Scheme'),0);
     }
     setNumber(param(m,'Aspect Ratio'),1);inserted.end=tm(ed);
     if(!matches(inserted,a,st,ed,c.data.plan.module))fail('MOGRT READBACK nereușit');
     if(otherPrint(c.seq,c.data.index)!==beforeOther)fail('ALERTĂ: o altă pistă s-a schimbat!');
     // Detect collateral changes to previously inserted clips. No destructively overwriting existing materials.
     if(c.track.clips.numItems!==t.initialCount+i+1)fail('Număr neașteptat de materiale pe pista țintă');
   }catch(e){var clean='';if(inserted)try{inserted.remove(false,false);}catch(r){clean=' ROLLBACK EȘUAT! NU SALVA.';}
      if(otherPrint(c.seq,c.data.index)!==beforeOther)clean+=' Piste externe modificate — verifică Undo/copiei!';
      if(!clean&&clipPrint(c.track)!==beforeTrack)clean=' Starea pistei după rollback diferă — NU SALVA.';
      fail('STOP '+a.id+': '+String(e&&e.message?e.message:e)+clean);}
   c.initialCount=t.initialCount;c.baseTarget=t.baseTarget;
   return result(true,(i+1)+'/'+items.length+' — MOGRT verificat pe V'+(c.data.index+1),
     {token:token(c,t.policy,t.offset),count:items.length,done:i+1,timing:c.data.plan.timing});
 });}
 function rollback(path,tok,count){return safe(function(){var c=loadContext(path),t=parseToken(tok,c),n=Number(count),items=c.data.plan.items;
   if(!num(n)||n<0||Math.floor(n)!==n||n>items.length||c.track.clips.numItems!==t.initialCount+n)fail('ROLLBACK: număr neașteptat de elemente; NU SALVA.');
   for(var i=n-1;i>=0;i--){var a=items[i],st=a.startSeconds+t.offset,ed=st+a.durationSeconds,hit=null,total=0;
     for(var j=0;j<c.track.clips.numItems;j++)if(matches(c.track.clips[j],a,st,ed,c.data.plan.module)){hit=c.track.clips[j];total++;}
     if(total!==1||!hit)fail('ROLLBACK: nu identific unic MOGRT '+a.id+'. NU SALVA.');
     if(hit.remove(false,false)===false)fail('ROLLBACK: Premiere a refuzat ștergerea '+a.id+'. NU SALVA.');
   }
   if(otherPrint(c.seq,c.data.index)!==t.other||clipPrint(c.track)!==t.baseTarget)
     fail('ROLLBACK: timeline diferit de preflight; NU SALVA.');
   return result(true,'ROLLBACK PASS: '+n+' MOGRT eliminate; conținutul anterior al pistei a fost păstrat.');
 });}
 function verify(path,tok){return safe(function(){var c=loadContext(path),t=parseToken(tok,c),items=c.data.plan.items,issues=[];
   if(c.track.clips.numItems!==t.initialCount+items.length)fail('READBACK: număr MOGRT neașteptat pe pista țintă');
   for(var i=0;i<items.length;i++){
     var a=items[i],start=a.startSeconds+t.offset,end=start+a.durationSeconds,matched=0;
     for(var j=0;j<c.track.clips.numItems;j++)if(matches(c.track.clips[j],a,start,end,c.data.plan.module))matched++;
     if(matched!==1)issues.push(a.id);
   }
   if(issues.length)fail('READBACK lipsă/diferit: '+issues.slice(0,12).join(', '));
   return result(true,'READBACK PASS: '+items.length+' MOGRT pe V'+(c.data.index+1)+' — '+c.data.plan.timing,
     {timing:c.data.plan.timing,count:items.length,done:items.length});
 });}
 return {validate:validate,buildOne:buildOne,verify:verify,rollback:rollback};
})();
