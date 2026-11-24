"""Evita rearmar o padrao durante deslocamento do mob ou dano em andamento."""
import math

class NormalTemplaria:
    def __init__(self):
        self.id=None;self.hp=None;self.pos=None;self.movendo_ate=0.;self.dano_em=-100.;self.envio_em=-100.;self.aguardar_ate=0.;self.execucao_em=-100.

    def observar(self,alvo,agora,controle=None):
        if not alvo:return
        if alvo['id']!=self.id:
            self.id=alvo['id'];self.hp=alvo['hp'];self.pos=tuple(alvo['position'])
            self.movendo_ate=agora+.2;self.dano_em=-100.;self.envio_em=-100.;self.aguardar_ate=0.;self.execucao_em=-100.
            return
        controle=controle or {};anim=controle.get('animation',-1)
        # Faixas consultadas por 0x5D1530/0x5D1550. HP caindo sozinho
        # pode ser dano da Pran ou de outro jogador, sem ataque do player.
        if (5<=anim<=22 or 44<=anim<=58) and not controle.get('casting'):self.execucao_em=agora
        if math.dist(self.pos,alvo['position'])>=.12:
            self.movendo_ate=agora+.4;self.pos=tuple(alvo['position'])
        if alvo['hp']<self.hp:self.dano_em=agora
        self.hp=alvo['hp']

    def parado(self,agora):return self.id is not None and agora>=self.movendo_ate

    def permitir(self,agora):
        andamento=agora-self.dano_em<1.8 and agora-self.execucao_em<1.8
        return self.parado(agora) and agora>=self.aguardar_ate and not andamento and agora-self.envio_em>=2.5

    def solicitado(self,agora):self.envio_em=agora

    def apos_conjuracao(self,agora):self.aguardar_ate=max(self.aguardar_ate,agora+.4)
