"""Reproduz uma gravacao do leitor no motor, sem abrir o Aika, e compara tracos entre versoes.

  Gravar (no jogo):   defina AIKA_GRAVAR_SESSAO=1 antes de iniciar o painel; o arquivo vai para app_sessions/.
  Reproduzir:         python tools/reproduzir_sessao.py leituras_AAAAMMDD_HHMMSS.jsonl --saida traco.json
  Comparar versoes:   python tools/reproduzir_sessao.py --comparar traco_a.json traco_b.json
"""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.leitura.replay import reproduzir,comparar

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('gravacao',nargs='?');ap.add_argument('--saida');ap.add_argument('--limite',type=float,default=120.)
    ap.add_argument('--comparar',nargs=2,metavar=('A','B'))
    a=ap.parse_args()
    if a.comparar:
        x,y=(json.loads(Path(f).read_text(encoding='utf-8')) for f in a.comparar)
        diff=comparar(x,y)
        print('Tracos identicos.' if diff is None else 'Divergencia: '+diff);return 0 if diff is None else 1
    if not a.gravacao:ap.error('informe a gravacao ou use --comparar')
    traco=reproduzir(a.gravacao,limite_segundos=a.limite)
    print(f"Duracao simulada {traco['duracao']}s; {len(traco['eventos'])} eventos; {len(traco['teclas'])} teclas; erro: {traco['erro']}")
    if a.saida:Path(a.saida).write_text(json.dumps(traco,ensure_ascii=False,default=str),encoding='utf-8')
    return 0 if traco['erro'] is None else 1

if __name__=='__main__':sys.exit(main())
