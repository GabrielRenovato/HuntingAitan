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
 for hwnd in (33818620,8980122):
  if not u.IsWindow(hwnd):continue
  pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
  if not h:raise RuntimeError('Nao consegui conferir Hunting aberto')
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise RuntimeError('Caminho indisponivel')
   if Path(buf.value).resolve()!=(raiz/'build/segundo-plano-alvo-local/win-unpacked/HuntingAitan.exe').resolve():raise RuntimeError('Janela Hunting mudou')
  finally:k.CloseHandle(h)
  u.PostMessageW(hwnd,0x10,0,0)
 for _ in range(100):
  if not any(u.IsWindow(h) for h in (33818620,8980122)):break
  time.sleep(.1)
 if any(u.IsWindow(h) for h in (33818620,8980122)):raise RuntimeError('Hunting ainda fechando; nao testei')
 preparar_runtime_visual();root=tk.Tk();root.title('HuntingAitan - verificando comandos ao fundo');root.geometry('420x95+100+100');tk.Label(root,text='Comparando TAB e movimento sem foco.\nOs dois macros estao parados.',pady=18).pack();root.update();root.lift();root.focus_force();time.sleep(.3);root.update();frente=u.GetForegroundWindow()
 r['testes']=[]
 for j in enumerar_clientes():
  d=DadosInternos(janela=j);e=EntradaJanela(d.hwnd,d.pid)
  try:
   teste=dict(pid=d.pid,nome=d.snapshot()['player']['name'],fases=[])
   for fase in (.06,.12,.25,.5):
    if u.GetForegroundWindow()==d.hwnd:raise RuntimeError('Aika em foco; teste interrompido')
    if d.snapshot()['player']['hp']/d.snapshot()['player']['hp_max']<.6:break
    antes=d.snapshot();e.keyDown('a');time.sleep(fase);e.keyUp('a');time.sleep(.5);apos=d.snapshot()
    f=dict(duracao=fase,heading_antes=antes['player']['heading'],heading_depois=apos['player']['heading'],sem_foco=u.GetForegroundWindow()!=d.hwnd)
    teste['fases'].append(f);root.update()
   r['testes'].append(teste)
  finally:
   e.keyUp('w');e.keyUp('1');e.keyUp('tab');d.close()
 r['ok']=True
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if root:root.destroy()
 (raiz/'build/teste_duracao_giros.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
