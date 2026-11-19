"""Caminho do save atual ate o portal, derivado da grade dos arquivos locais."""
import math,struct
from pathlib import Path
from navegacao_grade import Grade
from circuito_termes import distancia_segmento

PORTAL=(2716.,1611.)

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
        rota=g.caminho(pos,PORTAL,alcance=3,max_nos=w*(y1-y0+1))
        if not rota or not all(g.passagem(g.celula(a),g.celula(b)) for a,b in zip(rota,rota[1:])):raise RuntimeError('Sem passagem validada do save atual ate o portal da Mina.')
        self.rota=rota;self.trechos=[dict(ate='entrada',caminho=rota)];self.trecho=0;self.voltas=0;self.indice=0
        self.bloqueadores=set(bloqueadores);self.bloqueio_em=-float('inf')

    def observar_navegacao(self,pos,agora,plano):
        if math.dist(pos,PORTAL)<=8 and plano['estado'] in ('replanejar','bloqueado'):
            self.bloqueio_em=agora

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
        if len(self.rota)==1:return math.dist(pos,self.rota[0])<=12+margem
        return min(distancia_segmento(pos,a,b) for a,b in zip(self.rota,self.rota[1:]))<=12+margem

    def pausar(self,*args):pass

    def destino(self,pos,agora):
        if math.dist(pos,PORTAL)<=4.:return dict(estado='concluido',ponto='entrada',voltas=0)
        i=min(range(max(0,self.indice-8),len(self.rota)),key=lambda i:math.dist(pos,self.rota[i]))
        self.indice=max(self.indice,i) if math.dist(pos,self.rota[i])<=4 else i
        alvo=self.indice;dist=0.
        while alvo+1<len(self.rota) and dist<8:dist+=math.dist(self.rota[alvo],self.rota[alvo+1]);alvo+=1
        return dict(estado='andar',ponto='entrada',voltas=0,destino=tuple(self.rota[alvo]),chave=('circuito','entrada'))
