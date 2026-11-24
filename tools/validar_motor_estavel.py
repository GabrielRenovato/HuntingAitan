"""Validacao curta dos dois clientes, com perfis temporarios e parada normal."""
import ctypes,json,os,subprocess,sys,time
from ctypes import wintypes as w
from pathlib import Path

raiz=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.entrada.ponte_camera import PonteCamera

u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32')
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
k.CloseHandle.argtypes=[w.HANDLE]
dest=raiz/'build'/('validacao_estavel_'+time.strftime('%Y%m%d_%H%M%S'))
dest.mkdir(parents=True)
r=dict(fase='preparando',clientes=[],amostras_foco=[]);processos=[]
def salvar(): (dest/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
def fechar_apps():
    fechadas=[];callback=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @callback
    def visitar(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
        if not h:return True
        try:
            b=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(b))
            if k.QueryFullProcessImageNameW(h,0,b,ctypes.byref(n)):
                p=Path(b.value).resolve()
                if p.name.lower()=='huntingaitan.exe' and raiz/'build' in p.parents:
                    u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        finally:k.CloseHandle(h)
        return True
    u.EnumWindows.argtypes=[callback,w.LPARAM];u.EnumWindows(visitar,0)
    limite=time.monotonic()+12
    while any(u.IsWindow(w.HWND(h)) for h in fechadas) and time.monotonic()<limite:time.sleep(.1)
    if any(u.IsWindow(w.HWND(h)) for h in fechadas):raise RuntimeError('Hunting ainda fechando; teste nao iniciou')

try:
    fechar_apps();salvar()
    clientes=enumerar_clientes()
    for j in clientes:
        d=None;p=None;t=dict(pid=j['pid']);r['clientes'].append(t)
        try:
            d=DadosInternos(janela=j);s=d.snapshot();t['nome']=s['player']['name']
            if d.caca_original_ativa():raise RuntimeError('Caca original ligada')
            if s['player']['hp']/s['player']['hp_max']<.65:raise RuntimeError('Vida abaixo de 65%; teste nao iniciou')
            p=PonteCamera(d);alvo=s['target']
            if not alvo or not alvo['hostile'] or alvo['hp']<=0:
                p.selecionar();time.sleep(.2);alvo=d.snapshot()['target']
            if alvo and alvo['hostile'] and alvo['hp']>0:
                t['alvo_esperado']=alvo['id'];t['resposta']=p.focar(alvo)
                time.sleep(.1);atual=d.snapshot()['target'];t['id_confirmado']=atual['id'] if atual else None
                if t['id_confirmado']!=t['alvo_esperado']:raise RuntimeError('ID selecionado diferente do esperado')
                t['recuperacao_validada']=True
            else:t['recuperacao_validada']=False
        finally:
            if p:p.close();t['ponte_removida']=not p.instalada and not p.incerta
            if d:d.close()
        salvar()
    for nome in ('aika-caca-automatica','aika-caca-automatica-segundo'):
        perfil=json.loads((Path(os.environ['APPDATA'])/nome/'profile.json').read_text(encoding='utf-8'))
        if not any(j['pid']==perfil['client_pid'] and j['hwnd']==perfil['client_hwnd'] for j in clientes):raise RuntimeError('Perfil aponta para cliente fechado')
        pasta=dest/str(perfil['client_pid']);pasta.mkdir();perfil['auto_base']=True
        arquivo=pasta/'profile.json';arquivo.write_text(json.dumps(perfil),encoding='utf-8')
        out=(pasta/'stdout.jsonl').open('w',encoding='utf-8');err=(pasta/'stderr.txt').open('w',encoding='utf-8')
        env=dict(os.environ,AIKA_DATA_DIR=str(pasta),AIKA_CLIENT_PID=str(perfil['client_pid']),AIKA_CLIENT_HWND=str(perfil['client_hwnd']))
        proc=subprocess.Popen([sys.executable,'-u',str(raiz/'hunt_bridge.py'),'run',str(arquivo)],cwd=raiz,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True)
        processos.append((proc,out,err))
    r['fase']='farm';salvar();fim=time.monotonic()+120
    while time.monotonic()<fim and any(proc.poll() is None for proc,_,_ in processos):
        r['amostras_foco'].append(dict(em=time.time(),hwnd=u.GetForegroundWindow()));salvar();time.sleep(1)
except Exception as e:r['erro']=str(e)
finally:
    for proc,out,err in processos:
        if proc.poll() is None:
            try:proc.stdin.write('{"command":"stop"}\n');proc.stdin.flush();proc.wait(timeout=15)
            except Exception as e:r.setdefault('erros_parada',[]).append(str(e))
        out.close();err.close()
    r['fase']='encerrado';r['codigos']=[p.returncode for p,_,_ in processos];salvar()
