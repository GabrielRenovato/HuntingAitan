"""Circuito fechado de Verit Mutante em Termes."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path
from circuito_termes import CircuitoTermes,distancia_segmento

ARQUIVO=Path(__file__).resolve().parent/'dados'/'circuito_termes_verit.json'

@lru_cache(maxsize=1)
def plano_verit():
    d=json.loads(ARQUIVO.read_text(encoding='utf-8'))
    if d.get('schema')!=1 or not d.get('fechado') or len(d['trechos'])!=len(d['pontos']) or len(d['pontos'])<2:raise RuntimeError('Circuito Verit invalido')
    ids=[p['id'] for p in d['pontos']]
    if [(t['de'],t['ate']) for t in d['trechos']]!=list(zip(ids,ids[1:]+ids[:1])):raise RuntimeError('Circuito Verit sem fechamento valido')
    return d

def dentro_verit(pos,margem=0):
    d=plano_verit();pontos=[p['pos'] for p in d['pontos']]
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]+pontos[:1]))<=d['faixa']+margem

def conferir_verit(pasta):
    for n,h in plano_verit()['fontes'].items():
        p=Path(pasta)/n
        if not p.is_file():raise RuntimeError('Arquivo do circuito Verit ausente: '+n)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=h:raise RuntimeError('Os dados de Termes mudaram: '+n+'. Revalide o circuito Verit.')

class CircuitoVerit(CircuitoTermes):
    def __init__(self,pos):
        if not dentro_verit(pos):raise RuntimeError('Circuito Verit: comece perto dos pontos marcados, por exemplo 2748, 833 ou 2779, 844.')
        self.trechos=plano_verit()['trechos'];self.voltas=0;self.espera_ate=None
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))
