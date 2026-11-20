"""Percurso do Jardim Aereo de Mirza, com conclusao exclusiva por Seridunn."""
import hashlib,json,struct,time,os
from functools import lru_cache
from pathlib import Path
from mina_lenfer import MinaLenfer,normalizar
from navegacao_grade import Grade

@lru_cache(maxsize=1)
def plano_jardim():return json.loads(Path(__file__).with_name('jardim_aereo_rota.json').read_text(encoding='utf-8'))

def dentro_jardim(pos,margem=0):
    x0,y0,x1,y1=plano_jardim()['limites']
    return x0-margem<=pos[0]<x1+margem and y0-margem<=pos[1]<y1+margem

def salvar_diagnostico_dificuldade(tela,leituras):
    import cv2
    pasta=Path(os.environ.get('AIKA_DATA_DIR',str(Path(__file__).parent)))/'app_sessions'
    pasta.mkdir(parents=True,exist_ok=True)
    arquivo=pasta/('jardim_dificuldade_'+time.strftime('%Y%m%d_%H%M%S')+'_'+str(os.getpid()))
    h,w=tela.shape[:2];largura=min(w,max(480,round(w*.4)));altura=min(h,max(480,round(h*.75)))
    if not cv2.imwrite(str(arquivo.with_suffix('.png')),tela[:altura,w-largura:]):raise OSError('Nao foi possivel salvar o recorte do indicador')
    arquivo.with_suffix('.json').write_text(json.dumps(dict(leituras=leituras,recorte=[w-largura,0,w,altura]),ensure_ascii=False,indent=2),encoding='utf-8')
    return str(arquivo.with_suffix('.png'))

def conferir_dificil(auto_escala=True,emitir=None,ativo=None,parar=None):
    import mss
    from captura_aika import CapturaAika
    from interface_mina import VerificadorElite
    verificador=VerificadorElite(dificuldade='dificil',auto_escala=auto_escala)
    with (getattr(mss,'MSS',None) or mss.mss)() as sct:
        cap=CapturaAika(sct);confirmacoes=0;leituras=[];tela=None;pausado=False
        while len(leituras)<4:
            if parar and parar():return False
            if ativo and not ativo():
                confirmacoes=0
                if emitir and not pausado:emitir(dict(event='status',state='paused',message='Volte ao Aika para confirmar a dificuldade do Jardim.'))
                pausado=True;time.sleep(.05);continue
            # O foco pode mudar antes de o jogo desenhar o primeiro frame.
            time.sleep(.3)
            if parar and parar():return False
            if ativo and not ativo():continue
            tela=cap.capturar();correto=verificador.confirmar(tela)
            if ativo and not ativo():confirmacoes=0;continue
            pausado=False;leituras.append(dict(verificador.diagnostico))
            confirmacoes=confirmacoes+1 if correto else 0
            if confirmacoes>=2:
                if emitir:emitir(dict(event='log',message='Dificuldade do Jardim confirmada em duas capturas.',leitura_interface=verificador.diagnostico))
                return True
            if emitir:emitir(dict(event='log',message='Reconfirmando indicador da dificuldade do Jardim.',leitura_interface=verificador.diagnostico,tentativa=len(leituras)))
        arquivo=None
        try:arquivo=salvar_diagnostico_dificuldade(tela,leituras)
        except OSError as e:
            if emitir:emitir(dict(event='log',message='Nao foi possivel salvar o diagnostico da dificuldade.',detail=str(e)))
        if emitir:emitir(dict(event='log',message='Indicador do Jardim nao confirmado; recorte salvo nos diagnosticos.' if arquivo else 'Indicador do Jardim nao confirmado.',arquivo=arquivo,leituras=leituras))
        raise RuntimeError('Jardim: dificuldade Dificil nao confirmada ('+verificador.resumo()+'). '+('Use Comportamento > Escala da interface > Abrir diagnosticos para enviar o recorte.' if arquivo else ''))

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
