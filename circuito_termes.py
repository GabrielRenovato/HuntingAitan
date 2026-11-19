"""Circuito de Penza em Termes, com caminhos derivados da colisao local."""
import hashlib,json,math
from functools import lru_cache
from pathlib import Path

ARQUIVO=Path(__file__).resolve().with_name('circuito_termes_penza.json')

def distancia_segmento(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    t=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0.
    return math.dist(p,(a[0]+t*dx,a[1]+t*dy))

@lru_cache(maxsize=1)
def plano():
    d=json.loads(ARQUIVO.read_text(encoding='utf-8'))
    if d.get('schema')!=1 or len(d['trechos'])!=8:raise RuntimeError('Circuito de Termes invalido.')
    return d

def dentro_regiao(pos,margem=0):
    d=plano();pontos=[p['pos'] for p in d['pontos']]
    return min(distancia_segmento(pos,a,b) for a,b in zip(pontos,pontos[1:]))<=d['faixa']+margem

def conferir_arquivos(pasta):
    for nome,esperado in plano()['fontes'].items():
        p=Path(pasta)/nome
        if not p.is_file():raise RuntimeError('Arquivo de terreno ausente: '+nome)
        with p.open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=esperado:
            raise RuntimeError('Os dados de terreno mudaram: '+nome+'. Revalide o circuito antes de usar.')

class CircuitoTermes:
    def __init__(self,pos):
        if not dentro_regiao(pos):
            raise RuntimeError('Circuito de Termes: comece na faixa dos Penzas, por exemplo perto de 2652, 629 ou 2752, 635.')
        self.trechos=plano()['trechos'];self.voltas=0;self.espera_ate=None
        _,_,self.trecho,self.indice=min((math.dist(pos,p),j!=0,i,j) for i,t in enumerate(self.trechos) for j,p in enumerate(t['caminho']))

    def pausar(self,duracao):
        if self.espera_ate is not None:self.espera_ate+=duracao

    def destino(self,pos,agora):
        t=self.trechos[self.trecho];rota=t['caminho']
        if math.dist(pos,rota[-1])<=2:
            if self.espera_ate is None:self.espera_ate=agora+5
            if agora<self.espera_ate:return dict(estado='aguardar',ponto=t['ate'],voltas=self.voltas)
            self.trecho=(self.trecho+1)%len(self.trechos)
            if self.trecho==0:self.voltas+=1
            self.indice=0;self.espera_ate=None;t=self.trechos[self.trecho];rota=t['caminho']
        # A luta pode deslocar o personagem. Reencontra o trecho atual,
        # preservando o sentido e sem reiniciar o circuito no ponto 3.
        self.indice=min(range(max(0,self.indice-8),len(rota)),key=lambda i:math.dist(pos,rota[i]))
        alvo=min(self.indice+4,len(rota)-1)
        return dict(estado='andar',destino=tuple(rota[alvo]),chave=('circuito',self.trecho,alvo),ponto=t['ate'],voltas=self.voltas)
