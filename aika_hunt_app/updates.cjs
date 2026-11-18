module.exports=({app,send,isHunting,getWindow,log,updater,dialog})=>{
 if(!app.isPackaged)return {check:async()=>({development:true})};
 updater ||= require('electron-updater').autoUpdater;
 updater.autoDownload=true;
 updater.autoInstallOnAppQuit=true;
 updater.allowPrerelease=app.getVersion().includes('-');
 updater.channel=updater.allowPrerelease?'beta':'latest';
 let checking=false,ready=false;
 const emit=(state,message)=>send({event:'update',state,message,version:app.getVersion()});
 updater.on('error',e=>{log('erro-atualizacao',{erro:e.message});emit('error','Não foi possível verificar atualizações. Tente novamente depois.');});
 updater.on('update-available',info=>emit('downloading','Baixando atualização '+info.version+'…'));
 updater.on('update-not-available',()=>emit('current','Você está na versão mais recente.'));
 updater.on('update-downloaded',async info=>{
  ready=true;emit('ready','Versão '+info.version+' baixada. Será instalada ao fechar o aplicativo.');
  // Nunca interromper a caca para instalar uma atualizacao.
  if(isHunting())return;
  try{
   const r=await dialog.showMessageBox(getWindow(),{type:'info',title:'Atualização pronta',message:'A versão '+info.version+' foi baixada.',detail:'Reiniciar agora para instalar? Suas configurações serão preservadas.',buttons:['Reiniciar agora','Depois'],defaultId:0,cancelId:1});
   if(r.response===0&&!isHunting())updater.quitAndInstall(false,true);
  }catch(e){log('aviso-atualizacao',{erro:e.message});}
 });
 async function check(){
  if(checking)return {checking:true};
  if(ready){emit('ready','Atualização baixada. Feche e abra o aplicativo para instalar.');return {ready:true};}
  checking=true;
  try{emit('checking','Verificando atualizações…');await updater.checkForUpdates();return {checked:true};}
  catch(e){log('checagem-atualizacao',{erro:e.message});emit('error','Verificação indisponível. O aplicativo continua funcionando.');return {error:true};}
  finally{checking=false;}
 }
 return {check};
};
