const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');const path=require('node:path');
const handlers=new Map(),trace=[],children=[];let window;
class Child extends EventEmitter{
 constructor(mode){super();this.mode=mode;this.stdout=new EventEmitter();this.stderr=new EventEmitter();this.stdin={end:s=>{if(mode==='watch'){trace.push('watch-stop');setImmediate(()=>{trace.push('watch-close');this.emit('close',0);});}else{const p=JSON.parse(s||'{}');setImmediate(()=>{this.stdout.emit('data',Buffer.from(JSON.stringify(p.invalid?{ok:false,message:'invalid'}:{ok:true,data:p})+'\n'));this.emit('close',0);});}},write:s=>{if(JSON.parse(s).command==='stop')setImmediate(()=>this.emit('close',0));}};}
 kill(){this.emit('close',0);}
}
const app=new EventEmitter();app.whenReady=()=>Promise.resolve();app.getPath=()=>'/test';app.setPath=()=>{};app.quit=()=>{};
class Window extends EventEmitter{
 constructor(){super();window=this;this.destroyed=false;this.webContents=new EventEmitter();this.webContents.setWindowOpenHandler=()=>{};this.webContents.send=()=>{};}
 setMenu(){} loadFile(){setImmediate(()=>this.webContents.emit('did-finish-load'));} isDestroyed(){return this.destroyed;} destroy(){this.destroyed=true;this.emit('closed');} restore(){} show(){} minimize(){}
}
const fakefs={mkdirSync(){},appendFileSync(){},writeFileSync(){},renameSync(){}};
const sandbox={__dirname:path.join(__dirname,'aika_hunt_app'),require:name=>name==='electron'?{app,BrowserWindow:Window,ipcMain:{handle:(k,h)=>handlers.set(k,h)},dialog:{},shell:{}}:name==='node:child_process'?{spawn:(_exe,args)=>{const mode=args[2];trace.push(mode+'-spawn');const c=new Child(mode);children.push(c);return c;}}:name==='node:fs'?fakefs:name==='./updates.cjs'?()=>({check:async()=>({})}):name==='./runtime.cjs'?()=>({root:'/test',dataRoot:'/test',command:'python',args:['-u','/test/hunt_bridge.py']}):require(name),process:{env:{},on(){}},Buffer,console,clearTimeout,setInterval:()=>({unref(){}}),clearInterval(){},setTimeout:(f,t)=>{const x=setTimeout(f,t);x.unref();return x;}};
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'aika_hunt_app/main.cjs'),'utf8'),sandbox);
 await tick();await tick();assert.equal(children.filter(c=>c.mode==='watch').length,1);
 await assert.rejects(()=>handlers.get('hunt:start')(null,{invalid:true}),/invalid/);
 assert.equal(trace.filter(v=>v==='watch-stop').length,0,'Configuracao invalida nao deve desligar o monitor');
 await handlers.get('hunt:start')(null,{minimize_on_start:false,target:'qualquer'});
 assert.ok(trace.indexOf('watch-close')<trace.indexOf('run-spawn'),'Monitor deve encerrar antes de iniciar teclas da caca');
 await handlers.get('hunt:stop')();await tick();await tick();
 assert.equal(children.filter(c=>c.mode==='watch').length,2,'Monitor deve voltar depois de parar a caca');
 window.emit('close',{preventDefault(){}});await tick();await tick();
 assert.ok(window.destroyed,'Fechar o painel deve encerrar o monitor');
 console.log('OK: monitor ocioso, validacao, troca para caca, retomada e encerramento.');
})().catch(e=>{console.error(e);process.exitCode=1;});
