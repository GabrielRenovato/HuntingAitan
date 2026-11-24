"""Captura o HWND do cliente por Windows Graphics Capture, mesmo coberto por outra janela."""
import ctypes,threading,time
from ctypes import wintypes as w


class CapturaJanela:
    from huntingaitan.visao.captura_aika import CapturaAika
    pixels_fisicos=CapturaAika.pixels_fisicos
    def __init__(self,hwnd,pid):
        self.hwnd=hwnd;self.pid=pid;self.lock=threading.Lock();self.pronta=threading.Event()
        self.imagem=None;self.quando=0.;self.fechada=False;self.controle=None
        self.u=ctypes.WinDLL('user32',use_last_error=True)
        self.u.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
        self.u.ClientToScreen.argtypes=[w.HWND,ctypes.POINTER(w.POINT)]
        self.u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
        self.u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        self.u.IsIconic.argtypes=[w.HWND]

    def validar(self):
        pid=w.DWORD();self.u.GetWindowThreadProcessId(self.hwnd,ctypes.byref(pid))
        if pid.value!=self.pid or self.fechada:raise RuntimeError('Janela de captura fechada ou substituida')
        if self.u.IsIconic(self.hwnd):raise RuntimeError('Restaure o Aika; a captura ao fundo precisa da janela aberta')

    def __enter__(self):
        from windows_capture import WindowsCapture
        self.validar()
        self.captura=WindowsCapture(window_hwnd=self.hwnd,cursor_capture=False,minimum_update_interval=100)
        @self.captura.event
        def on_frame_arrived(frame,control):
            with self.lock:
                self.imagem=frame.frame_buffer[:,:,:3].copy();self.quando=time.monotonic()
            self.pronta.set()
        @self.captura.event
        def on_closed():
            self.fechada=True;self.pronta.set()
        self.controle=self.captura.start_free_threaded()
        return self

    def __exit__(self,*args):
        if self.controle:self.controle.stop();self.controle=None

    def capturar(self):
        with self.pixels_fisicos():return self._capturar()

    def _capturar(self):
        self.validar()
        if not self.pronta.wait(5):raise RuntimeError('Captura da janela nao respondeu')
        with self.lock:
            if self.imagem is None or time.monotonic()-self.quando>3:raise RuntimeError('Imagem do Aika parou de atualizar')
            imagem=self.imagem.copy()
        # WGC devolve a janela toda; os detectores do projeto usam a area cliente.
        r=w.RECT();origem=w.POINT();externa=w.RECT()
        self.u.GetClientRect(self.hwnd,ctypes.byref(r));self.u.ClientToScreen(self.hwnd,ctypes.byref(origem));self.u.GetWindowRect(self.hwnd,ctypes.byref(externa))
        self.area=dict(left=origem.x,top=origem.y,width=r.right,height=r.bottom)
        if imagem.shape[:2]!=(r.bottom,r.right):
            dwm=ctypes.WinDLL('dwmapi');dwm.DwmGetWindowAttribute.argtypes=[w.HWND,w.DWORD,ctypes.c_void_p,w.DWORD]
            dwm.DwmGetWindowAttribute(self.hwnd,9,ctypes.byref(externa),ctypes.sizeof(externa))
            x,y=origem.x-externa.left,origem.y-externa.top
            if min(x,y)<0 or x+r.right>imagem.shape[1] or y+r.bottom>imagem.shape[0]:raise RuntimeError('Area cliente nao corresponde a captura da janela')
            imagem=imagem[y:y+r.bottom,x:x+r.right].copy()
        if imagem.size==0 or imagem.std()<1:raise RuntimeError('Captura da janela vazia; teclas suspensas')
        return imagem
