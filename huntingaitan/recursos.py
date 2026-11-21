"""Localiza os dados do motor e a raiz de execucao, no repositorio e no pacote empacotado."""
from pathlib import Path
PACOTE=Path(__file__).resolve().parent
RAIZ=PACOTE.parent
DADOS=PACOTE/'dados'
