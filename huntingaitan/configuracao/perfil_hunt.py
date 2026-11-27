import copy,json,re
from pathlib import Path
from huntingaitan.combate.reacoes import validar_reacoes

DEFAULT={
 'client_pid':0,'client_hwnd':0,'background_keys':False,
 'version':3,'data_source':'native','auto_base':True,'base':[2767,846],'radius':20,'no_damage_seconds':5,'patrol_mode':'base',
 'mina_repeat':False,'mina_cycles':0,'jardim_repeat':True,'jardim_servico_npc':True,'jardim_cycles':0,'jardim_goal':'seridunn','auto_ui_scale':True,
 'cancel_normal':False,'combo_key_delay_ms':0,'combo_repeat_ms':0,'stationary_seconds':3,'unstuck_key':"'",'moving_target_key':'','attack_key':'1','action_gap':.7,
 'hp_percent':40,'mp_percent':40,'hp_keys':['8','',''],'mp_keys':['','',''],
 'heal_enabled':True,'heal_key':'7',
 'return_key':'','duration_minutes':240,'target':'qualquer','minimize_on_start':True,
 'periodic_item_key':'f3','extra_buff_keys':['ctrl+6','ctrl+8'],'f3_enabled':True,'f3_minutes':30,'extra_buffs_enabled':True,'extra_buff_minutes':11,'buffs_enabled':True,'buff_minutes':9,'buff_gap':2,'target_recovery_interval':.5,'buff_keys':['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5'],
 'skills':[{'key':str(i+2) if i<6 else '', 'seconds':[6,8,10,12,15,20,17,52,0,0][i],
             'enabled':i<6,'icon':i if i<8 else None,'native_id':None} for i in range(10)],
 'items':[{'key':'','seconds':0,'enabled':False} for _ in range(5)],
 'reacoes':[]}

def tecla(v,vazia=True):
 v=str(v or '').strip().lower()
 if not v and vazia:return ''
 if re.fullmatch(r"[a-z0-9']|f(?:[1-9]|10|11)",v):return v
 raise ValueError('Tecla invalida: '+v+'. Use letras, numeros, apostrofo ou F1 a F11.')

def validar(dados):
 p=copy.deepcopy(DEFAULT)
 if not isinstance(dados,dict):raise ValueError('Configuracao invalida')
 p.update({k:v for k,v in dados.items() if k in p})
 if p['jardim_goal'] not in ('seridunn','antes_shiraz'):raise ValueError('Objetivo do Jardim invalido')
 for k,limite in [('client_pid',0xffffffff),('client_hwnd',2**53-1)]:
  if isinstance(p[k],bool) or not isinstance(p[k],int) or not 0<=p[k]<=limite:raise ValueError('Cliente selecionado invalido: '+k)
 if bool(p['client_pid'])!=bool(p['client_hwnd']):raise ValueError('Selecione novamente o cliente na lista do painel')
 legado=int(dados.get('version',1))<2
 # Migra a pausa padrao antiga sem alterar intervalos personalizados.
 if int(dados.get('version',1))<3 and float(p['action_gap'])==1.4:p['action_gap']=.7
 p['version']=3
 for k,limite in [('combo_key_delay_ms',100),('combo_repeat_ms',2000)]:
  if isinstance(p[k],bool):raise ValueError(k+': valor invalido')
  p[k]=float(p[k])
  if not 0<=p[k]<=limite:raise ValueError(k+': valor fora do intervalo')
 for k,a,b in [('radius',10,50),('no_damage_seconds',1,60),('stationary_seconds',1,20),('hp_percent',1,99),('mp_percent',1,99),('duration_minutes',0,1440),('action_gap',.4,10),('f3_minutes',1,120),('extra_buff_minutes',1,120),('buff_minutes',1,120),('buff_gap',.5,10),('target_recovery_interval',.15,2)]:
  p[k]=float(p[k])
  if not a<=p[k]<=b:raise ValueError(k+': valor fora do intervalo')
 if p['data_source'] not in ['native','visual']:raise ValueError('Fonte de dados invalida')
 p['base']=[int(x) for x in p['base']]
 if len(p['base'])!=2 or any(not 0<=x<=9999 for x in p['base']):raise ValueError('Base invalida')
 if isinstance(p['mina_cycles'],bool) or not isinstance(p['mina_cycles'],(int,float)) or not 0<=p['mina_cycles']<=9999 or int(p['mina_cycles'])!=p['mina_cycles']:raise ValueError('Quantidade de ciclos da Mina invalida')
 p['mina_cycles']=int(p['mina_cycles'])
 if isinstance(p['jardim_cycles'],bool) or not isinstance(p['jardim_cycles'],(int,float)) or not 0<=p['jardim_cycles']<=9999 or int(p['jardim_cycles'])!=p['jardim_cycles']:raise ValueError('Quantidade de trechos do Jardim invalida')
 p['jardim_cycles']=int(p['jardim_cycles'])
 for k in ['auto_base','minimize_on_start','extra_buffs_enabled','f3_enabled','buffs_enabled','cancel_normal','heal_enabled','mina_repeat','jardim_repeat','jardim_servico_npc','auto_ui_scale','background_keys']:
  if not isinstance(p[k],bool):raise ValueError('Opcao invalida: '+k)
 for k in ['hp_keys','mp_keys']:
  if len(p[k])!=3:raise ValueError('Sao necessarios tres slots')
  p[k]=[tecla(v) for v in p[k]]
 p['attack_key']=tecla(p['attack_key'],False);p['unstuck_key']=tecla(p['unstuck_key']);p['moving_target_key']=tecla(p['moving_target_key']);p['return_key']=tecla(p['return_key'])
 p['heal_key']=tecla(p['heal_key'],False)
 if p['heal_enabled'] and p['heal_key']==p['attack_key']:raise ValueError('Cura e ataque normal precisam de teclas diferentes')
 if len(p['buff_keys'])!=5:raise ValueError('Configure cinco atalhos de buff')
 p['buff_keys']=[str(v).strip().lower() for v in p['buff_keys']]
 if any(v and not re.fullmatch(r'ctrl\+[1-8]|f(?:[1-9]|10|11)',v) for v in p['buff_keys']):raise ValueError('Buffs precisam de Ctrl+1 a Ctrl+8 ou F1 a F11')
 if not isinstance(p['extra_buff_keys'],list) or len(p['extra_buff_keys'])!=2:raise ValueError('Configure dois atalhos de buff adicional')
 p['extra_buff_keys']=[str(k).strip().lower() for k in p['extra_buff_keys']]
 if any(not re.fullmatch(r'ctrl\+[1-8]|f(?:[1-9]|10|11)',v) for v in p['extra_buff_keys']):raise ValueError('Buff adicional: use Ctrl+1 a Ctrl+8 ou F1 a F11')
 if len(set(p['extra_buff_keys']))!=2:raise ValueError('Buffs adicionais precisam de teclas diferentes')
 p['periodic_item_key']=tecla(p['periodic_item_key'],False)
 preenchidos=[v for v in p['buff_keys'] if v]
 if len(set(preenchidos))!=len(preenchidos):raise ValueError('Os buffs preenchidos precisam de atalhos diferentes')
 if p['extra_buffs_enabled'] and set(p['buff_keys']) & set(p['extra_buff_keys']):raise ValueError('Os atalhos adicionais estao reservados; remova-os dos cinco buffs')
 if p['target'] not in ['qualquer','verit','penza','croshu','croshu_ungor','tet','buto','planta']:raise ValueError('Filtro de alvo invalido')
 if p['patrol_mode'] not in ['base','buto_trio','cinzenta_croshu_trio','cinzenta_croshu_sul','ungor_plantas','ungor_croshu','termes_penza','termes_verit','termes_verit_leste','mina_lenfer','jardim_aereo']:raise ValueError('Circuito invalido')
 # O grupo observado corresponde aos slots 1, 6 e 7; o raio exclui os demais spawns cadastrados.
 if p['patrol_mode']=='buto_trio':p.update(target='buto',data_source='native',base=[2711,1292],auto_base=False,radius=30,mina_repeat=False)
 if p['patrol_mode']=='cinzenta_croshu_trio':p.update(target='croshu',data_source='native',base=[2882,1154],auto_base=False,radius=50,mina_repeat=False)
 if p['patrol_mode']=='cinzenta_croshu_sul':p.update(target='croshu',data_source='native',base=[2955,1311],auto_base=False,radius=50,mina_repeat=False)
 if p['patrol_mode']=='ungor_plantas':p.update(target='planta',data_source='native',base=[2440,1360],auto_base=False,radius=50,mina_repeat=False)
 if p['patrol_mode']=='ungor_croshu':p.update(target='croshu_ungor',data_source='native',base=[1895,1155],auto_base=False,radius=50,mina_repeat=False)
 if p['patrol_mode'] in ('termes_verit','termes_verit_leste'):p.update(target='verit',data_source='native')
 if p['patrol_mode']=='termes_penza':p.update(target='penza',data_source='native')
 if p['patrol_mode']=='mina_lenfer':p.update(target='qualquer',data_source='native')
 if p['patrol_mode']=='jardim_aereo':p.update(target='qualquer',data_source='native',mina_repeat=False)
 usadas=set([p['attack_key']]+[v for k in ['hp_keys','mp_keys'] for v in p[k] if v])
 for campo,n in [('skills',10),('items',5)]:
  if len(p[campo])!=n:raise ValueError('Quantidade de slots invalida')
  normal=[]
  for i,s in enumerate(p[campo]):
   key=tecla(s.get('key'));seconds=float(s.get('seconds',0));enabled=bool(s.get('enabled',False))
   # v1 deixou atalhos preenchidos silenciosamente inativos. Migra uma vez;
   # v2 preserva uma desativacao explicita feita pelo usuario.
   if legado and campo=='skills':enabled=bool(key and seconds>0 and key not in usadas)
   if not 0<=seconds<=86400:raise ValueError('Intervalo invalido')
   if enabled and (not key or seconds<=0):raise ValueError('Slot ativo precisa de tecla e intervalo')
   if enabled and p['f3_enabled'] and key==p['periodic_item_key']:raise ValueError('Atalho reservado ao item periodico')
   if enabled and key in usadas:raise ValueError('Atalho repetido: '+key)
   if enabled:usadas.add(key)
   normal.append(dict(key=key,seconds=seconds,enabled=enabled,icon=s.get('icon',i if campo=='skills' and i<8 else None),native_id=s.get('native_id')))
  p[campo]=normal
 # Reacoes de sobrevivencia (cura, defesa, emergencia, itens): teclas nao podem repetir as da rotacao.
 # Os buffs por tempo e o F3 automatico tambem usam teclas: uma reacao nao pode repeti-las.
 reservadas=set(usadas)
 if p['buffs_enabled']:reservadas|=set(p['buff_keys'])
 if p['extra_buffs_enabled']:reservadas|=set(p['extra_buff_keys'])
 if p['f3_enabled']:reservadas.add(p['periodic_item_key'])
 p['reacoes']=validar_reacoes(p['reacoes'],reservadas=reservadas)
 if p['background_keys']:
  if not p['client_hwnd']:raise ValueError('Segundo plano: selecione o personagem na lista')
  if p['patrol_mode']=='mina_lenfer':raise ValueError('Segundo plano ainda nao validado na Mina; use o modo normal nessa DG')
  ativas=list(reservadas)+([p['heal_key']] if p['heal_enabled'] else [])+[r['tecla'] for r in p['reacoes'] if r['ativa']]
  if any('+' in k for k in ativas if k):raise ValueError('Segundo plano: substitua atalhos com Ctrl/Alt/Shift por teclas simples')
 return p

def importar_nativo(caminho,atual=None):
 from huntingaitan.configuracao.config_nativa import decodificar_config
 raw=decodificar_config(Path(caminho).read_bytes());p=copy.deepcopy(atual or DEFAULT)
 p.update(auto_base=True,radius=max(10,min(50,raw['alcance'])),hp_percent=max(1,min(99,raw['hp_percentual'])),mp_percent=max(1,min(99,raw['mp_percentual'])))
 for i,(id_,cd) in enumerate(zip(raw['skills'],raw['intervalos_skills'])):
  p['skills'][i].update(native_id=id_ if id_>0 else None,seconds=max(0,cd),enabled=False,key='')
 for i,(id_,cd) in enumerate(zip(raw['itens_adicionais'],raw['intervalos_itens'])):
  p['items'][i].update(native_id=id_ if id_>0 else None,seconds=max(0,cd),enabled=False,key='')
 return validar(p)
