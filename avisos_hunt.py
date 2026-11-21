"""Reconhece convites CTE/Elter e a janela Social com conversa aberta."""
from pathlib import Path
import cv2,numpy as np
from aviso_elter import DetectorElter
P=Path(__file__).resolve().parent/'dados'
ESCALAS=(1.,.8,.9,1.1,1.25,1.5)

def melhor(im,tpl):
    if im.shape[0]<tpl.shape[0] or im.shape[1]<tpl.shape[1]:return -1,(0,0)
    r=cv2.matchTemplate(im,tpl,cv2.TM_CCOEFF_NORMED)
    _,score,_,pos=cv2.minMaxLoc(np.nan_to_num(r,nan=-1))
    return score,pos

class DetectorConversa:
    def __init__(self):
        nomes=['titulo','conversa','fechar']
        self.templates=[cv2.imread(str(P/('tpl_social_'+n+'.png')),0) for n in nomes]
        if any(t is None for t in self.templates):raise ValueError('Templates da conversa ausentes')
        self.escalas=[(s,[cv2.GaussianBlur(cv2.resize(t,None,fx=s,fy=s,interpolation=cv2.INTER_LINEAR),(3,3),0) for t in self.templates]) for s in ESCALAS]
    def localizar(self,tela):
        g=cv2.GaussianBlur(cv2.cvtColor(tela,cv2.COLOR_BGR2GRAY),(3,3),0)
        for s,(titulo,conversa,fechar) in self.escalas:
            score,(x,y)=melhor(g,titulo)
            if score<.90:continue
            # Confirma a faixa "Janela de Conversa" e o X da mesma janela.
            x1,y1=max(0,x-round(110*s)),max(0,y+round(25*s))
            roi=g[y1:y+round(61*s),x1:x+round(100*s)]
            if melhor(roi,conversa)[0]<.88:continue
            x2,y2=max(0,x+round(170*s)),max(0,y-round(5*s))
            roi=g[y2:y+round(25*s),x2:x+round(210*s)]
            score,(bx,by)=melhor(roi,fechar)
            if score<.90:continue
            return (x2+bx+fechar.shape[1]//2,y2+by+fechar.shape[0]//2)
        return None

class DetectorAvisos:
    def __init__(self):
        from dialogos_evento import DetectorEventos
        self.elter=DetectorElter();self.conversa=DetectorConversa();self.eventos=DetectorEventos()
    def localizar(self,tela,ao_bloquear=None):
        ponto=self.elter.localizar(tela)
        if ponto:
            if ao_bloquear:ao_bloquear()
            return dict(tipo='cte_elter',ponto=ponto)
        evento=self.eventos.localizar(tela,ao_bloquear)
        if evento:return evento
        ponto=self.conversa.localizar(tela)
        if ponto:
            if ao_bloquear:ao_bloquear()
            return dict(tipo='conversa_amigo',ponto=ponto)
        return None

def reconfirmar(aviso):
    # MSS e local a esta thread; nao reutiliza a captura da thread observadora.
    import mss
    from captura_aika import CapturaAika
    with (getattr(mss,'MSS',None) or mss.mss)() as sct:
        cap=CapturaAika(sct);tela=cap.capturar();ponto=None
        if aviso['tipo']=='cte_elter' and 'referencia' not in aviso:ponto=DetectorElter().localizar(tela)
        elif aviso['tipo']=='conversa_amigo':ponto=DetectorConversa().localizar(tela)
        elif aviso['tipo'] in ('cte_elter','arena_elter') and 'referencia' in aviso:
            from dialogos_evento import DetectorEventos
            ponto=DetectorEventos().reconfirmar(tela,aviso)
        if ponto:
            x,y=ponto;return (cap.area['left']+x,cap.area['top']+y)
    return None
