"""Busca ativa dos tres Croshus das Cinzas, sem abandonar um ponto nao visitado."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.visitas_circuito import VisitasCircuito
from huntingaitan.rotas.circuito_termes import CircuitoTermes,distancia_segmento

ARQUIVO=DADOS/'circuito_cinzenta_croshu.json'

@lru_cache(maxsize=1)
def plano_cinzas():
    d=json.loads(ARQUIVO.read_text(encoding='utf-8'))
    if d.get('schema')!=1 or not d.get('fechado') or [p['id'] for p in d['pontos']]!=[7,8,9]:raise RuntimeError('Busca dos tres Croshus invalida')
    if [(t['de'],t['ate']) for t in d['trechos']]!=[(7,8),(8,9),(9,7)]:raise RuntimeError('Busca dos tres Croshus sem fechamento valido')
    return d

def dentro_cinzas(pos,margem=0):
    d=plano_cinzas();pontos=[p['pos'] for p in d['pontos']]
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]+pontos[:1]))<=d['faixa']+margem

def conferir_cinzas(pasta):
    for nome,esperado in plano_cinzas()['fontes'].items():
        p=Path(pasta)/nome
        if not p.is_file():raise RuntimeError('Arquivo da busca dos Croshus ausente: '+nome)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=esperado:raise RuntimeError('Os dados da Floresta Cinzenta mudaram: '+nome+'. Revalide o percurso.')

class CircuitoCinzas(VisitasCircuito,CircuitoTermes):
    contem=staticmethod(dentro_cinzas)

    def __init__(self,pos):
        if not dentro_cinzas(pos):raise RuntimeError('Comece perto de 2882, 1154 na Floresta Cinzenta para buscar os tres Croshus.')
        self.trechos=plano_cinzas()['trechos'];self.voltas=0;self.espera_ate=None
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))

        self.iniciar_visitas(plano_cinzas()['pontos'])
