"""Impede puxar novos grupos enquanto o personagem esta sob pressao."""
import math


class DefesaDG:
    def __init__(self, hp_retomada=.7, sossego=4., alcance=8.):
        self.hp_retomada=hp_retomada
        self.sossego=sossego
        self.alcance=alcance
        self.hp_anterior=None
        self.pressao_em=-float('inf')
        self.ativa=False

    def observar(self, agora, hp, controle):
        dano=self.hp_anterior is not None and hp<self.hp_anterior-1e-6
        self.hp_anterior=hp
        cc=any(controle.get(k,False) for k in ('stunned','paralyzed','frozen'))
        if dano or cc:self.pressao_em=agora
        self.ativa=hp<self.hp_retomada or agora-self.pressao_em<self.sossego
        return self.ativa

    def candidatos(self, mobs, pos):
        # Recebe somente entidades hostis e com passagem ja validada.
        if not self.ativa:return mobs
        return sorted((m for m in mobs if math.dist(pos,m['position'])<=self.alcance),
                      key=lambda m:math.dist(pos,m['position']))

    def proximo(self, mobs, pos):
        return next(iter(self.candidatos(mobs,pos)),None)
