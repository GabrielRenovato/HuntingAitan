const {app,BrowserWindow,ipcMain,dialog,shell,screen}=require('electron');
const {spawn}=require('node:child_process');
const fs=require('node:fs');const path=require('node:path');
const runtime=require('./runtime.cjs')({app,dirname:__dirname});
// Cada perfil recebe uma identidade própria no Windows para não agrupar as
// três instâncias do Hunting no mesmo ícone da barra de tarefas.
const perfilAumid=(()=>{
 const argumentos=Array.isArray(process.argv)?process.argv:[];
 const arg=argumentos.find(v=>v.startsWith('--user-data-dir='));
 const nome=arg?path.basename(arg.slice('--user-data-dir='.length)):'padrao';
 return 'HuntingAitan.'+(nome.replace(/[^a-zA-Z0-9_-]/g,'')||'padrao');
})();
if(typeof app.setAppUserModelId==='function')app.setAppUserModelId(perfilAumid);
let win,worker=null,quitting=false,stopTimer=null,watcher=null,updates=null;
let clientSelection={client_pid:0,client_hwnd:0};
let profileLoadFailure=null;
const clientEnv=()=>({...process.env,PYTHONUTF8:'1',AIKA_DATA_DIR:runtime.dataRoot,AIKA_CLIENT_PID:String(clientSelection.client_pid||0),AIKA_CLIENT_HWND:String(clientSelection.client_hwnd||0)});
function registrarPainel(evento,dados={}){
 try{const dir=path.join(runtime.dataRoot,'app_sessions');fs.mkdirSync(dir,{recursive:true});fs.appendFileSync(path.join(dir,'painel.jsonl'),JSON.stringify({t:new Date().toISOString(),evento,...dados})+'\n','utf8');}catch{}
}
process.on('uncaughtException',e=>{registrarPainel('uncaughtException',{erro:e.stack||String(e)});stopWorker();if(win&&!win.isDestroyed()){win.restore();win.show();send({event:'error',message:'Falha no painel: '+e.message});}});
process.on('unhandledRejection',e=>{registrarPainel('unhandledRejection',{erro:e?.stack||String(e)});send({event:'error',message:'Falha no painel: '+String(e?.message||e)});});
if(process.env.AIKA_UI_TEST==='1')app.setPath('userData',path.join(runtime.root,'aika_hunt_app','ui-test-profile'));
const profilePath=()=>path.join(app.getPath('userData'),'profile.json');
const send=(event)=>{if(event.event==='input_recovery'&&event.state==='waiting'){win?.flashFrame?.(true);win?.showInactive?.();}if(event.event==='error'){registrarPainel('erro-motor',{mensagem:event.message});if(/fail-safe triggered from mouse moving to a corner/i.test(event.message||''))event={...event,message:'Caça parada: cursor no canto da tela. Retire o cursor e clique em Começar para retomar.'};win?.flashFrame?.(true);}if(win&&!win.isDestroyed())win.webContents.send('hunt:event',event);};
function utility(mode,data={}){
 return new Promise((resolve,reject)=>{
  const child=spawn(runtime.command,[...runtime.args,mode],{cwd:runtime.root,windowsHide:true,env:clientEnv(),stdio:['pipe','pipe','pipe']});
  let output='',error='';child.stdout.on('data',d=>output+=d);child.stderr.on('data',d=>error+=d);
  child.once('error',reject);const timer=setTimeout(()=>{child.kill();reject(new Error('A leitura demorou demais. Confira se o Aika esta aberto.'));},25000);
  child.on('close',code=>{clearTimeout(timer);try{const lines=output.trim().split(/\r?\n/);const r=JSON.parse(lines.at(-1));if(!r.ok)throw new Error(r.message||'Falha na leitura');resolve(r.data);}catch(e){reject(new Error(e.message||error||`Processo terminou (${code})`));}});
  child.stdin.end(JSON.stringify(data));
 });
}
async function saveProfile(p){if(profileLoadFailure)throw new Error('Perfil preservado apos erro de carregamento. Corrija o perfil e reabra o app antes de salvar.');const validated=await utility('validate',p);if(worker&&((validated.client_pid||0)!==(clientSelection.client_pid||0)||(validated.client_hwnd||0)!==(clientSelection.client_hwnd||0)))throw new Error('Pare a caça antes de trocar de cliente.');clientSelection={client_pid:validated.client_pid||0,client_hwnd:validated.client_hwnd||0};fs.mkdirSync(path.dirname(profilePath()),{recursive:true});if(fs.existsSync(profilePath()))fs.copyFileSync(profilePath(),profilePath()+'.bak');const temp=profilePath()+'.tmp';fs.writeFileSync(temp,JSON.stringify(validated,null,2),'utf8');fs.renameSync(temp,profilePath());return validated;}
function stopWorker(){
 if(!worker)return;
 try{worker.stdin.write(JSON.stringify({command:'stop'})+'\n');}catch{}
 clearTimeout(stopTimer);const child=worker;
 stopTimer=setTimeout(()=>{if(worker===child){child.kill();send({event:'status',state:'stopped',message:'Processo encerrado.'});}},5000);
}
function startWatcher(){
 if(quitting||worker||watcher||!win||win.isDestroyed()||process.env.AIKA_UI_TEST==='1')return;
 const child=spawn(runtime.command,[...runtime.args,'watch'],{cwd:runtime.root,windowsHide:true,env:clientEnv(),stdio:['pipe','pipe','pipe']});watcher=child;
 let buffer='';
 child.stdout.on('data',d=>{buffer+=d.toString('utf8');let at;while((at=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,at);buffer=buffer.slice(at+1);try{const e=JSON.parse(line);registrarPainel('monitor-janelas',e);if(e.event==='watcher')send({event:'log',message:e.message});}catch{}}});
 child.stderr.on('data',d=>registrarPainel('monitor-stderr',{erro:d.toString('utf8').slice(-1500)}));
 child.on('error',e=>registrarPainel('monitor-error',{erro:e.message}));
 child.on('close',code=>{if(watcher===child)watcher=null;registrarPainel('monitor-exit',{code});});
}
function stopWatcher(){
 const child=watcher;if(!child)return Promise.resolve();
 return new Promise(resolve=>{let timer;const done=()=>{clearTimeout(timer);resolve();};child.once('close',done);try{child.stdin.end(JSON.stringify({command:'stop'})+'\n');}catch{done();}timer=setTimeout(()=>{try{child.kill();}catch{}done();},3000);});
}
function createWindow(){
 win=new BrowserWindow({width:390,height:600,minWidth:390,maxWidth:390,minHeight:600,maxHeight:600,frame:false,resizable:false,transparent:true,backgroundColor:'#00000000',title:'Caça automática',icon:path.join(__dirname,'assets/app.ico'),webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
 win.setMenu(null);win.loadFile('index.html',{query:process.argv?.includes('--flow-editor')?{editor:'flow'}:{}});
 registrarPainel('aberto');
 updates=require('./updates.cjs')({app,send,isHunting:()=>!!worker,getWindow:()=>win,log:registrarPainel,dialog});
 win.webContents.once('did-finish-load',()=>{startWatcher();updates.check();});
 const updateTimer=setInterval(()=>updates.check(),30*60*1000);updateTimer.unref();win.once('closed',()=>clearInterval(updateTimer));
 win.webContents.on('render-process-gone',(_,details)=>{registrarPainel('render-process-gone',details);stopWorker();dialog.showErrorBox('Falha no painel','A interface encerrou inesperadamente ('+details.reason+'). O diagnostico foi salvo em app_sessions/painel.jsonl.');});
 win.webContents.on('did-fail-load',(_,code,description)=>registrarPainel('did-fail-load',{code,description}));
 win.on('closed',()=>registrarPainel('janela-fechada'));
 win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
 win.webContents.on('will-navigate',e=>e.preventDefault());
 win.on('close',e=>{registrarPainel('fechamento-solicitado',{worker:!!worker});if((worker||watcher)&&!quitting){e.preventDefault();quitting=true;stopWorker();stopWatcher().then(()=>{if(!worker&&!win.isDestroyed())win.destroy();});setTimeout(()=>{if(!win.isDestroyed())win.destroy();},6000);}else quitting=true;});
 if(process.env.AIKA_UI_TEST==='1'){
  win.webContents.once('did-finish-load',async()=>{
   try{
    await new Promise(r=>setTimeout(r,700));
    const out=path.join(runtime.root,'aika_hunt_app','ui-verificacao');fs.mkdirSync(out,{recursive:true});
    fs.writeFileSync(path.join(out,'basico.png'),(await win.webContents.capturePage()).toPNG());
    const initial=await win.webContents.executeJavaScript(`({title:document.title,skills:document.querySelectorAll('#skills .slot').length,items:document.querySelectorAll('#items .slot').length,base:document.querySelector('#base-value').textContent})`);
    const filtro=await win.webContents.executeJavaScript(`(async()=>{document.querySelector('[data-tab="behavior"]').click();const alvo=document.querySelector('#target');alvo.value='verit';alvo.dispatchEvent(new Event('change',{bubbles:true}));const p=await window.hunt.save(collect());const r=await window.hunt.load();return {selecionado:alvo.value,salvo:p.target,recarregado:r.target};})()`);
    if(filtro.salvo!=='verit'||filtro.recarregado!=='verit')throw new Error('Filtro Verit nao persistiu');
    fs.writeFileSync(path.join(out,'filtro-verit.json'),JSON.stringify(filtro,null,2));
    const saved=await win.webContents.executeJavaScript(`window.hunt.load().then(p=>window.hunt.save(p)).then(p=>({auto:p.auto_base,source:p.data_source,radius:p.radius}))`);
    fs.writeFileSync(path.join(out,'perfil-salvo.json'),JSON.stringify(saved,null,2));
    const coordenadas=await win.webContents.executeJavaScript(`(async()=>{
      const original=await window.hunt.load(),resultados=[];
      const errosBase=()=>errosDoFormulario(profile).filter(e=>e.fields.some(f=>['base-x','base-y'].includes(f.element?.id)));
      for(const [modo,auto] of [['base',true],['termes_verit_leste',false]]){
        profile={...original,patrol_mode:modo,auto_base:auto,base:[2859.75,829.25]};render();
        $('base-x').value='2859.75';$('base-y').value='829.25';
        if(!$('base-x').disabled||!$('base-y').disabled||errosBase().length)throw new Error('Base automatica/rota validou coordenadas ocultas');
        resultados.push(modo);
      }
      profile={...original,patrol_mode:'base',auto_base:false,base:[2859.75,829.25]};render();
      if($('base-x').disabled||$('base-x').value!=='2860'||$('base-y').value!=='829'||errosBase().length)throw new Error('Leitura decimal nao preencheu a base manual com inteiros');
      $('base-x').value='2859.75';if(!errosBase().length)throw new Error('Base manual fracionaria foi aceita');
      $('base-x').value='10000';if(!errosBase().length)throw new Error('Base manual fora do mapa foi aceita');
      profile=original;render();return {modos:resultados,manual:true,limites:true};
    })()`);
    fs.writeFileSync(path.join(out,'coordenadas.json'),JSON.stringify(coordenadas,null,2));
    const objetivosJardim=await win.webContents.executeJavaScript(`(async()=>{
      const original=await window.hunt.load(),resultados=[];
      for(const objetivo of ['seridunn','antes_shiraz']){
        profile={...original,patrol_mode:'jardim_aereo',jardim_goal:objetivo};render();
        if($('jardim-goal').value!==objetivo)throw new Error('Objetivo do Jardim nao renderizado');
        const salvo=await window.hunt.save(collect()),lido=await window.hunt.load();
        if(salvo.jardim_goal!==objetivo||lido.jardim_goal!==objetivo)throw new Error('Objetivo do Jardim nao persistiu');
        resultados.push(objetivo);
      }
      await window.hunt.save(original);profile=original;render();return resultados;
    })()`);
    fs.writeFileSync(path.join(out,'objetivos-jardim.json'),JSON.stringify(objetivosJardim,null,2));
    await win.webContents.executeJavaScript(`document.querySelector('[data-tab="behavior"]').click()`);
    await new Promise(r=>setTimeout(r,300));
    fs.writeFileSync(path.join(out,'comportamento.png'),(await win.webContents.capturePage()).toPNG());
    await win.webContents.executeJavaScript(`document.querySelector('[data-tab="extension"]').click()`);
    await new Promise(r=>setTimeout(r,300));
    fs.writeFileSync(path.join(out,'extensao.png'),(await win.webContents.capturePage()).toPNG());
    await win.webContents.executeJavaScript(`document.querySelector('[data-tab="basic"]').click();document.querySelector('#skills .slot').click()`);
    await new Promise(r=>setTimeout(r,300));
    fs.writeFileSync(path.join(out,'editar-slot.png'),(await win.webContents.capturePage()).toPNG());
    const dialogOpen=await win.webContents.executeJavaScript(`document.querySelector('#slot-dialog').open`);
    fs.writeFileSync(path.join(out,'resultado.json'),JSON.stringify({initial,dialogOpen},null,2));
    app.quit();
   }catch(e){fs.writeFileSync(path.join(runtime.root,'aika_hunt_app','ui-test-error.txt'),e.stack);app.quit();}
  });
 }
}
ipcMain.handle('profile:load',async()=>{let p;try{p=await require('./profile-store.cjs').loadProfile(profilePath(),{validate:p=>utility('validate',p),defaults:()=>utility('defaults')});profileLoadFailure=null;}catch(e){profileLoadFailure=e;registrarPainel('erro-carregar-perfil',{arquivo:profilePath(),erro:e.message});throw new Error('Nao foi possivel carregar suas configuracoes; arquivo preservado. '+e.message);}clientSelection={client_pid:p.client_pid||0,client_hwnd:p.client_hwnd||0};await stopWatcher();startWatcher();return p;});
ipcMain.handle('profile:save',async(_,p)=>{const v=await saveProfile(p);if(!worker){await stopWatcher();startWatcher();}return v;});
ipcMain.handle('clients:list',()=>utility('clients'));
ipcMain.handle('data:position',(_,p)=>utility('position',p||clientSelection));
ipcMain.handle('data:barra',(_,p)=>utility('barra',p||clientSelection));
ipcMain.handle('profile:native',async(_,p)=>{
 const r=await dialog.showOpenDialog(win,{title:'Importar configuração do assistente do Aika',defaultPath:'C:\\GoLevel\\AikaOnline\\UI',properties:['openFile'],filters:[{name:'Configuração do assistente (AHI)',extensions:['bin']}]});
 if(r.canceled)return null;
 if(!/^AHI.*\.bin$/i.test(path.basename(r.filePaths[0])))throw new Error('Selecione um arquivo AHI*.bin do assistente.');
 return utility('native',{path:r.filePaths[0],profile:p});
});
ipcMain.handle('hunt:start',async(_,p)=>{
 if(worker)throw new Error('A caça já está aberta. Pare antes de começar novamente.');
 const validated=await saveProfile(p);
 await stopWatcher();
 registrarPainel('inicio-caca',{alvo:validated.target});
 const child=spawn(runtime.command,[...runtime.args,'run',profilePath()],{cwd:runtime.root,windowsHide:true,env:clientEnv(),stdio:['pipe','pipe','pipe']});worker=child;
 let buffer='',error='';
 child.stdout.on('data',d=>{buffer+=d.toString('utf8');let at;while((at=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,at);buffer=buffer.slice(at+1);try{const event=JSON.parse(line);send(event);if(event.event==='error'&&!quitting){win.restore();win.show();}}catch{if(line.trim())send({event:'log',message:line});}}});
 child.stderr.on('data',d=>{error+=d.toString('utf8');if(error.length>6000)error=error.slice(-6000);});
 child.on('error',e=>{send({event:'error',message:e.message});worker=null;});
 child.on('close',code=>{clearTimeout(stopTimer);if(worker===child)worker=null;send({event:'exit',code,message:code?'A caça encerrou com erro. Confira o aviso no painel.':'Caça encerrada.'});if(quitting)win?.destroy();else startWatcher();});
 if(validated.minimize_on_start)setTimeout(()=>{if(worker){registrarPainel('minimizado-ao-iniciar');win.minimize();}},400);
 return {started:true};
});
ipcMain.handle('hunt:stop',()=>{stopWorker();return true;});
ipcMain.handle('hunt:pause',(_,paused)=>{if(worker)worker.stdin.write(JSON.stringify({command:paused?'pause':'resume'})+'\n');return !!worker;});
ipcMain.handle('window:minimize',()=>win.minimize());
ipcMain.handle('window:title',(_,title)=>{const nome=String(title||'').trim().slice(0,80);win.setTitle(nome||'Caça automática');return true;});
let boundsAntesFluxo=null;
ipcMain.handle('window:flow-editor',(_,aberto)=>{
 if(typeof aberto!=='boolean')throw new Error('Estado do editor invalido.');
 if(aberto){
  if(boundsAntesFluxo)return;
  boundsAntesFluxo=win.getBounds();const area=screen.getDisplayMatching(boundsAntesFluxo).workArea;
  const width=Math.min(1360,area.width),height=Math.min(860,area.height);
  win.setMaximumSize(10000,10000);win.setMinimumSize(Math.min(850,area.width),Math.min(600,area.height));win.setResizable(true);
  win.setBounds({x:area.x+Math.floor((area.width-width)/2),y:area.y+Math.floor((area.height-height)/2),width,height});
 }else if(boundsAntesFluxo){
  const bounds=boundsAntesFluxo;boundsAntesFluxo=null;win.setMinimumSize(390,600);win.setBounds(bounds);win.setMaximumSize(390,600);win.setResizable(false);
 }
});
ipcMain.handle('window:close',()=>{registrarPainel('botao-fechar');win.close();});
ipcMain.handle('app:info',()=>({version:app.getVersion(),packaged:app.isPackaged}));
ipcMain.handle('updates:check',()=>updates.check());
ipcMain.handle('logs:open',()=>{const pasta=path.join(runtime.dataRoot,'app_sessions');fs.mkdirSync(pasta,{recursive:true});return shell.openPath(pasta);});
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',()=>{if(worker)stopWorker();stopWatcher();});
app.whenReady().then(createWindow);
