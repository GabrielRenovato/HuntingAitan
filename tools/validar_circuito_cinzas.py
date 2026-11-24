"""Valida a busca ativa dos tres Croshus das Cinzas nos pontos 7, 8 e 9."""
import argparse,hashlib,json,struct
from pathlib import Path
from validar_circuito_termes import validar

def gerar(pasta):
    raiz=Path(pasta);bruto=(raiz/'UI/MN.bin').read_bytes();nomes=bytes((v-i)%256 for i,v in enumerate(bruto))
    posicoes=(raiz/'UI/MobPos.bin').read_bytes();id_=1376
    if nomes[id_*128:(id_+1)*128].split(b'\0')[0].decode('cp1252')!='Croshu Mutante das Cinzas':raise ValueError('Especie divergente')
    reg=posicoes[id_*416:(id_+1)*416]
    if struct.unpack_from('<I',reg)[0]!=id_:raise ValueError('Registro divergente')
    pontos=[(i,struct.unpack_from('<2i',reg,16+(i-1)*8)) for i in [7,8,9]]
    if pontos!=[(7,(2881,1189)),(8,(2881,1156)),(9,(2905,1143))]:raise ValueError('Pontos da busca mudaram')
    cadastro=[dict(id=i,pos=pos) for i,pos in pontos]
    # Posicao aproximada indicada pelo usuario em 22/11; o cadastro do
    # cliente continua preservado separadamente, sem inventar outro spawn.
    pontos=[(i,(2885,1196) if i==7 else pos) for i,pos in pontos]
    d=validar(pasta,pontos,'Croshu Mutante das Cinzas',True)
    d['pontos_cadastro']=cadastro
    d['ajustes_observados']=[dict(id=7,pos=[2885,1196],origem='Coordenada aproximada informada pelo usuario em 22/11/2026')]
    d.update(fechado=True,registro_mob=id_,mapa='Floresta Cinzenta')
    d['fontes'].update({'UI/MN.bin':hashlib.sha256(bruto).hexdigest(),'UI/MobPos.bin':hashlib.sha256(posicoes).hexdigest()})
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    d=gerar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {t['distancia']} unidades; passagem estatica validada")
