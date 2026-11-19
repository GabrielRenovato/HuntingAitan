from pathlib import Path
import json,subprocess
exe=Path(__file__).resolve().parents[1]/'build/backend/hunt_backend/hunt_backend.exe'
for modo,entrada in [('defaults',{}),('validate',{}),('selftest-monitor',{}),('selftest',{})]:
    r=subprocess.run([str(exe),modo],input=json.dumps(entrada),text=True,capture_output=True,timeout=30,check=True)
    resultado=json.loads(r.stdout.strip().splitlines()[-1])
    assert resultado['ok'],resultado
print('Motor empacotado: defaults, validate, monitor/interface concorrentes e dependencias/templates passaram sem abrir o Aika.')
