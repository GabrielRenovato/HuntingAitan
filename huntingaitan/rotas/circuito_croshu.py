"""Circuito de Croshu Mutante em Ungor com afastamento dos Croshus nao mutantes."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.circuito_termes import CircuitoTermes,distancia_segmento
from huntingaitan.rotas.evitar_mobs import aplicar_zonas,fora_das_zonas

ARQUIVO=DADOS/'circuito_ungor_croshu.json'
NOMES_MENORES={'Croshu Cinzento','Croshu Canino'}

@lru_cache(maxsize=1)
def plano_croshu():
    d=json.loads(ARQUIVO.read_text(encoding='utf-8'))
    if d.get('schema')!=1 or not d.get('fechado') or [p['id'] for p in d['pontos']]!=[6,3,7]:raise RuntimeError('Circuito de Croshu invalido')
    if [(t['de'],t['ate']) for t in d['trechos']]!=[(6,3),(3,7),(7,6)]:raise RuntimeError('Circuito de Croshu sem fechamento valido')
    if d.get('ponto_excluido')!=5 or d.get('raio_menores')!=10 or not d.get('menores'):raise RuntimeError('Afastamento dos Croshus menores ausente')
    return d

def dentro_croshu(pos,margem=0):
    d=plano_croshu();pontos=[p['pos'] for p in d['pontos']]
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]+pontos[:1]))<=d['faixa']+margem

def longe_menores(pos):
    d=plano_croshu()
    return fora_das_zonas(pos,[m['pos'] for m in d['menores']],d['raio_menores'])

def conferir_croshu(pasta):
    for nome,esperado in plano_croshu()['fontes'].items():
        p=Path(pasta)/nome
        if not p.is_file():raise RuntimeError('Arquivo do circuito de Croshu ausente: '+nome)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=esperado:raise RuntimeError('Os dados de Ungor mudaram: '+nome+'. Revalide o circuito de Croshu.')

class CircuitoCroshu(CircuitoTermes):
    contem=staticmethod(dentro_croshu)

    def __init__(self,pos):
        if not dentro_croshu(pos) or not longe_menores(pos):raise RuntimeError('Comece perto de 1895, 1155 em Ungor, afastado dos Croshus menores. O ponto 5 foi excluido.')
        self.trechos=plano_croshu()['trechos'];self.voltas=0;self.espera_ate=None;self.menores_vivos=[]
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))

    def atualizar_menores(self,mobs):
        self.menores_vivos=[m['position'] for m in mobs if m['name'] in NOMES_MENORES and m['hp']>0]

    def permite(self,pos,saida=None):
        centros=[m['pos'] for m in plano_croshu()['menores']]+self.menores_vivos
        if fora_das_zonas(pos,centros,plano_croshu()['raio_menores']):return True
        return saida is not None and tuple(map(math.floor,pos))==tuple(map(math.floor,saida))

    def aplicar_grade(self,grade,dados,pos):
        player=dados.snapshot()['player']
        self.atualizar_menores(dados.listar_mobs(pos,60,player))
        centros=[m['pos'] for m in plano_croshu()['menores']]+self.menores_vivos
        return aplicar_zonas(grade,centros,plano_croshu()['raio_menores'],saida=pos)
