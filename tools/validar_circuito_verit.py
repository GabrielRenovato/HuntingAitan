"""Gera o circuito escolhido usando nomes, posicoes e terreno locais."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mapear_verit_termes import extrair
from validar_circuito_termes import validar

ORDEM=[1,5,20,18,4,19,2,3]

def gerar(pasta):
    cadastro=extrair(pasta);por_id={p['ponto']:p for p in cadastro['pontos']}
    pontos=[(i,(por_id[i]['x'],por_id[i]['y'])) for i in ORDEM]
    d=validar(pasta,pontos,'Verit Mutante',True);d['fechado']=True
    d['fontes'].update({n:h for n,h in cadastro['fontes'].items() if n.startswith('UI/')})
    d['registro_mob']=cadastro['registro']
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    d=gerar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {len(t['caminho'])} celulas; {t['distancia']} unidades; passagem validada")
