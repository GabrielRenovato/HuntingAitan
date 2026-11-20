"""Captura a area cliente do Aika em coordenadas fisicas, em qualquer monitor."""
import ctypes
from contextlib import contextmanager
from ctypes import wintypes as w
import numpy as np

def validar_area(esquerda,topo,direita,baixo):
    largura=direita-esquerda;altura=baixo-topo
    if largura<640 or altura<480:raise ValueError('Janela do Aika minimizada ou pequena demais')
    return dict(left=esquerda,top=topo,width=largura,height=altura)

class CapturaAika:
    def __init__(self,sct):
        self.sct=sct;self.u=ctypes.windll.user32
        self.u.FindWindowW.argtypes=[w.LPCWSTR,w.LPCWSTR];self.u.FindWindowW.restype=w.HWND
        self.u.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
        self.u.ClientToScreen.argtypes=[w.HWND,ctypes.POINTER(w.POINT)]
        self.area=None
    @contextmanager
    def pixels_fisicos(self):
        # O contexto do processo pode ter sido definido por uma biblioteca
        # de entrada antes do MSS. Usa DPI por monitor apenas nesta captura
        # e restaura o contexto da thread ao terminar.
        ajustar=getattr(self.u,'SetThreadDpiAwarenessContext',None);anterior=None
        if ajustar is not None:
            ajustar.argtypes=[ctypes.c_void_p];ajustar.restype=ctypes.c_void_p
            anterior=ajustar(ctypes.c_void_p(-4)) or ajustar(ctypes.c_void_p(-3))
        try:yield
        finally:
            if anterior:ajustar(anterior)

    def regiao(self):
        with self.pixels_fisicos():return self._regiao()

    def _regiao(self):
        h=self.u.FindWindowW(None,'AikaClient')
        if not h:raise ValueError('Janela AikaClient nao encontrada')
        if self.u.IsIconic(h):raise ValueError('Aika minimizado')
        r=w.RECT();origem=w.POINT(0,0)
        if not self.u.GetClientRect(h,ctypes.byref(r)) or not self.u.ClientToScreen(h,ctypes.byref(origem)):
            raise OSError('Nao consegui ler a area cliente do Aika')
        self.area=validar_area(origem.x,origem.y,origem.x+r.right,origem.y+r.bottom)
        return self.area
    def capturar(self):
        with self.pixels_fisicos():return np.array(self.sct.grab(self._regiao()))[:,:,:3]
