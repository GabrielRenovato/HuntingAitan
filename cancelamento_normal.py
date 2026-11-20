"""Tentativa de cancelamento por entrada normal; sem escrita no cliente.
A queda de HP e evidencia de dano, nao comprova a autoria do golpe.
"""
import math,time

# Normal: sequencia informada em 20/11, sem esperas programadas.
# Skills: medianas das demonstracoes de 18/11; outra skill no mesmo atalho
# nao herda esse cancelamento.
PERFIS_COMBO={
    1:dict(ordem='1rr1ww',sequencia='1rr1ww',atraso=0.,duracao_tecla=0.,duracao_w=0.),
    177:dict(ordem='w+skill',atraso=.0035,duracao_tecla=.073,duracao_w=.061),
    273:dict(ordem='w+skill',atraso=.025,duracao_tecla=.061,duracao_w=.079),
}
DURACOES_TECLA={1:.065,113:.078,177:.073,273:.061,289:.078,49:.076}

def perfil_combo(tecla,normal,skill_id=None):
    if skill_id is None and normal:skill_id=1
    return PERFIS_COMBO.get(skill_id)

def duracao_tecla(skill_id):return DURACOES_TECLA.get(skill_id,.045)

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


def executar_combo(pressionar,liberar,esperar,permitido,tecla,normal,skill_id=None,relogio=None):
    """Reproduz ordem, sobreposicao e liberacao independentes da calibracao."""
    perfil=perfil_combo(tecla,normal,skill_id)
    if not permitido():return (False,False)
    relogio=relogio or time.monotonic
    primaria=False;w_enviado=False;seguradas=[]
    if perfil and perfil.get('sequencia'):
        for key in (tecla,'r','r',tecla,'w','w'):
            if not permitido():break
            try:
                if pressionar(key) is False:break
                if key==tecla:primaria=True
                if key=='w':w_enviado=True
            finally:liberar(key)
        return (primaria,primaria and w_enviado)
    if perfil is None:
        try:
            primaria=pressionar(tecla) is not False
            if primaria:esperar(duracao_tecla(skill_id))
            return (primaria,False)
        finally:liberar(tecla)
    primeiro_w=perfil['ordem'].startswith('w+')
    inicio_w=0. if primeiro_w else perfil['atraso']
    inicio_tecla=perfil['atraso'] if primeiro_w else 0.
    passos=sorted([(inicio_w,'down','w'),(inicio_tecla,'down',tecla),
                   (inicio_w+perfil['duracao_w'],'up','w'),
                   (inicio_tecla+perfil['duracao_tecla'],'up',tecla)],key=lambda p:p[0])
    inicio=relogio()
    try:
        for instante,acao,key in passos:
            restante=inicio+instante-relogio()
            if restante>0:esperar(restante)
            if acao=='down':
                if not permitido() or pressionar(key) is False:break
                seguradas.append(key)
                if key==tecla:primaria=True
                else:w_enviado=True
            else:
                liberar(key)
                if key in seguradas:seguradas.remove(key)
        return (primaria,primaria and w_enviado)
    finally:
        try:
            if seguradas:liberar(seguradas.pop())
        finally:
            if seguradas:liberar(seguradas.pop())
