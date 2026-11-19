import copy,json,re
from pathlib import Path

DEFAULT={
 'version':3,'data_source':'native','auto_base':True,'base':[2767,846],'radius':20,'no_damage_seconds':5,
 'cancel_normal':False,'stationary_seconds':3,'unstuck_key':"'",'attack_key':'1','action_gap':.7,
 'hp_percent':40,'mp_percent':40,'hp_keys':['8','',''],'mp_keys':['','',''],
 'heal_enabled':True,'heal_key':'7',
 'return_key':'','duration_minutes':240,'target':'qualquer','minimize_on_start':True,
 'buffs_enabled':True,'buff_minutes':9,'buff_gap':2,'buff_keys':['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5'],
 'skills':[{'key':str(i+2) if i<6 else '', 'seconds':[6,8,10,12,15,20,17,52,0,0][i],
             'enabled':i<6,'icon':i if i<8 else None,'native_id':None} for i in range(10)],
 'items':[{'key':'','seconds':0,'enabled':False} for _ in range(5)]}

def tecla(v,vazia=True):
 v=str(v or '').strip().lower()
 if not v and vazia:return ''
 if re.fullmatch(r"[a-z0-9']|f(?:[1-7]|9|10|11)",v):return v
 raise ValueError('Tecla invalida: '+v+'. Use letras, numeros, apostrofo ou F1 a F11, exceto F8.')

def validar(dados):
 p=copy.deepcopy(DEFAULT)
 if not isinstance(dados,dict):raise ValueError('Configuracao invalida')
 p.update({k:v for k,v in dados.items() if k in p})
 legado=int(dados.get('version',1))<2
 # Migra a pausa padrao antiga sem alterar intervalos personalizados.
 if int(dados.get('version',1))<3 and float(p['action_gap'])==1.4:p['action_gap']=.7
 p['version']=3
 for k,a,b in [('radius',10,50),('no_damage_seconds',1,60),('stationary_seconds',1,20),('hp_percent',1,99),('mp_percent',1,99),('duration_minutes',0,1440),('action_gap',.4,10),('buff_minutes',1,120),('buff_gap',.5,10)]:
  p[k]=float(p[k])
  if not a<=p[k]<=b:raise ValueError(k+': valor fora do intervalo')
 if p['data_source'] not in ['native','visual']:raise ValueError('Fonte de dados invalida')
 p['base']=[int(x) for x in p['base']]
 if len(p['base'])!=2 or any(not 0<=x<=9999 for x in p['base']):raise ValueError('Base invalida')
 for k in ['auto_base','minimize_on_start','buffs_enabled','cancel_normal','heal_enabled']:
  if not isinstance(p[k],bool):raise ValueError('Opcao invalida: '+k)
 for k in ['hp_keys','mp_keys']:
  if len(p[k])!=3:raise ValueError('Sao necessarios tres slots')
  p[k]=[tecla(v) for v in p[k]]
 p['attack_key']=tecla(p['attack_key'],False);p['unstuck_key']=tecla(p['unstuck_key']);p['return_key']=tecla(p['return_key'])
 p['heal_key']=tecla(p['heal_key'],False)
 if p['heal_enabled'] and p['heal_key']==p['attack_key']:raise ValueError('Cura e ataque normal precisam de teclas diferentes')
 if len(p['buff_keys'])!=5:raise ValueError('Configure cinco atalhos de buff')
 p['buff_keys']=[str(v).strip().lower() for v in p['buff_keys']]
 if any(not re.fullmatch(r'ctrl\+[1-8]',v) for v in p['buff_keys']):raise ValueError('Buffs precisam de atalhos Ctrl+1 a Ctrl+8')
 if len(set(p['buff_keys']))!=5:raise ValueError('Os cinco buffs precisam de atalhos diferentes')
 if p['target'] not in ['qualquer','verit','penza','croshu','tet']:raise ValueError('Filtro de alvo invalido')
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
   if enabled and key in usadas:raise ValueError('Atalho repetido: '+key)
   if enabled:usadas.add(key)
   normal.append(dict(key=key,seconds=seconds,enabled=enabled,icon=s.get('icon',i if campo=='skills' and i<8 else None),native_id=s.get('native_id')))
  p[campo]=normal
 return p

def importar_nativo(caminho,atual=None):
 from config_nativa import decodificar_config
 raw=decodificar_config(Path(caminho).read_bytes());p=copy.deepcopy(atual or DEFAULT)
 p.update(auto_base=True,radius=max(10,min(50,raw['alcance'])),hp_percent=max(1,min(99,raw['hp_percentual'])),mp_percent=max(1,min(99,raw['mp_percentual'])))
 for i,(id_,cd) in enumerate(zip(raw['skills'],raw['intervalos_skills'])):
  p['skills'][i].update(native_id=id_ if id_>0 else None,seconds=max(0,cd),enabled=False,key='')
 for i,(id_,cd) in enumerate(zip(raw['itens_adicionais'],raw['intervalos_itens'])):
  p['items'][i].update(native_id=id_ if id_>0 else None,seconds=max(0,cd),enabled=False,key='')
 return validar(p)
