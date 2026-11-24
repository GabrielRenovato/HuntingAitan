// Cada caminho representa uma regra AND do motor existente. Nao executa codigo.
(()=>{
const PADRAO={nome:'Nova regra',tecla:'',tipo:'ataque',ativa:true,skill_id:0,hp_max_pct:100,mp_max_pct:100,mp_min:0,so_em_combate:false,mobs_min:0,mobs_raio_m:6,alvo_hp_min_pct:0,alvo_hp_max_pct:100,alcance_m:0,intervalo_s:2.5};
const TIPOS={inicio:'Avaliar regra',hp:'Vida do personagem',mp:'Mana disponível',mp_pct:'Porcentagem de mana',combate:'Em combate',mobs:'Hostis próximos',alvo:'Vida do alvo',alcance:'Alcance do alvo',pronta:'Recarga e intervalo',acao:'Usar habilidade'};
function criar(regra){
 const r={...PADRAO,...regra},nodes=[{id:'inicio',type:'inicio',data:{}}];
 const add=(type,data)=>nodes.push({id:type,type,data});
 if(r.tipo==='item_mp')add('mp_pct',{value:r.mp_max_pct});else if(r.hp_max_pct<100)add('hp',{value:r.hp_max_pct});
 if(r.mp_min>0)add('mp',{value:r.mp_min});
 if(r.so_em_combate||['ataque','buff_combate'].includes(r.tipo))add('combate',{});
 if(r.mobs_min>0)add('mobs',{count:r.mobs_min,radius:r.mobs_raio_m});
 if(r.alvo_hp_min_pct>0||r.alvo_hp_max_pct<100)add('alvo',{min:r.alvo_hp_min_pct,max:r.alvo_hp_max_pct});
 if(r.alcance_m>0)add('alcance',{value:r.alcance_m});
 add('pronta',{seconds:r.intervalo_s});
 add('acao',{nome:r.nome,tecla:r.tecla,tipo:r.tipo,ativa:r.ativa,skill_id:r.skill_id});
 nodes.forEach((n,i)=>{n.x=60+i*250;n.y=150;});
 return {nodes,edges:nodes.slice(1).map((n,i)=>({from:nodes[i].id,to:n.id}))};
}
function validar(g){
 const errors=[],ids=new Set(g.nodes.map(n=>n.id)),byType=t=>g.nodes.filter(n=>n.type===t);
 const err=(message,nodes=[])=>errors.push({message,nodes});
 if(ids.size!==g.nodes.length)err('Existem blocos com identificação repetida.');
 for(const t of ['inicio','pronta','acao'])if(byType(t).length!==1)err('Mantenha exatamente um bloco de '+TIPOS[t]+'.');
 for(const e of g.edges)if(!ids.has(e.from)||!ids.has(e.to))err('Uma conexão aponta para um bloco removido.');
 for(const n of g.nodes){
  if(!TIPOS[n.type]){err('Tipo de bloco desconhecido.',[n.id]);continue;}
  const ins=g.edges.filter(e=>e.to===n.id).length,outs=g.edges.filter(e=>e.from===n.id).length;
  if(ins!==(n.type==='inicio'?0:1)||outs!==(n.type==='acao'?0:1))err('Conecte '+TIPOS[n.type]+' ao caminho. Cada regra usa uma sequência de condições.',[n.id]);
 }
 const start=byType('inicio')[0],visited=new Set();let n=start;
 while(n&&!visited.has(n.id)){visited.add(n.id);const e=g.edges.find(e=>e.from===n.id);n=e?g.nodes.find(v=>v.id===e.to):null;}
 if(n)err('O fluxo contém um ciclo. Conecte o final a Usar habilidade.',[n.id]);
 if(visited.size!==g.nodes.length)err('Há blocos desconectados do início.',g.nodes.filter(n=>!visited.has(n.id)).map(n=>n.id));
 const types=new Set();for(const n of g.nodes){if(types.has(n.type))err('Use apenas uma condição de cada tipo.',[n.id]);types.add(n.type);}
 const lim=(n,key,min,max,integer=false)=>{const v=n.data[key];if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max||(integer&&!Number.isInteger(v)))err(`${TIPOS[n.type]}: ${key} deve ficar entre ${min} e ${max}${integer?', em número inteiro':''}.`,[n.id]);};
 for(const n of g.nodes){
  if(['hp','mp_pct'].includes(n.type))lim(n,'value',1,100);
  if(n.type==='mp')lim(n,'value',0,10000000,true);
  if(n.type==='alcance')lim(n,'value',0,40);
  if(n.type==='mobs'){lim(n,'count',1,50,true);lim(n,'radius',1,40);}
  if(n.type==='alvo'){lim(n,'min',0,100);lim(n,'max',1,100);if(n.data.min>=n.data.max)err('Vida do alvo: o mínimo precisa ser menor que o máximo.',[n.id]);}
  if(n.type==='pronta')lim(n,'seconds',.5,3600);
  if(n.type==='acao'){
   lim(n,'skill_id',0,11999,true);
   if(!['emergencia','defesa','cura','item_hp','item_mp','buff','buff_combate','ataque'].includes(n.data.tipo))err('Escolha o tipo da ação.',[n.id]);
   if(n.data.ativa&&!/^(?:(?:ctrl|alt|shift)\+)?(?:[a-z0-9']|f(?:[1-9]|10|11))$/.test(String(n.data.tecla).trim().toLowerCase()))err('Informe a tecla da ação. F12 é reservado.',[n.id]);
  }
 }
 const action=byType('acao')[0]?.data;
 if(action){
  if(action.tipo==='item_mp'&&byType('hp').length)err('Item de mana usa o limite de mana. Remova Vida do personagem ou troque o tipo da ação.',byType('hp').map(n=>n.id));
  if(action.tipo!=='item_mp'&&byType('mp_pct').length)err('Porcentagem de mana é usada por Item de mana. Troque o tipo da ação ou use Mana disponível.',byType('mp_pct').map(n=>n.id));
  if(['ataque','buff_combate'].includes(action.tipo)&&!byType('combate').length)err('Ataques e buffs de combate precisam do bloco Em combate.',byType('acao').map(n=>n.id));
 }
 if(start){const path=[];let cur=start;const seen=new Set();while(cur&&!seen.has(cur.id)){seen.add(cur.id);path.push(cur.type);cur=g.nodes.find(n=>n.id===g.edges.find(e=>e.from===cur.id)?.to);}
  if(path.at(-1)!=='acao')err('O caminho deve terminar em Usar habilidade.');
 }
 return errors;
}
function compilar(g){
 const errors=validar(g);if(errors.length){const e=new Error(errors[0].message);e.errors=errors;throw e;}
 const action=g.nodes.find(n=>n.type==='acao').data,r={...PADRAO,...action,tecla:String(action.tecla).trim().toLowerCase()};
 for(const n of g.nodes){const d=n.data;
  if(n.type==='hp')r.hp_max_pct=d.value;
  if(n.type==='mp_pct')r.mp_max_pct=d.value;
  if(n.type==='mp')r.mp_min=d.value;
  if(n.type==='combate')r.so_em_combate=true;
  if(n.type==='mobs'){r.mobs_min=d.count;r.mobs_raio_m=d.radius;}
  if(n.type==='alvo'){r.alvo_hp_min_pct=d.min;r.alvo_hp_max_pct=d.max;}
  if(n.type==='alcance')r.alcance_m=d.value;
  if(n.type==='pronta')r.intervalo_s=d.seconds;
 }
 return r;
}
function conectar(g,from,to){
 if(from===to)throw Error('Um bloco não pode conectar a si mesmo.');
 const a=g.nodes.find(n=>n.id===from),b=g.nodes.find(n=>n.id===to);
 if(!a||!b||a.type==='acao'||b.type==='inicio')throw Error('Conecte uma saída à entrada de outro bloco.');
 g.edges=g.edges.filter(e=>e.from!==from&&e.to!==to);g.edges.push({from,to});
}
function remover(g,id){const n=g.nodes.find(n=>n.id===id);if(!n||['inicio','pronta','acao'].includes(n.type))throw Error('Início, recarga e ação fazem parte de toda regra.');
 const antes=g.edges.find(e=>e.to===id),depois=g.edges.find(e=>e.from===id);g.nodes=g.nodes.filter(n=>n.id!==id);g.edges=g.edges.filter(e=>e.from!==id&&e.to!==id);if(antes&&depois)g.edges.push({from:antes.from,to:depois.to});
}
const api={PADRAO,TIPOS,criar,validar,compilar,conectar,remover};if(typeof module!=='undefined')module.exports=api;else window.FluxoModelo=api;
})();
