"""Ritmo de repeticao regular, sem depender de um perfil externo de mouse."""
import ctypes
from ctypes import wintypes as w


def intervalo_por_velocidade(velocidade):
    if not 0<=velocidade<=31:raise ValueError('Velocidade do teclado fora do intervalo')
    # Estimativa documentada pelo Windows: 2,5 a 30 repeticoes/s.
    return 1/(2.5+27.5*velocidade/31)


def ler_velocidade_windows():
    valor=w.DWORD()
    try:
        consultar=ctypes.windll.user32.SystemParametersInfoW
        consultar.argtypes=[w.UINT,w.UINT,ctypes.c_void_p,w.UINT];consultar.restype=w.BOOL
        if consultar(0x000A,0,ctypes.byref(valor),0) and valor.value<=31:return int(valor.value)
    except (AttributeError,OSError):pass
    return None


def configurar_ritmo(perfil,consulta=None):
    pausa=float(perfil.get('combo_key_delay_ms',0))/1000
    repeticao=float(perfil.get('combo_repeat_ms',0))/1000
    velocidade=None;origem='configurado'
    if repeticao==0:
        velocidade=(consulta or ler_velocidade_windows)()
        repeticao=intervalo_por_velocidade(velocidade) if velocidade is not None else 1/30
        origem='windows_estimado' if velocidade is not None else 'padrao_30hz'
    return dict(pausa_teclas=pausa,intervalo_repeticao=repeticao,origem=origem,velocidade_windows=velocidade)
