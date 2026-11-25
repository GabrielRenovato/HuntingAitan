"""Confirma respostas do cliente e limita recuperacoes de comandos sem efeito."""
import math
from huntingaitan.combate.reacoes import grupo_de_recarga

class ConfirmacaoReacao:
    def __init__(self):
        self.pendente=None;self.falhas_cura=0;self.recuperacoes=0
        self.recuperando=False;self.manual=False;self.pedido=False;self.baseline=None
        self.limite_cura=.7;self.manual_cast=False

    @staticmethod
    def cura(r):
        return r['tipo']=='cura' or 1073<=r['skill_id']<=1088 or (r['skill_id']==0 and r['tipo'] in ('item_hp','emergencia'))

    @classmethod
    def verificavel(cls,r):
        return cls.cura(r) or (r['skill_id']>0 and r['tipo'] in ('buff','buff_combate','defesa','emergencia'))

    def enviada(self,r,agora,player,cc):
        if not self.verificavel(r):return
        grupo=grupo_de_recarga(r['skill_id']);cd=cc.get('recargas_grupos')
        self.pendente=dict(regra=r,em=agora,hp=player['hp']/player['hp_max'],mp=player['mp'],
            cd=cd[grupo] if grupo is not None and cd is not None and len(cd)>grupo else None,
            cast=False,ultimo_cast=None,efeitos_antes=tuple(cc.get('active_skill_ids') or ()))

    def pausar(self,segundos):
        if self.pendente:
            self.pendente['em']+=segundos
            if self.pendente['ultimo_cast'] is not None:self.pendente['ultimo_cast']+=segundos

    def interromper_por_emergencia(self,player,cc):
        if not self.pendente or self.cura(self.pendente['regra']) or cc.get('casting'):return None
        if player['hp']/player['hp_max']>.35:return None
        r=self.pendente['regra'];self.pendente=None
        return dict(ok=None,motivo='cura_emergencial_priorizada',regra=r)

    def observar(self,agora,player,cc,resposta_cliente=False):
        hp=player['hp']/player['hp_max'];x=self.pendente
        if x is None:
            # Reconhece intervencao manual sem soltar novamente a rotacao
            # somente porque o tempo passou ou a mana regenerou.
            if self.manual and self.baseline:
                b=self.baseline;andou=math.dist(player['position'],b['pos'])>=1
                conjurou=cc.get('casting_skill') is not None
                self.manual_cast=self.manual_cast or conjurou
                if hp>b['hp']+.02 and (andou or self.manual_cast):
                    self.reiniciar();return dict(ok=True,motivo='controle_manual_confirmado',regra=None)
            return None
        r=x['regra'];tempo=agora-x['em'];eh_cura=self.cura(r)
        if any(cc.get(k,False) for k in ('stunned','paralyzed','frozen')):
            self.pendente=None
            return dict(ok=None,motivo='interrompida_por_controle',regra=r)
        cast=bool(cc.get('casting')) and cc.get('casting_skill')==r['skill_id'] and r['skill_id']>0
        if cast:x['cast']=True;x['ultimo_cast']=agora
        grupo=grupo_de_recarga(r['skill_id']);cds=cc.get('recargas_grupos')
        cd=cds[grupo] if grupo is not None and cds is not None and len(cds)>grupo else None
        recarga=cd is not None and x['cd'] is not None and cd>x['cd']+.0001
        gasto=player['mp']<x['mp']-max(1,min(15,r['mp_min']*.05))
        subiu=hp>x['hp']+.02
        # Curas de efeito continuo podem ser aplicadas sem conjuracao e ter
        # seus ticks compensados pelo dano recebido. Exige efeito novo da
        # propria skill e inicio da recarga; efeito antigo nao confirma envio.
        efeito_cura=(eh_cura and not 1073<=r['skill_id']<=1088
            and r['skill_id'] not in x['efeitos_antes']
            and r['skill_id'] in (cc.get('active_skill_ids') or ()) and recarga)
        sinal=x['cast'] or recarga or gasto
        terminou=(not cc.get('casting') and (resposta_cliente or x['ultimo_cast'] is None or agora-x['ultimo_cast']>=.2))
        minimo=0. if resposta_cliente and x['cast'] else (2. if 1073<=r['skill_id']<=1088 else .2)
        # Para cura conjurada, o comeco da animacao nao e conclusao: aguarda
        # o termino, sem W/TAB/skills. Dano recebido pode mascarar a subida de HP.
        ok=terminou and (efeito_cura or (subiu and (sinal or r['skill_id']==0)) or
            (sinal and (not eh_cura or (x['cast'] and tempo>=minimo and (recarga or gasto)))))
        if ok:
            self.pendente=None
            if eh_cura:self.reiniciar()
            return dict(ok=True,motivo='hp_recuperado' if subiu else 'execucao_confirmada',regra=r)
        limite=6. if sinal else 1.25
        if cast and tempo<10:return None
        if cast:
            self.recuperando=True;self.recuperacoes=2;self.pedido=True
        if tempo<limite:return None
        self.pendente=None
        if eh_cura and r['skill_id']>0:
            self.limite_cura=r['hp_max_pct']/100
            self.falhas_cura+=1
            if self.falhas_cura>=2:
                self.recuperando=True
                if self.falhas_cura in (2,4,6):self.pedido=True
                if self.baseline is None:self.baseline=dict(hp=hp,pos=tuple(player['position']))
        return dict(ok=False,motivo='sem_resposta_do_cliente',regra=r)

    def recuperacao(self):
        if not self.pedido:return None
        self.pedido=False
        if self.recuperacoes>=2:self.manual=True;return 'manual'
        self.recuperacoes+=1;return 'revalidar'

    def proteger(self,hp):
        return self.manual or self.recuperando or (self.falhas_cura>0 and hp<=self.limite_cura)

    def reiniciar(self):
        self.falhas_cura=0;self.recuperacoes=0;self.recuperando=False
        self.manual=False;self.pedido=False;self.baseline=None
        self.pendente=None;self.manual_cast=False

    def telemetria(self):
        estado=None
        if self.manual:estado='aguardando_controle'
        elif self.recuperando:estado='recuperando_controle'
        elif self.pendente:estado='confirmando_cura' if self.cura(self.pendente['regra']) else 'confirmando_habilidade'
        return dict(state=estado,falhas=self.falhas_cura,tentativas=self.recuperacoes,tecla=self.pendente['regra']['tecla'] if self.pendente else None)
