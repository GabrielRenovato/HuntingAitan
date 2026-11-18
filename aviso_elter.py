"""Reconhece apenas o convite da escola de Elter e seu botao Cancelar."""
from pathlib import Path
import cv2,numpy as np
P=Path(__file__).resolve().parent

class DetectorElter:
    def __init__(self):
        self.titulo=cv2.imread(str(P/'tpl_elter_titulo.png'),0)
        self.cancelar=cv2.imread(str(P/'tpl_elter_cancelar.png'),0)
        if self.titulo is None or self.cancelar is None:raise ValueError('Templates Elter ausentes')
        self.escalas=[(s,cv2.resize(self.titulo,None,fx=s,fy=s),cv2.resize(self.cancelar,None,fx=s,fy=s)) for s in (1.,.8,.9,1.1,1.25,1.5)]
    def localizar(self,tela):
        for escala,titulo,cancelar in self.escalas:
            ponto=self._localizar(tela,escala,titulo,cancelar)
            if ponto:return ponto
        return None
    def _localizar(self,tela,escala,titulo,cancelar):
        g=cv2.cvtColor(tela,cv2.COLOR_BGR2GRAY)
        if g.shape[0]<round(230*escala) or g.shape[1]<round(295*escala):return None
        r=cv2.matchTemplate(g,titulo,cv2.TM_CCOEFF_NORMED)
        _,score,_,(x,y)=cv2.minMaxLoc(np.nan_to_num(r,nan=-1))
        if score<.90:return None
        # Cancelar fica a direita, 192px abaixo do titulo; confirma o botao.
        ox,oy=x+round(155*escala),y+round(180*escala)
        recorte=g[max(0,oy):oy+round(50*escala),max(0,ox):ox+round(115*escala)]
        if recorte.shape[0]<cancelar.shape[0] or recorte.shape[1]<cancelar.shape[1]:return None
        r=cv2.matchTemplate(recorte,cancelar,cv2.TM_CCOEFF_NORMED)
        _,score,_,p=cv2.minMaxLoc(np.nan_to_num(r,nan=-1))
        if score<.90:return None
        return (ox+p[0]+cancelar.shape[1]//2,oy+p[1]+cancelar.shape[0]//2)
