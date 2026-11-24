import sys,os,json,time,ctypes,tkinter as tk
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz));pasta=Path.home()/'AppData/Roaming/aika-caca-automatica';p=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.visao.captura_janela import CapturaJanela
r={};d=None;root=None
try:
 import cv2
 d=DadosInternos();u=d.u;u.GetForegroundWindow.restype=w.HWND;u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
 root=tk.Tk();root.title('Teste da captura do Aika ao fundo');root.geometry('350x100+150+100');tk.Label(root,text='Verificando imagem e botao do Aika\nsem usar seu mouse.',pady=20).pack();root.update();root.lift();root.focus_force();time.sleep(.3);root.update();frente=int(u.GetForegroundWindow() or 0)
 with CapturaJanela(d.hwnd,d.pid) as cap:
  im=cap.capturar();cv2.imwrite(str(raiz/'build/wgc_antes.png'),im)
  referencia=cv2.imread(str(raiz/'build/opcoes_barra.png'))[324:347,906:1019]
  def titulo(im):return cv2.minMaxLoc(cv2.matchTemplate(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),cv2.cvtColor(referencia,cv2.COLOR_BGR2GRAY),cv2.TM_CCOEFF_NORMED))[1]>.9
  if not titulo(im):
   vk=0x4f;lp=1|(u.MapVirtualKeyW(vk,0)<<16);u.PostMessageW(d.hwnd,0x100,vk,lp);time.sleep(.07);u.PostMessageW(d.hwnd,0x101,vk,lp|0xc0000000);time.sleep(.5);root.update();im=cap.capturar()
  cv2.imwrite(str(raiz/'build/wgc_configuracao.png'),im);aberta=titulo(im)
  if aberta:
   x,y=1125,330;lp=(y<<16)|x
   u.PostMessageW(d.hwnd,0x200,0,lp);time.sleep(.15);u.PostMessageW(d.hwnd,0x201,1,lp);time.sleep(.07);u.PostMessageW(d.hwnd,0x202,0,lp);time.sleep(.5);root.update();depois=cap.capturar();cv2.imwrite(str(raiz/'build/wgc_depois.png'),depois)
   r['clique_funcionou']=not titulo(depois)
  r.update(ok=True,configuracao_aberta=aberta,media=float(im.mean()),foco_preservado=int(u.GetForegroundWindow() or 0)==frente)
except Exception as e:r.update(ok=False,erro=str(e))
finally:
 if root:root.destroy()
 if d:d.close()
 (raiz/'build/teste_wgc.json').write_text(json.dumps(r),encoding='utf-8')
