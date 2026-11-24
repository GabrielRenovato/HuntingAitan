import ctypes,sys,os,time,json,math,tkinter as tk
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.visao.controle_avisos import preparar_runtime_visual
u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32');u.GetForegroundWindow.restype=w.HWND;u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND];k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
r={};root=None
try:
 for hwnd in (29624242,18155720):
  if not u.IsWindow(hwnd):continue
  pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
  if not h:raise RuntimeError('Nao consegui conferir Hunting aberto')
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise RuntimeError('Caminho indisponivel')
   if Path(buf.value).resolve()!=(raiz/'build/segundo-plano-aproximacao-local/win-unpacked/HuntingAitan.exe').resolve():raise RuntimeError('Janela Hunting mudou')
  finally:k.CloseHandle(h)
  u.PostMessageW(hwnd,0x10,0,0)
 for _ in range(100):
  if not any(u.IsWindow(h) for h in (29624242,18155720)):break
  time.sleep(.1)
 if any(u.IsWindow(h) for h in (29624242,18155720)):raise RuntimeError('Hunting ainda fechando; nao testei')
 preparar_runtime_visual();root=tk.Tk();root.title('HuntingAitan - verificando comandos ao fundo');root.geometry('420x95+100+100');tk.Label(root,text='Comparando TAB e movimento sem foco.\nOs dois macros estao parados.',pady=18).pack();root.update();root.lift();root.focus_force();time.sleep(.3);root.update();frente=u.GetForegroundWindow()
 r['testes']=[]
 for j in enumerar_clientes():
  d=DadosInternos(janela=j);e=EntradaJanela(d.hwnd,d.pid)
  try:
   teste=dict(pid=d.pid,nome=d.snapshot()['player']['name'],fases=[])
   for fase in (1,2):
    if u.GetForegroundWindow()==d.hwnd:raise RuntimeError('Aika em foco; teste interrompido')
    if d.snapshot()['player']['hp']/d.snapshot()['player']['hp_max']<.6:break
    antes=d.snapshot();cam0=d.camera_regional();rct=w.RECT();u.GetClientRect(d.hwnd,ctypes.byref(rct));x=rct.right//2;y=rct.bottom//2;lp=(y<<16)|x
    u.PostMessageW(d.hwnd,0x200,0,lp);u.PostMessageW(d.hwnd,0x204,2,lp);time.sleep(.1)
    for passo in range(1,11):
     xx=x+passo*8*(1 if fase==1 else -1);u.PostMessageW(d.hwnd,0x200,2,(y<<16)|xx);time.sleep(.035)
    u.PostMessageW(d.hwnd,0x205,0,(y<<16)|xx);time.sleep(.4);apos=d.snapshot();cam1=d.camera_regional()
    f=dict(vk=fase,heading_antes=antes['player']['heading'],heading_depois=apos['player']['heading'],camera_antes=cam0,camera_depois=cam1,sem_foco=u.GetForegroundWindow()!=d.hwnd)
    teste['fases'].append(f);root.update()
   r['testes'].append(teste)
  finally:
   e.keyUp('w');e.keyUp('1');e.keyUp('tab');d.close()
 r['ok']=True
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if root:root.destroy()
 (raiz/'build/teste_mouse_camera.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
