"""Libera entradas mantidas mesmo se o fail-safe impedir novas acoes."""
import inspect

def mover_cursor_fisico(entrada,x,y,u=None):
    """Move em pixels fisicos e confere a chegada, inclusive em monitores a esquerda."""
    import ctypes
    from ctypes import wintypes as w
    verificar=getattr(entrada,'failSafeCheck',None)
    if verificar:verificar()
    u=u or ctypes.windll.user32
    ajustar=getattr(u,'SetThreadDpiAwarenessContext',None);anterior=None
    if ajustar:
        ajustar.argtypes=[ctypes.c_void_p];ajustar.restype=ctypes.c_void_p
        anterior=ajustar(ctypes.c_void_p(-4))
    try:
        x,y=round(x),round(y)
        # SetCursorPos sozinho pode deixar a posicao mantida por DirectInput
        # desatualizada. O evento usa o desktop virtual, nao apenas a tela primaria.
        esquerda,topo,largura,altura=(u.GetSystemMetrics(i) for i in (76,77,78,79))
        if largura<=0 or altura<=0 or not esquerda<=x<esquerda+largura or not topo<=y<topo+altura:return False
        class Mouse(ctypes.Structure):
            _fields_=[('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',ctypes.c_size_t)]
        class Uniao(ctypes.Union):
            _fields_=[('mouse',Mouse)]
        class Input(ctypes.Structure):
            _fields_=[('tipo',w.DWORD),('uniao',Uniao)]
        evento=Input(0,Uniao(mouse=Mouse(int((x-esquerda+.5)*65536/largura),int((y-topo+.5)*65536/altura),0,0x8000|0x4000|1,0,0)))
        if u.SendInput(1,ctypes.byref(evento),ctypes.sizeof(evento))!=1:return False
        p=w.POINT()
        return bool(u.GetCursorPos(ctypes.byref(p))) and abs(p.x-round(x))<=1 and abs(p.y-round(y))<=1
    finally:
        if anterior:ajustar(anterior)

def preparar_pressao_sem_pausa(entrada):
    func=entrada.keyDown
    try:suporta='_pause' in inspect.signature(func).parameters
    except (TypeError,ValueError):suporta=False
    # Mantem o wrapper de fail-safe; desativa somente o sleep(PAUSE), que
    # tambem cedia a thread quando PAUSE era zero.
    return (lambda tecla:func(tecla,_pause=False)) if suporta else func

def liberar_tecla(entrada,tecla):
    # O wrapper do PyDirectInput verifica o canto ate no keyUp. A liberacao
    # deve funcionar mesmo quando o canto ja bloqueou o keyDown.
    func=entrada.keyUp
    return getattr(func,'__wrapped__',func)(tecla)

def liberar_mouse(entrada):
    func=entrada.mouseUp
    return getattr(func,'__wrapped__',func)()
