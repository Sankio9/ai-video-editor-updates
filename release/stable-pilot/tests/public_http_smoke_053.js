'use strict';
const assert=require('assert'),crypto=require('crypto'),https=require('https'),fs=require('fs'),path=require('path');
const feedUrl='https://raw.githubusercontent.com/Sankio9/ai-video-editor-updates/main/release/stable-pilot/channel.json';
const prefix='https://github.com/Sankio9/ai-video-editor-updates/releases/download/aive-stable-pilot-v0.5.3/';
const whitelist=new Set(['raw.githubusercontent.com','github.com','release-assets.githubusercontent.com','objects.githubusercontent.com']);
function get(url,cap,depth=0){return new Promise((resolve,reject)=>{
  if(depth>5)return reject(Error('Too many redirects'));
  const u=new URL(url);if(u.protocol!=='https:'||!whitelist.has(u.hostname))return reject(Error('Host forbidden: '+u.hostname));
  const req=https.get(url,{headers:{'User-Agent':'AIVE-Stable-Pilot-Updater/0.5.2','Accept':'application/octet-stream'},timeout:25000},res=>{
    if([301,302,303,307,308].includes(res.statusCode)){const dest=res.headers.location;res.resume();if(!dest)return reject(Error('No redirect location'));
      get(new URL(dest,u).href,cap,depth+1).then(resolve,reject);return;}
    if(res.statusCode!==200){res.resume();return reject(Error('HTTP '+res.statusCode+' '+url));}
    let size=0;const parts=[];res.on('data',chunk=>{size+=chunk.length;if(size>cap){res.destroy(Error('Oversized asset'));return;}parts.push(chunk);});
    res.on('error',reject);res.on('end',()=>resolve(Buffer.concat(parts)));
  });req.on('timeout',()=>req.destroy(Error('Download timeout')));req.on('error',reject);
});}
(async()=>{
 const feed=JSON.parse((await get(feedUrl,65536)).toString('utf8'));
 assert.equal(feed.schema,1);assert.equal(feed.channel,'stable-pilot');assert.equal(feed.version,'0.5.3');assert.equal(feed.minVersion,'0.5.2');
 assert(feed.asset.url.startsWith(prefix));assert(/^[a-f0-9]{64}$/.test(feed.asset.sha256));
 const bytes=await get(feed.asset.url,8*1024*1024);const h=crypto.createHash('sha256').update(bytes).digest('hex');
 assert.equal(h,feed.asset.sha256);assert.equal(bytes.length,feed.asset.size);assert(bytes.subarray(0,2).equals(Buffer.from('PK')));
 const out=path.join(process.env.RUNNER_TEMP||process.cwd(),'AIVE_STABLE_PILOT_0.5.3_UPDATE.zip');fs.writeFileSync(out,bytes);
 console.log(JSON.stringify({result:'PUBLIC_GET_AND_SHA_PASS',from:'0.5.2',to:feed.version,size:bytes.length,sha256:h,archive:out}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});