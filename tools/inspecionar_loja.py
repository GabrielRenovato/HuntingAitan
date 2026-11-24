"""Diagnostico somente leitura da estrutura acessada por VA 0x429df0."""
import sys,os,json,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    raiz=Path(__file__).resolve().parents[1];destino=raiz/'build/loja_native_inspecao.json'
    try:
        cfg=json.loads((Path.home()/'AppData/Roaming/aika-caca-automatica/profile.json').read_text(encoding='utf-8-sig'))
        for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(cfg['client_'+k])
        from huntingaitan.leitura.dados_internos import DadosInternos
        d=DadosInternos()
        try:
            from huntingaitan.leitura.inventario import ler_inventario,equipamento_candidato,nome_item
            resultado=ler_inventario(d)
            resultado['ok']=True
            resultado['equipamentos']=[dict(i,nome=nome_item(d,i)) for i in resultado['itens'] if equipamento_candidato(d,i)]
        finally:d.close()
    except Exception as e:resultado=dict(ok=False,erro=str(e))
    destino.write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
