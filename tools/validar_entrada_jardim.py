"""Reproduz a mascara de objetos do retorno ao Jardim usando os arquivos locais."""
import argparse,json
from pathlib import Path
from tools import validar_entrada_mina as malhas

def gerar(pasta):
    anterior=malhas.LIMITES
    try:
        malhas.LIMITES=(1810,1050,1900,1130)
        return malhas.gerar(pasta)
    finally:malhas.LIMITES=anterior

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('pasta');parser.add_argument('--out',default='huntingaitan/dados/entrada_jardim_geometria.json');a=parser.parse_args()
    d=gerar(a.pasta);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Entrada Jardim:',len(d['objetos']),'objetos estaticos;',len(d['ignorados']),'modelos nao interpretados.')
