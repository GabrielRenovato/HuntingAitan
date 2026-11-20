"""Reconhece somente controles conhecidos da saida e entrada da Mina."""
from pathlib import Path
import cv2,numpy as np
from avisos_hunt import melhor

P=Path(__file__).resolve().parent
ESCALAS=(1.,.9,1.1,.8,1.25,1.5)

class InterfaceMina:
    def __init__(self):
        nomes=['grupo','sair_grupo','pergunta','confirmar','elite','titulo_calabouco','titulo_mazmorra','entrar','entrar_mazmorra','portal_bin','entrar_mina_bin']
        self.tpl={n:cv2.imread(str(P/f'tpl_mina_{n}.png'),0) for n in nomes}
        if any(t is None for t in self.tpl.values()):raise RuntimeError('Modelos de interface da Mina ausentes.')
        for n in ['confirmar','elite','entrar','entrar_mazmorra']:self.tpl[n]=self.tpl[n][:,15:-15]
        # O fundo e a borda mudam com o realce do botao. Compara a faixa do
        # texto, dentro da janela ja reconhecida, sem depender desse estado.
        self.tpl['entrar_mazmorra']=self.tpl['entrar_mazmorra'][6:21,7:-7]

    def achar(self,tela,nome,roi=None,limiar=.90,binario=None):
        g=cv2.cvtColor(tela,cv2.COLOR_BGR2GRAY) if tela.ndim==3 else tela
        ox=oy=0
        if roi is not None:
            x0,y0,x1,y1=roi;ox,oy=max(0,int(x0)),max(0,int(y0));g=g[oy:max(0,int(y1)),ox:max(0,int(x1))]
        if g.size==0:return None
        if binario=='verde':
            if tela.ndim!=3:return None
            b,v,r=[tela[...,i].astype(int) for i in range(3)];g=((v>170)&(r<130)&(b<130)).astype(np.uint8)*255
        elif binario=='branco':g=(g>210).astype(np.uint8)*255
        for escala in ESCALAS:
            t=cv2.resize(self.tpl[nome],None,fx=escala,fy=escala)
            score,(x,y)=melhor(g,t)
            if score>=limiar:return dict(ponto=(ox+x+t.shape[1]//2,oy+y+t.shape[0]//2),xy=(ox+x,oy+y),escala=escala,score=float(score),tamanho=(t.shape[1],t.shape[0]))
        return None

    def saida(self,tela):
        pergunta=self.achar(tela,'pergunta',limiar=.94)
        if pergunta:
            x,y=pergunta['ponto'];s=pergunta['escala']
            confirmar=self.achar(tela,'confirmar',(x-160*s,y+15*s,x+140*s,y+100*s),.88)
            if confirmar:return dict(acao='confirmar_saida',ponto=confirmar['ponto'],score=confirmar['score'])
            return dict(acao='aguardar_confirmacao')
        sair=self.achar(tela,'sair_grupo',limiar=.92)
        if sair:return dict(acao='sair_grupo',ponto=sair['ponto'],score=sair['score'])
        grupo=self.achar(tela,'grupo',limiar=.90)
        if grupo:
            x,y=grupo['xy'];s=grupo['escala']
            return dict(acao='abrir_menu_grupo',ponto=(round(x+60*s),round(y+32*s)),botao='right',score=grupo['score'])
        return dict(acao='aguardar_saida')

    def entrada(self,tela,elite_selecionado=False):
        grupo=self.achar(tela,'titulo_mazmorra',limiar=.92)
        if grupo:
            x,y=grupo['ponto'];s=grupo['escala']
            botao=self.achar(tela,'entrar_mazmorra',(x-260*s,y+220*s,x+260*s,y+520*s),.89)
            if botao:return dict(acao='entrar_grupo_mazmorra',ponto=botao['ponto'])
            return dict(acao='aguardar_mazmorra')
        titulo=self.achar(tela,'titulo_calabouco',limiar=.92)
        if titulo:
            x,y=titulo['ponto'];s=titulo['escala'];roi=(x-330*s,y+12*s,x+330*s,y+610*s)
            nome='entrar' if elite_selecionado else 'elite';botao=self.achar(tela,nome,roi,.88)
            if botao:return dict(acao='confirmar_calabouco' if elite_selecionado else 'selecionar_elite',ponto=botao['ponto'])
            return dict(acao='aguardar_calabouco')
        menu=self.achar(tela,'entrar_mina_bin',limiar=.88,binario='branco')
        if menu:return dict(acao='entrar_mina_1',ponto=menu['ponto'])
        portal=self.achar(tela,'portal_bin',limiar=.83,binario='verde')
        if portal:return dict(acao='abrir_portal',ponto=portal['ponto'],duplo=True)
        return dict(acao='aguardar_portal')

class VerificadorElite:
    def __init__(self,ocr=None,dificuldade='elite',auto_escala=True):
        self.ocr=ocr;self.dificuldade=dificuldade;self.auto_escala=auto_escala;self.diagnostico={}
    def confirmar(self,tela):
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1)
        from dialogos_evento import normalizar
        h,w=tela.shape[:2]
        areas=[(min(w,480),min(h,480),3.)]
        if self.auto_escala:
            # A primeira leitura preserva o HUD pequeno em qualquer resolucao.
            # A segunda acompanha HUD ampliado; a terceira amplia a busca para
            # um indicador deslocado. Cada recorte e normalizado antes do OCR.
            escala=max(1.,min(3.,h/1080))
            areas.extend([(min(w,round(480*escala)),min(h,round(480*escala)),3/escala),
                          (min(w,max(480,round(w*.4))),min(h,max(480,round(h*.75))),None)])
        vistos=set();self.diagnostico=dict(resolucao=[w,h],automatico=self.auto_escala,tentativas=0,indicador=None,escala_texto=None)
        for largura,altura,fator in areas:
            if (largura,altura) in vistos:continue
            vistos.add((largura,altura));roi=tela[:altura,w-largura:]
            fator=fator or min(3.,1440/max(largura,altura))
            roi=cv2.resize(roi,None,fx=fator,fy=fator,interpolation=cv2.INTER_CUBIC)
            linhas,_=self.ocr(roi);self.diagnostico['tentativas']+=1
            indicadores=[l for l in linhas or [] if normalizar(l[1]) in ('normal','facil','dificil','elite','infernal') and float(l[2])>=.75]
            if not indicadores:continue
            nomes={normalizar(l[1]) for l in indicadores}
            self.diagnostico.update(indicador='/'.join(sorted(nomes)),recorte=[w-largura,0,w,altura])
            if nomes!={self.dificuldade}:return False
            l=max(indicadores,key=lambda l:float(l[2]));caixa=np.asarray(l[0],dtype=float)
            if caixa.shape==(4,2) and np.isfinite(caixa).all():
                altura_texto=(np.linalg.norm(caixa[3]-caixa[0])+np.linalg.norm(caixa[2]-caixa[1]))/2/fator
                self.diagnostico['escala_texto']=round(float(altura_texto)/12,2)
            self.diagnostico['confianca']=round(float(l[2]),3)
            return True
        return False

    def resumo(self):
        d=self.diagnostico;res='x'.join(map(str,d.get('resolucao',[])))
        return 'esperado '+self.dificuldade+'; indicador '+str(d.get('indicador') or 'ilegivel')+'; tela '+res+'; escala automatica '+('ativa' if self.auto_escala else 'desativada')
