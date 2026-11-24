"""Testa somente a templaria por ate tres minutos e encerra normalmente."""
import ctypes,json,os,subprocess,sys,time
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.rotas.circuito_verit_leste import dentro_leste
dest=raiz/'build'/('teste_templaria_'+time.strftime('%Y%m%d_%H%M%S'));dest.mkdir()
u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32')
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
u.IsWindow.argtypes=[w.HWND]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
k.CloseHandle.argtypes=[w.HANDLE]
r=dict(fase='preparando',foco=[]);proc=None;out=None;err=None;antigo_exe=None;fechadas=[]
def salvar(): (dest/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    # Confere condicoes antes de interromper a caca existente.
    perfil_atual=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    janela=next(j for j in enumerar_clientes() if j['pid']==perfil_atual['client_pid'] and j['hwnd']==perfil_atual['client_hwnd'])
    leitura=DadosInternos(janela=janela)
    try:
        inicial=leitura.snapshot();limite_vida=time.monotonic()+20
        while 0<inicial['player']['hp']/inicial['player']['hp_max']<.65 and time.monotonic()<limite_vida:
            time.sleep(.2);inicial=leitura.snapshot()
        r.update(nome=inicial['player']['name'],hp_inicial=inicial['player']['hp']/inicial['player']['hp_max'])
        if r['hp_inicial']<.65:raise RuntimeError('Vida abaixo de 65%; caca existente preservada')
        if not dentro_leste(inicial['player']['position']):raise RuntimeError('Personagem fora do circuito; caca existente preservada')
        if leitura.caca_original_ativa():raise RuntimeError('Caca original ativa; painel preservado')
    finally:leitura.close()
    antigo=json.loads((raiz/'build/ativar_verit_leste.json').read_text(encoding='utf-8'))
    fechadas=[];cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @cb
    def visitar(hwnd,_):
        global antigo_exe
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value!=antigo['pid']:return True
        h=k.OpenProcess(0x1000,False,pid.value)
        if not h:return True
        try:
            b=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(b))
            if k.QueryFullProcessImageNameW(h,0,b,ctypes.byref(n)):
                p=Path(b.value).resolve()
                if p.name.lower()=='huntingaitan.exe' and raiz/'build' in p.parents:
                    antigo_exe=p
                    u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        finally:k.CloseHandle(h)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    fim=time.monotonic()+15
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<fim:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Painel anterior ainda fechando')
    time.sleep(1)
    p=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    j=next(j for j in enumerar_clientes() if j['pid']==p['client_pid'] and j['hwnd']==p['client_hwnd'])
    d=DadosInternos(janela=j)
    try:
        s=d.snapshot();r['nome']=s['player']['name'];r['posicao']=s['player']['position']
        if d.caca_original_ativa():raise RuntimeError('Caca original ligada; teste nao iniciou')
        if not dentro_leste(s['player']['position']):raise RuntimeError('Templaria fora do circuito leste; teste nao iniciou')
        if s['player']['hp']/s['player']['hp_max']<.65:raise RuntimeError('Vida abaixo de 65%; teste nao iniciou')
    finally:d.close()
    p.update(patrol_mode='termes_verit_leste',background_keys=True)
    f=dest/'profile.json';f.write_text(json.dumps(p),encoding='utf-8')
    env=dict(os.environ,AIKA_DATA_DIR=str(dest),AIKA_CLIENT_PID=str(p['client_pid']),AIKA_CLIENT_HWND=str(p['client_hwnd']))
    out=(dest/'stdout.jsonl').open('w',encoding='utf-8');err=(dest/'stderr.txt').open('w',encoding='utf-8')
    proc=subprocess.Popen([sys.executable,'-u',str(raiz/'hunt_bridge.py'),'run',str(f)],cwd=raiz,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True)
    r['fase']='rodando';salvar();fim=time.monotonic()+180
    while proc.poll() is None and time.monotonic()<fim:
        r['foco'].append(dict(em=time.time(),hwnd=u.GetForegroundWindow()));salvar();time.sleep(1)
except Exception as e:r['erro']=str(e)
finally:
    if proc and proc.poll() is None:
        try:proc.stdin.write('{"command":"stop"}\n');proc.stdin.flush();proc.wait(timeout=15)
        except Exception as e:r['erro_parada']=str(e)
    if out:out.close()
    if err:err.close()
    if proc is None and antigo_exe is not None and not any(u.IsWindow(h) for h in fechadas):
        restaurado=subprocess.Popen([str(antigo_exe),'--user-data-dir='+str(Path(os.environ['APPDATA'])/'aika-caca-automatica')],cwd=antigo_exe.parent)
        antigo['pid']=restaurado.pid;(raiz/'build/ativar_verit_leste.json').write_text(json.dumps(antigo),encoding='utf-8')
        r['painel_restaurado_pid']=restaurado.pid
    r['codigo']=proc.returncode if proc else None;r['fase']='encerrado';salvar()
