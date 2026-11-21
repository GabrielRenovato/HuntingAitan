"""Abre o Aika, executa cada leitura interna e informa o que ainda funciona neste cliente.

Uso: python tools/verificar_layout.py   (com o jogo aberto, no mapa, como administrador)
Saida 0 se as leituras criticas passarem; 1 caso contrario. Somente leitura."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.verificacao import verificar,aprovado

def main():
    try:dados=DadosInternos()
    except RuntimeError as erro:
        print('Nao foi possivel abrir o leitor:',erro);return 1
    try:resultados=verificar(dados)
    finally:dados.close()
    for r in resultados:
        marca='OK   ' if r['ok'] else ('FALHA' if r['critica'] else 'aviso')
        print(f"[{marca}] {r['nome']}{' (critica)' if r['critica'] else ''}: {r['detalhe']}")
    print(json.dumps(dict(sha256=dados.sha256,aprovado=aprovado(resultados)),ensure_ascii=False))
    return 0 if aprovado(resultados) else 1

if __name__=='__main__':sys.exit(main())
