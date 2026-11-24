"""Remove somente a ponte identica a montagem do projeto deixada pelo teste de teleporte."""
import ctypes,json,os,struct,sys,threading
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.escolha_cliente import abrir_leitor
from huntingaitan.entrada.ponte_camera import PonteCamera,montar
r={};d=None;h=None;mutex=None
class MBI(ctypes.Structure):
    _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),('AllocationProtect',w.DWORD),
              ('PartitionId',w.WORD),('RegionSize',ctypes.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]
try:
    perfil=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    d=abrir_leitor(perfil['client_pid']);k=ctypes.WinDLL('kernel32',use_last_error=True);u=ctypes.WinDLL('user32',use_last_error=True)
    k.VirtualQueryEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.POINTER(MBI),ctypes.c_size_t];k.VirtualQueryEx.restype=ctypes.c_size_t
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE];k.VirtualFreeEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_size_t,w.DWORD]
    k.CreateMutexW.argtypes=[ctypes.c_void_p,w.BOOL,w.LPCWSTR];k.CreateMutexW.restype=w.HANDLE
    k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.ReleaseMutex.argtypes=[w.HANDLE]
    k.WriteProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=w.BOOL
    u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.GetWindowThreadProcessId.restype=w.DWORD
    u.SendMessageTimeoutW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM,w.UINT,w.UINT,ctypes.POINTER(ctypes.c_size_t)];u.SendMessageTimeoutW.restype=w.LPARAM
    mutex=k.CreateMutexW(None,False,'Local\\HuntingAitan.PonteCamera.'+str(d.pid))
    if not mutex or k.WaitForSingleObject(mutex,0) not in (0,0x80):raise RuntimeError('Ponte em uso por outra sessao; nenhuma escrita')
    h=k.OpenProcess(0x43a,False,d.pid)
    if not h:raise RuntimeError('Acesso negado')
    a=0x10000;achados=[]
    while a<0x80000000:
        mbi=MBI()
        if not k.VirtualQueryEx(h,a,ctypes.byref(mbi),ctypes.sizeof(mbi)):break
        proximo=int(mbi.BaseAddress or a)+mbi.RegionSize
        if mbi.State==0x1000 and mbi.Protect==0x20 and mbi.Type==0x20000 and mbi.RegionSize==4096:
            try:
                cab=d.read(a,8)
                if cab[:4]==bytes.fromhex('5589e5a1'):
                    data=struct.unpack('<I',cab[4:])[0]-8;raw=d.read(data,84)
                    valores=struct.unpack('<21I',raw)
                    if valores[14]==d.hwnd and valores[16]==1:
                        esperado=montar(data,a,d.base)
                        if d.read(a,len(esperado))==esperado:achados.append((a,data,valores))
            except (RuntimeError,ValueError):pass
        if proximo<=a:raise RuntimeError('Consulta de memoria sem avanco')
        a=proximo
    r['encontradas']=len(achados)
    if not 1<=len(achados)<=4:raise RuntimeError('Quantidade de pontes fora do esperado; nenhuma escrita')
    # Pontes de testes antigos podem estar encadeadas. Remover exclusivamente
    # uma cadeia unica completa, de cima para baixo, com bytes identicos.
    cadeia=[];pendentes=list(achados)
    while pendentes:
        originais={v[0] for c,data,v in pendentes};topos=[a for a in pendentes if a[0] not in originais]
        if len(topos)!=1:raise RuntimeError('Cadeia ambigua; nenhuma escrita')
        topo=topos[0]
        if cadeia and cadeia[-1][2][0]!=topo[0]:raise RuntimeError('Pontes nao formam cadeia unica; nenhuma escrita')
        cadeia.append(topo);pendentes.remove(topo)
    r['remocoes']=[]
    for codigo,data,v in cadeia:
        if h is None:h=k.OpenProcess(0x43a,False,d.pid)
        p=PonteCamera.__new__(PonteCamera)
        p.dados=d;p.hwnd=d.hwnd;p.pid=d.pid;p.h=h;p.k=k;p.u=u;p.codigo=codigo;p.d=data;p.instalada=True;p.incerta=False;p.seq=v[4];p.lock=threading.Lock();p.mutex=None
        p.thread=v[12];p.msg=v[2];p.token=v[3];p.original=v[0]
        resposta=p.pedir(3);p.close();h=None;r['remocoes'].append(resposta)
        if p.instalada or p.incerta:raise RuntimeError('Remocao sem confirmacao; restante preservado')
    r.update(ok=True,pid=d.pid)
except Exception as e:r.update(ok=False,erro=str(e))
finally:
    if h:k.CloseHandle(h)
    if mutex:k.ReleaseMutex(mutex);k.CloseHandle(mutex)
    if d:d.close()
    (raiz/'build/recuperacao_ponte_giovanni.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
