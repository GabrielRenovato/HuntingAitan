"""Percurso do Jardim Aereo de Mirza, com conclusao exclusiva por Seridunn."""
import hashlib,json,struct
from functools import lru_cache
from pathlib import Path
from mina_lenfer import MinaLenfer,normalizar
from navegacao_grade import Grade

@lru_cache(maxsize=1)
def plano_jardim():return json.loads(Path(__file__).with_name('jardim_aereo_rota.json').read_text(encoding='utf-8'))

def dentro_jardim(pos,margem=0):
    x0,y0,x1,y1=plano_jardim()['limites']
    return x0-margem<=pos[0]<x1+margem and y0-margem<=pos[1]<y1+margem

def conferir_dificil(auto_escala=True,emitir=None):
    import mss
    from captura_aika import CapturaAika
    from interface_mina import VerificadorElite
    verificador=VerificadorElite(dificuldade='dificil',auto_escala=auto_escala)
    with (getattr(mss,'MSS',None) or mss.mss)() as sct:
        cap=CapturaAika(sct)
        if not verificador.confirmar(cap.capturar()):raise RuntimeError('Jardim: dificuldade Dificil nao confirmada ('+verificador.resumo()+').')
        if emitir:emitir(dict(event='log',message='Dificuldade do Jardim confirmada; leitura da escala ajustada.',leitura_interface=verificador.diagnostico))

class JardimAereo(MinaLenfer):
    chefe='seridunn'
    obter_plano=staticmethod(plano_jardim)
    contem=staticmethod(dentro_jardim)

    def eh_chefe(self,nome):return normalizar(nome)=='seridunn'

    def conferir(self,pasta):
        p=Path(pasta)
        for nome,sha in plano_jardim()['fontes'].items():
            with (p/nome).open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
            if atual!=sha:raise RuntimeError('Dados do Jardim mudaram; revalide a rota: '+nome)
        a=[(p/f'Env/z01{t}12.att').read_bytes() for t in [13,14]];h=[struct.unpack('<65536h',(p/f'Env/z01{t}12.hgt').read_bytes()) for t in [13,14]]
        flags=bytearray();alturas=[]
        for y in range(256):
            for j in range(2):flags.extend(a[j][y*512:(y+1)*512:2]);alturas.extend(h[j][y*256:(y+1)*256])
        self.grade=Grade((3328,3072),(0,0),512,256,bytes(flags),tuple(alturas),1)
        rota=self.grade.caminho(self.inicio,self.pontos[-1]['pos'],max_nos=131072)
        if not rota:raise RuntimeError('Sem passagem estatica ate o altar de Seridunn.')
        self.trechos=[dict(ate=self.pontos[-1]['id'],caminho=rota)];self.rota_planejada=rota;self.indice=0
