"""Valida os blocos do Jardim e deriva o limite anterior aos Lazapas finais."""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from navegacao_grade import Grade

def carregar_grade(pasta):
    p=Path(pasta)/'Env';a=[(p/f'z01{t}12.att').read_bytes() for t in [13,14]]
    h=[(p/f'z01{t}12.hgt').read_bytes() for t in [13,14]]
    if any(len(b)!=131072 for b in a+h):raise ValueError('Formato dos blocos do Jardim divergente')
    alturas=[struct.unpack('<65536h',b) for b in h];flags=bytearray();hs=[]
    for y in range(256):
        for j in range(2):flags.extend(a[j][y*512:(y+1)*512:2]);hs.extend(alturas[j][y*256:(y+1)*256])
    return Grade((3328,3072),(0,0),512,256,bytes(flags),tuple(hs),1)

def validar(pasta):
    p=Path(pasta);b=(p/'UI/Dun.bin').read_bytes();r=[struct.unpack_from('<14H',b,i*28) for i in range(20,24)]
    if any(v[1:5]!=(3328,3072,3351,3295) for v in r):raise ValueError('Entrada do Jardim diferente da identificada')
    descricao=(p/'UI/Dungeon.bin').read_bytes()
    if b'Jardim A' not in descricao[320:384] or b'Seridunn' not in descricao:raise ValueError('Identidade da DG nao confirmada')
    objetos=(p/'Env/z011412.dat').read_bytes()
    if objetos[:2]!=bytes((14,12)) or (len(objetos)-2)%40:raise ValueError('Objetos do Jardim divergentes')
    altares=[struct.unpack_from('<3f',objetos,o+4) for o in range(2,len(objetos),40) if struct.unpack_from('<I',objetos,o)[0]==3721]
    if len(altares)!=1:raise ValueError('Altar final nao identificado unicamente')
    alvo=(3584+altares[0][0],3072+altares[0][1]);g=carregar_grade(p)
    candidatos=[g.mundo((x,y)) for x in range(math.floor(alvo[0]-3328)-8,math.floor(alvo[0]-3328)+9) for y in range(math.floor(alvo[1]-3072)-8,math.floor(alvo[1]-3072)+9) if g.livre((x,y))]
    meta=min(candidatos,key=lambda q:math.dist(q,alvo));rota=g.caminho((3351,3295),meta,max_nos=131072)
    if not rota or not all(g.passagem(g.celula(a),g.celula(b)) for a,b in zip(rota,rota[1:])):raise ValueError('Sem passagem validada ate o altar')
    # Primeiro grupo de Lazapas Tempestuosos observado no trecho final de
    # 19/11. Para 25 unidades antes
    # desse trecho; a deteccao ao vivo pode antecipar ainda mais a saida.
    referencia=(3756.95,3146.52)
    i=min(range(len(rota)),key=lambda i:math.dist(rota[i],referencia));distancia=0.
    while i>0 and distancia<25:distancia+=math.dist(rota[i],rota[i-1]);i-=1
    rota=rota[:i+1];meta=rota[-1]
    fontes=['UI/Dun.bin','UI/Dungeon.bin','Objects/mirzaF0099.MS3']+[f'Env/z01{t}12.{ext}' for t in [13,14] for ext in ['att','hgt','dat']]
    return dict(schema=1,nome='Jardim Aereo de Mirza',chefe='seridunn',objetivo='antes_lazapas',referencia_lazapas=referencia,dificuldade='dificil',registros_dun=[20,21,22,23],registro_dificil=21,origem=[3328,3072],entrada=[3351,3295],limites=[3328,3072,3840,3328],fontes={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in fontes},pontos=[dict(id='antes_lazapas',pos=meta,chefe=None,espera=0)],trechos=[dict(ate='antes_lazapas',caminho=rota,distancia=round(sum(math.dist(a,b) for a,b in zip(rota,rota[1:])),2))],criterio='Encerrar o trecho antes dos primeiros Lazapas do trecho final, sem ataca-los; sair do grupo e confirmar posicao fora do Jardim. Nao registra conclusao da DG nem abate de Seridunn.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args();d=validar(a.game_dir)
    Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print('Jardim: entrada',d['entrada'],'limite Lazapas finais',d['pontos'][0]['pos'],'celulas',len(d['trechos'][0]['caminho']),'distancia',d['trechos'][0]['distancia'])
