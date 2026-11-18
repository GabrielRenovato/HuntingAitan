"""Logica de combate independente de imagem/OCR."""

import math

def erro_angular(a,b):return (a-b+540)%360-180

class CadenciaCombate:
    """Uma unica agenda de acoes para toda a sessao, sem reset por mob."""
    def __init__(self,config):
        self.intervalo=max(.5,float(config.get('intervalo_skills',.7)))
        self.recargas={str(k):max(self.intervalo,float(v)) for k,v in
                       config.get('recargas',{'2':6,'3':8,'4':10,'5':12,'6':15,'7':20}).items()}
        self.pronta_em={};self.livre_em=0.;self.normal_em=0.;self.ultimo_envio={}

    def escolher(self,agora,alvo_valido,dano_recente,vida,em_alcance=None,recargas_reais=None):
        if not alvo_valido or vida<=0 or agora<self.livre_em:return None
        skills_liberadas=(dano_recente and vida>.12) if em_alcance is None else (dano_recente or em_alcance)
        if skills_liberadas:
            disponiveis=[]
            for tecla in self.recargas:
                real=(recargas_reais or {}).get(tecla)
                if real is not None:
                    # O cliente e a fonte da recarga; nao esperar o timer configurado.
                    # Se um comando for recusado, nao monopolizar a fila com repeticoes.
                    pronta=real['ready'] and agora-self.ultimo_envio.get(tecla,-float('inf'))>=max(1.,self.intervalo)
                else:pronta=agora>=self.pronta_em.get(tecla,0)
                if pronta:disponiveis.append(tecla)
            if disponiveis:return min(disponiveis,key=lambda k:self.ultimo_envio.get(k,-float('inf')))
        return '1' if agora>=self.normal_em else None

    def registrar(self,tecla,agora):
        if tecla in self.recargas:
            self.ultimo_envio[tecla]=agora
            self.pronta_em[tecla]=agora+self.recargas[tecla]
            self.livre_em=agora+self.intervalo
        elif tecla=='1':
            self.normal_em=agora+1.
            self.livre_em=agora+.12
        elif tecla=='8':
            self.livre_em=max(self.livre_em,agora+.5)

class VerificadorMovimento:
    def __init__(self,limite=3):self.limite=limite;self.origem=None;self.desde=None;self.ultima_acao=-100.
    def observar(self,pos,agora,deveria_mover):
        if not deveria_mover or pos is None:
            self.origem=None;self.desde=None;return False
        if self.origem is None or math.dist(pos,self.origem)>=1.5:
            self.origem=tuple(pos);self.desde=agora;return False
        if agora-self.desde>=self.limite and agora-self.ultima_acao>=self.limite:
            self.ultima_acao=agora;self.desde=agora;return True
        return False


class AgendaBuffs:
    def __init__(self,inicio,teclas,periodo=540,intervalo=2,ativo=True):
        self.teclas=list(teclas);self.periodo=periodo;self.intervalo=intervalo;self.ativo=ativo
        self.vencimentos={k:inicio for k in self.teclas};self.indice=None;self.proxima_acao=0
    @property
    def vencimento(self):return min(self.vencimentos.values(),default=float('inf'))
    @property
    def em_andamento(self):return self.indice is not None
    def proximo(self,agora,seguro):
        if not self.ativo or not seguro:return None
        if agora<self.proxima_acao:return None
        vencidas=[i for i,k in enumerate(self.teclas) if self.vencimentos[k]<=agora]
        if not vencidas:self.indice=None;return None
        self.indice=min(vencidas,key=lambda i:self.vencimentos[self.teclas[i]])
        return self.teclas[self.indice]
    def confirmar(self,agora):
        self.vencimentos[self.teclas[self.indice]]=agora+self.periodo
        self.proxima_acao=agora+self.intervalo
        vencidas=[i for i,k in enumerate(self.teclas) if self.vencimentos[k]<=agora]
        self.indice=min(vencidas,key=lambda i:self.vencimentos[self.teclas[i]]) if vencidas else None


def executar_buff(atalho,pressionar,liberar,esperar,permitido):
    modificador,tecla=atalho.split('+')
    if not permitido():return False
    if pressionar(modificador) is False:return False
    try:
        esperar(.025)
        if not permitido():return False
        if pressionar(tecla) is False:return False
        try:esperar(.06)
        finally:liberar(tecla)
        return permitido()
    finally:liberar(modificador)
