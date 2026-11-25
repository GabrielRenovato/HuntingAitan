const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {loadProfile}=require('./aika_hunt_app/profile-store.cjs');
(async()=>{
 assert.ok(require('./aika_hunt_app/package.json').build.files.includes('profile-store.cjs'));
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'hunting-perfil-')),file=path.join(dir,'profile.json');
 let padroes=0;const defaults=async()=>{padroes++;return {novo:true};};
 const validate=async p=>{if(p.invalido)throw new Error('Atalho repetido');return p;};
 assert.deepEqual(await loadProfile(file,{validate,defaults}),{novo:true});assert.equal(padroes,1);
 const personalizado=JSON.stringify({buff_keys:['f1','f2','f3'],reacoes:[{tecla:'f4'}]});fs.writeFileSync(file,personalizado);
 assert.deepEqual((await loadProfile(file,{validate,defaults})).buff_keys,['f1','f2','f3']);
 assert.equal(fs.readFileSync(file,'utf8'),personalizado);
 for(const texto of ['{"invalido":true}','{ quebrado']){
  fs.writeFileSync(file,texto);await assert.rejects(loadProfile(file,{validate,defaults}));
  assert.equal(fs.readFileSync(file,'utf8'),texto);assert.equal(padroes,1);
 }
 fs.writeFileSync(file,personalizado);
 await assert.rejects(loadProfile(file,{defaults,validate:async()=>{throw new Error('Motor demorou');}}),/Motor demorou/);
 assert.equal(fs.readFileSync(file,'utf8'),personalizado);assert.equal(padroes,1);
 await assert.rejects(loadProfile(dir,{validate,defaults}));assert.equal(padroes,1);
 console.log('OK: perfil personalizado preservado; erro de leitura/validacao nao restaura padroes silenciosamente.');
})().catch(e=>{console.error(e);process.exitCode=1;});
