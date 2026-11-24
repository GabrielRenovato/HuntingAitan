"""Teclas de pontuacao dependem do layout do teclado do cliente.

No ABNT2 o apostrofo (') e a tecla VK 192 e o VK 222 e o til (~); no layout americano e o contrario. O cliente do Aika
guarda o VK na tabela de atalhos, entao tanto o envio quanto a leitura da barra resolvem o VK pelo layout da janela."""
import ctypes
from ctypes import wintypes as w

PADRAO={"'":0xde}
MAPVK_VK_TO_CHAR=2


def layout_da_janela(u,hwnd):
    u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.GetWindowThreadProcessId.restype=w.DWORD
    u.GetKeyboardLayout.argtypes=[w.DWORD];u.GetKeyboardLayout.restype=ctypes.c_void_p
    return u.GetKeyboardLayout(u.GetWindowThreadProcessId(hwnd,None))


def vk_da_tecla(u,hwnd,tecla,padrao=None):
    """VK que produz `tecla` sem modificador no layout da janela; `padrao` (layout americano) se nao der para resolver."""
    padrao=PADRAO.get(tecla) if padrao is None else padrao
    try:
        u.VkKeyScanExW.argtypes=[ctypes.c_wchar,ctypes.c_void_p];u.VkKeyScanExW.restype=ctypes.c_short
        r=u.VkKeyScanExW(tecla,layout_da_janela(u,hwnd))
    except Exception:return padrao
    if not isinstance(r,int) or r==-1:return padrao
    vk,estado=r&0xff,(r>>8)&0xff
    return padrao if vk==0xff or estado else vk


def caractere_do_vk(u,hwnd,vk):
    """Caractere que o VK produz no layout da janela ('' se nao der para resolver ou se for tecla morta)."""
    try:
        u.MapVirtualKeyExW.argtypes=[w.UINT,w.UINT,ctypes.c_void_p];u.MapVirtualKeyExW.restype=w.UINT
        r=u.MapVirtualKeyExW(vk,MAPVK_VK_TO_CHAR,layout_da_janela(u,hwnd))
    except Exception:return ''
    if not isinstance(r,int) or r&0x80000000 or not r&0xffff:return ''
    return chr(r&0xffff)
