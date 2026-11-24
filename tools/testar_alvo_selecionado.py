import sys,json,time,ctypes,math
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.entrada.entrada_janela import EntradaJanela
u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND;r={};d=None;e=None
try:
 j=next(j for j in enumerar_clientes() if j['pid']==21108);d=DadosInternos(janela=j);e=EntradaJanela(d.hwnd,d.pid);r['quadros']=[]
 for i in range(60):
  if u.GetForegroundWindow()==d.hwnd:raise RuntimeError('Aika em foco; nao valida segundo plano')
  s=d.snapshot();a=s['target'];p=s['player'];r['quadros'].append(dict(t=time.time(),alvo=a,hp=p['hp']/p['hp_max'],controle=d.estados_controle()))
  if p['hp']/p['hp_max']<.6:raise RuntimeError('Vida baixa; teste encerrado')
  if not a or not a['hostile'] or a['hp']<=0:break
  if i==0:r['distancia_inicial']=math.dist(a['position'],p['position'])
  if i%6==0:e.keyDown('1');time.sleep(.07);e.keyUp('1')
  time.sleep(.1)
 r['ok']=True;r['sem_foco']=u.GetForegroundWindow()!=d.hwnd
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if e:e.keyUp('1')
 if d:d.close()
 (raiz/'build/ataque_alvo_selecionado.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
