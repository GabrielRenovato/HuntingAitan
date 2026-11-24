"""Troca apenas o painel da templaria para a compilacao do circuito leste."""
import ctypes,json,os,subprocess,sys,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.configuracao.perfil_hunt import validar
u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32')
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
u.IsWindow.argtypes=[w.HWND]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
k.CloseHandle.argtypes=[w.HANDLE]
r={}
try:
    estado=raiz/'build/ativar_verit_leste.json'
    if estado.exists():
        antigo=json.loads(estado.read_text(encoding='utf-8'))
    else:antigo=json.loads((raiz/'build/abertura_motor_estavel.json').read_text(encoding='utf-8'))[0]
    pid_antigo=antigo['pid'];fechadas=[];cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @cb
    def visitar(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value!=pid_antigo:return True
        h=k.OpenProcess(0x1000,False,pid.value)
        if not h:raise RuntimeError('Nao foi possivel conferir o painel antigo')
        try:
            b=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(b))
            if k.QueryFullProcessImageNameW(h,0,b,ctypes.byref(n)) and Path(b.value).name.lower()=='huntingaitan.exe' and raiz/'build' in Path(b.value).resolve().parents:
                u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        finally:k.CloseHandle(h)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    fim=time.monotonic()+15
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<fim:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Painel anterior ainda fechando')
    time.sleep(1)
    pasta=Path(os.environ['APPDATA'])/'aika-caca-automatica';f=pasta/'profile.json'
    texto=f.read_text(encoding='utf-8');p=json.loads(texto)
    if p['client_pid']!=antigo['cliente_pid']:raise RuntimeError('Cliente do perfil mudou; nao alterei a configuracao')
    (pasta/('profile_antes_verit_leste_'+time.strftime('%Y%m%d_%H%M%S')+'.json')).write_text(texto,encoding='utf-8')
    p.update(patrol_mode='termes_verit_leste',target='verit',radius=50,background_keys=True)
    p=validar(p);f.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    exe=raiz/'build/templaria-transicoes-local/win-unpacked/HuntingAitan.exe'
    proc=subprocess.Popen([str(exe),'--user-data-dir='+str(pasta)],cwd=exe.parent)
    r=dict(ok=True,pid=proc.pid,cliente_pid=p['client_pid'],circuito=p['patrol_mode'])
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/ativar_verit_leste.json').write_text(json.dumps(r),encoding='utf-8')
