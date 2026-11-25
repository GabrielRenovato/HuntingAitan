const fs=require('node:fs');

async function loadProfile(file,{validate,defaults}){
 let text;
 try{text=fs.readFileSync(file,'utf8');}
 catch(e){if(e.code==='ENOENT')return defaults();throw e;}
 // Perfil existente invalido ou motor indisponivel nao significam primeira
 // execucao. Propaga o erro e preserva o arquivo para recuperacao.
 return validate(JSON.parse(text));
}

module.exports={loadProfile};
