"""Retorno ao Altar da Ascensao, cadastrado no cliente como NPC 2040."""
import math,struct
from pathlib import Path
from huntingaitan.rotas.navegacao_grade import Grade
from huntingaitan.rotas.circuito_termes import distancia_segmento
from huntingaitan.rotas.geometria_jardim import GeometriaJardim

PORTAL=(1837.,1092.)
ALCANCE_ENTRADA=3.5


class EntradaJardim:
    nome='Jardim Aereo'
    def __init__(self,pasta,pos,bloqueadores=(),*,destino=PORTAL,cadastro=(2040,1837,1092),nome=None):
        self.portal=tuple(destino)
        if nome:self.nome=nome
        if not (1792<=pos[0]<1950 and 1024<=pos[1]<1160):
            raise RuntimeError('Posicao fora da regiao de retorno ao Jardim Aereo.')
        p=Path(pasta);npc=(p/'UI/npcpos.bin').read_bytes()
        if struct.pack('<iii',*cadastro) not in npc:
            raise RuntimeError('Cadastro do Altar da Ascensao mudou; revalide a entrada do Jardim.')
        a=(p/'Env/AttributeS01.dat').read_bytes();h=(p/'Env/z01.hgt').read_bytes()
        if len(a)!=4096*4096*2 or len(h)!=4+4096*4096*2:
            raise RuntimeError('Terreno externo diferente do validado.')
        x0,y0,x1,y1=1792,1024,1950,1160;w=x1-x0;flags=bytearray();alturas=[]
        for y in range(y0,y1):
            off=(y*4096+x0)*2;flags.extend(a[off:off+w*2:2]);alturas.extend(struct.unpack_from('<'+'h'*w,h,off+4))
        self.geometria=GeometriaJardim(pasta)
        self.grade_terreno=Grade((0,0),(x0,y0),w,y1-y0,bytes(flags),tuple(alturas),1)
        self.grade=self.geometria.aplicar(self.grade_terreno,saida=pos)
        self.obstaculos=[];self.revisao=0;self.trecho=0;self.voltas=0;self.indice=0
        self.bloqueadores=set(bloqueadores);self.bloqueio_em=-float('inf')
        self._planejar(pos)

    def passagem(self,pos):
        return self.grade.livre(self.grade.celula(pos)) and all(math.dist(pos,c)>1.2 for c in self.obstaculos)

    def _planejar(self,pos):
        self.grade=self.geometria.aplicar(self.grade_terreno,saida=pos)
        rota=self.grade.caminho(pos,self.portal,alcance=3,max_nos=self.grade.largura*self.grade.altura,limite=self.passagem)
        if not rota:raise RuntimeError('Sem passagem validada ate o Altar da Ascensao.')
        self.rota=rota;self.trechos=[dict(ate='entrada_jardim',caminho=rota)];self.indice=0

    def observar_navegacao(self,pos,agora,plano):
        if plano['estado'] not in ('replanejar','bloqueado'):return False
        if math.dist(pos,self.portal)<=8:self.bloqueio_em=agora;return False
        alvo=plano.get('ponto')
        if alvo is None or math.dist(pos,alvo)<.5:return False
        dx,dy=alvo[0]-pos[0],alvo[1]-pos[1];d=math.hypot(dx,dy)
        centro=(pos[0]+dx/d*2,pos[1]+dy/d*2)
        anteriores=self.obstaculos[:];self.obstaculos=(self.obstaculos+[centro])[-12:]
        try:self._planejar(pos)
        except RuntimeError:self.obstaculos=anteriores;return False
        self.revisao+=1;return True

    def permite_combate(self,id_,pos,alvo=None):
        return id_ in self.bloqueadores and math.dist(pos,self.portal)<=8 and (alvo is None or math.dist(alvo['position'],self.portal)<=8)

    def filtrar_mobs(self,mobs,pos,agora):
        if math.dist(pos,self.portal)>8:return []
        if agora-self.bloqueio_em<=3:
            self.bloqueadores.update(m['id'] for m in mobs if math.dist(pos,m['position'])<=3.5 and distancia_segmento(m['position'],pos,self.portal)<=1.5)
        return [m for m in mobs if self.permite_combate(m['id'],pos,m)]

    def contem(self,pos,margem=0):
        return 1792-margem<=pos[0]<1950+margem and 1024-margem<=pos[1]<1160+margem

    def pausar(self,*args):pass

    def destino(self,pos,agora):
        if math.dist(pos,self.portal)<=ALCANCE_ENTRADA:return dict(estado='concluido',ponto='entrada_jardim',voltas=0)
        # O deslocamento pode terminar na borda de outra celula da mascara
        # visual. Reabre apenas a celula ja ocupada, preservando o terreno,
        # antes de escolher o proximo destino; nao insiste no ponto atras.
        if not self.grade.livre(self.grade.celula(pos)):self._planejar(pos)
        for tentativa in range(2):
            i=min(range(len(self.rota)),key=lambda i:math.dist(pos,self.rota[i]));self.indice=i
            destino=self.grade.proximo(pos,self.rota[i:],distancia=5) or self.rota[i]
            if math.dist(pos,destino)<1.5:
                j=self.rota.index(destino)
                if j>0:
                    a=self.rota[j-1];dx,dy=destino[0]-a[0],destino[1]-a[1];d=math.hypot(dx,dy)
                    if d:
                        adiante=(destino[0]+dx/d*1.2,destino[1]+dy/d*1.2)
                        passos=max(1,math.ceil(math.dist(pos,adiante)/.25))
                        if (self.grade.linha_livre(self.grade.celula(pos),self.grade.celula(adiante))
                            and all(self.passagem((pos[0]+(adiante[0]-pos[0])*n/passos,pos[1]+(adiante[1]-pos[1])*n/passos)) for n in range(passos+1))):
                            destino=adiante
            if math.dist(pos,destino)>=1.5 or tentativa:break
            self._planejar(pos)
        return dict(estado='andar',ponto='entrada_jardim',voltas=0,destino=destino,chave=('circuito','entrada_jardim',self.revisao))
