"""Reconhece convites por dois botoes e texto permitido; nao usa horario fixo."""
from huntingaitan.recursos import DADOS
from pathlib import Path
import re,unicodedata
import cv2,numpy as np

P=DADOS
ESCALAS=(1.,.8,.9,1.1,1.25,1.5,1.75,2.)

def normalizar(texto):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',texto.lower()).encode('ascii','ignore').decode())

def tipo_convite(textos):
    texto=normalizar(' '.join(t for t,score in textos if score>=.72))
    evento=any(t in texto for t in ['comecaraembreve','temporestante','paraentrar','aguardando'])
    if 'arenaelter' in texto and evento:return 'arena_elter'
    if 'elter' in texto and 'treinamento' in texto and evento:return 'cte_elter'
    return None

class DetectorEventos:
    def __init__(self,ocr=None):
        self.ocr=ocr
        cancelar=cv2.imread(str(P/'tpl_elter_cancelar.png'),0)
        confirmar=cv2.imread(str(P/'tpl_elter_confirmar.png'),0)
        if cancelar is None or confirmar is None:raise ValueError('Botoes de convite ausentes')
        self.templates=[(s,cv2.resize(cancelar,None,fx=s,fy=s),cv2.resize(confirmar,None,fx=s,fy=s)) for s in ESCALAS]
        self.cache=None

    def preparar_ocr(self):
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1)

    def candidatos(self,tela):
        g=cv2.cvtColor(tela,cv2.COLOR_BGR2GRAY)
        pequeno=cv2.resize(g,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
        candidatos=[]
        for escala,cancelar,confirmar in self.templates:
            tpl=cv2.resize(cancelar,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
            if pequeno.shape[0]<tpl.shape[0] or pequeno.shape[1]<tpl.shape[1]:continue
            scores=cv2.matchTemplate(pequeno,tpl,cv2.TM_CCOEFF_NORMED)
            scores=np.nan_to_num(scores,nan=-1)
            for _ in range(3):
                _,score,_,(cx,cy)=cv2.minMaxLoc(scores)
                if score<.67:break
                scores[max(0,cy-tpl.shape[0]):cy+tpl.shape[0],max(0,cx-tpl.shape[1]):cx+tpl.shape[1]]=-1
                x0,y0=max(0,cx*2-5),max(0,cy*2-5)
                roi=g[y0:min(g.shape[0],cy*2+cancelar.shape[0]+6),x0:min(g.shape[1],cx*2+cancelar.shape[1]+6)]
                if roi.shape[0]<cancelar.shape[0] or roi.shape[1]<cancelar.shape[1]:continue
                _,preciso,_,(dx,dy)=cv2.minMaxLoc(np.nan_to_num(cv2.matchTemplate(roi,cancelar,cv2.TM_CCOEFF_NORMED),nan=-1))
                if preciso<.89:continue
                x,y=x0+dx,y0+dy
                esquerda,topo=max(0,x-round(190*escala)),max(0,y-round(12*escala))
                r=g[topo:min(g.shape[0],y+confirmar.shape[0]+round(12*escala)),esquerda:max(0,x-round(10*escala))]
                if r.shape[0]<confirmar.shape[0] or r.shape[1]<confirmar.shape[1]:continue
                _,score,_,(bx,by)=cv2.minMaxLoc(np.nan_to_num(cv2.matchTemplate(r,confirmar,cv2.TM_CCOEFF_NORMED),nan=-1))
                # O redimensionamento do HUD desloca bordas em subpixels.
                # Cancelar permanece mais estrito e o texto e validado por OCR.
                if score<.80:continue
                ponto=(x+cancelar.shape[1]//2,y+cancelar.shape[0]//2)
                if any(np.linalg.norm(np.subtract(ponto,a['ponto']))<12 for a in candidatos):continue
                ex,ey=max(0,esquerda+bx-round(55*escala)),max(0,y-round(260*escala))
                direita=min(g.shape[1],x+cancelar.shape[1]+round(55*escala))
                candidatos.append(dict(ponto=ponto,caixa=(ex,ey,direita-ex,max(1,y-ey-3)),escala=escala))
        return candidatos

    @staticmethod
    def comparar(tela,candidato,referencia):
        x,y,w,h=candidato['caixa'];atual=cv2.cvtColor(tela[y:y+h,x:x+w],cv2.COLOR_BGR2GRAY)
        # Se a janela saiu da borda da tela, a margem acima pode ter crescido.
        # A referencia continua alinhada aos botoes, pela borda inferior/direita.
        altura=min(atual.shape[0],referencia.shape[0]);largura=min(atual.shape[1],referencia.shape[1])
        if altura<100 or largura<140:return False
        atual=atual[-altura:,-largura:];referencia=referencia[-altura:,-largura:]
        if referencia.std()<2:return False
        score=cv2.matchTemplate(atual,referencia,cv2.TM_CCOEFF_NORMED)[0,0]
        return bool(np.isfinite(score) and score>=.88)

    def localizar(self,tela,ao_bloquear=None):
        candidatos=self.candidatos(tela)
        if not candidatos:return None
        if ao_bloquear:ao_bloquear()
        for candidato in candidatos:
            if self.cache and self.comparar(tela,candidato,self.cache['referencia']):
                return dict(self.cache,**candidato)
            x,y,w,h=candidato['caixa'];crop=tela[y:y+h,x:x+w]
            self.preparar_ocr()
            linhas,_=self.ocr(crop)
            tipo=tipo_convite([(l[1],float(l[2])) for l in linhas or []])
            if tipo:
                aviso=dict(candidato,tipo=tipo,referencia=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY).copy())
                self.cache=aviso;return aviso
        return dict(candidatos[0],tipo='janela_desconhecida')

    def reconfirmar(self,tela,aviso):
        if aviso.get('tipo') not in ('cte_elter','arena_elter') or 'referencia' not in aviso:return None
        for candidato in self.candidatos(tela):
            if self.comparar(tela,candidato,aviso['referencia']):return candidato['ponto']
        return None
