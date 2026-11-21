"""Impede puxar novos grupos enquanto o personagem esta sob pressao."""
import math
from collections import deque


class DefesaDG:
    def __init__(self, hp_retomada=.7, sossego=4., alcance=12., dano_minimo=.01):
        self.hp_retomada=hp_retomada
        self.sossego=sossego
        self.alcance=alcance
        self.hp_anterior=None
        self.danos=deque()
        self.dano_minimo=dano_minimo
        self.pressao_em=-float('inf')
        self.ativa=False

    def observar(self, agora, hp, controle):
        dano=max(0.,self.hp_anterior-hp) if self.hp_anterior is not None else 0.
        self.hp_anterior=hp
        if dano>1e-6:self.danos.append((agora,dano))
        while self.danos and agora-self.danos[0][0]>3.:self.danos.popleft()
        pressao=dano>1e-6 and sum(v for _,v in self.danos)>=self.dano_minimo-1e-9
        cc=any(controle.get(k,False) for k in ('stunned','paralyzed','frozen'))
        if pressao or cc:self.pressao_em=agora
        self.ativa=hp<self.hp_retomada or agora-self.pressao_em<self.sossego
        return self.ativa

    def candidatos(self, mobs, pos):
        # Recebe somente entidades hostis e com passagem ja validada.
        if not self.ativa:return mobs
        return sorted((m for m in mobs if math.dist(pos,m['position'])<=self.alcance),
                      key=lambda m:math.dist(pos,m['position']))

    def proximo(self, mobs, pos):
        return next(iter(self.candidatos(mobs,pos)),None)
