"""Gera a rota da primeira area usando os arquivos locais da Mina L'Enfer."""
import argparse,collections,hashlib,json,math,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.rotas.navegacao_grade import Grade

ORDEM=[15]
CHEFES={15:'malik'}

def validar(pasta):
    p=Path(pasta);dun=(p/'UI/Dun.bin').read_bytes()
    registros=[struct.unpack_from('<14H',dun,i*28) for i in range(16,20)]
    origem=registros[0][1:3];entrada=registros[0][3:5]
    if origem!=(2816,3328) or any(r[1:5]!=(*origem,*entrada) for r in registros):raise ValueError('Entrada da Mina diferente da identificada.')
    nomes=['Env/z011113.att','Env/z011113.hgt','Env/z011113.dat','UI/Dun.bin']
    fontes={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in nomes}
    a=(p/nomes[0]).read_bytes();h=(p/nomes[1]).read_bytes();b=(p/nomes[2]).read_bytes()
    if len(a)!=131072 or len(h)!=131072 or b[:2]!=bytes([11,13]) or (len(b)-2)%40:raise ValueError('Formato do terreno da Mina divergente.')
    g=Grade(origem,(0,0),256,256,a[::2],struct.unpack('<65536h',h),1)
    inicio=g.celula(entrada);vistos={inicio};fila=collections.deque([inicio])
    if not g.livre(inicio):raise ValueError('Entrada bloqueada na grade estatica.')
    while fila:
        c=fila.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n=(c[0]+dx,c[1]+dy)
            if n not in vistos and g.passagem(c,n):vistos.add(n);fila.append(n)
    modelos={}
    for off in range(2,len(b),40):
        mid=struct.unpack_from('<I',b,off)[0]
        if 4795<=mid<=4810:modelos[mid-4795]=struct.unpack_from('<3f',b,off+4)
    pontos=[];trechos=[];anterior=g.mundo(inicio)
    for i in ORDEM:
        bruto=modelos[i]
        cel=min(vistos,key=lambda c:math.dist((c[0]+.5,c[1]+.5),bruto[:2])+g.penalidade_parede(c)*.1)
        if math.dist((cel[0]+.5,cel[1]+.5),bruto[:2])>12:raise ValueError('Setor longe da area caminhavel: '+str(i))
        destino=g.mundo(cel);rota=g.caminho(anterior,destino,max_nos=65536)
        if not rota or not all(g.passagem(g.celula(a),g.celula(b)) for a,b in zip(rota,rota[1:])):raise ValueError('Sem passagem para o setor '+str(i))
        ponto=dict(id=i,pos=destino,modelo=f'Objects/ilenfF{i:04d}.MS3',chefe=CHEFES.get(i),espera=15 if i==15 else 5)
        pontos.append(ponto);trechos.append(dict(ate=i,caminho=rota,distancia=round(sum(math.dist(a,b) for a,b in zip(rota,rota[1:])),2)));anterior=destino
    return dict(schema=1,nome='Mina LEnfer - primeira area',origem=origem,entrada=entrada,limites=[2816,3328,3072,3584],fontes=fontes,pontos=pontos,trechos=trechos,celulas_alcancaveis=len(vistos),criterio_final='Malik abatido com vida zero confirmada e 15s sem hostis ao final. A sala de destino e uma referencia estatica; o alvo precisa ser reconhecido ao vivo. Nao representa leitura da recompensa ou da missao do servidor.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    d=validar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"Setor {t['ate']}: {len(t['caminho'])} celulas; {t['distancia']} unidades; passagem validada")
