"""Recuperacao por skill somente apos falta de deslocamento confirmada pelo navegador."""
import math


class DestravarColisao:
    def __init__(self):
        self.tentativa_em=-100.;self.origem=None;self.confirmado=False

    def tentar(self,agora,pos,tecla,controle,enviar):
        if not tecla or agora-self.tentativa_em<3:return None
        if any(controle.get(k) for k in ('casting','stunned','paralyzed','frozen')):return None
        recarga=controle.get('recargas_atalhos',{}).get(tecla)
        # Nao enviar tecla desconhecida nem disputar uma skill em recarga.
        if not recarga or not recarga.get('ready'):return None
        self.tentativa_em=agora
        aceito=bool(enviar(tecla))
        self.origem=tuple(pos) if aceito else None;self.confirmado=False
        return dict(tecla=tecla,skill=recarga['skill'],aceito=aceito)

    def observar(self,pos):
        if self.origem is None or self.confirmado:return False
        if math.dist(pos,self.origem)<.6:return False
        self.confirmado=True
        return True
