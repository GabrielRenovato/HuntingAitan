"""Empacota o motor sem depender do Python instalado no computador do usuario."""
from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parents[1]
pasta_dados=root/'huntingaitan'/'dados'
args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','hunt_backend','--distpath',str(root/'build/backend'),'--workpath',str(root/'build/pyinstaller'),'--specpath',str(root/'build')]
# Todos os dados (layout, rotas, templates) vao para huntingaitan/dados/ dentro do pacote, espelhando a arvore do repositorio.
for arquivo in sorted(p for p in pasta_dados.iterdir() if p.is_file()):
    args+=['--add-data',f'{arquivo};huntingaitan/dados']
args+=['--collect-data','rapidocr_onnxruntime']
subprocess.run(args+[str(root/'hunt_bridge.py')],cwd=root,check=True)
