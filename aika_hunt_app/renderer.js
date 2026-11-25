const $=id=>document.getElementById(id);
let profile=null,running=false,paused=false,editing=null,lastError=false;
const lines=[];let startedAt=null;
let openClients=[];
const names={confirmando_cura:'Confirmando cura',confirmando_habilidade:'Confirmando habilidade',recuperando_controle:'Recuperando comandos',aguardando_controle:'Comandos sem resposta',percorrer:'Percorrendo rota',aviso:'Fechando aviso',rebufar:'Renovando buffs',initializing:'Inicializando dados internos',inicio:'Confirmando posição',buscar:'Procurando alvo',combater:'Em combate',retornar:'Voltando à base',waiting:'Aguardando o Aika',paused:'Pausado',stopped:'Parado'};
function message(title,detail='',type='idle'){$('state-label').textContent=title;$('state-detail').textContent=detail;$('state-dot').className='dot '+type;}
function fail(e){lastError=true;const detail=String(e.message||e).replace(/^Error invoking remote method '[^']+': Error: /,'');marcarErrosConfig(e.configErrors||window.validacaoConfig.analisar(profile||{}),true);message('Confira a configuração',detail,'error');}
const idsConfig={attack_key:'attack',extra_buffs_enabled:'extra-buffs-enabled',f3_enabled:'f3-enabled'};
function campoConfig(path){return document.querySelector(`[data-config-path="${path}"]`)||$(idsConfig[path]||(/^buff_keys\.\d+$/.test(path)?'buff-key-'+path.split('.')[1]:''));}
function limparErrosConfig(){
 document.querySelectorAll('[aria-invalid="true"]').forEach(e=>{e.removeAttribute('aria-invalid');e.title=e.dataset.titleAntesErro||'';delete e.dataset.titleAntesErro;});
 document.querySelectorAll('.config-invalid').forEach(e=>e.classList.remove('config-invalid'));
 document.querySelectorAll('.config-error-note').forEach(e=>e.remove());
}
function marcarErrosConfig(erros,focar=false){
 limparErrosConfig();let primeiro=null;
 for(const erro of erros)for(const f of erro.fields){
  const e=f.element||campoConfig(f.path);if(!e)continue;
  if(!e.hasAttribute('aria-invalid'))e.dataset.titleAntesErro=e.title||'';
  e.classList.add('config-invalid');e.setAttribute('aria-invalid','true');e.title=erro.message;
  const card=e.closest('.reacao'),panel=e.closest('.tab-panel');if(card)card.classList.add('config-invalid');
  if(panel)document.querySelector(`[data-tab="${panel.id}"]`)?.classList.add('config-invalid');
  const box=card||e.closest('.setting')||e.closest('fieldset');
  if(box&&!box.querySelector('.config-error-note')){const nota=document.createElement('p');nota.className='config-error-note';nota.textContent=erro.message;box.append(nota);}
  primeiro??=e;
 }
 if(focar&&primeiro){const panel=primeiro.closest('.tab-panel');if(panel)document.querySelector(`[data-tab="${panel.id}"]`)?.click();primeiro.scrollIntoView({block:'center'});primeiro.focus({preventScroll:true});}
}
function errosDoFormulario(p){
 const erros=window.validacaoConfig.analisar(p);
 document.querySelectorAll('.tab-panel input[type="number"]').forEach(e=>{
  if(e.disabled||e.checkValidity())return;
  const nome=e.getAttribute('aria-label')||e.closest('label')?.textContent.trim()||e.id;
  const v=e.validity,numero=n=>Number(n).toLocaleString('pt-BR');
  let motivo='informe um número válido.';
  if(v.rangeUnderflow)motivo=`o mínimo permitido é ${numero(e.min)}.`;
  else if(v.rangeOverflow)motivo=`o máximo permitido é ${numero(e.max)}.`;
  else if(v.stepMismatch)motivo=e.step==='1'?'use um número inteiro, sem casas decimais.':`use incrementos de ${numero(e.step)} a partir de ${numero(e.min||0)}.`;
  erros.push({message:`${nome}: ${motivo}`,fields:[{element:e}]});
 });return erros;
}
function coletarValidado(){
 const p=collect(),erros=errosDoFormulario(p);
 marcarErrosConfig(erros);
 if(erros.length){const e=new Error(erros[0].message);e.configErrors=erros;throw e;}return p;
}
document.addEventListener('change',()=>{if(document.querySelector('.config-invalid')&&profile){try{marcarErrosConfig(errosDoFormulario(collect()));}catch{}}});
async function action(fn){try{await fn();}catch(e){fail(e);}}
function log(text){lines.push(new Date().toLocaleTimeString('pt-BR')+' · '+text);if(lines.length>120)lines.shift();$('log-lines').textContent=lines.join('\n');$('log-lines').scrollTop=$('log-lines').scrollHeight;}
function renderClients(){
 const select=$('client-select');select.replaceChildren();
 const auto=document.createElement('option');auto.value='0';auto.textContent='Automático · apenas um cliente';select.append(auto);
 for(const c of openClients){const o=document.createElement('option');o.value=`${c.pid}:${c.hwnd}`;o.textContent=`${c.name||'Personagem indisponível'} · PID ${c.pid}${c.ready?'':' · indisponível'}`;o.disabled=!c.ready;select.append(o);}
 const value=profile?.client_pid?`${profile.client_pid}:${profile.client_hwnd}`:'0';
 if(value!=='0'&&!Array.from(select.options).some(o=>o.value===value)){const o=document.createElement('option');o.value=value;o.textContent='Cliente anterior fechado · selecione novamente';select.append(o);}
 select.value=value;select.disabled=running;$('refresh-clients').disabled=running;
 const chosen=openClients.find(c=>`${c.pid}:${c.hwnd}`===value);
 $('client-state').textContent=chosen?(chosen.ready?`Personagem: ${chosen.name} · ${chosen.exe}`:chosen.error||'Leitura indisponível'):(value==='0'?'Escolha a conta desejada se houver mais de um Aika.':'O cliente salvo não está aberto. Atualize e selecione novamente.');
 if(chosen?.ready)$('player-read').textContent=chosen.name;
}
async function refreshClients(){
 if(running)throw new Error('Pare a caça antes de atualizar os clientes.');
 $('refresh-clients').disabled=true;
 try{openClients=await window.hunt.clients();renderClients();}finally{$('refresh-clients').disabled=running;}
}
function baseLabel(){const manual=profile.patrol_mode==='base'&&!profile.auto_base;for(const id of ['base-x','base-y'])$(id).disabled=!manual;if(profile.patrol_mode==='cinzenta_croshu_sul'){$('base-value').textContent='6 Croshus roxos · Sul · 2955, 1311';$('manual-base').classList.add('hidden');return;}if(profile.patrol_mode==='cinzenta_croshu_trio'){$('base-value').textContent='5 Croshus · 7 → 8 → 9 → 11 → 10';$('manual-base').classList.add('hidden');return;}if(profile.patrol_mode==='ungor_croshu'){$('base-value').textContent='Croshu · 6 → 3 → 7 · Ungor';$('manual-base').classList.add('hidden');return;}if(profile.patrol_mode==='ungor_plantas'){$('base-value').textContent='4 Plantas · Ungor · 2440, 1360';$('manual-base').classList.add('hidden');return;}if(profile.patrol_mode==='buto_trio'){$('base-value').textContent='Butos · 2711, 1292 · raio 30';$('manual-base').classList.add('hidden');return;}if(profile.patrol_mode!=='base'){$('base-value').textContent=profile.patrol_mode==='mina_lenfer'?'Mina L’Enfer → Malik':profile.patrol_mode==='jardim_aereo'?'Jardim Aéreo · Shiraz Infernais':profile.patrol_mode==='termes_verit_leste'?'Verits · Termes leste · 7 pontos':profile.patrol_mode==='termes_verit'?'Circuito Verit · Termes':'Circuito de ida e volta';$('manual-base').classList.add('hidden');return;}const p=profile.base;$('base-value').textContent=profile.auto_base?(startedAt?`${Math.round(p[0])}, ${Math.round(p[1])}`:'Capturada ao começar'):`${Math.round(p[0])}, ${Math.round(p[1])}`;$('manual-base').classList.toggle('hidden',profile.auto_base);}
function slotButton(kind,index,icon,key,enabled=true){const b=document.createElement('button');b.className='slot'+(enabled?'':' inactive');b.type='button';b.title=(kind==='skills'?'Habilidade '+(index+1):kind==='items'?'Item '+(index+1):kind.toUpperCase()+' '+(index+1))+' · clique para configurar';if(icon){const img=document.createElement('img');img.src='assets/'+icon;img.alt='';b.append(img);}const k=document.createElement('span');k.className='key';k.textContent=key?key.toUpperCase():'';b.append(k);b.addEventListener('click',()=>openSlot(kind,index));return b;}
function renderSlots(){
 for(const kind of ['hp','mp']){const box=$(kind+'-slots');box.replaceChildren();profile[kind+'_keys'].forEach((key,i)=>box.append(slotButton(kind,i,i===0?kind+'.png':null,key,!!key)));}
 for(const kind of ['skills','items']){const box=$(kind);box.replaceChildren();profile[kind].forEach((s,i)=>{const wrap=document.createElement('div');wrap.className='skill-wrap';wrap.append(slotButton(kind,i,kind==='skills'&&s.icon!==null?'skill'+s.icon+'.png':null,s.key,s.enabled));const cd=document.createElement('span');cd.className='cooldown';const number=document.createElement('b');number.textContent=s.seconds?String(s.seconds):'';cd.append(number,document.createTextNode(s.seconds?' segundos':'segundos'));wrap.append(cd);box.append(wrap);});}
 $('return-slot').querySelector('.key').textContent=profile.return_key.toUpperCase();
 for(const kind of ['skills','items','hp','mp'])document.querySelectorAll(`#${kind==='hp'||kind==='mp'?kind+'-slots':kind} .slot`).forEach((b,i)=>{b.dataset.configPath=kind==='hp'||kind==='mp'?`${kind}_keys.${i}`:`${kind}.${i}.key`;});
}
function render(){
 renderClients();
 if(window.renderizarReacoes)window.renderizarReacoes(profile);
 $('cinzas-sul-hint').classList.toggle('hidden',profile.patrol_mode!=='cinzenta_croshu_sul');$('cinzas-hint').classList.toggle('hidden',profile.patrol_mode!=='cinzenta_croshu_trio');$('croshu-hint').classList.toggle('hidden',profile.patrol_mode!=='ungor_croshu');$('plantas-hint').classList.toggle('hidden',profile.patrol_mode!=='ungor_plantas');$('buto-hint').classList.toggle('hidden',profile.patrol_mode!=='buto_trio');$('radius').disabled=['buto_trio','cinzenta_croshu_trio','cinzenta_croshu_sul','ungor_plantas','ungor_croshu'].includes(profile.patrol_mode);$('auto-base').disabled=['buto_trio','cinzenta_croshu_trio','cinzenta_croshu_sul','ungor_plantas','ungor_croshu'].includes(profile.patrol_mode);
 $('background-keys').checked=!!profile.background_keys;
 $('auto-ui-scale').checked=profile.auto_ui_scale;
 $('jardim-hint').classList.toggle('hidden',profile.patrol_mode!=='jardim_aereo');$('jardim-repeat-settings').classList.toggle('hidden',profile.patrol_mode!=='jardim_aereo');$('jardim-repeat').checked=profile.jardim_repeat!==false;$('jardim-servico-npc').checked=profile.jardim_servico_npc!==false;$('jardim-cycles').value=profile.jardim_cycles||0;$('mina-repeat').checked=!!profile.mina_repeat;$('mina-cycles').value=profile.mina_cycles||0;
 $('target').disabled=profile.patrol_mode!=='base';$('patrol-mode').value=profile.patrol_mode||'base';$('patrol-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_penza');$('verit-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_verit');$('verit-leste-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_verit_leste');$('mina-hint').classList.toggle('hidden',profile.patrol_mode!=='mina_lenfer');
 $('cancel-normal').checked=!!profile.cancel_normal;$('combo-key-delay').value=profile.combo_key_delay_ms;$('combo-repeat').value=profile.combo_repeat_ms;
 $('heal-enabled').checked=profile.heal_enabled;$('heal-key').value=profile.heal_key;
 $('periodic-item-key').value=profile.periodic_item_key||'f3';
 (profile.extra_buff_keys||['ctrl+6','ctrl+8']).forEach((k,i)=>$('extra-buff-key-'+i).value=k);
 $('f3-enabled').checked=profile.f3_enabled;$('f3-minutes').value=profile.f3_minutes;
 $('extra-buffs-enabled').checked=profile.extra_buffs_enabled;$('extra-buff-minutes').value=profile.extra_buff_minutes;
 $('buff-enabled').checked=profile.buffs_enabled;$('buff-minutes').value=profile.buff_minutes;$('buff-gap').value=profile.buff_gap;profile.buff_keys.forEach((k,i)=>$('buff-key-'+i).value=k);$('buff-next').textContent=profile.buffs_enabled?'Ao iniciar e a cada '+profile.buff_minutes+' minutos':'Desativado';
 $('hp-percent').value=profile.hp_percent;$('mp-percent').value=profile.mp_percent;
 for(const [id,key] of Object.entries({gap:'action_gap',attack:'attack_key',duration:'duration_minutes',radius:'radius',target:'target','no-damage':'no_damage_seconds',stationary:'stationary_seconds',unstuck:'unstuck_key'}))$(id).value=profile[key];
 $('auto-base').checked=profile.auto_base;$('minimize-start').checked=profile.minimize_on_start;$('base-x').value=Math.round(profile.base[0]);$('base-y').value=Math.round(profile.base[1]);
 $('action-gap').textContent=String(profile.action_gap).replace('.',',')+'seg';$('time-left').textContent=profile.duration_minutes?profile.duration_minutes+'min':'Sem limite';baseLabel();renderSlots();
}
function collect(){
 if(!profile)throw new Error('Aguarde a configuração carregar.');
 const selected=$('client-select').value.split(':');profile.client_pid=selected[0]==='0'?0:Number(selected[0]);profile.client_hwnd=selected[0]==='0'?0:Number(selected[1]);
 profile.patrol_mode=$('patrol-mode').value;
 profile.background_keys=$('background-keys').checked;
 profile.periodic_item_key=$('periodic-item-key').value.trim().toLowerCase();
 profile.extra_buff_keys=[0,1].map(i=>$('extra-buff-key-'+i).value.trim().toLowerCase());
 profile.auto_ui_scale=$('auto-ui-scale').checked;
 profile.jardim_repeat=$('jardim-repeat').checked;profile.jardim_servico_npc=$('jardim-servico-npc').checked;profile.jardim_cycles=Number($('jardim-cycles').value);profile.mina_repeat=$('mina-repeat').checked;profile.mina_cycles=Number($('mina-cycles').value);
 profile.cancel_normal=$('cancel-normal').checked;profile.combo_key_delay_ms=Number($('combo-key-delay').value);profile.combo_repeat_ms=Number($('combo-repeat').value);
 profile.heal_enabled=$('heal-enabled').checked;profile.heal_key=$('heal-key').value.trim().toLowerCase();
 profile.f3_enabled=$('f3-enabled').checked;profile.f3_minutes=Number($('f3-minutes').value);
 profile.extra_buffs_enabled=$('extra-buffs-enabled').checked;profile.extra_buff_minutes=Number($('extra-buff-minutes').value);
 profile.buffs_enabled=$('buff-enabled').checked;profile.buff_minutes=Number($('buff-minutes').value);profile.buff_gap=Number($('buff-gap').value);profile.buff_keys=Array.from({length:5},(_,i)=>$('buff-key-'+i).value.trim().toLowerCase());
 profile.hp_percent=Number($('hp-percent').value);profile.mp_percent=Number($('mp-percent').value);
 for(const [id,key] of Object.entries({gap:'action_gap',duration:'duration_minutes',radius:'radius','no-damage':'no_damage_seconds',stationary:'stationary_seconds'}))profile[key]=Number($(id).value);
 if(['termes_verit','termes_verit_leste'].includes(profile.patrol_mode))$('target').value='verit';
 if(profile.patrol_mode==='termes_penza')$('target').value='penza';
 if(['mina_lenfer','jardim_aereo'].includes(profile.patrol_mode))$('target').value='qualquer';
 profile.attack_key=$('attack').value.trim().toLowerCase();profile.unstuck_key=$('unstuck').value.trim().toLowerCase();profile.target=$('target').value;profile.auto_base=$('auto-base').checked;profile.minimize_on_start=$('minimize-start').checked;
 if(!profile.auto_base)profile.base=[Number($('base-x').value),Number($('base-y').value)];
 if(profile.patrol_mode==='buto_trio'){profile.target='buto';profile.base=[2711,1292];profile.auto_base=false;profile.radius=30;profile.data_source='native';profile.mina_repeat=false;}
 if(profile.patrol_mode==='cinzenta_croshu_sul'){profile.target='croshu';profile.base=[2955,1311];profile.auto_base=false;profile.radius=50;profile.data_source='native';profile.mina_repeat=false;}
 if(profile.patrol_mode==='cinzenta_croshu_trio'){profile.target='croshu';profile.base=[2882,1154];profile.auto_base=false;profile.radius=50;profile.data_source='native';profile.mina_repeat=false;}
 if(profile.patrol_mode==='ungor_plantas'){profile.target='planta';profile.base=[2440,1360];profile.auto_base=false;profile.radius=50;profile.data_source='native';profile.mina_repeat=false;}
 if(profile.patrol_mode==='ungor_croshu'){profile.target='croshu_ungor';profile.base=[1895,1155];profile.auto_base=false;profile.radius=50;profile.data_source='native';profile.mina_repeat=false;}
 return structuredClone(profile);
}
function openSlot(kind,index=0){
 if(running){message('Pause e pare antes de editar','As mudanças serão usadas na próxima sessão.');return;}
 collect();editing={kind,index};const full=['skills','items'].includes(kind);let s=full?profile[kind][index]:{key:kind==='return'?profile.return_key:profile[kind+'_keys'][index],seconds:3};
 $('slot-title').textContent=kind==='skills'?'Configurar habilidade '+(index+1):kind==='items'?'Configurar item '+(index+1):kind==='return'?'Item de retorno':'Suprimento '+kind.toUpperCase();
 $('slot-key').value=s.key||'';$('slot-seconds').value=s.seconds||1;$('slot-enabled').checked=full?s.enabled:!!s.key;$('slot-seconds-row').classList.toggle('hidden',!full);
 $('slot-native').textContent=s.native_id?'ID no cliente: '+s.native_id+' · escolha a tecla da sua barra.':kind==='return'?'Item opcional para encerramento pelo tempo configurado. O retorno à base usa as coordenadas.':'';
 $('slot-dialog').showModal();$('slot-key').focus();
}
$('slot-form').addEventListener('submit',e=>{e.preventDefault();const {kind,index}=editing;const key=$('slot-key').value.trim().toLowerCase();const enabled=$('slot-enabled').checked;if(enabled&&!key){$('slot-key').focus();return;}
 if(['skills','items'].includes(kind)){const seconds=Number($('slot-seconds').value);if(enabled&&seconds<=0)return;profile[kind][index]={...profile[kind][index],key,seconds,enabled};}
 else if(kind==='return')profile.return_key=enabled?key:'';else profile[kind+'_keys'][index]=enabled?key:'';
 $('slot-dialog').close();renderSlots();
});
$('slot-cancel').addEventListener('click',()=>$('slot-dialog').close());$('return-slot').addEventListener('click',()=>openSlot('return'));
for(const b of document.querySelectorAll('[data-tab]'))b.addEventListener('click',()=>{document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.tab-panel').forEach(x=>x.classList.toggle('hidden',x.id!==b.dataset.tab));});
$('patrol-mode').addEventListener('change',()=>{collect();render();});
$('auto-base').addEventListener('change',()=>{collect();baseLabel();});
$('save').addEventListener('click',()=>action(async()=>{profile=await window.hunt.save(coletarValidado());render();message('Configuração salva','Ela será carregada automaticamente na próxima abertura.');}));
$('reset').addEventListener('click',()=>action(async()=>{if(running)return;profile=await window.hunt.load();render();message('Configuração recarregada');}));
$('start').addEventListener('click',()=>action(async()=>{if(running)return;lastError=false;$('start').disabled=true;message('Preparando a caça','Volte ao Aika. A base será capturada ao começar.');try{await window.hunt.start(coletarValidado());running=true;paused=false;startedAt=Date.now();renderClients();$('running-tools').classList.remove('hidden');}catch(e){$('start').disabled=false;throw e;}}));
$('stop').addEventListener('click',()=>action(async()=>{await window.hunt.stop();message('Encerrando a caça','Liberando as teclas do jogo.');}));
$('pause').addEventListener('click',()=>action(async()=>{paused=!paused;await window.hunt.pause(paused);$('pause').textContent=paused?'Retomar':'Pausar';message(paused?'Caça pausada':'Aguardando o Aika',paused?'Use Retomar para continuar.':'Volte ao jogo para retomar.');}));
$('read-data').addEventListener('click',()=>action(readData));
$('open-diagnostics').addEventListener('click',()=>action(()=>window.hunt.logs()));
async function readData(){
 $('read-data').disabled=true;message('Lendo dados do Aika','Lendo atributos internos do cliente.');try{const d=await window.hunt.position({client_pid:profile.client_pid||0,client_hwnd:profile.client_hwnd||0});$('player-read').textContent=d.player||'—';$('position-read').textContent=d.position.join(', ');$('vitals-read').textContent=Math.round(d.hp*100)+'% / '+(d.mp===null?'—':Math.round(d.mp*100)+'%');$('target-read').textContent=d.target||'Sem alvo';$('data-source').textContent=d.source==='native'?'Memória do cliente':'Leitura visual';profile.base=d.position;profile.auto_base=$('auto-base').checked;render();message('Dados lidos',`Dados internos: ${d.position.map(v=>Math.round(v)).join(', ')}. A base será capturada novamente ao começar.`);}finally{$('read-data').disabled=false;}
}
$('import-native').addEventListener('click',()=>action(async()=>{if(running)throw new Error('Pare a caça antes de importar.');const d=await window.hunt.native(collect());if(d){profile=d;render();message('Configuração nativa importada','Defina os atalhos e ative as habilidades nos slots.');}}));
$('minimize').addEventListener('click',()=>window.hunt.minimize());$('close').addEventListener('click',()=>window.hunt.close());
$('show-log').addEventListener('click',()=>$('activity').classList.remove('hidden'));$('hide-log').addEventListener('click',()=>$('activity').classList.add('hidden'));
window.hunt.onEvent(e=>{
 window.fluxoEditor?.event(e);
 if(e.event==='log'){log(e.message);if(e.personagem){$('player-read').textContent=e.personagem;$('client-state').textContent=`Controlando ${e.personagem} · PID ${e.pid}`;}if(!lastError)message(e.message,e.posicao?'Posição: '+e.posicao.join(', '):'F12 para encerrar.',running?'running':'idle');}
 if(e.event==='jardim_limit'){log(e.message);message('Saindo antes dos Shiraz Infernais',e.message,'running');}
 if(e.event==='dungeon_complete'){log(e.message);message(profile.patrol_mode==='jardim_aereo'?'Jardim finalizado':'Mina finalizada',e.message,'idle');}
 if(e.event==='cycle'){const etapas={jardim_npc_retornar:'Indo ao Luis Mandez',jardim_npc_servico:'Serviço no NPC',jardim_npc_reparar:'Reparando equipamentos',jardim_npc_vender:'Vendendo equipamentos',jardim_npc_concluido:'Reparo e venda concluídos',jardim_percurso:'Percorrendo o Jardim',jardim_retornar:'Voltando ao Altar da Ascensão',jardim_entrar:'Entrando no Jardim · Difícil',jardim_corrigir_entrada:'Reconfirmando o modo Difícil',jardim_liberar_entrada:'Liberando a entrada do Jardim',dificil_confirmado:'Entrada Difícil confirmada',jardim_sair:'Saindo do Jardim',jardim_saida_confirmada:'Saída do Jardim confirmada',dg:'Indo até Malik',sair:'Saindo do grupo',retornar:'Voltando à entrada',entrar:'Entrando no Elite',liberar_entrada:'Liberando acesso ao portal',corrigir_entrada:'Reconfirmando dificuldade',dg_concluida:'Malik abatido',save_confirmado:'Retorno ao save confirmado',elite_confirmado:'Entrada Elite confirmada'};if(e.message)log(e.message);message(etapas[e.state]||(profile.patrol_mode==='jardim_aereo'?'Ciclo do Jardim':'Ciclo da Mina'),e.message||(profile.patrol_mode==='jardim_aereo'?`${e.segments_completed||0} trechos concluídos`:`${e.cycles_completed||0} DGs concluídas`),'running');}
 if(e.event==='base'){profile.base=e.base;baseLabel();log('Base capturada: '+e.base.map(v=>Math.round(v)).join(', '));}
 if(e.event==='telemetry'){if(e.mobs_regiao!==undefined)$('mobs-read').textContent=e.mobs_regiao===null?'Aguardando leitura':String(e.mobs_regiao);if(e.next_buff_seconds!==undefined)$('buff-next').textContent=e.next_buff_seconds===null?'Desativado':e.next_buff_seconds>0?Math.ceil(e.next_buff_seconds/60)+' min':'Após terminar o alvo';$('target-read').textContent=e.target||'Sem alvo';$('data-source').textContent=e.source==='native'?'Memória do cliente':'Leitura visual';profile.base=e.base;baseLabel();$('position-read').textContent=e.position.map(v=>Math.round(v)).join(', ');$('vitals-read').textContent=Math.round(e.hp*100)+'% / '+(e.mp===null?'—':Math.round(e.mp*100)+'%');if(!lastError)message(e.controle?.stunned?'Atordoado · aguardando':e.controle?.paralyzed?'Paralisado · aguardando':e.controle?.frozen?'Congelado · aguardando':e.controle?.casting?'Executando habilidade':names[e.state]||'Caçando',e.patrol_point!==null&&e.patrol_point!==undefined?`Posição ${e.position.map(v=>Math.round(v)).join(', ')} · setor ${e.patrol_point}${e.dungeon?'':(' · voltas '+e.patrol_laps)}`:`Posição ${e.position.map(v=>Math.round(v)).join(', ')} · base ${e.base.map(v=>Math.round(v)).join(', ')}`,'running');if(e.input_guard?.state){const state=e.input_guard.state;message(names[state],state==='aguardando_controle'?'Caça suspensa. Assuma o personagem; retoma após confirmar resposta no jogo.':state==='recuperando_controle'?'Revalidando foco e cura. Movimento e ataques suspensos.':state==='confirmando_cura'?'Aguardando o cliente reconhecer e concluir a cura.':'Aguardando resposta da habilidade antes da próxima ação.',state==='aguardando_controle'?'error':'running');}if(profile.duration_minutes)$('time-left').textContent=Math.max(0,Math.ceil(profile.duration_minutes-e.elapsed/60))+'min';}
 if(e.event==='status'&&!lastError)message(names[e.state]||e.state,e.message,e.state==='paused'?'idle':'running');
 if(e.event==='error'){lastError=true;log(e.message);message('Não foi possível iniciar',e.message,'error');}
 if(e.event==='finished'||e.event==='exit'){running=false;startedAt=null;renderClients();$('start').disabled=false;$('running-tools').classList.add('hidden');if(!lastError)message('Caça encerrada','Você pode alterar a configuração e começar novamente.');}
});
$('refresh-clients').addEventListener('click',()=>action(refreshClients));
$('client-select').addEventListener('change',()=>action(async()=>{if(running)throw new Error('Pare a caça antes de trocar o cliente.');profile=await window.hunt.save(collect());renderClients();}));
action(async()=>{profile=await window.hunt.load();profile.data_source='native';render();await refreshClients();if(new URLSearchParams(location.search).get('editor')==='flow')await window.fluxoEditor.abrir();});

$('check-updates').addEventListener('click',()=>action(()=>window.hunt.checkUpdates()));
action(async()=>{const info=await window.hunt.info();$('app-version').textContent='HuntingAitan v'+info.version;});
window.fluxoHost={
 profile:()=>collect(),running:()=>running,error:fail,resize:aberto=>window.hunt.flowEditor(aberto),
 save:async regras=>{if(running)throw new Error('Pare a caça antes de salvar as regras.');const p={...collect(),reacoes:regras};profile=await window.hunt.save(p);render();message('Fluxo salvo','As regras visuais serão usadas na próxima caça.');return profile.reacoes;}
};
$('open-flow').addEventListener('click',()=>window.fluxoEditor.abrir());
window.hunt.onEvent(e=>{if(e.event==='update'){$('update-status').textContent=e.message;log(e.message);}});
