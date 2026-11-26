"""Teclas destinadas ao HWND validado, sem teclado ou mouse globais."""
import ctypes
from contextlib import contextmanager
from ctypes import wintypes as w
from huntingaitan.entrada import layout_teclado


def codigo_tecla(tecla):
    tecla=str(tecla).lower()
    if len(tecla)==1 and tecla.isascii() and tecla.isalnum():return ord(tecla.upper())
    if tecla.startswith('f') and tecla[1:].isdigit() and 1<=int(tecla[1:])<=11:return 111+int(tecla[1:])
    especiais={'tab':9,'enter':13,'space':32,'esc':27,"'":0xde}
    if tecla in especiais:return especiais[tecla]
    raise ValueError('Segundo plano aceita teclas simples; atalho nao suportado: '+tecla)


class EntradaJanela:
    PAUSE=0
    def __init__(self,hwnd,pid,u=None):
        self.hwnd=hwnd;self.pid=pid;self.u=u or ctypes.WinDLL('user32',use_last_error=True);self.pressionadas=set()
        self.posicao=None;self.botoes=set();self.vk_layout={}
        if u is None:
            self.u.IsWindow.argtypes=[w.HWND]
            self.u.IsIconic.argtypes=[w.HWND]
            self.u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
            self.u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];self.u.PostMessageW.restype=w.BOOL
            self.u.GetAsyncKeyState.argtypes=[ctypes.c_int];self.u.GetAsyncKeyState.restype=ctypes.c_short
            self.u.MapVirtualKeyW.argtypes=[w.UINT,w.UINT];self.u.MapVirtualKeyW.restype=w.UINT
            self.u.ScreenToClient.argtypes=[w.HWND,ctypes.POINTER(w.POINT)]
            self.u.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]

    def validar(self):
        pid=w.DWORD();self.u.GetWindowThreadProcessId(self.hwnd,ctypes.byref(pid))
        if not self.u.IsWindow(self.hwnd) or pid.value!=self.pid:
            raise RuntimeError('Cliente do segundo plano foi fechado ou mudou; teclas suspensas')

    @contextmanager
    def pixels_fisicos(self):
        ajustar=getattr(self.u,'SetThreadDpiAwarenessContext',None);anterior=None
        if ajustar:
            ajustar.argtypes=[ctypes.c_void_p];ajustar.restype=ctypes.c_void_p
            anterior=ajustar(ctypes.c_void_p(-4))
        try:yield
        finally:
            if anterior:ajustar(anterior)

    def modificadores_livres(self):
        return not any(self.u.GetAsyncKeyState(k)&0x8000 for k in (0x10,0x11,0x12))

    def disponivel(self):
        return self.motivo_indisponivel() is None

    def motivo_indisponivel(self):
        self.validar()
        if self.u.IsIconic(self.hwnd):return 'Segundo plano pausado: o Windows minimizou o Aika. Restaure a janela do jogo.'
        modificadores=[nome for vk,nome in ((0x10,'Shift'),(0x11,'Ctrl'),(0x12,'Alt')) if self.u.GetAsyncKeyState(vk)&0x8000]
        if modificadores:return 'Segundo plano pausado: '+', '.join(modificadores)+' pressionado. Solte para retomar.'
        return None

    def vk(self,tecla):
        """VK da tecla; pontuacao (apostrofo) segue o layout de teclado do cliente (ABNT2: 192, americano: 222)."""
        tecla=str(tecla).lower()
        if tecla not in layout_teclado.PADRAO:return codigo_tecla(tecla)
        if tecla not in self.vk_layout:self.vk_layout[tecla]=layout_teclado.vk_da_tecla(self.u,self.hwnd,tecla)
        return self.vk_layout[tecla]

    def keyDown(self,tecla,_pause=False):
        vk=self.vk(tecla);self.validar()
        if not self.modificadores_livres():return False
        lp=1|(self.u.MapVirtualKeyW(vk,0)<<16)
        if vk in self.pressionadas:lp|=1<<30
        if not self.u.PostMessageW(self.hwnd,0x100,vk,lp):
            raise RuntimeError('Windows recusou tecla destinada ao Aika')
        self.pressionadas.add(vk);return True

    def keyUp(self,tecla,_pause=False):
        vk=self.vk(tecla)
        try:self.validar()
        except RuntimeError:return False
        lp=1|(self.u.MapVirtualKeyW(vk,0)<<16)|0xc0000000
        if not self.u.PostMessageW(self.hwnd,0x101,vk,lp):return False
        self.pressionadas.discard(vk);return True

    def mover_sem_cursor(self,x,y):
        self.validar();p=w.POINT(round(x),round(y));r=w.RECT()
        self.posicao=None
        with self.pixels_fisicos():
            if not self.u.ScreenToClient(self.hwnd,ctypes.byref(p)) or not self.u.GetClientRect(self.hwnd,ctypes.byref(r)):return False
        if not 0<=p.x<r.right or not 0<=p.y<r.bottom:return False
        self.posicao=(p.y<<16)|p.x
        flags=(1 if 'left' in self.botoes else 0)|(2 if 'right' in self.botoes else 0)
        return bool(self.u.PostMessageW(self.hwnd,0x200,flags,self.posicao))

    moveTo=mover_sem_cursor

    def mouseDown(self,button='left',duplo=False):
        self.validar()
        if self.posicao is None:raise RuntimeError('Posicao do clique na janela indisponivel')
        if button not in ('left','right'):raise ValueError('Botao nao suportado')
        self.botoes.add(button);flags=(1 if 'left' in self.botoes else 0)|(2 if 'right' in self.botoes else 0)
        mensagem=(0x203 if button=='left' else 0x206) if duplo else (0x201 if button=='left' else 0x204)
        if not self.u.PostMessageW(self.hwnd,mensagem,flags,self.posicao):raise RuntimeError('Clique na janela recusado')
        return True

    def mouseUp(self,button='left'):
        if button not in self.botoes:return True
        self.validar();self.botoes.discard(button)
        flags=(1 if 'left' in self.botoes else 0)|(2 if 'right' in self.botoes else 0)
        return bool(self.u.PostMessageW(self.hwnd,0x202 if button=='left' else 0x205,flags,self.posicao))
