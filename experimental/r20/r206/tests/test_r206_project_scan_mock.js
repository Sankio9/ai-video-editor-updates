/* Strict mock only: reproduces documented Premiere ProjectItem read-only API. */
'use strict';
const assert=require('assert'), fs=require('fs'),vm=require('vm'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../cep/jsx/r206_project_scan.jsx'),'utf8');
function collection(items){items.numItems=items.length;return items;}
function bin(name,nodeId,children){return {type:2,name,nodeId,children:collection(children)};}
function clip(name,nodeId,mediaPath,offline=false,type=1){
    return {type,name,nodeId,getMediaPath(){return mediaPath;},
      isOffline(){return offline},isSequence(){return false}};
}
const media1=clip('CAM_9981_interview.mov','m1','D:\\PRIVATE\\CAM_9981_interview.mov');
const media2=clip('9974_AMB.wav','m2','E:\\PRIVATE\\9974_AMB.wav');
const root=bin('root','r1',[
    bin('Footage','b1',[bin('A camera','b2',[media1]),
                           bin('Audio','b3',[media2])]),
    {type:1,name:'Sequence 01',nodeId:'s1',isSequence(){return true},
     isOffline(){throw Error('Do not check sequences')},
     getMediaPath(){throw Error('Do not read sequence media')}}
]);
const context={$:{},app:{project:{rootItem:root}},JSON,String,Error};
vm.runInNewContext(source,context,{timeout:1200});
function scan(){return JSON.parse(context.$._AIVE_R206_SCAN_.scan());}
let result=scan();
assert.equal(result.ok,true,JSON.stringify(result));
assert.equal(result.nodeCount,7);
assert.equal(result.inventory.schema,'aive-r206-project-panel-v1');
assert.equal(result.inventory.items[0].children[0].children[0].children[0].mediaPath,
             'D:\\PRIVATE\\CAM_9981_interview.mov');
assert.equal(result.inventory.items[1].type,'sequence');
assert.equal(result.inventory.items[0].children[1].children[0].offline,false);
const initial=JSON.stringify(root);
assert.equal(scan().ok,true);
assert.equal(JSON.stringify(root),initial,'scan must never mutate the source project');
const prev=root.children;
root.children=collection([clip('Bad','x','C:\\bad.mov')]);
root.children[0].isOffline=undefined;
result=scan();
assert.equal(result.ok,true);
assert.equal(result.inventory.items[0].offline,null,'Unknown offline must fail in Python, never be online');
root.children=collection([bin('Unreadable','broken',[])]);
root.children[0].children=null;
assert.match(scan().message,/Unreadable bin/);
root.children=prev;
const dup=bin('deep','x',[]);
for(let i=0;i<54;i++)dup.children=collection([bin('depth_'+i,'d'+i,dup.children)]);
root.children=collection([dup]);
result=scan();
assert.equal(result.ok,false);assert.match(result.message,/scan limit/);
root.children=prev;
console.log('PASS: Premiere ExtendScript R206 read-only nested bins, offline unknown, sequence skip, depth guard');
