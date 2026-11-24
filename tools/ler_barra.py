r"""Mostra a barra de atalhos do personagem: cada slot, a skill e seus dados (somente leitura).

Com o jogo aberto, no mapa, e este terminal como administrador:
  .\.venv\Scripts\python.exe tools\ler_barra.py [--pid NUMERO]"""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.leitura.escolha_cliente import abrir_leitor
from huntingaitan.leitura.skills_cliente import descrever_barra

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pid',type=int,default=0,help='PID do cliente, se houver mais de um aberto')
    a=ap.parse_args()
    try:dados=abrir_leitor(a.pid)
    except RuntimeError as erro:
        print('Nao foi possivel abrir o leitor:',erro);return 1
    try:barra=descrever_barra(dados)
    except RuntimeError as erro:
        print('Nao foi possivel ler a barra:',erro);return 1
    finally:dados.close()
    print('linha col | tipo skill_id | tipo_skill  recarga   mana  cast | nome (nivel)')
    for s in barra:
        k=s['skill']
        if k:print(f"  {s['linha']}    {s['coluna']}  |  {s['tipo_slot']:2}  {s['skill_id']:6} | {k['tipo']:10} {k['recarga_s']:7.1f}s {k['mana']:5} {k['conjuracao_s']:4.1f}s | {k['nome']} / {k['nome_en']} (nv {k['nivel']})")
        elif s['tipo_slot'] or s['skill_id']:print(f"  {s['linha']}    {s['coluna']}  |  {s['tipo_slot']:2}  {s['skill_id']:6} | (nao e skill)")
    return 0

if __name__=='__main__':sys.exit(main())
