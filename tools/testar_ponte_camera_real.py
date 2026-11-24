import sys,time,json,ctypes
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.entrada.ponte_camera import PonteCamera
saida=raiz/'build/teste_ponte_camera_real.json';r={};d=None;ponte=None
try:
 j=next(j for j in enumerar_clientes() if j['pid']==21108);d=DadosInternos(janela=j);u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND;frente=u.GetForegroundWindow()
 if frente==d.hwnd:raise RuntimeError('Deixe outro programa em primeiro plano para validar')
 r.update(fase='antes_instalacao',pid=d.pid,hwnd=d.hwnd,antes=d.camera_regional());saida.write_text(json.dumps(r),encoding='utf-8')
 ponte=PonteCamera(d);r.update(fase='instalada',thread=ponte.thread);saida.write_text(json.dumps(r),encoding='utf-8')
 r['confirmacao']=ponte.girar(.03);time.sleep(.3);r['depois']=d.camera_regional();r['delta']=(r['depois']['yaw']-r['antes']['yaw']+540)%360-180
 r['foco_preservado']=u.GetForegroundWindow()==frente;r['camera_moveu']=abs(r['delta'])>.5
 ponte.girar(-.03);time.sleep(.2);ponte.close();r['ponte_removida']=not ponte.instalada and not ponte.incerta;r['ok']=r['camera_moveu'] and r['ponte_removida'] and r['foco_preservado'];r['fase']='finalizado'
except Exception as e:r.update(ok=False,erro=str(e))
finally:
 if ponte:ponte.close()
 if d:d.close()
 saida.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
