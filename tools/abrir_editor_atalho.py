import sys,os,json,time,ctypes
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz));pasta=Path.home()/'AppData/Roaming/aika-caca-automatica';p=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.visao.controle_avisos import preparar_runtime_visual
r={};d=None
try:
 preparar_runtime_visual();d=DadosInternos();u=d.u;u.GetForegroundWindow.restype=w.HWND
 g=d.u32(d.base+d.cfg('bar_manager_rva'));bloco=d.read(g,0x900);hot=(d.caminho.parent/'UI/HotKey.bin').read_bytes();off=bloco.find(hot[:40]);r=dict(hotkeys_offset=hex(off),hotkeys=list(bloco[off:off+468]) if off>=0 else None)
 u.ShowWindow.argtypes=[w.HWND,ctypes.c_int];u.SetForegroundWindow.argtypes=[w.HWND]
 for _ in range(10):
  u.ShowWindow(d.hwnd,9);u.SetForegroundWindow(d.hwnd);time.sleep(.3)
  if u.GetForegroundWindow()==d.hwnd:break
 if u.GetForegroundWindow()!=d.hwnd:raise RuntimeError('Aika nao obteve foco para reorganizar barra')
 import pydirectinput as entrada
 from huntingaitan.entrada.entrada_segura import mover_cursor_fisico
 if not mover_cursor_fisico(entrada,1465,112):raise RuntimeError('Cursor nao confirmado')
 entrada.mouseDown();time.sleep(.06);entrada.mouseUp();time.sleep(.3)
 if not mover_cursor_fisico(entrada,1254,935):raise RuntimeError('Cursor nao confirmado sobre atalho vazio')
 entrada.mouseDown(button='right');time.sleep(.06);entrada.mouseUp(button='right');time.sleep(.3)
 import mss,cv2
 from huntingaitan.visao.captura_aika import CapturaAika
 with mss.MSS() as sct:
  cap=CapturaAika(sct);cv2.imwrite(str(raiz/'build/editar_atalho.png'),cap.capturar());r['area']=cap.area
 r['ok']=True
except Exception as e:r.update(ok=False,erro=str(e))
finally:
 if d:d.close()
 (raiz/'build/editar_atalho.json').write_text(json.dumps(r),encoding='utf-8')
