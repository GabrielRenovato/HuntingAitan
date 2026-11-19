"""Valida ida e volta usando SOMENTE arquivos locais, sem controlar o jogo."""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from navegacao_grade import Grade

PONTOS=[(3,(2652,629)),(2,(2700,630)),(12,(2752,635)),(18,(2840,637)),(17,(2889,614))]

def validar(pasta):
    nomes=['Env/AttributeS01.dat','Env/z01.hgt']
    buffers=[(Path(pasta)/n).read_bytes() for n in nomes];atributos,alturas=buffers
    if len(atributos)!=4096*4096*2 or len(alturas)!=4+4096*4096*2 or struct.unpack_from('<I',alturas)[0]!=1:
        raise ValueError('Formato do terreno diferente do validado.')
    # Os arquivos por tile comprovam a orientacao e o encaixe da grade global.
    for tx in range(10,12):
        for ext,global_,skip in [('att',atributos,0),('hgt',alturas,4)]:
            nome=f'Env/z01{tx:02d}02.{ext}';tile=(Path(pasta)/nome).read_bytes()
            if len(tile)!=256*256*2:raise ValueError('Tile com tamanho inesperado: '+nome)
            for y in range(256):
                off=skip+((2*256+y)*4096+tx*256)*2
                if tile[y*512:(y+1)*512]!=global_[off:off+512]:raise ValueError('Orientacao do tile divergente: '+nome)
    x0,y0,x1,y1=2620,580,2920,680;w=x1-x0+1;flags=bytearray();hs=[]
    for y in range(y0,y1+1):
        off=(y*4096+x0)*2;flags.extend(atributos[off:off+w*2:2]);hs.extend(struct.unpack_from('<'+'h'*w,alturas,off+4))
    grade=Grade((0,0),(x0,y0),w,y1-y0+1,bytes(flags),tuple(hs),1)
    def dentro(pos):
        from circuito_termes import distancia_segmento
        return min(distancia_segmento(pos,a[1],b[1]) for a,b in zip(PONTOS,PONTOS[1:]))<=20
    caminho=PONTOS+list(reversed(PONTOS[:-1]));trechos=[]
    for (id_a,a),(id_b,b) in zip(caminho,caminho[1:]):
        rota=grade.caminho(a,b,max_nos=30000,limite=dentro)
        if not rota:raise ValueError(f'Sem passagem entre {id_a} e {id_b}.')
        if not all(grade.passagem(grade.celula(a),grade.celula(b)) for a,b in zip(rota,rota[1:])):raise ValueError('Passagem invalida.')
        trechos.append(dict(de=id_a,ate=id_b,caminho=rota,distancia=round(sum(math.dist(a,b) for a,b in zip(rota,rota[1:])),2)))
    return dict(schema=1,faixa=20,mob='Penza Poderosa Mutante',pontos=[dict(id=i,pos=p) for i,p in PONTOS],fontes={n:hashlib.sha256(b).hexdigest() for n,b in zip(nomes,buffers)},trechos=trechos,nota='Colisao e alturas estaticas validadas. Requer reconfirmacao na grade carregada durante a navegacao.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    d=validar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {len(t['caminho'])} celulas, {t['distancia']} unidades; passagem estatica validada")
