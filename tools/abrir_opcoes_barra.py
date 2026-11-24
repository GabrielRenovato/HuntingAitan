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
 u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];scan=u.MapVirtualKeyW(0x4f,0)
 u.PostMessageW(d.hwnd,0x100,0x4f,1|(scan<<16));time.sleep(.08);u.PostMessageW(d.hwnd,0x101,0x4f,1|(scan<<16)|0xc0000000);time.sleep(.4)
 import mss,cv2
 from huntingaitan.visao.captura_aika import CapturaAika
 with mss.MSS() as sct:
  cap=CapturaAika(sct);cv2.imwrite(str(raiz/'build/opcoes_barra.png'),cap.capturar());r['area']=cap.area
 r['ok']=True
except Exception as e:r.update(ok=False,erro=str(e))
finally:
 if d:d.close()
 (raiz/'build/opcoes_barra.json').write_text(json.dumps(r),encoding='utf-8')
