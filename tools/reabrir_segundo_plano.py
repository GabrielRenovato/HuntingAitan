import ctypes,time,subprocess,json,shutil
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1]
u=ctypes.WinDLL('user32',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True)
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
r={}
try:
 from huntingaitan.configuracao.perfil_hunt import validar
except ModuleNotFoundError:
 import sys;sys.path.insert(0,str(raiz));from huntingaitan.configuracao.perfil_hunt import validar
try:
 exe=raiz/'build/segundo-plano-local/win-unpacked/HuntingAitan.exe'
 if not exe.is_file():raise RuntimeError('Novo aplicativo nao encontrado')
 novo=validar(json.loads((raiz/'build/profile_segundo_plano_proposto.json').read_text(encoding='utf-8')))
 hwnd=9898036
 if u.IsWindow(hwnd):
  pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
  if not h:raise RuntimeError('Nao consegui conferir o aplicativo antigo')
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise RuntimeError('Caminho indisponivel')
   if Path(buf.value).resolve()!=(raiz/'build/jardim-npc-confirmacao-local/win-unpacked/HuntingAitan.exe').resolve():raise RuntimeError('Janela mudou; nada foi fechado')
  finally:k.CloseHandle(h)
  u.PostMessageW(hwnd,0x10,0,0)
  for _ in range(100):
   if not u.IsWindow(hwnd):break
   time.sleep(.1)
  if u.IsWindow(hwnd):raise RuntimeError('Aplicativo anterior ainda esta fechando')
 perfil=Path.home()/'AppData/Roaming/aika-caca-automatica/profile.json'
 backup=perfil.with_name('profile_antes_segundo_plano_'+time.strftime('%Y%m%d_%H%M%S')+'.json');shutil.copy2(perfil,backup)
 atual=json.loads(perfil.read_text(encoding='utf-8-sig'))
 if (atual['client_hwnd'],atual['client_pid'])!=(novo['client_hwnd'],novo['client_pid']):raise RuntimeError('Cliente selecionado mudou; confira novamente')
 perfil.write_text(json.dumps(novo,ensure_ascii=False,indent=2),encoding='utf-8')
 proc=subprocess.Popen([str(exe)],cwd=str(exe.parent));r=dict(ok=True,pid=proc.pid,caminho=str(exe),backup=str(backup))
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reabertura_segundo_plano_resultado.json').write_text(json.dumps(r),encoding='utf-8')
