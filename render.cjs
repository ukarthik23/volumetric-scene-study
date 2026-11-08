// Deterministic frame renderer. All 960 frames come from one 3D field and one clock.
"use strict";
const fs=require("node:fs"),path=require("node:path"),http=require("node:http");
const {spawn}=require("node:child_process"),{once}=require("node:events");
const {chromium}=require("playwright");
const root=__dirname,mode=process.argv[2]||"preview";
const previewFrames=[0,240,480,720,959];
let server,browser,encoder;
async function main(){
 server=http.createServer((req,res)=>{
  const name=decodeURIComponent(new URL(req.url,"http://localhost").pathname).slice(1);
  if(!["scene.html","density.r8"].includes(name)){res.writeHead(404);return res.end()}
  const target=path.join(root,name);if(!fs.existsSync(target)){res.writeHead(404);return res.end()}
  res.writeHead(200,{"content-type":name.endsWith("html")?"text/html":"application/octet-stream"});fs.createReadStream(target).pipe(res);
 });await new Promise(r=>server.listen(0,"127.0.0.1",r));
 browser=await chromium.launch({headless:true,args:["--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"]});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 page.on("pageerror",e=>console.error("Page error:",e.message));
 await page.goto(`http://127.0.0.1:${server.address().port}/scene.html`);
 await page.evaluate(()=>window.ready);
 const output=path.join(root,"output");fs.mkdirSync(output,{recursive:true});
 async function frame(n){return Buffer.from(await page.evaluate(f=>window.renderFrame(f),n),"base64")}
 if(mode==="preview"){
  for(const n of previewFrames){fs.writeFileSync(path.join(output,`frame_${String(n).padStart(4,"0")}.jpg`),await frame(n));console.log("Preview",n)}
 }else if(mode==="full"){
  encoder=spawn("ffmpeg",["-hide_banner","-loglevel","error","-y","-f","image2pipe","-framerate","24","-vcodec","mjpeg","-i","pipe:0","-an","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-threads","2","-frames:v","960","-movflags","+faststart",path.join(output,"continuous_nebula_40s_720p.mp4")],{stdio:["pipe","ignore","pipe"]});
  let err="";encoder.stderr.on("data",d=>err+=d);const finished=once(encoder,"exit");
  for(let n=0;n<960;n++){const jpg=await frame(n);if(!encoder.stdin.write(jpg))await once(encoder.stdin,"drain");if(previewFrames.includes(n))fs.writeFileSync(path.join(output,`frame_${String(n).padStart(4,"0")}.jpg`),jpg);if(n%48===0)console.log(`${n}/960 frames`)}
  encoder.stdin.end();const [code]=await finished;encoder=null;if(code!==0)throw Error(err);console.log("Saved 40-second video");
 }else throw Error("Use preview or full");
}
main().catch(e=>{console.error(e);process.exitCode=1}).finally(async()=>{if(encoder)encoder.kill();if(browser)await browser.close();if(server)server.close()});
