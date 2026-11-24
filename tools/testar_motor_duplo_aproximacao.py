import sys,os,json,time,subprocess,threading
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];exe=raiz/'build/segundo-plano-retomada-local/win-unpacked/resources/backend/hunt_backend.exe';processos=[];r=[]
try:
 for nome in ('aika-caca-automatica','aika-caca-automatica-segundo'):
  pasta=Path(os.environ['APPDATA'])/nome;p=json.loads((pasta/'profile.json').read_text(encoding='utf-8'));p['auto_base']=True;teste=raiz/('build/teste_integrado_'+str(p['client_pid']));teste.mkdir(exist_ok=True);perfil=teste/'profile.json';perfil.write_text(json.dumps(p),encoding='utf-8');env=dict(os.environ,AIKA_DATA_DIR=str(teste),AIKA_CLIENT_PID=str(p['client_pid']),AIKA_CLIENT_HWND=str(p['client_hwnd']));out=(teste/'stdout.jsonl').open('w',encoding='utf-8');err=(teste/'stderr.txt').open('w',encoding='utf-8');proc=subprocess.Popen([sys.executable,str(raiz/'hunt_bridge.py'),'run',str(perfil)],cwd=str(exe.parent),env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True);processos.append((proc,out,err));r.append(dict(cliente_pid=p['client_pid'],pasta=str(teste)))
 time.sleep(30)
finally:
 for proc,out,err in processos:
  try:proc.stdin.write('{"command":"stop"}\n');proc.stdin.flush();proc.wait(timeout=8)
  except Exception:
   if proc.poll() is None:proc.terminate()
  out.close();err.close()
 (raiz/'build/teste_integrado_duplo.json').write_text(json.dumps(r),encoding='utf-8')
