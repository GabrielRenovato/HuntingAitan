"""Exporta a tabela de skills decifrada da memoria do Aika (somente leitura).

Com o jogo aberto, no mapa, e este terminal como administrador:
  .\\.venv\\Scripts\\python.exe tools\\exportar_skills.py

Grava capturas_leitor/skills_memoria.bin (+ .json). A pasta e ignorada pelo Git e a copia e de dados do
jogo: nao compartilhe."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.leitura.escolha_cliente import abrir_leitor
from huntingaitan.leitura.skills_cliente import exportar

SAIDA=Path(__file__).resolve().parents[1]/'capturas_leitor'/'skills_memoria.bin'

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pid',type=int,default=0,help='PID do cliente, se houver mais de um aberto')
    a=ap.parse_args()
    try:dados=abrir_leitor(a.pid)
    except RuntimeError as erro:
        print('Nao foi possivel abrir o leitor:',erro);return 1
    try:meta=exportar(dados,SAIDA)
    finally:dados.close()
    ruins=len(meta['blocos_ilegiveis'])
    print(f"{meta['quantidade']} registros ({meta['tamanho']/1e6:.1f} MB) em {SAIDA}; blocos ilegiveis: {ruins}")
    return 0 if ruins==0 else 2

if __name__=='__main__':sys.exit(main())
