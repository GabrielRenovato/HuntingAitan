import ctypes,subprocess,json,os,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32');u.IsWindow.argtypes=[w.HWND];u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
r={}
try:
 for hwnd in (9635856,42862658):
  if not u.IsWindow(hwnd):continue
  pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
  if not h:raise RuntimeError('Caminho do Hunting indisponivel')
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)) or Path(buf.value).resolve()!=(raiz/'build/motor-interno-local/win-unpacked/HuntingAitan.exe').resolve():raise RuntimeError('Janela mudou; nao fechei')
  finally:k.CloseHandle(h)
  u.PostMessageW(hwnd,0x10,0,0)
 for _ in range(100):
  if not any(u.IsWindow(h) for h in (9635856,42862658)):break
  time.sleep(.1)
 if any(u.IsWindow(h) for h in (9635856,42862658)):raise RuntimeError('Hunting ainda fechando')
 exe=raiz/'build/motor-interno-local/win-unpacked/HuntingAitan.exe';abertos=[]
 for nome in ('aika-caca-automatica','aika-caca-automatica-segundo'):
  pasta=Path(os.environ['APPDATA'])/nome;perfil=pasta/'profile.json';conteudo=perfil.read_text(encoding='utf-8');perfil.with_name('profile_antes_motor_interno_'+time.strftime('%Y%m%d_%H%M%S')+'.json').write_text(conteudo,encoding='utf-8');p=json.loads(conteudo);p['auto_base']=True;perfil.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');proc=subprocess.Popen([str(exe),'--user-data-dir='+str(pasta)],cwd=str(exe.parent));abertos.append(proc.pid)
 r=dict(ok=True,pids=abertos)
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reabrir_dois_alvo_resultado.json').write_text(json.dumps(r),encoding='utf-8')
