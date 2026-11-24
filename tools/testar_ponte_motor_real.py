import sys,time,json,ctypes,math
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.entrada.ponte_camera import PonteCamera
from huntingaitan.rotas.navegacao_grade import ler_grade
saida=raiz/'build/teste_ponte_motor_real.json';r=dict(testes=[]);u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
for j in enumerar_clientes():
 d=None;p=None;t=dict(pid=j['pid']);r['testes'].append(t)
 try:
  d=DadosInternos(janela=j);s=d.snapshot();t['nome']=s['player']['name'];frente=u.GetForegroundWindow()
  if frente==d.hwnd:raise RuntimeError('Cliente ganhou foco; nao testei')
  if d.caca_original_ativa():raise RuntimeError('Caca original ligada; teste recusado')
  if s['player']['hp']/s['player']['hp_max']<.65:raise RuntimeError('Vida baixa; teste recusado')
  p=PonteCamera(d);t['fase']='instalada';saida.write_text(json.dumps(r),encoding='utf-8')
  a=d.camera_regional()['yaw'];p.girar(.03);time.sleep(.2);b=d.camera_regional()['yaw'];p.girar(-.03);t['delta_camera']=(b-a+540)%360-180
  antes=d.snapshot()['target'];t['selecao']=p.selecionar();time.sleep(.2);depois=d.snapshot()['target'];t['alvo_antes']=antes['id'] if antes else None;t['alvo_depois']=depois['id'] if depois else None
  cc=d.recargas_atalhos();sk=cc.get('f3');mp=d.snapshot()['player']['mp']
  if sk and sk['ready']:
   t['skill']=p.usar(sk['skill']);time.sleep(3.3);t['skill_cd_depois']=d.recargas_atalhos().get('f3');t['mp_antes']=mp;t['mp_depois']=d.snapshot()['player']['mp']
  s=d.snapshot();pos=s['player']['position'];h=math.radians(s['player']['heading']);dest=(pos[0]+math.sin(h)*2,pos[1]+math.cos(h)*2)
  grade=ler_grade(d,pos)
  if grade.caminho(pos,dest):
   scene=d.cena_validada();assist=d.u32(scene+0xeadf4);base0=d.read(assist+0x274,8);t['movimento']=p.mover(*dest);time.sleep(.8);apos=d.snapshot()['player']['position'];t['deslocamento']=math.dist(pos,apos);t['base_preservada']=base0==d.read(assist+0x274,8);t['parada']=p.mover(*apos)
  else:t['movimento_pulado']='Grade nao confirmou o trecho de 2 unidades'
  t['foco_preservado']=u.GetForegroundWindow()==frente;t['ok']=True
 except Exception as ex:t.update(ok=False,erro=str(ex))
 finally:
  if p:
   p.close();t['ponte_removida']=not p.instalada and not p.incerta
  if d:d.close()
  saida.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
