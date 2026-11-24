"""Gera a volta pelas Plantas Mutantes 7, 8, 9 e 10 usando colisao e altura locais."""
import argparse,hashlib,json,struct
from pathlib import Path
from validar_circuito_termes import validar

ORDEM=[7,8,9,10]

def gerar(pasta):
    raiz=Path(pasta);bruto=(raiz/'UI/MN.bin').read_bytes()
    nomes=bytes((v-i)%256 for i,v in enumerate(bruto));posicoes=(raiz/'UI/MobPos.bin').read_bytes()
    if len(nomes)!=4096*128 or len(posicoes)!=4096*416:raise ValueError('Tabelas divergentes')
    mob='Planta Carnívora Mutante'
    ids=[i for i in range(4096) if nomes[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252')==mob]
    if len(ids)!=1:raise ValueError('Identidade da Planta ambigua ou ausente')
    id_=ids[0];registro=posicoes[id_*416:(id_+1)*416]
    if struct.unpack_from('<I',registro)[0]!=id_:raise ValueError('Registro de posicoes divergente')
    pontos=[(i,struct.unpack_from('<2i',registro,16+(i-1)*8)) for i in ORDEM]
    if [p for _,p in pontos]!=[(2430,1367),(2450,1378),(2457,1350),(2426,1346)]:raise ValueError('Os quatro pontos mudaram; revalide a selecao')
    d=validar(pasta,pontos,mob,True);d.update(fechado=True,registro_mob=id_,mapa='Floresta Ungor')
    d['fontes'].update({'UI/MN.bin':hashlib.sha256(bruto).hexdigest(),'UI/MobPos.bin':hashlib.sha256(posicoes).hexdigest()})
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    d=gerar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {len(t['caminho'])} celulas; {t['distancia']} unidades; passagem estatica validada")
