"""Etapas transacionais do reparo e da venda; nao interpreta clique como sucesso."""
from dataclasses import dataclass
import re,unicodedata
from huntingaitan.rotas.entrada_jardim import EntradaJardim
import math

NPC=(1892.,1066.)
ALCANCE_NPC=5.

class RotaLuis(EntradaJardim):
    def __init__(self,pasta,pos,bloqueadores=()):
        super().__init__(pasta,pos,bloqueadores,destino=NPC,cadastro=(2034,1892,1066),nome='Luis Mandez')

    def destino(self,pos,agora):
        if math.dist(pos,self.portal)<=ALCANCE_NPC:
            return dict(estado='concluido',ponto='entrada_jardim',voltas=0)
        return super().destino(pos,agora)

def normalizar(texto):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',texto.lower()).encode('ascii','ignore').decode())

def distancia_nome(a,b):
    a,b=normalizar(a),normalizar(b)
    anterior=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        atual=[i]
        for j,cb in enumerate(b,1):atual.append(min(atual[-1]+1,anterior[j]+1,anterior[j-1]+(ca!=cb)))
        anterior=atual
    return anterior[-1]

def nome_corresponde(lido,esperado,alternativas=()):
    a,b=normalizar(lido),normalizar(esperado)
    if a==b:return True
    if min(len(a),len(b))<10 or distancia_nome(a,b)!=1:return False
    # Uma letra perdida pelo OCR so e aceita quando nao aponta para outro
    # equipamento carregado com nome igual ou mais proximo.
    return all(distancia_nome(a,n)>1 for n in set(map(normalizar,alternativas)) if n!=b)

def inteiro_moeda(texto):
    texto=texto.strip()
    if not re.fullmatch(r'\d+(?:[., ]\d{3})*',texto):return None
    return int(re.sub(r'\D','',texto))

def durabilidade(textos):
    # O OCR costuma omitir o primeiro l: "Durabiidade".
    m=re.search(r'durabi[l1i]?id(?:ade|ad)\s*:?\s*(\d+)\s*/\s*(\d+)', ' '.join(textos),re.I)
    if not m:return None
    atual,maxima=map(int,m.groups())
    return (atual,maxima) if 0<=atual<=maxima<=255 and maxima>0 else None

def avaliar_equipamento(nome,textos):
    """Recebe apenas a descricao do item da mochila, sem o painel equipado."""
    if not nome or not textos:return False,'Descricao do item indisponivel'
    linhas=[t.strip() for t in textos if t.strip()];titulo=linhas[0];n=normalizar(' '.join(linhas))
    if not nome_corresponde(re.sub(r'[+＋]\s*\d+','',titulo),nome):return False,'Nome da descricao diferente da venda'
    if re.search(r'[+＋]\s*[1-9]\d*',titulo):return False,'Equipamento refinado'
    if any(v in n for v in ('equipeditem','equippeditem','itemequipado')):return False,'Painel de equipamento equipado'
    if any(v in n for v in ('vinculado','bound','naopodesernegociado','intransferivel','naonegociavel','bloqueado','locked')):
        return False,'Item vinculado ou bloqueado'
    if durabilidade(linhas) is None:
        return False,'Durabilidade nao identificada; nao confirmado como equipamento'
    if not any(re.search(r'clas[se]{1,2}\s*:',t,re.I) for t in linhas):return False,'Classe do equipamento nao identificada'
    return True,'Equipamento da mochila identificado'

@dataclass
class TransacaoNPC:
    reparado:bool=False
    ouro_antes:int|None=None
    custo:int|None=None
    item:str|None=None
    preco:int|None=None
    vendidos:int=0

    def preparar_reparo(self,ouro,custo):
        if not isinstance(ouro,int) or not isinstance(custo,int) or custo<0 or ouro<custo:return False
        self.ouro_antes=ouro;self.custo=custo;self.reparado=False;return True

    def confirmar_reparo(self,ouro,dialogo_fechado,erro=False):
        self.reparado=bool(not erro and dialogo_fechado and self.custo is not None and self.ouro_antes is not None and ouro==self.ouro_antes-self.custo)
        return self.reparado

    def preparar_venda(self,nome,preco,descricao,ouro):
        ok,motivo=avaliar_equipamento(nome,descricao)
        if not self.reparado:return False,'Reparo ainda nao confirmado'
        if not ok:return False,motivo
        if not isinstance(preco,int) or preco<=0 or not isinstance(ouro,int):return False,'Preco ou saldo indisponivel'
        self.item=nome;self.preco=preco;self.ouro_antes=ouro;return True,'Venda preparada'

    def mesma_venda(self,nome,preco):return self.item==nome and self.preco==preco and self.preco is not None

    def confirmar_venda(self,ouro,item_removido):
        if self.item is None or self.preco is None or not item_removido or ouro!=self.ouro_antes+self.preco:return False
        self.vendidos+=1;self.item=None;self.preco=None;return True
