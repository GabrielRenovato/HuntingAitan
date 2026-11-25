"""Gera circuito separado dos seis Croshus perto de 2955, 1311."""
import argparse,hashlib,json,struct
from pathlib import Path
from validar_circuito_termes import validar

ORDEM=(6,2,1,3,5,4)
CADASTRO={1:(2982,1338),2:(3009,1321),3:(2862,1387),4:(2866,1321),5:(2884,1350),6:(2955,1310)}

def gerar(pasta):
    raiz=Path(pasta);bruto=(raiz/'UI/MN.bin').read_bytes()
    nomes=bytes((v-i)%256 for i,v in enumerate(bruto));posicoes=(raiz/'UI/MobPos.bin').read_bytes();id_=1376
    if nomes[id_*128:(id_+1)*128].split(b'\0')[0].decode('cp1252')!='Croshu Mutante das Cinzas':raise ValueError('Especie divergente')
    reg=posicoes[id_*416:(id_+1)*416]
    if struct.unpack_from('<I',reg)[0]!=id_:raise ValueError('Registro divergente')
    pontos=[(i,struct.unpack_from('<2i',reg,16+(i-1)*8)) for i in ORDEM]
    if any(pos!=CADASTRO[i] for i,pos in pontos):raise ValueError('Os seis pontos do grupo sul mudaram')
    d=validar(pasta,pontos,'Croshu Mutante das Cinzas',True)
    d.update(fechado=True,registro_mob=id_,mapa='Floresta Cinzenta',grupo='sul',referencia_usuario=[2955,1311])
    d['fontes'].update({'UI/MN.bin':hashlib.sha256(bruto).hexdigest(),'UI/MobPos.bin':hashlib.sha256(posicoes).hexdigest()})
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    d=gerar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {t['distancia']} unidades; passagem estatica validada")
