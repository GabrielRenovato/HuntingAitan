"""Reconhece duas partes do passe antes de autorizar um toque em ESC."""
import cv2
from huntingaitan.recursos import DADOS


class DetectorSeasonPass:
    def __init__(self):
        self.templates = []
        titulo = cv2.imread(str(DADOS / 'tpl_season_titulo.png'), 0)
        abas = cv2.imread(str(DADOS / 'tpl_season_abas.png'), 0)
        if titulo is None or abas is None:
            raise ValueError('Templates do Season Pass ausentes')
        for escala in (1., .8, .9, 1.1, 1.25, 1.5, 1.75, 2.):
            self.templates.append((escala, cv2.resize(titulo, None, fx=escala, fy=escala),
                                   cv2.resize(abas, None, fx=escala, fy=escala)))

    def localizar(self, tela):
        from huntingaitan.visao.avisos_hunt import melhor
        cinza = cv2.cvtColor(tela, cv2.COLOR_BGR2GRAY)
        for escala, titulo, abas in self.templates:
            score, (x, y) = melhor(cinza, titulo)
            if score < .92:
                continue
            ax, ay = x + round(133 * escala), y + round(87 * escala)
            roi = cinza[max(0, ay-4):ay+abas.shape[0]+5, max(0, ax-4):ax+abas.shape[1]+5]
            if melhor(roi, abas)[0] >= .90:
                return (x + titulo.shape[1]//2, y + titulo.shape[0]//2)
        return None


def fechar_com_escape(entrada, ativo, esperar):
    """Chamado somente apos reconfirmar visualmente o passe no cliente correto."""
    if not ativo():
        return False
    try:
        return entrada.keyDown('esc') is not False
    finally:
        try:
            esperar(.045)
        finally:
            entrada.keyUp('esc')
