"""Conferencias transacionais do Favor de Giovanni, independentes da interface."""
import math,re,unicodedata

NPC=(3442.,688.)
CIDADE=(3399.,564.)
TERMES=(2681.,683.)
CUSTO=50000
EFEITOS=frozenset((8500,8501,9607))

def zona_cidade(pos):return math.dist(pos,CIDADE)<260

def opcao_favor(texto):
    # OCR confunde apenas zeros do preco com a letra O. Mantem nome, moeda,
    # cinco algarismos e todos os outros numeros estritamente conferidos.
    nome=re.sub('[^a-z0-9]','',texto.lower())
    return bool(re.fullmatch(r'favordegiovanni5[0o]{4}oro',nome))

def opcao_gratuita(texto):
    texto=''.join(c for c in unicodedata.normalize('NFKD',texto.lower()) if not unicodedata.combining(c))
    return re.sub('[^a-z0-9]','',texto)=='bendiciondegiovanni'

def pode_usar_cidade(player,mobs,controle):
    if mobs is None or any(math.dist(player['position'],m['position'])<35 for m in mobs if m['hp']>0):return False
    if player['hp']<=0 or player['hp']/player['hp_max']<.8:return False
    return not any(controle.get(k) for k in ('casting','stunned','paralyzed','frozen'))

class CompraGiovanni:
    def __init__(self,ouro,efeitos,custo=CUSTO):
        if custo not in (0,CUSTO):raise ValueError('Custo nao permitido para renovacao')
        if ouro<custo:raise ValueError('Saldo insuficiente para Favor de Giovanni')
        if EFEITOS.intersection(efeitos):raise ValueError('Bencao de Giovanni ja ativa; nao repetir compra no teste')
        self.ouro=ouro;self.efeitos=set(efeitos);self.custo=custo

    def conferir(self,ouro,efeitos):
        novos=EFEITOS.intersection(set(efeitos)-self.efeitos)
        if ouro==self.ouro-self.custo and len(novos)==1:return next(iter(novos))
        return None
