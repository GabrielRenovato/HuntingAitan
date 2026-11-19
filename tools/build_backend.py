"""Empacota o motor sem depender do Python instalado no computador do usuario."""
from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parents[1]
dados=['native_layout.json','circuito_termes_penza.json','mina_lenfer_rota.json','tpl_elter_titulo.png','tpl_elter_cancelar.png','tpl_elter_confirmar.png','tpl_social_titulo.png','tpl_social_conversa.png','tpl_social_fechar.png']
args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','hunt_backend','--distpath',str(root/'build/backend'),'--workpath',str(root/'build/pyinstaller'),'--specpath',str(root/'build')]
dados += [p.name for p in sorted(root.glob('tpl_mina_*.png'))]
dados += ['entrada_mina_geometria.json']
for nome in dados:args+=['--add-data',str(root/nome)+';.']
args+=['--collect-data','rapidocr_onnxruntime']
subprocess.run(args+[str(root/'hunt_bridge.py')],cwd=root,check=True)
