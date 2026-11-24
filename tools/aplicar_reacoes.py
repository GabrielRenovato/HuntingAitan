r"""Aplica as reacoes de sobrevivencia de uma predefinicao ao perfil do painel.

Feche o painel antes (ele so le o perfil ao abrir). Uma copia do perfil e guardada ao lado dele.
  .\.venv\Scripts\python.exe tools\aplicar_reacoes.py              (templario: Remediar a 40% de vida)
  .\.venv\Scripts\python.exe tools\aplicar_reacoes.py --perfil CAMINHO"""
from pathlib import Path
import argparse,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.configuracao.predefinicoes import PREDEFINICOES,aplicar_em_arquivo

PERFIL_PADRAO=Path(os.environ.get('APPDATA',''))/'aika-caca-automatica'/'profile.json'

def painel_aberto():
    try:saida=subprocess.run(['tasklist'],capture_output=True,text=True,timeout=20).stdout.lower()
    except Exception:return False
    return 'electron.exe' in saida or 'huntingaitan.exe' in saida

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('predefinicao',nargs='?',default='templario',choices=sorted(PREDEFINICOES))
    ap.add_argument('--perfil',type=Path,default=PERFIL_PADRAO);ap.add_argument('--forcar',action='store_true',help='aplica mesmo com o painel aberto')
    a=ap.parse_args()
    if not a.perfil.is_file():print('Perfil nao encontrado:',a.perfil);return 1
    if painel_aberto() and not a.forcar:
        print('O painel parece estar aberto: feche-o e rode de novo (ou use --forcar). Salvar no painel aberto apagaria as reacoes.');return 1
    try:p=aplicar_em_arquivo(a.perfil,a.predefinicao)
    except (ValueError,KeyError) as erro:
        print('Nao foi possivel aplicar:',erro);return 1
    for r in p['reacoes']:print(f"{r['nome']}: tecla {r['tecla']}, {r['tipo']}, vida <= {r['hp_max_pct']:g}%, mana >= {r['mp_min']}, intervalo {r['intervalo_s']:g}s")
    print('Perfil gravado em',a.perfil);return 0

if __name__=='__main__':sys.exit(main())
