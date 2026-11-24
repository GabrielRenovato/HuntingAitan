import sys,json,time,ctypes,math
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.entrada.entrada_janela import EntradaJanela
u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND;r=dict(testes=[])
for j in enumerar_clientes():
 d=None;e=None;t=dict(pid=j['pid'],quadros=[]);r['testes'].append(t)
 try:
  d=DadosInternos(janela=j);e=EntradaJanela(d.hwnd,d.pid);s=d.snapshot();t['nome']=s['player']['name'];a=s['target']
  if not a or not a['hostile'] or a['hp']<=0:raise RuntimeError('Sem alvo hostil vivo no inicio')
  alvo_id=a['id'];t['distancia_inicial']=math.dist(a['position'],s['player']['position'])
  for i in range(60):
   if u.GetForegroundWindow()==d.hwnd:raise RuntimeError('Aika em foco; teste interrompido')
   s=d.snapshot();a=s['target'];p=s['player'];cc=d.estados_controle();t['quadros'].append(dict(t=time.time(),alvo=a,pos=p['position'],hp=p['hp']/p['hp_max'],normal_cooldown=cc.get('normal_cooldown'),animation=cc.get('animation')))
   if p['hp']/p['hp_max']<.6:raise RuntimeError('Vida baixa; teste encerrado')
   if not a or a['id']!=alvo_id or a['hp']<=0:break
   if i%6==0:e.keyDown('1');time.sleep(.07);e.keyUp('1')
   time.sleep(.1)
  t.update(ok=True,sem_foco=u.GetForegroundWindow()!=d.hwnd)
 except Exception as ex:t.update(ok=False,erro=str(ex))
 finally:
  if e:e.keyUp('1')
  if d:d.close()
(raiz/'build/ataque_dois_alvos.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
