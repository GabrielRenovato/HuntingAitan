"""Circuito leste sem os mutantes misturados aos Verits normais."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.visitas_circuito import VisitasCircuito
from huntingaitan.rotas.circuito_termes import CircuitoTermes,distancia_segmento

ORDEM=(15,14,7,17,16,6,11)

@lru_cache(maxsize=1)
def plano_leste():
    d=json.loads((DADOS/'circuito_termes_verit_leste.json').read_text(encoding='utf-8'))
    if d.get('schema')!=1 or not d.get('fechado') or tuple(p['id'] for p in d['pontos'])!=ORDEM:raise RuntimeError('Circuito Verit leste invalido')
    if [(t['de'],t['ate']) for t in d['trechos']]!=list(zip(ORDEM,ORDEM[1:]+ORDEM[:1])):raise RuntimeError('Circuito leste sem fechamento')
    return d

def dentro_leste(pos,margem=0):
    d=plano_leste();pontos=[p['pos'] for p in d['pontos']]
    if any(math.dist(pos,m['pos'])<=d['raio_normais'] for m in d['normais']):return False
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]+pontos[:1]))<=d['faixa']+margem

def conferir_leste(pasta):
    for nome,h in plano_leste()['fontes'].items():
        p=Path(pasta)/nome
        if not p.is_file():raise RuntimeError('Arquivo do circuito leste ausente: '+nome)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=h:raise RuntimeError('Dados de Termes alterados: '+nome+'. Revalide o circuito.')

class CircuitoVeritLeste(VisitasCircuito,CircuitoTermes):
    contem=staticmethod(dentro_leste)
    def __init__(self,pos):
        if not dentro_leste(pos):raise RuntimeError('Comece na regiao leste dos Verits, por exemplo 2864, 821 ou 2889, 794.')
        self.trechos=plano_leste()['trechos'];self.voltas=0;self.espera_ate=None
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))
        self.iniciar_visitas(plano_leste()['pontos'])

    def aplicar_grade(self,grade,pos):
        from huntingaitan.rotas.evitar_mobs import aplicar_zonas
        d=plano_leste()
        return aplicar_zonas(grade,[m['pos'] for m in d['normais']],d['raio_normais'],saida=pos)
