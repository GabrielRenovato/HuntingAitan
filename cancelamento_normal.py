"""Tentativa de cancelamento por entrada normal; sem escrita no cliente.
A queda de HP e evidencia de dano, nao comprova a autoria do golpe.
"""
import math

class CancelamentoNormal:
    def __init__(self,ativo=False):
        self.ativo=ativo;self.alvo=None;self.hp=None;self.pos=None
        self.normal_em=None;self.bloqueado_ate=0.;self.ultimo=-100.
        self.pendente=None;self.aguarda_dano=None;self.suspenso=False

    def suspender_alvo(self,identidade):
        self.alvo=identidade;self.suspenso=True;self.pendente=None;self.normal_em=None

    def permitir_combo(self,alvo,pos,identidade,dano_confirmado):
        if not self.ativo or not dano_confirmado or not alvo:return False
        if alvo['id']!=identidade or alvo['hp']<=0:return False
        if self.alvo!=identidade:
            self.alvo=identidade;self.suspenso=False
        return not self.suspenso and math.dist(pos,alvo['position'])<=2.2

    def acao(self,normal,agora,livre_em):
        if normal:self.normal_em=agora
        else:
            self.normal_em=None;self.pendente=None
            self.bloqueado_ate=max(self.bloqueado_ate,livre_em+.25)

    def observar(self,agora,alvo,pos,identidade):
        if not self.ativo:return False
        if not alvo or alvo['id']!=identidade or alvo['hp']<=0:
            self.pendente=None;self.pos=None
            return False
        if self.alvo!=identidade:
            self.alvo=identidade;self.hp=alvo['hp'];self.pos=tuple(pos)
            self.pendente=None;self.aguarda_dano=None;self.suspenso=False
            self.normal_em=None
            return False
        dano=alvo['hp']<self.hp
        parado=self.pos is not None and math.dist(pos,self.pos)<.25
        perto=math.dist(pos,alvo['position'])<=2.2
        self.hp=alvo['hp'];self.pos=tuple(pos)
        if dano:self.aguarda_dano=None
        if self.aguarda_dano is not None and agora-self.aguarda_dano>=2.:
            self.suspenso=True
        permitido=(not self.suspenso and perto and parado and agora>=self.bloqueado_ate
                    and self.normal_em is not None and 0<=agora-self.normal_em<=1.5)
        if not permitido:self.pendente=None;return False
        if dano and agora-self.ultimo>=.35:self.pendente=agora+.06
        if self.pendente is None or agora<self.pendente:return False
        self.pendente=None;self.ultimo=agora;self.aguarda_dano=agora
        return True


def executar_cancelamento(pulso,permitido,ataque):
    # pulso sempre solta W em finally, inclusive ao perder foco.
    if not permitido() or not pulso('w',.035):return False
    if not permitido():return False
    return pulso(ataque)


def executar_combo(pressionar,liberar,esperar,permitido,tecla,normal):
    """W+ataque sobrepostos; skill seguida imediatamente de W. Sem fila extra."""
    primeira,segunda=('w',tecla) if normal else (tecla,'w')
    if not permitido():return (False,False)
    try:
        if pressionar(primeira) is False:return (False,False)
        if not permitido():return (not normal,False)
        if pressionar(segunda) is False:return (not normal,False)
        esperar(.035)
        return (True,True)
    finally:
        try:liberar(segunda)
        finally:liberar(primeira)
