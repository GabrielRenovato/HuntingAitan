"""Reacoes por tecla: sobrevivencia (cura, defesa, emergencia, itens) e skills de combate (buff, ataque).

Cada reacao e uma regra. A ordem de avaliacao e a prioridade do tipo e, dentro do tipo, a ordem da lista.
A primeira regra cujas condicoes valem e cuja skill esta pronta e a escolhida. Este modulo so decide: o
motor envia a tecla."""
import re

TIPOS=('emergencia','defesa','cura','item_hp','item_mp','buff','buff_combate','ataque')
PRIORIDADE={'emergencia':0,'defesa':1,'cura':2,'item_hp':3,'item_mp':4,'buff':5,'buff_combate':5,'ataque':6}
# vida/mana do jogador, vida do alvo (%), contagem de mobs perto, alcance ao alvo (m), intervalo minimo entre usos
PADRAO=dict(nome='',tecla='',tipo='cura',ativa=True,skill_id=0,hp_max_pct=60.,mp_max_pct=100.,mp_min=0,
            so_em_combate=False,mobs_min=0,mobs_raio_m=6.,alvo_hp_min_pct=0.,alvo_hp_max_pct=100.,alcance_m=0.,intervalo_s=2.5)
# Limite de vida padrao por tipo quando a regra nao informa hp_max_pct (buff e ataque nao dependem da vida).
HP_PADRAO={'emergencia':30.,'defesa':50.,'cura':60.,'item_hp':50.,'item_mp':100.,'buff':100.,'buff_combate':100.,'ataque':100.}
TECLA=re.compile(r"(?:(?:ctrl|alt|shift)\+)?(?:[a-z0-9']|f(?:[1-9]|10|11))")
GRUPOS=43
# Tipos que so fazem sentido lutando: exigem combate mesmo que a regra nao marque.
EM_COMBATE=('buff_combate','ataque')

def grupo_de_recarga(skill_id):
    """Grupo de recarga do cliente para uma skill, ou None se fora da tabela."""
    if not 0<skill_id<12000:return None
    grupo=((skill_id-1)%960)//16
    return grupo if grupo<GRUPOS else None

def validar_regra(bruta):
    if not isinstance(bruta,dict):raise ValueError('Reacao invalida')
    r=dict(PADRAO);r.update({k:v for k,v in bruta.items() if k in PADRAO})
    if 'hp_max_pct' not in bruta and r['tipo'] in HP_PADRAO:r['hp_max_pct']=HP_PADRAO[r['tipo']]
    r['nome']=str(r['nome']).strip()[:40]
    tecla=str(r['tecla'] or '').strip().lower()
    if r['tipo'] not in TIPOS:raise ValueError('Tipo de reacao invalido: '+str(r['tipo']))
    if not isinstance(r['ativa'],bool) or not isinstance(r['so_em_combate'],bool):raise ValueError('Opcao invalida na reacao '+r['nome'])
    if r['ativa'] and not TECLA.fullmatch(tecla):raise ValueError('Tecla invalida na reacao '+(r['nome'] or '?')+': '+tecla+'. Use letras, numeros, F1 a F11 ou ctrl+/alt+/shift+ com uma tecla.')
    r['tecla']=tecla
    for campo,a,b in [('hp_max_pct',1,100),('mp_max_pct',1,100),('intervalo_s',.5,3600),('mobs_min',0,50),('mobs_raio_m',1,40),
                      ('mp_min',0,10_000_000),('skill_id',0,11999),('alvo_hp_min_pct',0,100),('alvo_hp_max_pct',1,100),('alcance_m',0,40)]:
        v=r[campo]
        if isinstance(v,bool) or not isinstance(v,(int,float)):raise ValueError(f'{campo} invalido na reacao {r["nome"]}')
        if not a<=v<=b:raise ValueError(f'{campo} fora do intervalo na reacao {r["nome"]}')
    if r['alvo_hp_min_pct']>=r['alvo_hp_max_pct']:raise ValueError('Vida do alvo: o minimo precisa ser menor que o maximo na reacao '+r['nome'])
    for c in ('hp_max_pct','mp_max_pct','intervalo_s','mobs_raio_m','alvo_hp_min_pct','alvo_hp_max_pct','alcance_m'):r[c]=float(r[c])
    r['mp_min']=int(r['mp_min']);r['mobs_min']=int(r['mobs_min']);r['skill_id']=int(r['skill_id'])
    return r

def validar_reacoes(lista,reservadas=()):
    """Valida a lista e impede teclas repetidas entre regras ativas ou com as teclas ja reservadas."""
    if not isinstance(lista,list) or len(lista)>20:raise ValueError('Reacoes: ate 20 regras')
    regras=[validar_regra(x) for x in lista];usadas=set(reservadas)
    for r in regras:
        if not r['ativa']:continue
        if r['tecla'] in usadas:raise ValueError('Atalho repetido nas reacoes: '+r['tecla'])
        usadas.add(r['tecla'])
    return regras

class Reacoes:
    def __init__(self,regras):
        self.indices={id(r):i for i,r in enumerate(regras)}
        ativas=[r for r in regras if r['ativa']]
        self.regras=[r for _,r in sorted(enumerate(ativas),key=lambda x:(PRIORIDADE[x[1]['tipo']],x[0]))]
        self.proximo_em={};self.falhas={};self.efeitos_ativos=None

    def atualizar_efeitos(self,ids):self.efeitos_ativos=set(ids) if ids is not None else None

    def __bool__(self):return bool(self.regras)

    def tem_cura(self):return any(r['tipo']=='cura' for r in self.regras)
    def tem_item(self,tipo):return any(r['tipo']==tipo for r in self.regras)

    def raio_mobs(self):
        """Maior raio de contagem pedido por uma regra com mobs_min, ou 0 se nenhuma precisa contar."""
        return max((r['mobs_raio_m'] for r in self.regras if r['mobs_min']),default=0.)

    def _pronta(self,regra,agora,recargas_grupos):
        if regra['tipo'] in ('buff','buff_combate','defesa') and regra['skill_id'] and self.efeitos_ativos is not None and regra['skill_id'] in self.efeitos_ativos:return False
        if agora<self.proximo_em.get(regra['nome'] or regra['tecla'],0.):return False
        grupo=grupo_de_recarga(regra['skill_id']) if regra['skill_id'] else None
        if regra['tipo']=='buff' and grupo is not None and (recargas_grupos is None or len(recargas_grupos)<=grupo):return False
        if grupo is not None and recargas_grupos is not None and len(recargas_grupos)>grupo:
            return recargas_grupos[grupo]==0
        return True

    def escolher(self,agora,hp,mp,mp_abs,em_combate,distancias_mobs,recargas_grupos,alvo=None,ofensivas_liberadas=True,buffs_liberados=True):
        """hp e mp em fracao (0..1); mp_abs em pontos; distancias_mobs = distancia de cada hostil perto (None se a
        leitura falhou); alvo = dict(hp_pct, dist) do alvo selecionado vivo e hostil, ou None."""
        if hp<=0:return None
        for r in self.regras:
            if self.avaliar(r,agora,hp,mp,mp_abs,em_combate,distancias_mobs,recargas_grupos,alvo,ofensivas_liberadas,buffs_liberados)['pronta']:return r
        return None

    def avaliar(self,r,agora,hp,mp,mp_abs,em_combate,distancias_mobs,recargas_grupos,alvo=None,ofensivas_liberadas=True,buffs_liberados=True):
        """A mesma avaliacao decide a acao e explica o fluxo; nao inventa telemetria."""
        precisa_alvo=r['tipo']=='ataque' or r['alvo_hp_min_pct']>0 or r['alvo_hp_max_pct']<100 or r['alcance_m']
        checks=dict(inicio=hp>0,
            hp=r['tipo']=='item_mp' or hp<=r['hp_max_pct']/100,
            mp_pct=r['tipo']!='item_mp' or mp<=r['mp_max_pct']/100,
            mp=mp_abs>=r['mp_min'],
            combate=not (r['so_em_combate'] or r['tipo'] in EM_COMBATE) or em_combate,
            mobs=not r['mobs_min'] or (distancias_mobs is not None and sum(d<=r['mobs_raio_m'] for d in distancias_mobs)>=r['mobs_min']),
            alvo=not precisa_alvo or (alvo is not None and r['alvo_hp_min_pct']<alvo['hp_pct']<=r['alvo_hp_max_pct']),
            alcance=not r['alcance_m'] or (alvo is not None and alvo['dist']<=r['alcance_m']),
            pronta=self._pronta(r,agora,recargas_grupos),
            agenda=(buffs_liberados if r['tipo']=='buff' else r['tipo'] not in EM_COMBATE or ofensivas_liberadas))
        motivos=dict(inicio='Personagem sem vida',hp='Vida acima do limite configurado',mp_pct='Mana acima do limite configurado',mp='Mana insuficiente',combate='Aguardando combate',mobs='Aguardando hostis no raio configurado',alvo='Aguardando alvo na faixa de vida',alcance='Alvo fora do alcance',pronta='Aguardando recarga ou intervalo',agenda='Aguardando a agenda de combate')
        bloqueio=next((k for k,v in checks.items() if not v),None)
        return dict(index=self.indices[id(r)],pronta=bloqueio is None,condicoes=checks,motivo=motivos[bloqueio] if bloqueio else 'Condições atendidas')

    def diagnostico(self,*args,escolhida=None,**kwargs):
        saida=[]
        for r in self.regras:
            d=self.avaliar(r,*args,**kwargs);d['escolhida']=r is escolhida
            if d['pronta']:d['motivo']='Ação liberada' if d['escolhida'] else 'Aguardando prioridade'
            saida.append(d)
        return saida

    def enviada(self,regra,agora):
        self.proximo_em[regra['nome'] or regra['tecla']]=agora+regra['intervalo_s']

    def recusada(self,regra,agora):
        # Uma recusa nao consome a recarga configurada e nao monopoliza a fila.
        chave=regra['nome'] or regra['tecla']
        self.proximo_em[chave]=agora+(.3 if regra['tipo'] in ('cura','emergencia','item_hp') else .75)

    def resultado(self,regra,ok,agora):
        """Recebe o veredito do VigiaReacao. Buff cujo cast nao registra espera cada vez mais para tentar de novo
        (ate 20x o intervalo); cura e defesa continuam no ritmo normal, pois repetir pode ser o que salva."""
        chave=regra['nome'] or regra['tecla']
        if ok:self.falhas[chave]=0;return
        self.falhas[chave]=self.falhas.get(chave,0)+1
        if regra['tipo'] in ('buff','buff_combate'):
            self.proximo_em[chave]=agora+regra['intervalo_s']*min(2**self.falhas[chave],20)

class VigiaReacao:
    """Confere se uma reacao enviada teve efeito no jogo e avisa quando a cura para de funcionar.

    O envio da tecla nao prova nada: no log de 22/11 o Remediar foi enviado 29 vezes sem gastar mana nem
    subir a vida e o personagem morreu. Uma reacao tem efeito se, em ate JANELA segundos, o cliente passa a
    conjurar a skill, o grupo de recarga dela sobe, a mana cai ou (para cura) a vida sobe. Itens e ataques
    nao tem sinal confiavel e ficam de fora."""
    JANELA=3.5
    ALERTA=4          # falhas seguidas que geram aviso
    ABORTAR=6         # falhas seguidas que, com vida baixa, encerram a caca
    HP_ABORTAR=.6
    SUBIDA_HP=.02
    QUEDA_MP=.005

    def __init__(self):
        self.pendentes=[];self.falhas=0;self.alertado=False

    @staticmethod
    def verificavel(regra):
        return bool(regra['skill_id']) and regra['tipo']!='ataque'

    def enviada(self,regra,agora,hp,mp_abs):
        if not self.verificavel(regra):return
        self.pendentes.append(dict(regra=regra,em=agora,hp=hp,mp=mp_abs))

    def observar(self,agora,hp,mp_abs,mp_max,casting_skill,recargas_grupos):
        """Devolve [(regra, ok)] das reacoes cujo veredito saiu agora; atualiza a sequencia de falhas."""
        saida=[];restantes=[]
        for x in self.pendentes:
            r=x['regra'];grupo=grupo_de_recarga(r['skill_id'])
            ok=(casting_skill==r['skill_id']
                or (grupo is not None and recargas_grupos is not None and len(recargas_grupos)>grupo and recargas_grupos[grupo]>0)
                or (bool(mp_max) and mp_abs<=x['mp']-self.QUEDA_MP*mp_max)
                or (r['tipo'] in ('cura','emergencia') and hp>=x['hp']+self.SUBIDA_HP))
            if ok:saida.append((r,True))
            elif agora-x['em']>=self.JANELA:saida.append((r,False))
            else:restantes.append(x)
        self.pendentes=restantes
        for _,ok in saida:
            if ok:self.falhas=0;self.alertado=False
            else:self.falhas+=1
        return saida

    def nivel(self,hp):
        """'ok', 'alerta' (primeira vez que atinge ALERTA) ou 'abortar'."""
        if self.falhas>=self.ABORTAR and hp<=self.HP_ABORTAR:return 'abortar'
        if self.falhas>=self.ALERTA and not self.alertado:self.alertado=True;return 'alerta'
        return 'ok'
