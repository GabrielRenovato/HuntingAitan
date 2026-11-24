import ctypes,subprocess,json,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE];k.TerminateProcess.argtypes=[w.HANDLE,w.UINT];k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
r={}
try:
 exe=Path(r'C:\GoLevel\AikaOnline\AikaLauncher.exe');h=k.OpenProcess(0x1000|1|0x100000,False,12008)
 if h:
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise RuntimeError('Caminho indisponivel')
   if Path(buf.value).resolve()!=exe.resolve():raise RuntimeError('Processo mudou; nao encerrei')
   if not k.TerminateProcess(h,0):raise RuntimeError('Nao consegui encerrar launcher antigo')
   k.WaitForSingleObject(h,3000)
  finally:k.CloseHandle(h)
 p=subprocess.Popen([str(exe)],cwd=str(exe.parent));r=dict(ok=True,pid=p.pid)
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reabrir_launcher_resultado.json').write_text(json.dumps(r),encoding='utf-8')
