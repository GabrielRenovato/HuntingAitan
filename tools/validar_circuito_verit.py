"""Gera o circuito escolhido usando nomes, posicoes e terreno locais."""
import argparse,hashlib,json,sys,struct,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mapear_verit_termes import extrair
from validar_circuito_termes import validar

ORDEM=[1,5,20,18,4,19,2,3]
ORDEM_LESTE=[9,8,10,12,15,14,7,17,16,6,11,13]
RAIO_NORMAIS=25

def normais(pasta):
    raiz=Path(pasta);b=(raiz/'UI/MN.bin').read_bytes();nomes=bytes((v-i)%256 for i,v in enumerate(b));pos=(raiz/'UI/MobPos.bin').read_bytes()
    ids=[i for i in range(4096) if nomes[i*128:(i+1)*128].split(b'\0')[0]==b'Verit']
    if len(ids)!=1 or len(pos)!=4096*416:raise ValueError('Cadastro do Verit normal divergente')
    i=ids[0]
    if struct.unpack_from('<I',pos,i*416)[0]!=i:raise ValueError('Registro Verit divergente')
    return [dict(registro=i,slot=j+1,pos=list(p)) for j in range(50) if (p:=struct.unpack_from('<2i',pos,i*416+16+j*8))!=(0,0)]

def gerar(pasta,leste=False):
    cadastro=extrair(pasta);por_id={p['ponto']:p for p in cadastro['pontos']}
    pontos=[(i,(por_id[i]['x'],por_id[i]['y'])) for i in (ORDEM_LESTE if leste else ORDEM)]
    menores=normais(pasta) if leste else [];centros=[m['pos'] for m in menores]
    excluidos=[dict(id=i,pos=p,distancia_normal=round(min(math.dist(p,c) for c in centros),2)) for i,p in pontos if centros and min(math.dist(p,c) for c in centros)<=RAIO_NORMAIS]
    pontos=[(i,p) for i,p in pontos if i not in {e['id'] for e in excluidos}]
    d=validar(pasta,pontos,'Verit Mutante',True,exclusoes=centros,raio_exclusao=RAIO_NORMAIS);d['fechado']=True
    if leste:d.update(normais=menores,raio_normais=RAIO_NORMAIS,excluidos=excluidos)
    d['fontes'].update({n:h for n,h in cadastro['fontes'].items() if n.startswith('UI/')})
    d['registro_mob']=cadastro['registro']
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);p.add_argument('--leste',action='store_true');a=p.parse_args()
    d=gerar(a.game_dir,a.leste);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {len(t['caminho'])} celulas; {t['distancia']} unidades; passagem validada")
