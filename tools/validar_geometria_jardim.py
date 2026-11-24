"""Rasteriza as malhas internas usando as alturas dos blocos reais da DG."""
import sys,json,argparse,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validar_entrada_mina import gerar as rasterizar

def gerar(pasta):
    import numpy as np
    p=Path(pasta);alturas=np.zeros((4096,4096),dtype=np.int16);fontes={}
    for tx in (13,14):
        nome=f'Env/z01{tx}12.hgt';raw=(p/nome).read_bytes()
        alturas[3072:3328,tx*256:(tx+1)*256]=np.frombuffer(raw,dtype='<i2').reshape(256,256)
        fontes[nome]=hashlib.sha256(raw).hexdigest()
    d=rasterizar(p,limites=(3328,3072,3840,3328),alturas=alturas)
    d['fontes'].update(fontes);d['criterio']+=' Alturas internas obtidas dos dois blocos da DG, sem substituir por alturas do mundo externo.'
    return d

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('pasta');parser.add_argument('--out',default='huntingaitan/dados/jardim_geometria.json');a=parser.parse_args()
    d=gerar(a.pasta);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Jardim interno:',len(d['objetos']),'objetos;',len(d['ignorados']),'formatos nao lidos.')
