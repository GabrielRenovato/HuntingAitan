import sys,os,json,ctypes,time
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz));pasta=Path.home()/'AppData/Roaming/aika-caca-automatica';p=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
r={};d=None
try:
 import numpy as np,cv2
 d=DadosInternos();u=ctypes.WinDLL('user32');g=ctypes.WinDLL('gdi32')
 u.GetDC.argtypes=[w.HWND];u.GetDC.restype=w.HDC;u.ReleaseDC.argtypes=[w.HWND,w.HDC];u.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)];u.PrintWindow.argtypes=[w.HWND,w.HDC,w.UINT]
 g.CreateCompatibleDC.argtypes=[w.HDC];g.CreateCompatibleDC.restype=w.HDC;g.CreateCompatibleBitmap.argtypes=[w.HDC,ctypes.c_int,ctypes.c_int];g.CreateCompatibleBitmap.restype=w.HBITMAP
 g.SelectObject.argtypes=[w.HDC,w.HGDIOBJ];g.SelectObject.restype=w.HGDIOBJ;g.DeleteObject.argtypes=[w.HGDIOBJ];g.DeleteDC.argtypes=[w.HDC];g.GetDIBits.argtypes=[w.HDC,w.HBITMAP,w.UINT,w.UINT,ctypes.c_void_p,ctypes.c_void_p,w.UINT]
 rect=w.RECT();u.GetClientRect(d.hwnd,ctypes.byref(rect));largura,altura=rect.right,rect.bottom
 dc=u.GetDC(d.hwnd);mem=g.CreateCompatibleDC(dc);bmp=g.CreateCompatibleBitmap(dc,largura,altura);old=g.SelectObject(mem,bmp)
 try:
  t=time.perf_counter();ok=u.PrintWindow(d.hwnd,mem,3);dur=time.perf_counter()-t
  header=ctypes.create_string_buffer(40);import struct
  struct.pack_into('<IiiHHIIiiII',header,0,40,largura,-altura,1,32,0,largura*altura*4,0,0,0,0)
  bits=ctypes.create_string_buffer(largura*altura*4);linhas=g.GetDIBits(mem,bmp,0,altura,bits,header,0)
  imagem=np.frombuffer(bits,dtype=np.uint8).reshape(altura,largura,4)[...,:3].copy();cv2.imwrite(str(raiz/'build/teste_captura_janela.png'),imagem)
  r=dict(ok=bool(ok),linhas=linhas,media=float(imagem.mean()),desvio=float(imagem.std()),segundos=dur)
 finally:g.SelectObject(mem,old);g.DeleteObject(bmp);g.DeleteDC(mem);u.ReleaseDC(d.hwnd,dc)
except Exception as e:r.update(ok=False,erro=str(e))
finally:
 if d:d.close()
 (raiz/'build/teste_captura_janela.json').write_text(json.dumps(r),encoding='utf-8')
