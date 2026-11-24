"""Identifica a janela pelo processo do cliente, pois varias contas compartilham o titulo."""
import ctypes,os
from ctypes import wintypes as w
from pathlib import PureWindowsPath


EXECUTAVEIS={'aikacl.exe','aikacl-multiinstancia-teste.exe'}

def escolher_janela(janelas,primeiro_plano,pid=0,hwnd=0):
    candidatos=[j for j in janelas if PureWindowsPath(j['caminho']).name.lower() in EXECUTAVEIS]
    if pid or hwnd:
        escolhido=next((j for j in candidatos if j['pid']==pid and j['hwnd']==hwnd),None)
        if escolhido:return escolhido
        raise RuntimeError('O cliente selecionado foi fechado ou mudou. Atualize a lista e selecione o personagem novamente.')
    atual=next((j for j in candidatos if j['hwnd']==primeiro_plano),None)
    if atual:return atual
    if len(candidatos)==1:return candidatos[0]
    if not candidatos:raise RuntimeError('Nenhum cliente Aika compativel aberto. Abra o jogo e atualize a lista.')
    raise RuntimeError('Mais de um cliente aberto; selecione o personagem no painel ou deixe o Aika desejado em primeiro plano.')


def enumerar_clientes(u=None,k=None):
    u=u or ctypes.WinDLL('user32',use_last_error=True)
    k=k or ctypes.WinDLL('kernel32',use_last_error=True)
    callback_tipo=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    u.EnumWindows.argtypes=[callback_tipo,w.LPARAM];u.EnumWindows.restype=w.BOOL
    u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    u.GetForegroundWindow.restype=w.HWND
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
    k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    k.QueryFullProcessImageNameW.restype=w.BOOL
    janelas=[]
    @callback_tipo
    def visitar(hwnd,param):
        titulo=ctypes.create_unicode_buffer(256);u.GetWindowTextW(hwnd,titulo,256)
        if titulo.value!='AikaClient':return True
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        handle=k.OpenProcess(0x1000,False,pid.value)
        if handle:
            try:
                caminho=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(caminho))
                if k.QueryFullProcessImageNameW(handle,0,caminho,ctypes.byref(n)):
                    janelas.append(dict(hwnd=hwnd,pid=pid.value,caminho=caminho.value))
            finally:k.CloseHandle(handle)
        return True
    if not u.EnumWindows(visitar,0):raise RuntimeError('Nao foi possivel enumerar as janelas do Aika.')
    return [j for j in janelas if PureWindowsPath(j['caminho']).name.lower() in EXECUTAVEIS]


def localizar_cliente(u=None,k=None):
    u=u or ctypes.WinDLL('user32',use_last_error=True)
    janelas=enumerar_clientes(u,k)
    return escolher_janela(janelas,u.GetForegroundWindow(),int(os.environ.get('AIKA_CLIENT_PID','0')),int(os.environ.get('AIKA_CLIENT_HWND','0')))


def configurar_cliente(perfil):
    """Compartilha a escolha entre leitores, capturas e etapas da DG no mesmo processo."""
    os.environ['AIKA_CLIENT_PID']=str(perfil.get('client_pid',0))
    os.environ['AIKA_CLIENT_HWND']=str(perfil.get('client_hwnd',0))


def janela_em_foco(u,hwnd):
    """Um titulo igual em outra conta nao autoriza enviar teclas para ela."""
    return bool(hwnd) and u.GetForegroundWindow()==hwnd
