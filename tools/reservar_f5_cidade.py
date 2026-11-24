"""Reserva F5 para viagem no perfil da templaria e reabre somente seu painel."""
import ctypes,json,os,re,subprocess,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];pasta=Path(os.environ['APPDATA'])/'aika-caca-automatica'
u=ctypes.WinDLL('user32');u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
r={}
try:
    cmd="[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); Get-CimInstance Win32_Process -Filter \"name='HuntingAitan.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    saida=subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,encoding='utf-8',check=True).stdout.strip()
    processos=json.loads(saida) if saida else []
    if isinstance(processos,dict):processos=[processos]
    ids={p['ProcessId'] for p in processos if '--type=' not in (p.get('CommandLine') or '') and re.search(re.escape(str(pasta).lower())+r'(?![\w-])',(p.get('CommandLine') or '').lower())}
    cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM);fechadas=[]
    @cb
    def visitar(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value in ids:u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    prazo=time.monotonic()+15
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<prazo:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Painel ainda aberto; perfil preservado')
    time.sleep(1)
    arquivo=pasta/'profile.json';antes=arquivo.read_text(encoding='utf-8');perfil=json.loads(antes)
    (pasta/('profile.antes-f5-cidade-'+time.strftime('%Y%m%d_%H%M%S')+'.json')).write_text(antes,encoding='utf-8')
    removidas=[]
    for lista,campo in (('reacoes','tecla'),('skills','key'),('items','key')):
        for regra in perfil.get(lista,[]):
            if str(regra.get(campo,'')).lower()=='f5':
                regra['ativa' if lista=='reacoes' else 'enabled']=False;removidas.append(regra.get('nome',lista))
    for lista in ('buff_keys','extra_buff_keys'):
        perfil[lista]=['' if str(k).lower()=='f5' else k for k in perfil.get(lista,[])]
    if perfil.get('periodic_item_key','').lower()=='f5':perfil['f3_enabled']=False
    if perfil.get('return_key','').lower()=='f5':perfil['return_key']=''
    arquivo.write_text(json.dumps(perfil,ensure_ascii=False,indent=2),encoding='utf-8')
    exe=raiz/'build/colisao-local/win-unpacked/HuntingAitan.exe'
    proc=subprocess.Popen([str(exe),'--user-data-dir='+str(pasta)],cwd=exe.parent)
    r=dict(ok=True,pid=proc.pid,regras_desativadas=removidas,cliente_pid=perfil['client_pid'])
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reservar_f5_cidade.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
