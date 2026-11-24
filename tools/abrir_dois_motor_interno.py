import subprocess,json,os
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];exe=raiz/'build/motor-interno-local/win-unpacked/HuntingAitan.exe';r=[]
for nome in ('aika-caca-automatica','aika-caca-automatica-segundo'):
 pasta=Path(os.environ['APPDATA'])/nome;p=json.loads((pasta/'profile.json').read_text(encoding='utf-8'));proc=subprocess.Popen([str(exe),'--user-data-dir='+str(pasta)],cwd=str(exe.parent));r.append(dict(pid=proc.pid,perfil=nome,cliente_pid=p['client_pid']))
(raiz/'build/abertura_dois_hunting.json').write_text(json.dumps(r),encoding='utf-8')
