const $=id=>document.getElementById(id);
let profile=null,running=false,paused=false,editing=null,lastError=false;
const lines=[];let startedAt=null;
const names={percorrer:'Percorrendo rota',aviso:'Fechando aviso',rebufar:'Renovando buffs',initializing:'Inicializando dados internos',inicio:'Confirmando posição',buscar:'Procurando alvo',combater:'Em combate',retornar:'Voltando à base',waiting:'Aguardando o Aika',paused:'Pausado',stopped:'Parado'};
function message(title,detail='',type='idle'){$('state-label').textContent=title;$('state-detail').textContent=detail;$('state-dot').className='dot '+type;}
function fail(e){lastError=true;message('Confira a configuração',String(e.message||e).replace(/^Error invoking remote method '[^']+': Error: /,''),'error');}
async function action(fn){try{await fn();}catch(e){fail(e);}}
function log(text){lines.push(new Date().toLocaleTimeString('pt-BR')+' · '+text);if(lines.length>120)lines.shift();$('log-lines').textContent=lines.join('\n');$('log-lines').scrollTop=$('log-lines').scrollHeight;}
function baseLabel(){if(profile.patrol_mode!=='base'){$('base-value').textContent=profile.patrol_mode==='mina_lenfer'?'Mina L’Enfer → Malik':profile.patrol_mode==='jardim_aereo'?'Jardim Aéreo · Lazapas finais':profile.patrol_mode==='termes_verit'?'Circuito Verit · Termes':'Circuito de ida e volta';$('manual-base').classList.add('hidden');return;}const p=profile.base;$('base-value').textContent=profile.auto_base?(startedAt?`${Math.round(p[0])}, ${Math.round(p[1])}`:'Capturada ao começar'):`${Math.round(p[0])}, ${Math.round(p[1])}`;$('manual-base').classList.toggle('hidden',profile.auto_base);}
function slotButton(kind,index,icon,key,enabled=true){const b=document.createElement('button');b.className='slot'+(enabled?'':' inactive');b.type='button';b.title=(kind==='skills'?'Habilidade '+(index+1):kind==='items'?'Item '+(index+1):kind.toUpperCase()+' '+(index+1))+' · clique para configurar';if(icon){const img=document.createElement('img');img.src='assets/'+icon;img.alt='';b.append(img);}const k=document.createElement('span');k.className='key';k.textContent=key?key.toUpperCase():'';b.append(k);b.addEventListener('click',()=>openSlot(kind,index));return b;}
function renderSlots(){
 for(const kind of ['hp','mp']){const box=$(kind+'-slots');box.replaceChildren();profile[kind+'_keys'].forEach((key,i)=>box.append(slotButton(kind,i,i===0?kind+'.png':null,key,!!key)));}
 for(const kind of ['skills','items']){const box=$(kind);box.replaceChildren();profile[kind].forEach((s,i)=>{const wrap=document.createElement('div');wrap.className='skill-wrap';wrap.append(slotButton(kind,i,kind==='skills'&&s.icon!==null?'skill'+s.icon+'.png':null,s.key,s.enabled));const cd=document.createElement('span');cd.className='cooldown';const number=document.createElement('b');number.textContent=s.seconds?String(s.seconds):'';cd.append(number,document.createTextNode(s.seconds?' segundos':'segundos'));wrap.append(cd);box.append(wrap);});}
 $('return-slot').querySelector('.key').textContent=profile.return_key.toUpperCase();
}
function render(){
 $('auto-ui-scale').checked=profile.auto_ui_scale;
 $('jardim-hint').classList.toggle('hidden',profile.patrol_mode!=='jardim_aereo');$('mina-repeat').checked=!!profile.mina_repeat;$('mina-cycles').value=profile.mina_cycles||0;
 $('target').disabled=profile.patrol_mode!=='base';$('patrol-mode').value=profile.patrol_mode||'base';$('patrol-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_penza');$('verit-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_verit');$('mina-hint').classList.toggle('hidden',profile.patrol_mode!=='mina_lenfer');
 $('cancel-normal').checked=!!profile.cancel_normal;$('combo-key-delay').value=profile.combo_key_delay_ms;$('combo-repeat').value=profile.combo_repeat_ms;
 $('heal-enabled').checked=profile.heal_enabled;$('heal-key').value=profile.heal_key;
 $('f3-enabled').checked=profile.f3_enabled;$('f3-minutes').value=profile.f3_minutes;
 $('extra-buffs-enabled').checked=profile.extra_buffs_enabled;$('extra-buff-minutes').value=profile.extra_buff_minutes;
 $('buff-enabled').checked=profile.buffs_enabled;$('buff-minutes').value=profile.buff_minutes;$('buff-gap').value=profile.buff_gap;profile.buff_keys.forEach((k,i)=>$('buff-key-'+i).value=k);$('buff-next').textContent=profile.buffs_enabled?'Ao iniciar e a cada '+profile.buff_minutes+' minutos':'Desativado';
 $('hp-percent').value=profile.hp_percent;$('mp-percent').value=profile.mp_percent;
 for(const [id,key] of Object.entries({gap:'action_gap',attack:'attack_key',duration:'duration_minutes',radius:'radius',target:'target','no-damage':'no_damage_seconds',stationary:'stationary_seconds',unstuck:'unstuck_key'}))$(id).value=profile[key];
 $('auto-base').checked=profile.auto_base;$('minimize-start').checked=profile.minimize_on_start;$('base-x').value=profile.base[0];$('base-y').value=profile.base[1];
 $('action-gap').textContent=String(profile.action_gap).replace('.',',')+'seg';$('time-left').textContent=profile.duration_minutes?profile.duration_minutes+'min':'Sem limite';baseLabel();renderSlots();
}
function collect(){
 if(!profile)throw new Error('Aguarde a configuração carregar.');
 profile.patrol_mode=$('patrol-mode').value;
 profile.auto_ui_scale=$('auto-ui-scale').checked;
 profile.mina_repeat=$('mina-repeat').checked;profile.mina_cycles=Number($('mina-cycles').value);
 profile.cancel_normal=$('cancel-normal').checked;profile.combo_key_delay_ms=Number($('combo-key-delay').value);profile.combo_repeat_ms=Number($('combo-repeat').value);
 profile.heal_enabled=$('heal-enabled').checked;profile.heal_key=$('heal-key').value.trim().toLowerCase();
 profile.f3_enabled=$('f3-enabled').checked;profile.f3_minutes=Number($('f3-minutes').value);
 profile.extra_buffs_enabled=$('extra-buffs-enabled').checked;profile.extra_buff_minutes=Number($('extra-buff-minutes').value);
 profile.buffs_enabled=$('buff-enabled').checked;profile.buff_minutes=Number($('buff-minutes').value);profile.buff_gap=Number($('buff-gap').value);profile.buff_keys=Array.from({length:5},(_,i)=>$('buff-key-'+i).value.trim().toLowerCase());
 profile.hp_percent=Number($('hp-percent').value);profile.mp_percent=Number($('mp-percent').value);
 for(const [id,key] of Object.entries({gap:'action_gap',duration:'duration_minutes',radius:'radius','no-damage':'no_damage_seconds',stationary:'stationary_seconds'}))profile[key]=Number($(id).value);
 if(profile.patrol_mode==='termes_verit')$('target').value='verit';
 if(profile.patrol_mode==='termes_penza')$('target').value='penza';
 if(['mina_lenfer','jardim_aereo'].includes(profile.patrol_mode))$('target').value='qualquer';
 profile.attack_key=$('attack').value.trim().toLowerCase();profile.unstuck_key=$('unstuck').value.trim().toLowerCase();profile.target=$('target').value;profile.auto_base=$('auto-base').checked;profile.minimize_on_start=$('minimize-start').checked;
 if(!profile.auto_base)profile.base=[Number($('base-x').value),Number($('base-y').value)];
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
$('patrol-mode').addEventListener('change',()=>{collect();baseLabel();$('target').disabled=profile.patrol_mode!=='base';$('patrol-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_penza');$('verit-hint').classList.toggle('hidden',profile.patrol_mode!=='termes_verit');$('mina-hint').classList.toggle('hidden',profile.patrol_mode!=='mina_lenfer');});
$('auto-base').addEventListener('change',()=>{collect();baseLabel();});
$('save').addEventListener('click',()=>action(async()=>{profile=await window.hunt.save(collect());render();message('Configuração salva','Ela será carregada automaticamente na próxima abertura.');}));
$('reset').addEventListener('click',()=>action(async()=>{if(running)return;profile=await window.hunt.load();render();message('Configuração recarregada');}));
$('start').addEventListener('click',()=>action(async()=>{if(running)return;lastError=false;$('start').disabled=true;message('Preparando a caça','Volte ao Aika. A base será capturada ao começar.');try{await window.hunt.start(collect());running=true;paused=false;startedAt=Date.now();$('running-tools').classList.remove('hidden');}catch(e){$('start').disabled=false;throw e;}}));
$('stop').addEventListener('click',()=>action(async()=>{await window.hunt.stop();message('Encerrando a caça','Liberando as teclas do jogo.');}));
$('pause').addEventListener('click',()=>action(async()=>{paused=!paused;await window.hunt.pause(paused);$('pause').textContent=paused?'Retomar':'Pausar';message(paused?'Caça pausada':'Aguardando o Aika',paused?'Use Retomar para continuar.':'Volte ao jogo para retomar.');}));
$('read-data').addEventListener('click',()=>action(readData));
$('open-diagnostics').addEventListener('click',()=>action(()=>window.hunt.logs()));
async function readData(){
 $('read-data').disabled=true;message('Lendo dados do Aika','Lendo atributos internos do cliente.');try{const d=await window.hunt.position();$('position-read').textContent=d.position.join(', ');$('vitals-read').textContent=Math.round(d.hp*100)+'% / '+(d.mp===null?'—':Math.round(d.mp*100)+'%');$('target-read').textContent=d.target||'Sem alvo';$('data-source').textContent=d.source==='native'?'Memória do cliente':'Leitura visual';profile.base=d.position;profile.auto_base=$('auto-base').checked;render();message('Dados lidos',`Dados internos: ${d.position.map(v=>Math.round(v)).join(', ')}. A base será capturada novamente ao começar.`);}finally{$('read-data').disabled=false;}
}
$('import-native').addEventListener('click',()=>action(async()=>{if(running)throw new Error('Pare a caça antes de importar.');const d=await window.hunt.native(collect());if(d){profile=d;render();message('Configuração nativa importada','Defina os atalhos e ative as habilidades nos slots.');}}));
$('minimize').addEventListener('click',()=>window.hunt.minimize());$('close').addEventListener('click',()=>window.hunt.close());
$('show-log').addEventListener('click',()=>$('activity').classList.remove('hidden'));$('hide-log').addEventListener('click',()=>$('activity').classList.add('hidden'));
window.hunt.onEvent(e=>{
 if(e.event==='log'){log(e.message);if(!lastError)message(e.message,e.posicao?'Posição: '+e.posicao.join(', '):'F12 para encerrar.',running?'running':'idle');}
 if(e.event==='jardim_limit'){log(e.message);message('Saindo antes dos Lazapas finais',e.message,'running');}
 if(e.event==='dungeon_complete'){log(e.message);message(profile.patrol_mode==='jardim_aereo'?'Jardim finalizado':'Mina finalizada',e.message,'idle');}
 if(e.event==='cycle'){const etapas={jardim_sair:'Saindo do Jardim',jardim_saida_confirmada:'Saída do Jardim confirmada',dg:'Indo até Malik',sair:'Saindo do grupo',retornar:'Voltando à entrada',entrar:'Entrando no Elite',liberar_entrada:'Liberando acesso ao portal',corrigir_entrada:'Reconfirmando dificuldade',dg_concluida:'Malik abatido',save_confirmado:'Retorno ao save confirmado',elite_confirmado:'Entrada Elite confirmada'};if(e.message)log(e.message);message(etapas[e.state]||'Ciclo da Mina',e.message||`${e.cycles_completed||0} DGs concluídas`,'running');}
 if(e.event==='base'){profile.base=e.base;baseLabel();log('Base capturada: '+e.base.map(v=>Math.round(v)).join(', '));}
 if(e.event==='telemetry'){if(e.mobs_regiao!==undefined)$('mobs-read').textContent=e.mobs_regiao===null?'Aguardando leitura':String(e.mobs_regiao);if(e.next_buff_seconds!==undefined)$('buff-next').textContent=e.next_buff_seconds===null?'Desativado':e.next_buff_seconds>0?Math.ceil(e.next_buff_seconds/60)+' min':'Após terminar o alvo';$('target-read').textContent=e.target||'Sem alvo';$('data-source').textContent=e.source==='native'?'Memória do cliente':'Leitura visual';profile.base=e.base;baseLabel();$('position-read').textContent=e.position.map(v=>Math.round(v)).join(', ');$('vitals-read').textContent=Math.round(e.hp*100)+'% / '+(e.mp===null?'—':Math.round(e.mp*100)+'%');if(!lastError)message(e.controle?.stunned?'Atordoado · aguardando':e.controle?.paralyzed?'Paralisado · aguardando':e.controle?.frozen?'Congelado · aguardando':e.controle?.casting?'Executando habilidade':names[e.state]||'Caçando',e.patrol_point!==null&&e.patrol_point!==undefined?`Posição ${e.position.map(v=>Math.round(v)).join(', ')} · setor ${e.patrol_point}${e.dungeon?'':(' · voltas '+e.patrol_laps)}`:`Posição ${e.position.map(v=>Math.round(v)).join(', ')} · base ${e.base.map(v=>Math.round(v)).join(', ')}`,'running');if(profile.duration_minutes)$('time-left').textContent=Math.max(0,Math.ceil(profile.duration_minutes-e.elapsed/60))+'min';}
 if(e.event==='status'&&!lastError)message(names[e.state]||e.state,e.message,e.state==='paused'?'idle':'running');
 if(e.event==='error'){lastError=true;log(e.message);message('Não foi possível iniciar',e.message,'error');}
 if(e.event==='finished'||e.event==='exit'){running=false;startedAt=null;$('start').disabled=false;$('running-tools').classList.add('hidden');if(!lastError)message('Caça encerrada','Você pode alterar a configuração e começar novamente.');}
});
action(async()=>{profile=await window.hunt.load();profile.data_source='native';render();});

$('check-updates').addEventListener('click',()=>action(()=>window.hunt.checkUpdates()));
action(async()=>{const info=await window.hunt.info();$('app-version').textContent='HuntingAitan v'+info.version;});
window.hunt.onEvent(e=>{if(e.event==='update'){$('update-status').textContent=e.message;log(e.message);}});
