"""Captura de etapas de interface, isolada na janela escolhida ao fundo."""
from contextlib import contextmanager

@contextmanager
def captura_interface(dados,segundo_plano,mss,normal):
    if segundo_plano:
        from huntingaitan.visao.captura_janela import CapturaJanela
        with CapturaJanela(dados.hwnd,dados.pid) as cap:yield cap
    else:
        with (getattr(mss,'MSS',None) or mss.mss)() as sct:yield normal(sct)
