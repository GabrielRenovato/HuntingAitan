"""Captura e compara estados do cliente para descobrir campos (somente leitura).

Capturar (jogo aberto, no mapa, como administrador):
  python tools/capturar_estado.py capturar dialogo_fechado --n 5
  (abra o dialogo)
  python tools/capturar_estado.py capturar dialogo_aberto --n 5

Comparar (nao precisa do jogo):
  python tools/capturar_estado.py comparar dialogo_fechado dialogo_aberto

Para olhar o que um ponteiro candidato aponta, repita a captura com --extra cena+0x1a8->0x400.
As capturas ficam em capturas_leitor/ (ignorada pelo Git) e contem dados do processo: nao compartilhe.
"""
from pathlib import Path
import argparse,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.leitura import captura as cap

PASTA_PADRAO='capturas_leitor'

def comando_capturar(a):
    from huntingaitan.leitura.escolha_cliente import abrir_leitor
    try:dados=abrir_leitor(a.pid)
    except RuntimeError as erro:
        print('Nao foi possivel abrir o leitor:',erro);return 1
    try:
        for extra in a.extra:cap.analisar_extra(extra)
        for i in range(1,a.n+1):
            c=cap.capturar(dados,a.rotulo,mob=a.mob,extras=a.extra)
            destino=Path(a.pasta)/f'{a.rotulo}_{i:03d}.cap.zip';cap.salvar(c,destino)
            ausentes=sum(len(r['ausentes']) for r in c['meta']['regioes'].values())
            print(f"{destino} ({', '.join(c['regioes'])}; blocos ilegiveis: {ausentes})")
            if i<a.n:time.sleep(a.intervalo)
    except (RuntimeError,ValueError) as erro:
        print('Falha na captura:',erro);return 1
    finally:dados.close()
    return 0

def _grupo(pasta,rotulo):
    arquivos=sorted(Path(pasta).glob(f'{rotulo}_*.cap.zip'))
    if not arquivos:raise SystemExit(f'Nenhuma captura de {rotulo!r} em {pasta}.')
    return [cap.carregar(f) for f in arquivos]

def comando_comparar(a):
    A,B=_grupo(a.pasta,a.a),_grupo(a.pasta,a.b)
    if len(A)<2 or len(B)<2:print('Aviso: com menos de 2 capturas por estado o ruido nao e filtrado.')
    regioes=a.regiao or cap.regioes_comuns(A,B)
    if not regioes:print('Nenhuma regiao presente em todas as capturas.');return 1
    for regiao in regioes:
        achados=cap.classificar(cap.candidatos(A,B,regiao))
        blocos=cap.agrupar_adjacentes(achados)
        print(f'\n== {regiao}: {len(achados)} palavras diferentes ({len(blocos)} blocos) ==')
        mostrados=0
        for c in achados:
            if mostrados>=a.limite:print(f'  ... (use --limite para ver mais)');break
            print(f"  +{c['offset']:#07x}  {c['tipo']:<18} {c['a_desc']['u32']} -> {c['b_desc']['u32']}"
                  +(f"  (f32 {c['a_desc']['f32']} -> {c['b_desc']['f32']})" if c['a_desc']['f32'] is not None and c['b_desc']['f32'] is not None else ''))
            mostrados+=1
    print('\nConfirme repetindo a troca de estado: um candidato verdadeiro muda sempre e so com o estado.')
    return 0

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    sub=ap.add_subparsers(dest='comando',required=True)
    c=sub.add_parser('capturar');c.add_argument('rotulo');c.add_argument('--n',type=int,default=5)
    c.add_argument('--intervalo',type=float,default=1.0);c.add_argument('--mob',action='store_true',help='inclui o mob mais proximo')
    c.add_argument('--extra',action='append',default=[],metavar='REGIAO+OFFSET->TAMANHO');c.add_argument('--pasta',default=PASTA_PADRAO);c.add_argument('--pid',type=int,default=0,help='PID do cliente, se houver mais de um aberto')
    d=sub.add_parser('comparar');d.add_argument('a');d.add_argument('b');d.add_argument('--pasta',default=PASTA_PADRAO)
    d.add_argument('--regiao',action='append');d.add_argument('--limite',type=int,default=40)
    a=ap.parse_args()
    return comando_capturar(a) if a.comando=='capturar' else comando_comparar(a)

if __name__=='__main__':sys.exit(main())
