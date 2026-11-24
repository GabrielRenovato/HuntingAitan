// Aba "Reações": configura cura, defesa, emergência, itens, buffs e ataques por tecla.
// Altera profile.reacoes no lugar; o botão "Salvar configuração" existente grava o perfil.
(()=>{
const TIPOS=[['emergencia','Emergência'],['defesa','Defesa'],['cura','Cura'],['item_hp','Item de vida'],['item_mp','Item de mana'],['buff','Buff contínuo'],['buff_combate','Buff combate'],['ataque','Ataque']];
const NOME_TIPO=Object.fromEntries(TIPOS);
const PADRAO_HP={emergencia:30,defesa:50,cura:60,item_hp:50,item_mp:100,buff:100,buff_combate:100,ataque:100};
const COMBATE=['buff_combate','ataque'];
const ITENS=['item_hp','item_mp'];
const TIPO_SKILL={cura:'cura',defesa:'defesa',buff:'buff',ataque:'ataque',ameaca:'ameaça',passiva:'passiva',utilidade:'utilidade',item:'item'};
// Valores padrão iguais aos do Python (reacoes.py); o painel os mostra mesmo quando a regra ainda não os traz.
const BASE={mp_max_pct:100,mp_min:0,mobs_min:0,mobs_raio_m:6,alvo_hp_min_pct:0,alvo_hp_max_pct:100,alcance_m:0,intervalo_s:2.5,so_em_combate:false,skill_id:0};
function completar(r){
 for(const [k,v] of Object.entries(BASE))if(r[k]===undefined||r[k]===null)r[k]=v;
 if(r.hp_max_pct===undefined||r.hp_max_pct===null)r.hp_max_pct=PADRAO_HP[r.tipo]??60;
 return r;
}
let perfil=null,barra=[];

const el=(tag,props={},...filhos)=>{
 const e=document.createElement(tag);
 for(const [k,v] of Object.entries(props)){if(k==='class')e.className=v;else if(k==='text')e.textContent=v;else if(k.startsWith('on'))e.addEventListener(k.slice(2),v);else if(v!==undefined&&v!==null)e.setAttribute(k,v);}
 e.append(...filhos.filter(x=>x!==null&&x!==undefined));return e;
};
const status=(texto)=>{const s=document.getElementById('bar-status');if(s)s.textContent=texto;};
const regras=()=>perfil.reacoes;

function numero(regra,chave,rotulo,{min=0,max=100,passo='any',sufixo=''}={}){
 const entrada=el('input',{type:'number',min,max,step:passo,value:regra[chave],'aria-label':rotulo});
 entrada.dataset.configPath=`reacoes.${regras().indexOf(regra)}.${chave}`;
 entrada.addEventListener('change',()=>{const v=Number(entrada.value);if(Number.isFinite(v))regra[chave]=v;});
 return el('label',{class:'campo'},el('span',{text:rotulo}),entrada,sufixo?el('span',{class:'sufixo',text:sufixo}):null);
}

function cartao(regra,indice){
 const card=el('div',{class:'reacao'+(regra.ativa?'':' inativa')+(regra.ativa&&!regra.tecla?' sem-tecla':'')});
 const ativa=el('input',{type:'checkbox','aria-label':'Ativar reação'});ativa.checked=!!regra.ativa;
 ativa.addEventListener('change',()=>{regra.ativa=ativa.checked;desenhar();});
 const nome=el('input',{type:'text',class:'nome',maxlength:40,value:regra.nome||'',placeholder:'Nome','aria-label':'Nome'});
 nome.addEventListener('change',()=>{regra.nome=nome.value.trim();});
 const tecla=el('input',{type:'text',class:'tecla',maxlength:12,value:regra.tecla||'',placeholder:'tecla','aria-label':'Tecla',title:'Ex.: f2, 3, ctrl+3'});
 tecla.dataset.configPath=`reacoes.${indice}.tecla`;
 tecla.addEventListener('change',()=>{regra.tecla=tecla.value.trim().toLowerCase();desenhar();});
 const tipo=el('select',{'aria-label':'Tipo'},...TIPOS.map(([v,t])=>el('option',{value:v,text:t})));tipo.value=regra.tipo;
 tipo.addEventListener('change',()=>{regra.tipo=tipo.value;regra.hp_max_pct=PADRAO_HP[tipo.value];desenhar();});
 const remover=el('button',{class:'remover',type:'button','aria-label':'Remover reação',text:'×',onclick:()=>{regras().splice(indice,1);desenhar();}});
 const linha1=el('div',{class:'linha'},ativa,nome,tecla,tipo,remover);

 const campos=[];
 if(regra.tipo==='item_mp')campos.push(numero(regra,'mp_max_pct','Mana ≤',{min:1,max:100,sufixo:'%'}));
 else campos.push(numero(regra,'hp_max_pct','Vida ≤',{min:1,max:100,sufixo:'%'}));
 if(!ITENS.includes(regra.tipo))campos.push(numero(regra,'mp_min','Mana ≥',{min:0,max:10000000,passo:1}));
 campos.push(numero(regra,'intervalo_s','Intervalo',{min:.5,max:3600,sufixo:'s'}));
 if(!ITENS.includes(regra.tipo)){
  campos.push(numero(regra,'mobs_min','Mobs ≥',{min:0,max:50,passo:1}));
  if(regra.mobs_min>0)campos.push(numero(regra,'mobs_raio_m','em',{min:1,max:40,sufixo:'m'}));
 }
 if(regra.tipo==='ataque'){
  campos.push(numero(regra,'alcance_m','Alcance ≤',{min:0,max:40,sufixo:'m'}));
  campos.push(numero(regra,'alvo_hp_min_pct','Alvo >',{min:0,max:100,sufixo:'%'}));
  campos.push(numero(regra,'alvo_hp_max_pct','Alvo ≤',{min:1,max:100,sufixo:'%'}));
 }
 if(!COMBATE.includes(regra.tipo)){
  const combate=el('input',{type:'checkbox'});combate.checked=!!regra.so_em_combate;
  combate.addEventListener('change',()=>{regra.so_em_combate=combate.checked;});
  campos.push(el('label',{class:'campo marcar'},combate,el('span',{text:'só em combate'})));
 }
 const dica=regra.skill_id?el('span',{class:'dica',text:'skill '+regra.skill_id,title:'Recarga real lida do cliente'}):null;
 card.append(linha1,el('div',{class:'linha campos'},...campos,dica));
 return card;
}

function desenhar(){
 const raiz=document.getElementById('reactions-rules');if(!raiz||!perfil)return;
 raiz.replaceChildren();
 if(!regras().length){raiz.append(el('p',{class:'muted',text:'Nenhuma reação. Leia a barra do jogo e clique em uma habilidade ou item para adicionar.'}));return;}
 regras().forEach((r,i)=>{const c=cartao(r,i);raiz.append(c);});
}

// Uma habilidade entra uma vez (pelo id); um item entra uma vez por tecla.
function jaAdicionada(item){
 const s=item.sugestao;if(!s)return false;
 return regras().some(r=>s.skill_id?r.skill_id===s.skill_id:r.tecla===s.tecla);
}

function adicionar(item){
 const s=item.sugestao;if(!s)return;
 if(regras().length>=20){window.message('Limite de reações','Remova uma reação antes de adicionar outra.','error');return;}
 const nova=completar({ativa:true,...s});
 if(nova.tecla&&regras().some(r=>r.ativa&&r.tecla===nova.tecla)){window.message('Tecla já usada',`Já existe uma reação na tecla ${nova.tecla}.`,'error');return;}
 if(nova.tecla&&nova.tecla===perfil.attack_key){window.message('Tecla do ataque normal',`A tecla ${nova.tecla} é o ataque normal; escolha outra para a reação.`,'error');return;}
 // A rotação antiga usa as mesmas teclas 1-8: desativa a habilidade repetida para a validação aceitar.
 const movidas=(perfil.skills||[]).filter(sk=>sk.enabled&&nova.tecla&&sk.key===nova.tecla);
 movidas.forEach(sk=>{sk.enabled=false;});
 regras().push(nova);desenhar();desenharBarra();
 if(typeof renderSlots==='function')renderSlots();
 const buffs=[...(perfil.buffs_enabled?perfil.buff_keys||[]:[]),...(perfil.extra_buffs_enabled?['ctrl+6','ctrl+8']:[]),...(perfil.f3_enabled?['f3']:[])];
 if(nova.tecla&&buffs.includes(nova.tecla)){window.message('Tecla dos buffs por tempo',`A tecla ${nova.tecla} também é usada pelos buffs por tempo (aba Extensão). Mude esse atalho ou desative os buffs antes de salvar.`,'error');return;}
 const aviso=!nova.tecla?'Informe a tecla desta reação.':movidas.length?`A habilidade da rotação na tecla ${nova.tecla} foi desativada para não repetir.`:'Ajuste os limites e salve a configuração.';
 window.message('Reação adicionada',aviso,nova.tecla?'idle':'error');
}

function desenharBarra(){
 const raiz=document.getElementById('bar-slots');if(!raiz)return;raiz.replaceChildren();
 if(!barra.length)return;
 for(const item of barra){
  const sug=item.sugestao,usada=jaAdicionada(item);
  const rotulo=`${item.tecla||'—'} · ${item.nome}`;
  const detalhe=item.tipo_slot==='skill'?`${TIPO_SKILL[item.tipo]||item.tipo} · ${item.recarga_s>=60?Math.round(item.recarga_s/60*10)/10+' min':item.recarga_s+' s'} · mana ${item.mana}`:'item da barra (escolha vida ou mana)';
  const botao=el('button',{class:'chip'+(sug?'':' sem-reacao')+(usada?' ja-usada':''),type:'button',title:item.descricao||detalhe,onclick:()=>adicionar(item)},
                 el('b',{text:rotulo}),el('span',{text:detalhe}));
  botao.disabled=!sug||usada;
  raiz.append(botao);
 }
}

async function lerBarra(){
 const botao=document.getElementById('read-bar');botao.disabled=true;status('Lendo a barra do jogo…');
 try{
  const r=await window.hunt.bar();barra=r.slots||[];desenharBarra();
  const skills=barra.filter(i=>i.tipo_slot==='skill').length,itens=barra.length-skills;
  status(barra.length?`${skills} habilidades e ${itens} itens encontrados. Clique para adicionar uma reação.`:'Nenhuma habilidade encontrada na barra.');
 }catch(e){barra=[];desenharBarra();status('');throw e;}
 finally{botao.disabled=false;}
}

window.renderizarReacoes=p=>{
 perfil=p;if(!Array.isArray(perfil.reacoes))perfil.reacoes=[];
 perfil.reacoes.forEach(completar);
 desenhar();desenharBarra();
};
window.addEventListener('DOMContentLoaded',()=>{
 const botao=document.getElementById('read-bar');
 if(botao)botao.addEventListener('click',()=>window.action(lerBarra));
});
})();
