"""Percurso unico da primeira Mina, com combate e conclusao por abates confirmados."""
import hashlib,heapq,json,math,struct,unicodedata
from functools import lru_cache
from pathlib import Path
from navegacao_grade import Grade
from circuito_termes import distancia_segmento

@lru_cache(maxsize=1)
def plano_mina():return json.loads(Path(__file__).resolve().with_name('mina_lenfer_rota.json').read_text(encoding='utf-8'))

def dentro_mina(pos,margem=0):
    x0,y0,x1,y1=plano_mina()['limites']
    return x0-margem<=pos[0]<x1+margem and y0-margem<=pos[1]<y1+margem

def normalizar(nome):return ''.join(c for c in unicodedata.normalize('NFKD',nome.lower()) if 'a'<=c<='z')

class MinaLenfer:
    def __init__(self,pos):
        d=plano_mina()
        if not dentro_mina(pos):raise RuntimeError('Mina LEnfer: entre na primeira area antes de iniciar o caminho para Malik.')
        self.inicio=tuple(pos);self.trechos=d['trechos'];self.pontos=d['pontos'];self.trecho=0;self.indice=0;self.voltas=0
        self.espera_ate=None;self.abates={};self.grade=None;self.custo_origem=None;self.custos={};self.concluida=False
        self.rota_planejada=self.trechos[0]['caminho'];self.indice=min(range(len(self.rota_planejada)),key=lambda i:math.dist(pos,self.rota_planejada[i]))

    def conferir(self,pasta):
        for nome,sha in plano_mina()['fontes'].items():
            f=Path(pasta)/nome
            if not f.is_file():raise RuntimeError('Arquivo da Mina ausente: '+nome)
            with f.open('rb') as stream:atual=hashlib.file_digest(stream,'sha256').hexdigest()
            if atual!=sha:raise RuntimeError('Dados da Mina mudaram; revalide a rota: '+nome)
        a=(Path(pasta)/'Env/z011113.att').read_bytes();h=(Path(pasta)/'Env/z011113.hgt').read_bytes()
        self.grade=Grade(tuple(plano_mina()['origem']),(0,0),256,256,a[::2],struct.unpack('<65536h',h),1)
        rota=self.grade.caminho(self.inicio,self.pontos[-1]['pos'],max_nos=65536)
        if not rota:raise RuntimeError('Sem passagem estatica da posicao atual ate a sala final da Mina.')
        self.trechos=[dict(ate=self.pontos[-1]['id'],caminho=rota)];self.rota_planejada=rota;self.indice=0

    def filtrar_mobs(self,mobs,pos,raio):
        if not mobs:return []
        if self.grade is None:raise RuntimeError('Grade da Mina ainda nao conferida.')
        # Segue o corredor em vez de interromper a marcha para perseguir
        # mobs distantes. Malik conserva o alcance configurado.
        chefe_presente=any(normalizar(m['name']).startswith('malik') for m in mobs)
        raio=min(raio,50 if chefe_presente else 12)
        origem=self.grade.celula(pos);chave=(origem,raio)
        if chave!=self.custo_origem:
            custos={origem:0.};fila=[(0.,origem)];vistos=set()
            while fila:
                custo,c=heapq.heappop(fila)
                if c in vistos:continue
                vistos.add(c)
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    n=c[0]+dx,c[1]+dy;novo=custo+math.hypot(dx,dy)
                    if novo>raio or n in vistos or not self.grade.passagem(c,n):continue
                    if novo<custos.get(n,float('inf')):custos[n]=novo;heapq.heappush(fila,(novo,n))
            self.custos=custos;self.custo_origem=chave
        validos=[]
        for m in mobs:
            malik=normalizar(m['name']).startswith('malik')
            # O objetivo e chegar ao chefe. Evita abandonar a rota para limpar
            # salas laterais; Malik tem prioridade quando for reconhecido.
            distancia_rota=min((distancia_segmento(m['position'],a,b) for a,b in zip(self.rota_planejada,self.rota_planejada[1:])),default=math.dist(m['position'],self.rota_planejada[0]))
            if not malik and distancia_rota>12:continue
            c=self.grade.celula(m['position'])
            custo=min((self.custos.get((c[0]+dx,c[1]+dy),float('inf')) for dx in range(-2,3) for dy in range(-2,3) if dx*dx+dy*dy<=4),default=float('inf'))
            if custo<=min(raio,50 if malik else 12):validos.append(m)
        chefes=[m for m in validos if normalizar(m['name']).startswith('malik')]
        return chefes or validos

    def combate_ativo(self):self.espera_ate=None

    def registrar_abate(self,id_,nome,pos,agora):
        if normalizar(nome).startswith('malik') and dentro_mina(pos):
            self.abates['malik']=dict(id=id_,nome=nome,pos=pos,tempo=agora)
            self.espera_ate=None
            return 'malik'
        return None

    def pausar(self,duracao):
        if self.espera_ate is not None:self.espera_ate+=duracao

    def destino(self,pos,agora):
        if self.concluida:return dict(estado='concluido',ponto=self.pontos[-1]['id'],voltas=0,abates=self.abates)
        t=self.trechos[self.trecho];p=self.pontos[self.trecho];rota=t['caminho']
        if 'malik' in self.abates or math.dist(pos,p['pos'])<=3:
            if p['chefe'] and p['chefe'] not in self.abates:
                return dict(estado='aguardar_chefe',ponto=p['id'],voltas=0,chefe=p['chefe'])
            if self.espera_ate is None:self.espera_ate=agora+p['espera']
            if agora<self.espera_ate:return dict(estado='aguardar',ponto=p['id'],voltas=0)
            if self.trecho==len(self.trechos)-1:
                if 'malik' not in self.abates:return dict(estado='aguardar_confirmacao',ponto=p['id'],voltas=0)
                self.concluida=True
                return dict(estado='concluido',ponto=p['id'],voltas=0,abates=self.abates)
            self.trecho+=1;self.indice=0;self.espera_ate=None
            t=self.trechos[self.trecho];p=self.pontos[self.trecho];rota=t['caminho']
        proximo=min(range(max(0,self.indice-8),len(rota)),key=lambda i:math.dist(pos,rota[i]))
        self.indice=max(self.indice,proximo) if math.dist(pos,rota[proximo])<=4 else proximo
        alvo=self.indice;dist=0.
        while alvo+1<len(rota) and dist<8:dist+=math.dist(rota[alvo],rota[alvo+1]);alvo+=1
        return dict(estado='andar',destino=tuple(rota[alvo]),chave=('circuito',self.trecho),ponto=p['id'],voltas=0)
