"""Segue rotas da grade com realimentacao de posicao e orientacao reais."""
import math
from navegacao_grade import ler_grade

class NavegadorLocal:
    def __init__(self,leitor=ler_grade):
        self.leitor=leitor;self.grade=None;self.rota=None;self.meta=None;self.chave=None
        self.planejado=-100.;self.grade_em=-100.;self.pos_ancora=None;self.ancora_em=0.;self.falhas=0
    def invalidar(self):self.rota=None;self.planejado=-100.
    def suspender(self,pos,agora):self.pos_ancora=tuple(pos);self.ancora_em=agora
    def planejar(self,dados,pos,heading,destino,chave,agora,alcance=0,limite=None,parcial=False):
        if heading is None:return dict(estado='sem_orientacao',w=False)
        if chave!=self.chave:
            self.chave=chave;self.invalidar();self.falhas=0;self.suspender(pos,agora)
        if self.pos_ancora is None or math.dist(pos,self.pos_ancora)>=.6:
            self.suspender(pos,agora);self.falhas=0
        if math.dist(pos,destino)<=max(1.,alcance):return dict(estado='chegou',w=False)
        if parcial and self.rota and math.dist(self.rota[-1],destino)>max(1.,alcance) and math.dist(pos,self.rota[-1])<=1.5:
            # Chegou ao fim do trecho, nao ao destino. Ler nova janela e continuar.
            self.grade=None;self.invalidar()
        if self.grade is None or agora-self.grade_em>=2 or self.grade.indice(self.grade.celula(pos)) is None:
            nova=self.leitor(dados,pos)
            manter=self.grade is not None and self.grade.mapa==nova.mapa and self.grade.origem==nova.origem
            if manter and self.rota:manter=all(nova.livre(nova.celula(p)) for p in self.rota)
            self.grade=nova;self.grade_em=agora
            if not manter:self.invalidar()
        if self.rota is None or agora-self.planejado>=5. or self.meta is None or math.dist(destino,self.meta)>1.5:
            argumentos=dict(alcance=alcance,limite=limite)
            if parcial:argumentos['parcial']=True
            self.rota=self.grade.caminho(pos,destino,**argumentos)
            self.meta=tuple(destino);self.planejado=agora
        if not self.rota:return dict(estado='sem_caminho',w=False)
        ponto=self.grade.proximo(pos,self.rota,4.5)
        if ponto is None:return dict(estado='sem_caminho',w=False)
        dx,dy=ponto[0]-pos[0],ponto[1]-pos[1]
        erro=(math.degrees(math.atan2(dx,dy))-heading+540)%360-180
        andar=abs(erro)<=18
        if not andar:self.suspender(pos,agora)
        if andar and agora-self.ancora_em>=2.:
            self.falhas+=1;self.ancora_em=agora;self.invalidar()
            return dict(estado='bloqueado' if self.falhas>=3 else 'replanejar',w=False,tentativa=self.falhas)
        return dict(estado='andando',w=andar,giro=('d' if erro>0 else 'a') if abs(erro)>6 else None,tempo=min(.08,max(.015,abs(erro)/150)),erro=erro,ponto=ponto,pontos=len(self.rota))
