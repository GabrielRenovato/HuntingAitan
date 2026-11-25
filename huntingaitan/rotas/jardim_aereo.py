"""Percurso curto do Jardim, encerrado antes dos Lazapas do trecho final."""
from huntingaitan.recursos import DADOS,RAIZ
import hashlib,json,struct,time,os,math
from functools import lru_cache
from pathlib import Path
from huntingaitan.rotas.mina_lenfer import MinaLenfer,normalizar
from huntingaitan.rotas.navegacao_grade import Grade

@lru_cache(maxsize=1)
def plano_jardim():return json.loads((DADOS/'jardim_aereo_rota.json').read_text(encoding='utf-8'))

def conferir_nome_jardim(descricao):
    # Dungeon.bin contem textos localizados. O registro 5 identifica o Jardim;
    # os dados usados para navegar sao conferidos separadamente por hash.
    if len(descricao)<384 or len(descricao)%64:
        raise RuntimeError('UI/Dungeon.bin: formato da tabela de nomes nao reconhecido.')
    nome=descricao[320:384].split(b'\0')[0].decode('cp1252',errors='replace')
    if normalizar(nome) not in ('jardimaereodemirza','kynariaviary'):
        raise RuntimeError('UI/Dungeon.bin: nome do Jardim nao reconhecido no registro 5: '+nome)
    return nome

def conferir_fontes_jardim(pasta,plano=None):
    p=Path(pasta)
    for nome,sha in (plano or plano_jardim())['fontes'].items():
        if nome=='UI/Dungeon.bin':
            conferir_nome_jardim((p/nome).read_bytes())
            continue
        with (p/nome).open('rb') as f:atual=hashlib.file_digest(f,'sha256').hexdigest()
        if atual!=sha:raise RuntimeError('Dados do Jardim mudaram; revalide a rota: '+nome)

def dentro_jardim(pos,margem=0):
    x0,y0,x1,y1=plano_jardim()['limites']
    return x0-margem<=pos[0]<x1+margem and y0-margem<=pos[1]<y1+margem

def eh_lazapa(nome):
    n=normalizar(nome)
    return 'lazapa' in n or 'lapaza' in n

def eh_shiraz_infernal(nome):
    n=normalizar(nome)
    return 'shiraz' in n and ('infernal' in n or 'hell' in n)

def na_area_lazapas_finais(pos):
    if math.dist(pos,plano_jardim()['referencia_lazapas'])<=40:return True
    rota=plano_jardim()['trechos'][0]['caminho']
    i=min(range(len(rota)),key=lambda i:math.dist(pos,rota[i]))
    return i>=max(0,len(rota)-120)

def lazapa_protegido(nome,pos):
    n=normalizar(nome)
    return eh_lazapa(nome) and ('tempestu' in n or 'storm' in n or na_area_lazapas_finais(pos))

def salvar_diagnostico_dificuldade(tela,leituras,arquivo=None,etapa='leitura_concluida'):
    import cv2
    pasta=Path(os.environ.get('AIKA_DATA_DIR',str(RAIZ)))/'app_sessions'
    pasta.mkdir(parents=True,exist_ok=True)
    arquivo=Path(arquivo) if arquivo else pasta/('jardim_dificuldade_'+time.strftime('%Y%m%d_%H%M%S')+'_'+str(os.getpid()))
    h,w=tela.shape[:2];largura=min(w,max(480,round(w*.4)));altura=min(h,max(480,round(h*.75)))
    if not cv2.imwrite(str(arquivo.with_suffix('.png')),tela[:altura,w-largura:]):raise OSError('Nao foi possivel salvar o recorte do indicador')
    arquivo.with_suffix('.json').write_text(json.dumps(dict(etapa=etapa,leituras=leituras,recorte=[w-largura,0,w,altura]),ensure_ascii=False,indent=2),encoding='utf-8')
    return str(arquivo.with_suffix('.png'))

def conferir_dificil(auto_escala=True,emitir=None,ativo=None,parar=None,janela=None):
    import mss
    from huntingaitan.visao.captura_aika import CapturaAika
    from huntingaitan.rotas.interface_mina import VerificadorElite
    verificador=VerificadorElite(dificuldade='dificil',auto_escala=auto_escala)
    from types import SimpleNamespace
    from huntingaitan.visao.captura_interface import captura_interface
    dados=SimpleNamespace(hwnd=janela[0],pid=janela[1]) if janela else None
    with captura_interface(dados,bool(janela),mss,CapturaAika) as cap:
        confirmacoes=0;leituras=[];tela=None;pausado=False;arquivo=None
        def registrar(etapa):
            nonlocal arquivo
            try:
                primeiro=arquivo is None
                arquivo=salvar_diagnostico_dificuldade(tela,leituras,arquivo=arquivo,etapa=etapa)
                if emitir and primeiro:emitir(dict(event='log',message='Recorte do Jardim salvo antes do OCR; disponivel em Abrir diagnosticos.',arquivo=arquivo))
            except OSError as e:
                if emitir:emitir(dict(event='log',message='Nao foi possivel salvar o diagnostico da dificuldade.',detail=str(e)))
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
            tela=cap.capturar();registrar('antes_ocr')
            correto=verificador.confirmar(tela)
            if ativo and not ativo():confirmacoes=0;continue
            pausado=False;leituras.append(dict(verificador.diagnostico))
            confirmacoes=confirmacoes+1 if correto else 0
            registrar('confirmado' if confirmacoes>=2 else 'leitura_concluida')
            if confirmacoes>=2:
                if emitir:emitir(dict(event='log',message='Dificuldade do Jardim confirmada em duas capturas.',leitura_interface=verificador.diagnostico))
                return True
            if emitir:emitir(dict(event='log',message='Reconfirmando indicador da dificuldade do Jardim.',leitura_interface=verificador.diagnostico,tentativa=len(leituras)))
        registrar('nao_confirmado')
        if emitir:emitir(dict(event='log',message='Indicador do Jardim nao confirmado; recorte salvo nos diagnosticos.' if arquivo else 'Indicador do Jardim nao confirmado.',arquivo=arquivo,leituras=leituras))
        raise RuntimeError('Jardim: dificuldade Dificil nao confirmada ('+verificador.resumo()+'). '+('Use Comportamento > Escala da interface > Abrir diagnosticos para enviar o recorte.' if arquivo else ''))

class JardimAereo(MinaLenfer):
    chefe='seridunn'
    obter_plano=staticmethod(plano_jardim)
    contem=staticmethod(dentro_jardim)

    def __init__(self,pos):
        super().__init__(pos)
        from huntingaitan.rotas.recuperacao_jardim import RecuperacaoJardim
        self.recuperacao=RecuperacaoJardim(pos)

    def aplicar_grade(self,grade,pos):
        if hasattr(self,'geometria'):grade=self.geometria.aplicar(grade,saida=pos)
        return self.recuperacao.aplicar(grade,pos)

    def adotar_rota(self,grade,rota,pos):
        self.grade=grade;self.rota_planejada=rota;self.trechos[0]['caminho']=rota
        self.indice=0;self.antecipacao=2.5;self.replanejado_em=tuple(pos);self.revisao+=1
        self.custo_origem=None

    def observar_navegacao(self,pos,agora,plano):
        return self.recuperacao.observar(self,pos,agora,plano)

    def replanejar_passagem(self,pos):
        # A recuperacao possui os bloqueios e ja replaneja usando-os. O
        # recalculo herdado nao pode substituir isso pela mesma rota antiga.
        return False

    def eh_chefe(self,nome):return False

    def registrar_abate(self,*args):return None

    def filtrar_mobs(self,mobs,pos,raio,defendendo=False):
        permitidos=[m for m in mobs if normalizar(m['name'])!='seridunn' and not eh_shiraz_infernal(m['name']) and not lazapa_protegido(m['name'],pos)]
        return super().filtrar_mobs(permitidos,pos,raio,defendendo)

    def atingiu_limite(self,pos):return math.dist(pos,self.pontos[-1]['pos'])<=3

    def limite_proximo(self,mobs,pos):
        for m in mobs:
            if not eh_shiraz_infernal(m['name']) or math.dist(pos,m['position'])>32:continue
            rota=self.grade.caminho(pos,m['position'],alcance=2,max_nos=4096)
            if rota and sum(math.dist(a,b) for a,b in zip(rota,rota[1:]))<=35:return m
        return None

    def lazapa_proximo(self,mobs,pos):
        if not na_area_lazapas_finais(pos):return None
        for m in mobs:
            if not eh_lazapa(m['name']) or math.dist(pos,m['position'])>27:continue
            rota=self.grade.caminho(pos,m['position'],alcance=2,max_nos=4096)
            if rota and sum(math.dist(a,b) for a,b in zip(rota,rota[1:]))<=25:return m
        return None

    def destino(self,pos,agora):
        if self.recuperacao.recuo is not None:
            if math.dist(pos,self.recuperacao.recuo)>1:
                return dict(estado='andar',destino=self.recuperacao.recuo,chave=('circuito','recuo_jardim',self.revisao),ponto='recuo_jardim',voltas=0)
            self.recuperacao.recuo=None
            g=self.aplicar_grade(self.grade_terreno,pos)
            rota=g.caminho(pos,self.pontos[-1]['pos'],max_nos=g.largura*g.altura)
            if rota:self.adotar_rota(g,rota,pos)
            else:return dict(estado='andar',destino=tuple(pos),chave=('circuito','reavaliar_jardim',self.revisao),ponto='recuo_jardim',voltas=0)
        if self.atingiu_limite(pos):return dict(estado='limite_shiraz',ponto='antes_shiraz',voltas=0)
        return super().destino(pos,agora)

    def conferir(self,pasta):
        p=Path(pasta)
        conferir_fontes_jardim(pasta,self.obter_plano())
        a=[(p/f'Env/z01{t}12.att').read_bytes() for t in [13,14]];h=[struct.unpack('<65536h',(p/f'Env/z01{t}12.hgt').read_bytes()) for t in [13,14]]
        flags=bytearray();alturas=[]
        for y in range(256):
            for j in range(2):flags.extend(a[j][y*512:(y+1)*512:2]);alturas.extend(h[j][y*256:(y+1)*256])
        self.grade_terreno=Grade((3328,3072),(0,0),512,256,bytes(flags),tuple(alturas),1)
        from huntingaitan.rotas.geometria_dg_jardim import GeometriaDGJardim
        self.geometria=GeometriaDGJardim(pasta)
        self.grade=self.aplicar_grade(self.grade_terreno,self.inicio)
        rota=self.grade.caminho(self.inicio,self.pontos[-1]['pos'],max_nos=131072)
        if not rota:raise RuntimeError('Sem passagem estatica ate o objetivo selecionado do Jardim.')
        self.trechos=[dict(ate=self.pontos[-1]['id'],caminho=rota)];self.rota_planejada=rota;self.indice=0
