"""Acesso a area final, com Seridunn reconhecido ao vivo e combate restrito ao necessario."""
import json,math
from functools import lru_cache
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.jardim_aereo import JardimAereo
from huntingaitan.rotas.mina_lenfer import MinaLenfer,normalizar
from huntingaitan.rotas.circuito_termes import distancia_segmento


@lru_cache(maxsize=1)
def plano_seridunn():return json.loads((DADOS/'jardim_seridunn_rota.json').read_text(encoding='utf-8'))


class JardimSeridunn(JardimAereo):
    obter_plano=staticmethod(plano_seridunn)

    def __init__(self,pos):
        super().__init__(pos);self.bloqueio_em=-float('inf');self.agora=0.

    def eh_chefe(self,nome):return normalizar(nome)=='seridunn'

    def registrar_abate(self,id_,nome,pos,agora):
        return MinaLenfer.registrar_abate(self,id_,nome,pos,agora)

    def atingiu_limite(self,pos):return False

    def limite_proximo(self,mobs,pos):return None

    def destino(self,pos,agora):
        self.agora=agora
        return super().destino(pos,agora)

    def observar_navegacao(self,pos,agora,plano):
        self.agora=agora
        if plano['estado'] in ('replanejar','bloqueado','sem_caminho'):self.bloqueio_em=agora
        return super().observar_navegacao(pos,agora,plano)

    def bloqueia_percurso(self,mob,pos):
        if math.dist(pos,mob['position'])>3.5:return False
        if self.agora-self.bloqueio_em<=3:return True
        rota=self.rota_planejada
        i=min(range(len(rota)),key=lambda i:math.dist(pos,rota[i]));trecho=[tuple(pos)]+rota[i:i+7]
        return any(distancia_segmento(mob['position'],a,b)<=1.25 for a,b in zip(trecho,trecho[1:]) if math.dist(a,b)>.1)

    def filtrar_mobs(self,mobs,pos,raio,defendendo=False):
        # Mobs laterais nao interrompem a marcha. Dano/controle de grupo
        # mantem a defesa existente, limitada ao entorno imediato.
        permitidos=[m for m in mobs if self.eh_chefe(m['name']) or
            (math.dist(pos,m['position'])<=8 if defendendo else self.bloqueia_percurso(m,pos))]
        return MinaLenfer.filtrar_mobs(self,permitidos,pos,raio,defendendo)

    def permite_perseguir(self,mob,pos,defendendo=False):
        if self.eh_chefe(mob['name']):return True
        return math.dist(pos,mob['position'])<=8 and (defendendo or self.bloqueia_percurso(mob,pos))
