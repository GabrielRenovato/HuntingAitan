"""Colisao das malhas internas do Jardim, conferida contra os arquivos locais."""
import base64,hashlib,json,zlib
from functools import lru_cache
from pathlib import Path
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.geometria_entrada import GeometriaEntrada

@lru_cache(maxsize=1)
def plano():return json.loads((DADOS/'jardim_geometria.json').read_text(encoding='utf-8'))

class GeometriaDGJardim(GeometriaEntrada):
    def aplicar(self,grade,saida=None):
        from huntingaitan.rotas.navegacao_grade import Grade
        # Malhas de renderizacao incluem plantas atravessaveis. Elas orientam
        # a escolha da passagem, sem inventar paredes que o cliente nao tem.
        # Uma colisao constatada pelo movimento vira bloqueio na recuperacao.
        custos=tuple(4. if not self.livre(grade.mundo((grade.canto[0]+x,grade.canto[1]+y))) else 0.
                     for y in range(grade.altura) for x in range(grade.largura))
        return Grade(grade.origem,grade.canto,grade.largura,grade.altura,grade.flags,grade.alturas,grade.mapa,custos)

    def __init__(self,pasta):
        d=plano();self.limites=d['limites'];self.largura=d['largura']
        self.mascara=zlib.decompress(base64.b64decode(d['mascara']))
        if len(self.mascara)!=d['largura']*d['altura']:raise RuntimeError('Mascara interna do Jardim invalida.')
        self.conferir(Path(pasta))

    @staticmethod
    @lru_cache(maxsize=3)
    def conferir(pasta):
        for nome,sha in plano()['fontes'].items():
            with (pasta/nome).open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
            if atual!=sha:raise RuntimeError('Objeto interno do Jardim mudou; revalide: '+nome)
