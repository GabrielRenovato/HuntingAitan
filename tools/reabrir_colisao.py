"""Fecha os paineis da templaria e do guerreiro e reabre os dois na compilacao build/colisao-local.

Precisa rodar como administrador (os paineis exigem elevacao e so um processo elevado consegue fecha-los).
Na templaria tambem define a tecla de destravar como 4, guardando copia do perfil."""
import ctypes,json,os,re,subprocess,sys,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.configuracao.perfil_hunt import validar
appdata=Path(os.environ['APPDATA'])
PERFIS={'templaria':appdata/'aika-caca-automatica','guerreiro':appdata/'aika-caca-automatica-segundo'}
exe=raiz/'build/colisao-local/win-unpacked/HuntingAitan.exe'
u=ctypes.WinDLL('user32')
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
r=dict(ok=False)

def paineis():
    """PIDs dos processos principais do HuntingAitan.exe (sem --type=) por pasta de perfil."""
    cmd="[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); Get-CimInstance Win32_Process -Filter \"name='HuntingAitan.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    saida=subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,encoding='utf-8',check=True).stdout.strip()
    lista=json.loads(saida) if saida else []
    if isinstance(lista,dict):lista=[lista]
    achados={}
    for p in lista:
        linha=(p.get('CommandLine') or '')
        if '--type=' in linha:continue
        for nome,pasta in PERFIS.items():
            # "aika-caca-automatica" e prefixo de "aika-caca-automatica-segundo": exige o fim do nome da pasta.
            if re.search(re.escape(str(pasta).lower())+r'(?![\w-])',linha.lower()):achados[nome]=p['ProcessId']
    return achados

try:
    if not exe.exists():raise RuntimeError('Compilacao nao encontrada: '+str(exe))
    antigos=paineis();ids=set(antigos.values());fechadas=[];cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @cb
    def visitar(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value in ids:u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    fim=time.monotonic()+20
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<fim:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Paineis antigos ainda fechando; nada foi reaberto')
    time.sleep(1.5)
    novos={}
    for nome,pasta in PERFIS.items():
        arquivo=pasta/'profile.json'
        if nome=='templaria':
            texto=arquivo.read_text(encoding='utf-8');p=json.loads(texto)
            (pasta/('profile.antes-destravar-'+time.strftime('%Y%m%d_%H%M%S')+'.json')).write_text(texto,encoding='utf-8')
            p['unstuck_key']='4';arquivo.write_text(json.dumps(validar(p),ensure_ascii=False,indent=2),encoding='utf-8')
        novos[nome]=subprocess.Popen([str(exe),'--user-data-dir='+str(pasta)],cwd=exe.parent).pid
    r=dict(ok=True,fechados=antigos,abertos=novos)
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/reabertura_colisao.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
