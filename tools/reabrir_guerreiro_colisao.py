"""Reabre somente o perfil do guerreiro na compilacao local atual."""
import ctypes,json,os,subprocess,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];perfil=Path(os.environ['APPDATA'])/'aika-caca-automatica-segundo'
u=ctypes.WinDLL('user32');u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
r={}
try:
    comando="[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); Get-CimInstance Win32_Process -Filter \"name='HuntingAitan.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    consulta=subprocess.run(['powershell','-NoProfile','-Command',comando],capture_output=True,encoding='utf-8',check=True)
    processos=json.loads(consulta.stdout) if consulta.stdout.strip() else []
    if isinstance(processos,dict):processos=[processos]
    ids=set()
    for p in processos:
        linha=p.get('CommandLine') or '';caminho=p.get('ExecutablePath')
        if caminho and Path(caminho).name.lower()=='huntingaitan.exe' and str(perfil).lower() in linha.lower() and '--type=' not in linha:
            ids.add(p['ProcessId'])
    fechadas=[];cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @cb
    def visitar(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value in ids:u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    fim=time.monotonic()+15
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<fim:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Painel antigo do guerreiro ainda fechando')
    time.sleep(1)
    p=json.loads((perfil/'profile.json').read_text(encoding='utf-8'))
    exe=raiz/'build/colisao-local/win-unpacked/HuntingAitan.exe'
    proc=subprocess.Popen([str(exe),'--user-data-dir='+str(perfil)],cwd=exe.parent)
    r=dict(ok=True,pid=proc.pid,cliente_pid=p['client_pid'],circuito=p['patrol_mode'],perfil=str(perfil))
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reabertura_guerreiro_colisao.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
