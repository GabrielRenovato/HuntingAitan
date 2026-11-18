"""Planejamento local independente usando a grade de colisao lida do cliente."""
import math,heapq,struct
from dataclasses import dataclass

@dataclass
class Grade:
    origem:tuple
    canto:tuple
    largura:int
    altura:int
    flags:bytes
    alturas:tuple
    mapa:int
    def indice(self,p):
        x,y=p;x-=self.canto[0];y-=self.canto[1]
        return y*self.largura+x if 0<=x<self.largura and 0<=y<self.altura else None
    def celula(self,p):return (math.floor(p[0]-self.origem[0]),math.floor(p[1]-self.origem[1]))
    def mundo(self,c):return (c[0]+self.origem[0]+.5,c[1]+self.origem[1]+.5)
    def livre(self,c):
        i=self.indice(c);return i is not None and not(self.flags[i]&1)
    def passagem(self,a,b):
        ia=self.indice(a);ib=self.indice(b)
        if ia is None or ib is None or not self.livre(b):return False
        dx=b[0]-a[0];dy=b[1]-a[1]
        if abs(dx)>1 or abs(dy)>1:return False
        if dx and dy and (not self.livre((a[0]+dx,a[1])) or not self.livre((a[0],a[1]+dy))):return False
        ha,hb=self.alturas[ia],self.alturas[ib]
        return hb-ha<13 and ha-hb<(18 if self.flags[ia]&4 else 39)
    def linha_livre(self,a,b):
        dx=b[0]-a[0];dy=b[1]-a[1];n=max(abs(dx),abs(dy));anterior=a
        for j in range(1,n+1):
            atual=(round(a[0]+dx*j/n),round(a[1]+dy*j/n))
            if not self.passagem(anterior,atual):return False
            anterior=atual
        return self.livre(a)
    def penalidade_parede(self,c):
        return sum(not self.livre((c[0]+dx,c[1]+dy)) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))*.6
    def caminho(self,inicio,destino,alcance=0,max_nos=16000,limite=None,parcial=False):
        inicio=self.celula(inicio);fim=self.celula(destino)
        if not self.livre(inicio):return None
        r=math.ceil(alcance);metas=set()
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                c=(fim[0]+dx,fim[1]+dy)
                if self.livre(c) and math.hypot(dx,dy)<=alcance:metas.add(c)
        # Retorno longo pode terminar fora da janela local. Nesse caso procura
        # o trecho alcancavel que mais aproxima da meta, sem ignorar colisoes.
        parcial=parcial and self.indice(fim) is None
        if not metas and not parcial:return None
        def h(c):return max(0,math.dist(c,fim)-alcance)
        fila=[(h(inicio),0,inicio)];custos={inicio:0};pais={};visitados=set();melhor=inicio
        def reconstruir(c):
            rota=[c]
            while c in pais:c=pais[c];rota.append(c)
            return [self.mundo(v) for v in reversed(rota)]
        while fila and len(visitados)<max_nos:
            _,custo,c=heapq.heappop(fila)
            if c in visitados:continue
            visitados.add(c)
            if h(c)<h(melhor):melhor=c
            if c in metas:
                return reconstruir(c)
            if parcial and h(inicio)-h(c)>=2 and any(self.indice((c[0]+dx,c[1]+dy)) is None for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                return reconstruir(c)
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                novo=(c[0]+dx,c[1]+dy)
                if novo in visitados or not self.passagem(c,novo):continue
                if limite and math.dist(self.mundo(novo),limite[0])>limite[1]:continue
                valor=custo+math.hypot(dx,dy)+self.penalidade_parede(novo)
                if valor<custos.get(novo,float('inf')):
                    custos[novo]=valor;pais[novo]=c;heapq.heappush(fila,(valor+h(novo),valor,novo))
        return reconstruir(melhor) if parcial and h(inicio)-h(melhor)>=2 else None
    def proximo(self,pos,rota,distancia=3.):
        if not rota:return None
        proximo=min(range(len(rota)),key=lambda i:math.dist(pos,rota[i]))
        escolhido=rota[proximo]
        for alvo in rota[proximo+1:]:
            if math.dist(pos,alvo)>distancia:break
            if not self.linha_livre(self.celula(pos),self.celula(alvo)):break
            escolhido=alvo
        return escolhido

def ler_grade(dados,centro,raio=48):
    if not 4<=raio<=64:raise ValueError('Raio da grade fora dos limites')
    b=dados.base-0x400000;cena=dados.cena_validada();mapa=dados.u32(cena+0x38)
    origem=struct.unpack('<2i',dados.read(b+0x322c3b4,8))[::-1]
    x=math.floor(centro[0]-origem[0]);y=math.floor(centro[1]-origem[1])
    if not 0<=x<768 or not 0<=y<768:raise RuntimeError('Origem da grade nao corresponde a posicao atual')
    hp=dados.u32(b+0x7c5bc8)
    if not 0x10000<=hp<=0xffff0000-768*768*2:raise RuntimeError('Tabela de alturas indisponivel')
    x0,x1=max(0,x-raio),min(767,x+raio);y0,y1=max(0,y-raio),min(767,y+raio)
    largura=x1-x0+1;flags=bytearray();alturas=[]
    for linha in range(y0,y1+1):
        offset=(linha*768+x0)*2
        r=dados.read(b+0xb8b2f0+offset,largura*2);flags.extend(r[::2])
        alturas.extend(struct.unpack('<'+'h'*largura,dados.read(hp+offset,largura*2)))
    if dados.cena_validada()!=cena or dados.u32(cena+0x38)!=mapa or struct.unpack('<2i',dados.read(b+0x322c3b4,8))[::-1]!=origem or dados.u32(b+0x7c5bc8)!=hp:
        raise RuntimeError('Mapa mudou durante a leitura da grade')
    grade=Grade(origem,(x0,y0),largura,y1-y0+1,bytes(flags),tuple(alturas),mapa)
    if not grade.livre((x,y)):raise RuntimeError('Celula do personagem aparece bloqueada; grade nao validada nesta posicao')
    return grade
