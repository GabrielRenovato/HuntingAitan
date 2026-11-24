"""Segue rotas da grade com realimentacao de posicao e orientacao reais."""
import math
from dataclasses import replace
from huntingaitan.rotas.navegacao_grade import ler_grade

class NavegadorLocal:
    def __init__(self,leitor=ler_grade):
        self.leitor=leitor;self.grade=None;self.rota=None;self.meta=None;self.chave=None
        self.planejado=-100.;self.grade_em=-100.;self.pos_ancora=None;self.ancora_em=0.;self.falhas=0
        self.movendo=False;self.virando=None;self.giro_em=0.
        self.erro_melhor=None;self.alinhamento_em=0.
        self.passagens_falhas={}
    def invalidar(self):self.rota=None;self.planejado=-100.

    def replanejar_agora(self,dados,pos,heading,destino,chave,agora,plano,**opcoes):
        if not plano.get('passagem_bloqueada'):return plano
        # A passagem ja foi excluida pelo primeiro planejamento. Uma unica
        # busca adicional usa essa exclusao antes de mandar parar o motor.
        novo=self.planejar(dados,pos,heading,destino,chave,agora,**opcoes)
        novo['passagem_recalculada']=plano['passagem_bloqueada']
        novo['replanejado_imediato']=novo['estado']=='andando'
        return novo
    def ancorar(self,pos,agora):self.pos_ancora=tuple(pos);self.ancora_em=agora
    def suspender(self,pos,agora):
        self.ancorar(pos,agora);self.movendo=False;self.virando=None;self.giro_em=agora
        self.erro_melhor=None;self.alinhamento_em=agora
    def parar(self,estado,**extras):
        self.movendo=False;self.virando=None
        return dict(estado=estado,w=False,**extras)
    def frente_livre(self,pos,heading,limite,distancia):
        ang=math.radians(heading);anterior=self.grade.celula(pos)
        for i in range(1,math.ceil(distancia/.25)+1):
            p=(pos[0]+math.sin(ang)*min(i*.25,distancia),pos[1]+math.cos(ang)*min(i*.25,distancia))
            c=self.grade.celula(p)
            if not self.grade.passagem(anterior,c):return False
            if limite:
                permitido=limite(p) if callable(limite) else math.dist(p,limite[0])<=limite[1]
                if not permitido:return False
            anterior=c
        return True
    def planejar(self,dados,pos,heading,destino,chave,agora,alcance=0,limite=None,parcial=False,controle_interno=False):
        if heading is None and not controle_interno:return self.parar('sem_orientacao')
        if chave!=self.chave:
            self.chave=chave;self.invalidar();self.falhas=0;self.suspender(pos,agora)
        if self.pos_ancora is None or math.dist(pos,self.pos_ancora)>=.6:
            self.ancorar(pos,agora);self.falhas=0
            self.erro_melhor=None;self.alinhamento_em=agora
        if math.dist(pos,destino)<=max(1.,alcance):return self.parar('chegou')
        if parcial and self.rota and math.dist(self.rota[-1],destino)>max(1.,alcance) and math.dist(pos,self.rota[-1])<=1.5:
            # Chegou ao fim do trecho, nao ao destino. Ler nova janela e continuar.
            self.grade=None;self.invalidar()
        if self.grade is None or agora-self.grade_em>=2 or self.grade.indice(self.grade.celula(pos)) is None:
            nova=self.leitor(dados,pos)
            self.passagens_falhas={k:v for k,v in self.passagens_falhas.items() if v>agora}
            arestas=frozenset((a,b) for (mapa,origem,a,b),v in self.passagens_falhas.items() if mapa==nova.mapa and origem==nova.origem)
            if arestas:nova=replace(nova,arestas_bloqueadas=nova.arestas_bloqueadas|arestas)
            manter=self.grade is not None and self.grade.mapa==nova.mapa and self.grade.origem==nova.origem
            if manter and self.rota:manter=all(nova.livre(nova.celula(p)) for p in self.rota)
            self.grade=nova;self.grade_em=agora
            if not manter:self.invalidar()
        if self.rota is None or agora-self.planejado>=5. or self.meta is None or math.dist(destino,self.meta)>1.5:
            argumentos=dict(alcance=alcance,limite=limite)
            if parcial:argumentos['parcial']=True
            self.rota=self.grade.caminho(pos,destino,**argumentos)
            self.meta=tuple(destino);self.planejado=agora
        if not self.rota:return self.parar('sem_caminho')
        ponto=self.grade.proximo(pos,self.rota,7.)
        if ponto is None:return self.parar('sem_caminho')
        dx,dy=ponto[0]-pos[0],ponto[1]-pos[1]
        erro=(math.degrees(math.atan2(dx,dy))-(heading or 0)+540)%360-180
        # Histerese evita soltar e reapertar W ao redor do mesmo angulo.
        # O avanço durante a curva exige dois metros livres na direcao atual.
        frente=True if controle_interno else self.frente_livre(pos,heading,limite,min(2.,math.dist(pos,ponto)))
        if not frente and abs(erro)<7:
            # Perto de uma quina, a linha entre centros de celulas pode ser
            # livre enquanto a posicao real esta deslocada para a parede.
            # Mira uma celula mais proxima para recentralizar antes de avancar.
            curto=self.grade.proximo(pos,self.rota,1.5)
            if curto is not None and math.dist(pos,curto)>.1:
                ponto=curto;dx,dy=ponto[0]-pos[0],ponto[1]-pos[1]
                erro=(math.degrees(math.atan2(dx,dy))-heading+540)%360-180
                frente=self.frente_livre(pos,heading,limite,min(2.,math.dist(pos,ponto)))
        andar=controle_interno or (abs(erro)<=(42 if self.movendo else 24) and frente)
        if not andar:
            self.ancorar(pos,agora)
            # Girar sem reduzir o erro nao pode reiniciar o prazo para sempre.
            # Casts, stun e pausas chamam suspender e iniciam uma nova medicao.
            if self.erro_melhor is None or abs(erro)<=self.erro_melhor-5:
                self.erro_melhor=abs(erro);self.alinhamento_em=agora
            elif agora-self.alinhamento_em>=3.:
                self.invalidar()
                return self.parar('bloqueado',motivo='alinhamento_sem_progresso',erro=erro,ponto=ponto)
        else:self.erro_melhor=None;self.alinhamento_em=agora
        if andar and agora-self.ancora_em>=2.:
            self.falhas+=1;self.ancora_em=agora;self.invalidar()
            # Excluir a primeira aresta do segmento realmente enviado. O sinal
            # de dx/dy inventava uma diagonal em trajetos quase retos; a linha
            # suavizada continuava livre e repetia o mesmo choque na arvore.
            a=self.grade.celula(pos);fim=self.grade.celula(ponto)
            passos=max(abs(fim[0]-a[0]),abs(fim[1]-a[1]))
            b=(round(a[0]+(fim[0]-a[0])/passos),round(a[1]+(fim[1]-a[1])/passos)) if passos else a
            if a!=b:
                for inicio,fim in ((a,b),(b,a)):self.passagens_falhas[(self.grade.mapa,self.grade.origem,inicio,fim)]=agora+20
                self.grade=replace(self.grade,arestas_bloqueadas=self.grade.arestas_bloqueadas|{(a,b),(b,a)})
            return self.parar('bloqueado' if self.falhas>=3 else 'replanejar',tentativa=self.falhas,ponto=ponto,passagem_bloqueada=(a,b))
        self.movendo=andar
        sentido='d' if erro>0 else 'a'
        if abs(erro)<=3 or (self.virando is not None and self.virando!=sentido):self.virando=None
        if abs(erro)>=7 or (not andar and abs(erro)>1):self.virando=sentido
        giro=self.virando if not controle_interno and agora>=self.giro_em else None
        tempo=min(.08,max(.006 if abs(erro)<3 else .012,abs(erro)/240*.65)) if giro else 0.
        if giro:self.giro_em=agora+tempo+.045
        return dict(estado='andando',w=andar,giro=giro,tempo=tempo,erro=erro,ponto=ponto,pontos=len(self.rota))
