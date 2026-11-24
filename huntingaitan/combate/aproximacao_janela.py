"""Aproximacao pelo ataque do cliente, conferida por deslocamento real."""
import math

class AproximacaoJanela:
    def __init__(self):self.id=None;self.pos=None;self.em=0.;self.envio=-100.

    def decidir(self,id_,pos,agora):
        if self.id!=id_ or self.pos is None or math.dist(pos,self.pos)>=.6:
            self.id=id_;self.pos=tuple(pos);self.em=agora
        if agora-self.em>=3:return 'bloqueado'
        if agora-self.envio>=.6:
            self.envio=agora;return 'atacar'
        return 'aguardar'

    def reiniciar(self):self.id=None;self.pos=None;self.envio=-100.
