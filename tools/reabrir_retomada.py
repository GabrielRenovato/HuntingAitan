import ctypes,time,subprocess,json
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32')
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
r={}
try:
 hwnd=3475742
 if u.IsWindow(hwnd):
  pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
  if not h:raise RuntimeError('Nao consegui conferir aplicativo aberto')
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise RuntimeError('Caminho indisponivel')
   if Path(buf.value).resolve()!=(raiz/'build/segundo-plano-local/win-unpacked/HuntingAitan.exe').resolve():raise RuntimeError('Janela mudou; nada fechado')
  finally:k.CloseHandle(h)
  u.PostMessageW(hwnd,0x10,0,0)
  for _ in range(100):
   if not u.IsWindow(hwnd):break
   time.sleep(.1)
  if u.IsWindow(hwnd):raise RuntimeError('Aplicativo antigo ainda fechando')
 exe=raiz/'build/segundo-plano-retomada-local/win-unpacked/HuntingAitan.exe'
 proc=subprocess.Popen([str(exe)],cwd=str(exe.parent));r=dict(ok=True,pid=proc.pid,caminho=str(exe))
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reabertura_retomada_resultado.json').write_text(json.dumps(r),encoding='utf-8')
