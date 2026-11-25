"""Circuito independente dos seis Croshus do sul da Floresta Cinzenta."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.visitas_circuito import VisitasCircuito
from huntingaitan.rotas.circuito_termes import CircuitoTermes,distancia_segmento

ARQUIVO=DADOS/'circuito_cinzenta_croshu_sul.json'
ORDEM=(6,2,1,3,5,4)

@lru_cache(maxsize=1)
def plano_cinzas_sul():
    d=json.loads(ARQUIVO.read_text(encoding='utf-8'))
    if d.get('schema')!=1 or not d.get('fechado') or tuple(p['id'] for p in d['pontos'])!=ORDEM:raise RuntimeError('Circuito sul dos seis Croshus invalido')
    if [(t['de'],t['ate']) for t in d['trechos']]!=list(zip(ORDEM,ORDEM[1:]+ORDEM[:1])):raise RuntimeError('Circuito sul dos seis Croshus sem fechamento valido')
    return d

def dentro_cinzas_sul(pos,margem=0):
    d=plano_cinzas_sul();pontos=[p['pos'] for p in d['pontos']]
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]+pontos[:1]))<=d['faixa']+margem

def conferir_cinzas_sul(pasta):
    for nome,esperado in plano_cinzas_sul()['fontes'].items():
        p=Path(pasta)/nome
        if not p.is_file():raise RuntimeError('Arquivo do circuito sul ausente: '+nome)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=esperado:raise RuntimeError('Os dados da Floresta Cinzenta mudaram: '+nome+'. Revalide o circuito sul.')

class CircuitoCinzasSul(VisitasCircuito,CircuitoTermes):
    contem=staticmethod(dentro_cinzas_sul)

    def __init__(self,pos):
        if not dentro_cinzas_sul(pos):raise RuntimeError('Comece perto de 2955, 1311 ou de outro trecho do circuito sul dos seis Croshus.')
        self.trechos=plano_cinzas_sul()['trechos'];self.voltas=0;self.espera_ate=None
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))
        self.iniciar_visitas(plano_cinzas_sul()['pontos'])
