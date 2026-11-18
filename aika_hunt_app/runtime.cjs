const fs=require('node:fs');
const path=require('node:path');
module.exports=({app,dirname})=>{
 const root=path.resolve(dirname,'..');
 if(app.isPackaged){
  const command=path.join(process.resourcesPath,'backend','hunt_backend.exe');
  if(!fs.existsSync(command))throw new Error('Motor ausente. Reinstale o HuntingAitan.');
  return {root:path.dirname(command),dataRoot:app.getPath('userData'),command,args:[]};
 }
 const local=path.join(dirname,'runtime.local.json');
 const config=fs.existsSync(local)?JSON.parse(fs.readFileSync(local,'utf8')):{};
 return {root,dataRoot:root,command:process.env.AIKA_PYTHON||config.python||'python',args:['-u',path.join(root,'hunt_bridge.py')]};
};
