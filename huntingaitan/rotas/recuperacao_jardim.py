"""Replanejamento por colisao confirmada, preservando a grade e os objetos."""
import math
from huntingaitan.rotas.navegacao_grade import Grade


class RecuperacaoJardim:
    def __init__(self,inicio):
        self.bloqueios=set();self.trilha=[tuple(inicio)];self.recuo=None
        self.ancora=tuple(inicio);self.progresso_em=None;self.observado_em=None
        self.ultima_tentativa=-float('inf');self.reiniciar=False

    def aplicar(self,grade,pos):
        flags=bytearray(grade.flags);atual=grade.celula(pos)
        for x,y in self.bloqueios:
            c=grade.celula((x+.5,y+.5));i=grade.indice(c)
            if i is not None and c!=atual:flags[i]|=1
        return Grade(grade.origem,grade.canto,grade.largura,grade.altura,bytes(flags),grade.alturas,grade.mapa,grade.custos)

    def observar(self,circuito,pos,agora,plano):
        if self.observado_em is None or agora-self.observado_em>1.5:
            self.ancora=tuple(pos);self.progresso_em=agora
        self.observado_em=agora
        if math.dist(pos,self.ancora)>=1.2:
            self.ancora=tuple(pos);self.progresso_em=agora
            if math.dist(pos,self.trilha[-1])>=1:self.trilha=(self.trilha+[tuple(pos)])[-48:]
        parado=agora-self.progresso_em
        if parado>=25:
            self.reiniciar=True;return False
        falhou=plano['estado'] in ('replanejar','bloqueado','sem_caminho')
        # Uma quina reconhecida pela grade tambem pode impedir W sem gerar
        # deslocamento. Nao espere indefinidamente virado para essa quina.
        quina=plano['estado']=='andando' and not plano.get('w') and not plano.get('giro') and parado>=3
        if not (falhou or quina) or agora-self.ultima_tentativa<1:return False
        self.ultima_tentativa=agora
        alvo=plano.get('ponto')
        if alvo is None:
            alvo=circuito.grade.proximo(pos,circuito.rota_planejada,3)
        if alvo is None or math.dist(pos,alvo)<.2:return False
        dx,dy=alvo[0]-pos[0],alvo[1]-pos[1];d=math.hypot(dx,dy)
        centro=(pos[0]+dx/d*1.4,pos[1]+dy/d*1.4)
        novos={(math.floor(centro[0]),math.floor(centro[1]))}
        # Nunca bloqueia a celula ocupada nem a saida de um recuo conhecido.
        novos.discard(tuple(map(math.floor,pos)))
        self.bloqueios.update(novos)
        grade=circuito.aplicar_grade(circuito.grade_terreno,pos)
        rota=grade.caminho(pos,circuito.pontos[-1]['pos'],max_nos=grade.largura*grade.altura)
        if rota:
            circuito.adotar_rota(grade,rota,pos);self.recuo=None;return True
        # Se a passagem ficou fechada, recua por um trecho ja percorrido.
        # Os bloqueios continuam ativos; o proximo plano nao repete a parede.
        for anterior in reversed(self.trilha):
            if not 2<=math.dist(pos,anterior)<=7:continue
            retorno=grade.caminho(pos,anterior,alcance=.7,max_nos=4096)
            if retorno:
                self.recuo=anterior;circuito.adotar_rota(grade,retorno,pos);return True
        return False
