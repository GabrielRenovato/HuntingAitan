"""Confirma buffs da agenda sem confundir envio, conjuracao e efeito aplicado."""
from huntingaitan.combate.reacoes import grupo_de_recarga

class ConfirmacaoBuff:
    def __init__(self):self.pendente=None;self.falhas={}

    def iniciar(self,tecla,skill,agora,player,cc):
        grupo=grupo_de_recarga(skill);cds=cc.get('recargas_grupos')
        cd=cds[grupo] if cds is not None and grupo is not None and len(cds)>grupo else None
        self.pendente=dict(tecla=tecla,skill=skill,em=agora,mp=player['mp'],cast=False,cd=cd)

    def pausar(self,segundos):
        if self.pendente:self.pendente['em']+=segundos

    def observar(self,agora,player,cc):
        x=self.pendente
        if not x:return None
        skill=x['skill'];ativos=cc.get('active_skill_ids')
        if any(cc.get(k,False) for k in ('stunned','paralyzed','frozen')):
            self.pendente=None;return dict(tecla=x['tecla'],ok=None,motivo='interrompido_por_controle',repetir_em=1.)
        cast=cc.get('casting') and cc.get('casting_skill')==skill
        x['cast']|=bool(cast)
        if cast and agora-x['em']<10:return None
        aplicado=ativos is not None and skill in ativos
        grupo=grupo_de_recarga(skill);cds=cc.get('recargas_grupos')
        recarga=cds is not None and grupo is not None and len(cds)>grupo and x['cd'] is not None and cds[grupo]>x['cd']+.0001
        # Quando a lista de efeitos existe, recarga e gasto nao substituem o efeito.
        executado=ativos is None and (recarga or (x['cast'] and player['mp']<x['mp']))
        if aplicado or executado:
            self.pendente=None;self.falhas[x['tecla']]=0
            return dict(tecla=x['tecla'],ok=True,motivo='efeito_ativo_confirmado' if aplicado else 'execucao_confirmada_sem_lista_de_efeitos')
        if agora-x['em']<6:return None
        self.pendente=None;n=self.falhas.get(x['tecla'],0)+1;self.falhas[x['tecla']]=n
        espera=min(30.,2.**n)
        return dict(tecla=x['tecla'],ok=False,motivo='efeito_nao_confirmado',repetir_em=espera)

    def interromper_por_cura(self):
        if not self.pendente:return None
        x=self.pendente;self.pendente=None
        return dict(tecla=x['tecla'],ok=None,motivo='cura_priorizada',repetir_em=1.)
