"""Caminho do save atual ate o portal, derivado da grade dos arquivos locais."""
import math,struct
from pathlib import Path
from navegacao_grade import Grade
from circuito_termes import distancia_segmento
from geometria_entrada import GeometriaEntrada

PORTAL=(2716.,1611.)
EIXO_ESTRADA=((2696.5,1715.5),(2699.5,1675.5),(2708.5,1645.5),PORTAL)

def passagem_estrada(pos):
    if not 1614<=pos[1]<=1718:return True
    return min(distancia_segmento(pos,a,b) for a,b in zip(EIXO_ESTRADA,EIXO_ESTRADA[1:]))<=3

def recuo_caixas(pos):return (2709.5,min(1689.5,max(1685.5,pos[1]+2)))

class EntradaMina:
    def __init__(self,pasta,pos,bloqueadores=()):
        if not(2400<pos[0]<2850 and 1500<pos[1]<2000):raise RuntimeError('Save fora da regiao validada para a entrada da Mina.')
        p=Path(pasta)/'Env';a=(p/'AttributeS01.dat').read_bytes();h=(p/'z01.hgt').read_bytes()
        if len(a)!=4096*4096*2 or len(h)!=4+4096*4096*2:raise RuntimeError('Terreno externo diferente do validado.')
        x0=max(0,math.floor(min(pos[0],PORTAL[0]))-40);x1=min(4095,math.ceil(max(pos[0],PORTAL[0]))+40)
        y0=max(0,math.floor(min(pos[1],PORTAL[1]))-40);y1=min(4095,math.ceil(max(pos[1],PORTAL[1]))+40)
        w=x1-x0+1;flags=bytearray();alturas=[]
        for y in range(y0,y1+1):
            off=(y*4096+x0)*2;flags.extend(a[off:off+w*2:2]);alturas.extend(struct.unpack_from('<'+'h'*w,h,off+4))
        g=Grade((0,0),(x0,y0),w,y1-y0+1,bytes(flags),tuple(alturas),1)
        self.geometria=GeometriaEntrada(pasta);g=self.geometria.aplicar(g)
        recuo=recuo_caixas(pos) if 1679<=pos[1]<=1687 and pos[0]>=2712 else None
        if recuo is not None:
            saida=g.caminho(pos,recuo,alcance=.5,limite=lambda q:passagem_estrada(q) or distancia_segmento(q,pos,recuo)<=2)
            if not saida:raise RuntimeError('Sem passagem validada para sair do canto das caixas.')
        # Guias do centro da estrada impedem que o menor caminho do terreno
        # corte pelo patio da caixa-dagua e das caixas, fora da estrada.
        metas=[q for q in EIXO_ESTRADA[:-1] if q[1]<pos[1]-1]+[PORTAL]
        rota=[];origem=recuo or pos
        for i,meta in enumerate(metas):
            limite=lambda q,a=origem,b=meta,i=i:passagem_estrada(q) or (i==0 and distancia_segmento(q,a,b)<=(12 if recuo is not None else 3))
            trecho=g.caminho(origem,meta,alcance=3 if meta==PORTAL else 1,max_nos=w*(y1-y0+1),limite=limite)
            if not trecho:raise RuntimeError('Sem passagem validada pelo centro da estrada ate a Mina.')
            rota.extend(trecho if not rota else trecho[1:]);origem=trecho[-1]
        if not rota or not all(g.passagem(g.celula(a),g.celula(b)) for a,b in zip(rota,rota[1:])):raise RuntimeError('Sem passagem validada do save atual ate o portal da Mina.')
        self.rota=rota;self.trechos=[dict(ate='entrada',caminho=rota)];self.trecho=0;self.voltas=0;self.indice=0
        self.bloqueadores=set(bloqueadores);self.bloqueio_em=-float('inf')
        self.grade=g;self.trilha=[tuple(pos)];self.obstaculos=[];self.recuo=recuo;self.revisao=0

    def passagem(self,pos):
        return passagem_estrada(pos) and (not hasattr(self,'geometria') or self.geometria.livre(pos)) and all(math.dist(pos,c)>1.15 for c in self.obstaculos)

    def observar_navegacao(self,pos,agora,plano):
        if math.dist(pos,PORTAL)<=8 and plano['estado'] in ('replanejar','bloqueado'):
            self.bloqueio_em=agora
        if plano['estado'] not in ('replanejar','bloqueado') or math.dist(pos,PORTAL)<=8:return False
        if not hasattr(self,'grade') or self.recuo is not None:return False
        alvo=plano.get('ponto')
        if alvo is None:return False
        dx,dy=alvo[0]-pos[0],alvo[1]-pos[1];dist=math.hypot(dx,dy)
        if dist<.5:return False
        # A colisao foi confirmada pelo deslocamento real com W enviado.
        # Exclui a pequena area a frente e volta a um ponto ja percorrido.
        centro=(pos[0]+dx/dist*1.8,pos[1]+dy/dist*1.8)
        novos=self.obstaculos+[centro]
        livre=lambda p:passagem_estrada(p) and all(math.dist(p,c)>1.15 for c in novos)
        anteriores=[p for p in reversed(self.trilha) if 2<=math.dist(pos,p)<=5 and livre(p)]
        recuo=anteriores[0] if anteriores else (pos[0]-dx/dist*2.5,pos[1]-dy/dist*2.5)
        if not livre(recuo):return False
        retorno=self.grade.caminho(pos,recuo,alcance=.5,limite=livre)
        rota=self.grade.caminho(recuo,PORTAL,alcance=3,max_nos=self.grade.largura*self.grade.altura,limite=livre)
        if not retorno or not rota:return False
        self.obstaculos=novos[-12:];self.recuo=tuple(recuo);self.revisao+=1
        self.rota=rota;self.trechos[0]['caminho']=rota;self.indice=0
        return True

    def permite_combate(self,id_,pos,alvo=None):
        return id_ in self.bloqueadores and math.dist(pos,PORTAL)<=8 and (alvo is None or math.dist(alvo['position'],PORTAL)<=8)

    def filtrar_mobs(self,mobs,pos,agora):
        if math.dist(pos,PORTAL)>8:return []
        if agora-self.bloqueio_em<=3:
            # A ausencia de movimento precisa ter sido confirmada pelo
            # navegador. Proximidade sozinha nao autoriza iniciar combate.
            for m in mobs:
                if math.dist(pos,m['position'])<=3.5 and distancia_segmento(m['position'],pos,PORTAL)<=1.5:
                    self.bloqueadores.add(m['id'])
        return [m for m in mobs if self.permite_combate(m['id'],pos,m)]

    def contem(self,pos,margem=0):
        if margem==0 and not self.passagem(pos):return False
        rota=self.rota
        if self.recuo is not None:rota=[self.trilha[-1],self.recuo]+rota
        if len(rota)==1:return math.dist(pos,rota[0])<=12+margem
        return min(distancia_segmento(pos,a,b) for a,b in zip(rota,rota[1:]))<=12+margem

    def pausar(self,*args):pass

    def destino(self,pos,agora):
        if math.dist(pos,PORTAL)<=4.:return dict(estado='concluido',ponto='entrada',voltas=0)
        if math.dist(pos,self.trilha[-1])>=1:self.trilha.append(tuple(pos));self.trilha=self.trilha[-24:]
        if 1679<=pos[1]<=1687 and pos[0]>=2712 and self.recuo is None:
            # Tambem permite retomar uma execucao que ja comecou presa ali.
            self.recuo=recuo_caixas(pos)
            self.revisao+=1
        if self.recuo is not None:
            if math.dist(pos,self.recuo)>1.:
                return dict(estado='andar',ponto='entrada',voltas=0,destino=self.recuo,chave=('circuito','recuo_entrada',self.revisao))
            self.recuo=None
        i=min(range(max(0,self.indice-8),len(self.rota)),key=lambda i:math.dist(pos,self.rota[i]))
        self.indice=max(self.indice,i) if math.dist(pos,self.rota[i])<=4 else i
        alvo=self.indice;dist=0.
        while alvo+1<len(self.rota) and dist<8:dist+=math.dist(self.rota[alvo],self.rota[alvo+1]);alvo+=1
        return dict(estado='andar',ponto='entrada',voltas=0,destino=tuple(self.rota[alvo]),chave=('circuito','entrada',self.revisao))
