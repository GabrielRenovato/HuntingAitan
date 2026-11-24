import sys,os,json,time,ctypes,tkinter as tk
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
p=json.loads((raiz/'build/profile_segundo_plano_proposto.json').read_text(encoding='utf-8'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.visao.captura_janela import CapturaJanela
from huntingaitan.visao.controle_avisos import preparar_runtime_visual
r={};d=None;root=None
try:
 preparar_runtime_visual();d=DadosInternos();e=EntradaJanela(d.hwnd,d.pid);u=e.u;u.GetForegroundWindow.restype=w.HWND
 root=tk.Tk();root.title('HuntingAitan - verificacao segundo plano');root.geometry('390x90+140+100');tk.Label(root,text='Conferindo F3 e captura ao fundo.\nA caca continua parada.',pady=18).pack();root.update();root.lift();root.focus_force();time.sleep(.3);root.update()
 frente=int(u.GetForegroundWindow() or 0);cursor=w.POINT();u.GetCursorPos(ctypes.byref(cursor));antes=d.snapshot();cd0=d.recargas_atalhos().get('f3');r['recargas_f']=list(k for k in d.recargas_atalhos() if k.startswith('f'))
 with CapturaJanela(d.hwnd,d.pid) as cap:
  imagem=cap.capturar();r['captura']=list(imagem.shape)
  if cd0 and cd0['ready'] and frente and frente!=d.hwnd:
   e.keyDown('f3');time.sleep(.07);e.keyUp('f3');casting=[];cds=[]
   for _ in range(70):
    root.update();time.sleep(.1);cc=d.estados_controle();casting.append(cc.get('casting'));cds.append(d.recargas_atalhos().get('f3',{}).get('cooldown',0))
   depois=d.snapshot();r['f3_confirmado']=max(cds)>0 or depois['player']['mp']<antes['player']['mp'];r['cooldown_max']=max(cds)
  else:r['teste_pulado']=dict(cd=cd0,frente=frente)
  cap.capturar();r['captura_atualizada']=True
 cursor2=w.POINT();u.GetCursorPos(ctypes.byref(cursor2));r.update(ok=True,foco_preservado=int(u.GetForegroundWindow() or 0)==frente,cursor_preservado=(cursor.x,cursor.y)==(cursor2.x,cursor2.y))
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if d:d.close()
 if root:root.destroy()
 (raiz/'build/validacao_segundo_plano.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
