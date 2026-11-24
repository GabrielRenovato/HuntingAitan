"""Abre a compilacao local com os perfis existentes, sem iniciar caca."""
import json,os,subprocess
from pathlib import Path
raiz=Path(__file__).resolve().parents[1]
exe=raiz/'build/motor-interno-estavel-local/win-unpacked/HuntingAitan.exe'
r=[]
for nome in ('aika-caca-automatica','aika-caca-automatica-segundo'):
    pasta=Path(os.environ['APPDATA'])/nome
    p=json.loads((pasta/'profile.json').read_text(encoding='utf-8'))
    proc=subprocess.Popen([str(exe),'--user-data-dir='+str(pasta)],cwd=exe.parent)
    r.append(dict(pid=proc.pid,perfil=nome,cliente_pid=p['client_pid'],circuito=p['patrol_mode']))
(raiz/'build/abertura_motor_estavel.json').write_text(json.dumps(r),encoding='utf-8')
