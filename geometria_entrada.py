"""Ocupacao externa derivada das malhas do cliente; sem carregar bibliotecas graficas."""
import base64,hashlib,json,math,zlib
from functools import lru_cache
from pathlib import Path
from navegacao_grade import Grade

@lru_cache(maxsize=1)
def plano_geometria():return json.loads((Path(__file__).parent/'dados'/'entrada_mina_geometria.json').read_text(encoding='utf-8'))

class GeometriaEntrada:
    def __init__(self,pasta):
        d=plano_geometria();self.limites=d['limites'];self.largura=d['largura']
        self.mascara=zlib.decompress(base64.b64decode(d['mascara']))
        if len(self.mascara)!=d['largura']*d['altura']:raise RuntimeError('Mascara de objetos da entrada invalida.')
        self.conferir(Path(pasta))

    @staticmethod
    @lru_cache(maxsize=3)
    def conferir(pasta):
        for nome,sha in plano_geometria()['fontes'].items():
            with (pasta/nome).open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
            if atual!=sha:raise RuntimeError('Geometria da entrada mudou; revalide os arquivos: '+nome)

    def livre(self,pos):
        x,y=map(math.floor,pos);x0,y0,x1,y1=self.limites
        return x0<=x<x1 and y0<=y<y1 and not self.mascara[(y-y0)*self.largura+x-x0]

    def permite_saida(self,pos,origem):
        # A mascara rasterizada pode cobrir a borda de uma celula que o
        # personagem ja ocupa. Permite sair somente dessa celula, sem abrir
        # uma passagem pelas demais celulas do objeto.
        x,y=map(math.floor,origem);x0,y0,x1,y1=self.limites
        return self.livre(pos) or (x0<=x<x1 and y0<=y<y1 and tuple(map(math.floor,pos))==(x,y))

    def aplicar(self,grade,saida=None):
        flags=bytearray(grade.flags)
        for y in range(grade.altura):
            for x in range(grade.largura):
                c=(grade.canto[0]+x,grade.canto[1]+y)
                if not self.livre(grade.mundo(c)):flags[y*grade.largura+x]|=1
        if saida is not None:
            c=grade.celula(saida);i=grade.indice(c)
            if i is not None and grade.livre(c) and self.permite_saida(saida,saida):
                # Preserva a colisao nativa: apenas a mascara adicional pode
                # ser relaxada, apenas na celula atualmente ocupada.
                flags[i]=grade.flags[i]
        return Grade(grade.origem,grade.canto,grade.largura,grade.altura,bytes(flags),grade.alturas,grade.mapa)
