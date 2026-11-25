"""Reconhece o Altar da Ascensao e a escolha Dificil/Hard por texto."""
import cv2,numpy as np
from huntingaitan.rotas.interface_mina import InterfaceMina
from huntingaitan.visao.dialogos_evento import normalizar
from huntingaitan.recursos import DADOS


class InterfaceJardim(InterfaceMina):
    def __init__(self,ocr=None):
        super().__init__(ocr)
        for n in ('dificil','altar_bin'):
            self.tpl['jardim_'+n]=cv2.imread(str(DADOS/f'tpl_jardim_{n}.png'),0)
            if self.tpl['jardim_'+n] is None:raise RuntimeError('Modelo da entrada do Jardim ausente: '+n)

    def textos_regiao(self,tela,roi):
        x0,y0,x1,y1=map(round,roi);h,w=tela.shape[:2]
        x0,y0=max(0,x0),max(0,y0);x1,y1=min(w,x1),min(h,y1)
        if x1<=x0 or y1<=y0:return []
        return [dict(t,ponto=(t['ponto'][0]+x0,t['ponto'][1]+y0)) for t in self.textos(tela[y0:y1,x0:x1])]

    def reconfirmar(self,tela,acao,selecionado=False):
        # Reconfirma apenas o texto ja reconhecido; evita outro OCR completo
        # entre reconhecer um botao e clicar nele.
        if 'ponto' not in acao:return dict(acao='aguardar_portal')
        x,y=acao['ponto'];cache=getattr(self,'_controle',None)
        if cache is None or cache['acao']!=acao['acao']:return self.entrada(tela,selecionado)
        h,w=tela.shape[:2];x0,y0=max(0,x-42),max(0,y-15);x1,y1=min(w,x+42),min(h,y+15)
        g=cv2.cvtColor(tela[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
        modelo=cache['modelo']
        if g.shape[0]<modelo.shape[0] or g.shape[1]<modelo.shape[1]:return dict(acao='aguardar_portal')
        _,score,_,p=cv2.minMaxLoc(cv2.matchTemplate(g,modelo,cv2.TM_CCOEFF_NORMED))
        if score<.90:return dict(acao='aguardar_portal')
        return dict(acao,ponto=(x0+p[0]+modelo.shape[1]//2,y0+p[1]+modelo.shape[0]//2))

    def textos(self,tela):
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False)
        fator=max(1.,min(2.,1600/tela.shape[1]))
        linhas,_=self.ocr(cv2.resize(tela,None,fx=fator,fy=fator))
        resultado=[]
        for caixa,texto,score in linhas or []:
            c=np.asarray(caixa,dtype=float)/fator
            if float(score)>=.8 and c.shape==(4,2) and np.isfinite(c).all():
                resultado.append(dict(nome=normalizar(texto),ponto=tuple(map(lambda v:round(float(v)),c.mean(axis=0)))))
        return resultado

    def entrada(self,tela,elite_selecionado=False):
        acao=self._entrada(tela,elite_selecionado)
        if 'ponto' in acao:
            x,y=acao['ponto'];h,w=tela.shape[:2]
            if 36<=x<w-36 and 9<=y<h-9:
                self._controle=dict(acao=acao['acao'],modelo=cv2.cvtColor(tela[y-9:y+9,x-36:x+36],cv2.COLOR_BGR2GRAY).copy())
        return acao

    def grupo_por_texto(self,textos,w,h):
        titulo=next((t for t in textos if t['nome'] in {'grupodemazmorra','grupodecalabouco','dungeongroup','dungeonparty','partydungeon'}),None)
        if titulo:
            x,y=titulo['ponto']
            botao=next((t for t in textos if t['nome'] in {'entrar','enter','ingresar'}
                and abs(t['ponto'][0]-x)<w*.3 and h*.15<t['ponto'][1]-y<h*.65),None)
            return dict(acao='entrar_grupo_mazmorra',ponto=botao['ponto']) if botao else dict(acao='aguardar_mazmorra')
        return None

    def _entrada(self,tela,elite_selecionado=False):
        # A assinatura comum permite reaproveitar o controlador de entrada;
        # o booleano significa que a dificuldade desejada ja foi selecionada.
        h,w=tela.shape[:2]
        titulo=self.achar(tela,'titulo_calabouco',roi=(w*.12,h*.08,w*.88,h*.85),limiar=.92)
        textos=[]
        if not titulo:
            grupo=self.achar(tela,'titulo_mazmorra',roi=(w*.12,h*.08,w*.88,h*.85),limiar=.92)
            if grupo:
                x,y=grupo['ponto'];s=grupo['escala']
                botao=self.achar(tela,'entrar_mazmorra',(x-260*s,y+220*s,x+260*s,y+520*s),.89)
                if botao:return dict(acao='entrar_grupo_mazmorra',ponto=botao['ponto'])
                textos_grupo=self.textos_regiao(tela,(w*.15,h*.1,w*.85,h*.87))
                return self.grupo_por_texto(textos_grupo,w,h) or dict(acao='aguardar_mazmorra')
        if titulo:
            x,y=titulo['ponto'];s=titulo['escala']
            roi=(x-330*s,y+12*s,x+330*s,y+610*s)
            botao=self.achar(tela,'entrar' if elite_selecionado else 'jardim_dificil',roi,.88)
            if botao:return dict(acao='confirmar_calabouco' if elite_selecionado else 'selecionar_dificil',ponto=botao['ponto'])
            textos=self.textos_regiao(tela,roi)
            candidatos=[t for t in textos if abs(t['ponto'][0]-x)<330*s and 12*s<t['ponto'][1]-y<610*s]
            nomes={'entrar','enter','ingresar','aceptar','confirmar','confirm'} if elite_selecionado else {'dificil','diffcil','difficil','hard'}
            b=next((t for t in candidatos if t['nome'] in nomes),None)
            if b:return dict(acao='confirmar_calabouco' if elite_selecionado else 'selecionar_dificil',ponto=b['ponto'])
            return dict(acao='aguardar_calabouco')
        textos=self.textos_regiao(tela,(w*.15,h*.1,w*.85,h*.87))
        grupo_texto=self.grupo_por_texto(textos,w,h)
        if grupo_texto:return grupo_texto
        # Pode estar em outro idioma ou ter escala sem modelo correspondente.
        titulo_texto=next((t for t in textos if t['nome'] in {'calaboucoinstantaneo','instantdungeon','dungeon','calabozo'}),None)
        if titulo_texto:
            x,y=titulo_texto['ponto']
            nomes={'entrar','enter','ingresar','confirmar','confirm'} if elite_selecionado else {'dificil','diffcil','difficil','hard'}
            b=next((t for t in textos if t['nome'] in nomes and abs(t['ponto'][0]-x)<w*.3 and y<t['ponto'][1]<y+h*.55),None)
            if b:return dict(acao='confirmar_calabouco' if elite_selecionado else 'selecionar_dificil',ponto=b['ponto'])
            return dict(acao='aguardar_calabouco')
        for t in textos:
            n=t['nome']
            if any(v in n for v in ('jardim','aviary','jardinceleste','jardinaereo')) and any(v in n for v in ('entrar','enter','ingresar','entrance')):
                return dict(acao='entrar_jardim',ponto=t['ponto'])
        for t in textos:
            if t['nome'] in {'altardaascensao','altardaascensio','altardeascension','altardelaascension','altarofascension','ascensionaltar'}:
                return dict(acao='abrir_portal',ponto=t['ponto'],duplo=True)
        if getattr(self,'_controle',None) is None:
            altar=self.achar(tela,'jardim_altar_bin',limiar=.86,binario='verde')
            if altar:return dict(acao='abrir_portal',ponto=altar['ponto'],duplo=True)
        return dict(acao='aguardar_portal')
