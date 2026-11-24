"""Decisoes da templaria: custo de caminho e recuperacao sem trocar identidade."""
import math
from huntingaitan.combate.identidade_mob import verit_mutante
from huntingaitan.combate.normal_templaria import NormalTemplaria
from huntingaitan.combate.escolha_por_caminho import EscolhaPorCaminho

class CacaTemplaria(EscolhaPorCaminho):
    def __init__(self):
        super().__init__(prioridade=verit_mutante)
        self.limpeza_centro=None;self.limpeza_ids=set();self.vazio_desde=None;self.sem_passagem_desde=None;self.limpeza_repetir_em=0.
        self.ultimo_reparo=-100.
        self.normal=NormalTemplaria()

    def reter_verit(self,mob,player):
        return bool(verit_mutante(mob) and mob.get('hostile') and mob.get('hp',0)>0 and
            abs(mob['height']-player['height'])<=3 and math.dist(mob['position'],player['position'])<=5)

    def pode_reparar(self,agora):return agora-self.ultimo_reparo>=4.5 and self.normal.parado(agora)

    def perto(self,mob,pos,player,centro=None):
        return bool(mob and mob.get('hostile') and mob.get('hp',0)>0 and
            abs(mob['height']-player['height'])<=3 and math.dist(pos,mob['position'])<=5 and
            (centro is None or math.dist(centro,mob['position'])<=5))

    def atualizar_limpeza(self,lista,pos,player,agora):
        proximos=[m for m in lista if self.perto(m,pos,player,self.limpeza_centro)]
        if self.limpeza_centro is None and len(proximos)>=3 and agora>=self.limpeza_repetir_em:
            self.limpeza_centro=tuple(pos);self.vazio_desde=None
            self.limpeza_ids={m['id'] for m in proximos};return 'iniciada'
        if self.limpeza_centro is not None:
            self.limpeza_ids={m['id'] for m in proximos}
            if proximos:self.vazio_desde=None
            elif self.vazio_desde is None:self.vazio_desde=agora
            elif agora-self.vazio_desde>=.4:
                self.limpeza_centro=None;self.sem_passagem_desde=None;return 'concluida'
        return None

    def permite_limpeza(self,mob,pos,player):
        return self.limpeza_centro is not None and mob is not None and mob['id'] in self.limpeza_ids and self.perto(mob,pos,player,self.limpeza_centro)

    def aguardar_limpeza(self,agora,acessiveis):
        if self.limpeza_centro is None or acessiveis:self.sem_passagem_desde=None;return False
        if self.sem_passagem_desde is None:self.sem_passagem_desde=agora
        if agora-self.sem_passagem_desde<2:return True
        # Um mob atras de uma parede nao pode prender a rota indefinidamente.
        self.limpeza_centro=None;self.limpeza_ids.clear();self.limpeza_repetir_em=agora+10
        self.sem_passagem_desde=None;return False

    def recuperar(self,dados,progresso,pos,raio,player):
        try:m=dados.entidade(progresso.ref)
        except RuntimeError:m=None
        if m and m['id']==progresso.id:return m
        # Uma referencia pode mudar durante stun. O ID e o nome precisam
        # continuar iguais; nunca usa o primeiro mob encontrado no pool.
        for m in dados.listar_mobs(pos,raio,player):
            if m['id']==progresso.id and (m.get('template_id')==getattr(progresso,'template_id',None) if m.get('template_id') is not None and getattr(progresso,'template_id',None) is not None else m['name']==progresso.nome_original):return m
        return None
