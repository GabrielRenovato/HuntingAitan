"""Detecta comandos de ataque sem progresso; nao presume autoria do dano."""


class VigiaAtaque:
    def __init__(self):
        self.id=None;self.hp=None;self.desde=0.;self.envios=0;self.recuperar_ate=0.

    def suspender(self,agora):
        self.desde=agora;self.envios=0;self.recuperar_ate=0.

    def observar(self,alvo,agora):
        if alvo['id']!=self.id or alvo['hp']!=self.hp:
            self.suspender(agora)
        self.id=alvo['id'];self.hp=alvo['hp']

    def enviado(self):self.envios+=1

    def iniciar(self,agora,distancia):
        if self.hp is None or self.hp<=0 or distancia>3 or self.envios<2 or agora-self.desde<3:return False
        self.recuperar_ate=agora+1.5
        return True
