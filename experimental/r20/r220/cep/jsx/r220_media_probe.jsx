/* R2.2 Premiere Project Panel recursive read-only inventory.
 * Includes nodeId to bind ASR-confirmed source path to exact ProjectItem.
 * No QE, no track writes. All values kept locally.
 */
if(typeof $==="undefined"){$={};}
$._AIVE_R220_=(function(){
 function scan(){
  try{
    if(!app||!app.project||!app.project.rootItem||!app.project.activeSequence)
      throw Error("Active Premiere project/sequence required");
    var s=app.project.activeSequence,found=[],seen={},nodes=0;
    function walk(item,depth){
      if(depth>48)throw Error("PROJECT_BINS_TOO_DEEP");
      var children=item&&item.children;
      if(!children||typeof children.numItems!=="number")return;
      for(var i=0;i<children.numItems;i++){
        if(++nodes>20000)throw Error("TOO_MANY_PROJECT_ITEMS");
        var x=children[i];if(!x)continue;
        var id=String(x.nodeId||"");
        if(id&&seen[id])continue;
        if(id)seen[id]=true;
        var t=String(x.type).toUpperCase(),n=Number(x.type);
        if(t==="BIN"||t==="ROOT"||n===2||n===3){
          walk(x,depth+1);continue;
        }
        if(typeof x.getMediaPath!=="function"||!id)continue;
        var p="";try{p=String(x.getMediaPath()||"");}catch(e){}
        if(!p||p==="undefined"||p==="null")continue;
        var offline=false;
        try{offline=typeof x.isOffline==="function"&&x.isOffline();}catch(e){offline=true;}
        found.push({name:String(x.name||""),nodeId:id,path:p,offline:offline});
      }
    }
    walk(app.project.rootItem,0);
    return JSON.stringify({ok:true,sequence:String(s.name||""),
       sequenceId:String(s.sequenceID||s.id||""),media:found,scanned:nodes});
  }catch(e){return JSON.stringify({ok:false,message:String(e.message||e)});}
 }
 return {scan:scan};
})();
