"""Volta fechada pelas quatro Plantas Mutantes de Ungor, com terreno validado."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.circuito_termes import CircuitoTermes,distancia_segmento

ARQUIVO=DADOS/'circuito_ungor_plantas.json'

@lru_cache(maxsize=1)
def plano_plantas():
    d=json.loads(ARQUIVO.read_text(encoding='utf-8'))
    if d.get('schema')!=1 or not d.get('fechado') or [p['id'] for p in d['pontos']]!=[7,8,9,10]:raise RuntimeError('Circuito de Plantas invalido')
    if [(t['de'],t['ate']) for t in d['trechos']]!=[(7,8),(8,9),(9,10),(10,7)]:raise RuntimeError('Circuito de Plantas sem fechamento valido')
    return d

def dentro_plantas(pos,margem=0):
    d=plano_plantas();pontos=[p['pos'] for p in d['pontos']]
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]+pontos[:1]))<=d['faixa']+margem

def conferir_plantas(pasta):
    for nome,esperado in plano_plantas()['fontes'].items():
        p=Path(pasta)/nome
        if not p.is_file():raise RuntimeError('Arquivo do circuito de Plantas ausente: '+nome)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=esperado:raise RuntimeError('Os dados de Ungor mudaram: '+nome+'. Revalide o circuito das Plantas.')

class CircuitoPlantas(CircuitoTermes):
    contem=staticmethod(dentro_plantas)

    def __init__(self,pos):
        if not dentro_plantas(pos):raise RuntimeError('Comece perto de 2440, 1360 na Floresta Ungor para percorrer as quatro Plantas Mutantes.')
        self.trechos=plano_plantas()['trechos'];self.voltas=0;self.espera_ate=None
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))
