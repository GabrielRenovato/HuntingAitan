"""Confirma o objeto 3D sob o cursor antes de interagir com o altar."""
import math,struct,time
from huntingaitan.visao.dialogos_evento import normalizar
from huntingaitan.rotas.entrada_jardim import PORTAL

NOMES={'altardaascensao','altardaascensio','altardeascension','altardelaascension','altarofascension','ascensionaltar'}


def altar_sob_cursor(dados):
    cena=dados.cena_validada();ref=dados.u32(cena+0x108)
    if not ref:return None
    nome=dados.read(ref+0x19ac,128).split(b'\0')[0].decode('cp1252',errors='replace')
    if normalizar(nome) not in NOMES:return None
    pos=struct.unpack('<3f',dados.read(ref+0x1c,12))
    if not all(math.isfinite(v) for v in pos) or math.dist(pos[:2],PORTAL)>4:return None
    player=dados.snapshot()['player']
    if player['hp']<=0 or math.dist(player['position'],PORTAL)>4:return None
    return dict(ref=ref,id=dados.u32(ref+4),nome=nome,posicao=pos[:2])


def pontos_busca(ponto,largura,altura,atual=None):
    # Apenas movimenta o cursor virtual. Nenhum desses candidatos e clicado
    # sem a identificacao posterior do objeto pelo cliente.
    x,y=ponto;vistos=set()
    candidatos=([atual] if atual else [])+[ponto]
    candidatos += [(x+dx*largura,y+dy*altura)
        for dy in (.12,.24,.36,.06,.18,.30,.42)
        for dx in (0,.10,-.10,.20,-.20,.30,-.30)]
    for px,py in candidatos:
        p=(round(px),round(py))
        if .08*largura<=p[0]<.95*largura and .10*altura<=p[1]<.80*altura and p not in vistos:
            vistos.add(p);yield p


def localizar_altar_clicavel(dados,entrada,cap,ponto,ativo,*,limite=6,relogio=time.monotonic,dormir=time.sleep):
    cap.capturar();area=cap.area.copy();fim=relogio()+limite
    gerente=dados.u32(dados.base+0x2f4cd90)
    atual=struct.unpack('<2h',dados.read(gerente+0x3c,4))
    for p in pontos_busca(ponto,area['width'],area['height'],atual):
        if not ativo() or relogio()>=fim:return None
        if not entrada.mover_sem_cursor(area['left']+p[0],area['top']+p[1]):return None
        dormir(.065)
        if not ativo():return None
        primeiro=altar_sob_cursor(dados)
        if primeiro:
            dormir(.065)
            if not ativo():return None
            segundo=altar_sob_cursor(dados)
            if segundo and primeiro['ref']==segundo['ref'] and primeiro['id']==segundo['id']:
                return dict(ponto=(area['left']+p[0],area['top']+p[1]),altar=segundo)
    return None
