"""Gravacao e reproducao das leituras do cliente, para validar o motor sem o jogo aberto.

O gravador e um proxy do leitor: repassa cada chamada e grava o resultado em JSONL. O replay
devolve esses resultados, metodo a metodo, na ordem gravada. Os arquivos contem o nome do
personagem e posicoes: revise antes de compartilhar."""
import json,math,os,time
from pathlib import Path
from types import SimpleNamespace
from huntingaitan.recursos import RAIZ

METODOS_GRAVADOS=('snapshot','listar_mobs','estados_controle','recargas_atalhos','camera_regional','cena_validada','caca_original_ativa','entidade','u32')

def para_json(v):
    """Converte para JSON preservando tuplas, chaves nao textuais e valores nao finitos."""
    if isinstance(v,tuple):return {'__t__':[para_json(x) for x in v]}
    if isinstance(v,dict):
        if all(isinstance(k,str) for k in v) and not any(k.startswith('__') for k in v):return {k:para_json(x) for k,x in v.items()}
        return {'__d__':[[para_json(k),para_json(x)] for k,x in v.items()]}
    if isinstance(v,(list,set,frozenset)):return [para_json(x) for x in v]
    if isinstance(v,float) and not math.isfinite(v):return {'__f__':repr(v)}
    if isinstance(v,bytes):return {'__b__':v.hex()}
    if v is None or isinstance(v,(bool,int,float,str)):return v
    return {'__r__':repr(v)}

def de_json(v):
    if isinstance(v,list):return [de_json(x) for x in v]
    if isinstance(v,dict):
        if '__t__' in v:return tuple(de_json(x) for x in v['__t__'])
        if '__d__' in v:return {de_json(k):de_json(x) for k,x in v['__d__']}
        if '__f__' in v:return float(v['__f__'])
        if '__b__' in v:return bytes.fromhex(v['__b__'])
        if '__r__' in v:return v['__r__']
        return {k:de_json(x) for k,x in v.items()}
    return v

def caminho_gravacao(agora=None):
    pasta=Path(os.environ.get('AIKA_DATA_DIR',str(RAIZ)))/'app_sessions'
    return pasta/('leituras_'+time.strftime('%Y%m%d_%H%M%S',agora or time.localtime())+'.jsonl')

class DadosGravador:
    def __init__(self,dados,arquivo,relogio=time.monotonic):
        self._dados=dados;self._relogio=relogio;self._inicio=relogio()
        Path(arquivo).parent.mkdir(parents=True,exist_ok=True)
        self._arquivo=open(arquivo,'a',encoding='utf-8')
    def __getattr__(self,nome):
        atributo=getattr(self._dados,nome)
        if nome not in METODOS_GRAVADOS or not callable(atributo):return atributo
        def chamada(*args,**kwargs):
            try:resultado=atributo(*args,**kwargs)
            except RuntimeError as erro:
                self._gravar(dict(m=nome,erro=str(erro)));raise
            self._gravar(dict(m=nome,r=para_json(resultado)));return resultado
        return chamada
    def _gravar(self,registro):
        registro['t']=round(self._relogio()-self._inicio,4)
        self._arquivo.write(json.dumps(registro,ensure_ascii=False)+'\n');self._arquivo.flush()
    def close(self):
        try:self._dados.close()
        finally:self._arquivo.close()

def ler_registros(arquivo):
    with open(arquivo,encoding='utf-8') as f:return [json.loads(l) for l in f if l.strip()]

class DadosReplay:
    """Leitor falso que devolve as leituras gravadas, por metodo, na ordem original."""
    def __init__(self,registros,ao_acabar=None):
        self._filas={};self._pos={};self._ultimo={};self._ao_acabar=ao_acabar
        for r in registros:self._filas.setdefault(r['m'],[]).append(r)
        self.hwnd=1;self.sha256='replay';self.caminho=Path('replay')/'AIKACL.exe'
        self.u=SimpleNamespace(GetForegroundWindow=lambda:1)
    def __getattr__(self,nome):
        if nome in METODOS_GRAVADOS:return lambda *args,**kwargs:self._responder(nome)
        raise AttributeError(nome)
    def _responder(self,nome):
        fila=self._filas.get(nome,[]);i=self._pos.get(nome,0)
        if i>=len(fila):
            # Sessao acabou: pede parada limpa e repete a ultima leitura ate o laco encerrar.
            if nome=='snapshot' and self._ao_acabar:self._ao_acabar()
            if nome in self._ultimo:return self._ultimo[nome]
            raise RuntimeError(f'Replay sem leituras gravadas para {nome}.')
        self._pos[nome]=i+1;registro=fila[i]
        if 'erro' in registro:raise RuntimeError(registro['erro'])
        valor=de_json(registro['r']);self._ultimo[nome]=valor;return valor
    def restantes(self):
        return {m:len(f)-self._pos.get(m,0) for m,f in self._filas.items()}
    def close(self):pass
