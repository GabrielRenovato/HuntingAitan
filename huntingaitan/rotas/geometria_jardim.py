"""Mascara estatica do caminho entre o save e o Altar da Ascensao."""
import base64,hashlib,json,zlib
from functools import lru_cache
from huntingaitan.recursos import DADOS
from huntingaitan.rotas.geometria_entrada import GeometriaEntrada

@lru_cache(maxsize=1)
def plano():return json.loads((DADOS/'entrada_jardim_geometria.json').read_text(encoding='utf-8'))

class GeometriaJardim(GeometriaEntrada):
    def __init__(self,pasta):
        d=plano();self.limites=d['limites'];self.largura=d['largura']
        self.mascara=zlib.decompress(base64.b64decode(d['mascara']))
        if len(self.mascara)!=d['largura']*d['altura']:raise RuntimeError('Mascara da entrada do Jardim invalida.')
        self.conferir(pasta)

    @staticmethod
    @lru_cache(maxsize=3)
    def conferir(pasta):
        from pathlib import Path
        for nome,sha in plano()['fontes'].items():
            with (Path(pasta)/nome).open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
            if atual!=sha:raise RuntimeError('Geometria da entrada do Jardim mudou: '+nome)
