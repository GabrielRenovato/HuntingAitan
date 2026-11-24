// Caminhos estaveis permitem marcar todos os lados de um conflito entre abas.
(()=>{
function analisar(p){
 const campos=[],erros=[];
 const add=(key,path,label)=>{key=String(key||'').trim().toLowerCase();if(key)campos.push({key,path,label});};
 add(p.attack_key,'attack_key','Ataque normal');
 for(const k of ['hp','mp'])(p[k+'_keys']||[]).forEach((v,i)=>add(v,`${k}_keys.${i}`,`${k.toUpperCase()} ${i+1}`));
 for(const k of ['skills','items'])(p[k]||[]).forEach((s,i)=>{if(s.enabled)add(s.key,`${k}.${i}.key`,`${k==='skills'?'Habilidade':'Item'} ${i+1}`);});
 if(p.buffs_enabled)(p.buff_keys||[]).forEach((v,i)=>add(v,`buff_keys.${i}`,`Buff por tempo ${i+1}`));
 if(p.extra_buffs_enabled)(p.extra_buff_keys||['ctrl+6','ctrl+8']).forEach((key,i)=>add(key,`extra_buff_keys.${i}`,`Buff adicional ${i+1}`));
 if(p.f3_enabled)add(p.periodic_item_key||'f3','periodic_item_key','Consumível periódico');
 (p.reacoes||[]).forEach((r,i)=>{
  if(!r.ativa)return;
  const path=`reacoes.${i}.tecla`,label=r.nome||`Reação ${i+1}`;
  if(!/^(?:(?:ctrl|alt|shift)\+)?(?:[a-z0-9']|f(?:[1-9]|10|11))$/.test(String(r.tecla||'').trim().toLowerCase()))erros.push({message:`Informe uma tecla válida em ${label}.`,fields:[{path,label}]});
  add(r.tecla,path,label);
  if(Number(r.alvo_hp_min_pct)>=Number(r.alvo_hp_max_pct))erros.push({message:`${label}: a vida mínima do alvo precisa ser menor que a máxima.`,fields:[{path:`reacoes.${i}.alvo_hp_min_pct`,label},{path:`reacoes.${i}.alvo_hp_max_pct`,label}]});
 });
 if(p.background_keys)for(const c of campos)if(c.key.includes('+'))erros.push({message:'Segundo plano exige teclas simples: '+c.label,fields:[c]});
 const grupos=new Map();for(const c of campos){if(!grupos.has(c.key))grupos.set(c.key,[]);grupos.get(c.key).push(c);}
 for(const [key,fields] of grupos)if(fields.length>1)erros.push({message:`Atalho ${key.toUpperCase()} repetido: ${fields.map(f=>f.label).join(' e ')}.`,fields});
 return erros;
}
if(typeof module!=='undefined')module.exports={analisar};else window.validacaoConfig={analisar};
})();
