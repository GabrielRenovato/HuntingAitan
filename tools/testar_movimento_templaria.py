import sys,time,json,ctypes,math
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.entrada.ponte_camera import PonteCamera
from huntingaitan.rotas.navegacao_grade import ler_grade
r={};d=None;p=None;u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
try:
 j=next(j for j in enumerar_clientes() if j['pid']==21108);d=DadosInternos(janela=j);frente=u.GetForegroundWindow()
 if frente==d.hwnd:raise RuntimeError('Aika em foco')
 p=PonteCamera(d);r['tentativas']=[]
 for offset in (0,90,-90):
  s=d.snapshot();pos=s['player']['position'];cc=d.estados_controle()
  if s['player']['hp']/s['player']['hp_max']<.65:break
  if cc['casting']:time.sleep(2);continue
  h=math.radians(s['player']['heading']+offset);dest=(pos[0]+math.sin(h)*2,pos[1]+math.cos(h)*2);grade=ler_grade(d,pos)
  if not grade.caminho(pos,dest):continue
  t=dict(pos_antes=pos,cc=cc,destino=dest,envio=p.mover(*dest));r['tentativas'].append(t);time.sleep(1.2);apos=d.snapshot()['player']['position'];t['pos_depois']=apos;t['deslocamento']=math.dist(pos,apos)
  p.mover(*apos);time.sleep(.5);t['movimento_apos_parar']=math.dist(apos,d.snapshot()['player']['position'])
  if t['deslocamento']>.5:break
 r['foco_preservado']=u.GetForegroundWindow()==frente;r['ok']=any(t['deslocamento']>.5 for t in r['tentativas'])
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if p:p.close();r['ponte_removida']=not p.instalada and not p.incerta
 if d:d.close()
 (raiz/'build/teste_movimento_templaria.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
