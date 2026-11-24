import json,os,sys,subprocess,time
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.clientes import listar_clientes
from huntingaitan.configuracao.perfil_hunt import validar
r={}
try:
 atual=Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json';p=json.loads(atual.read_text(encoding='utf-8-sig'))
 outros=[c for c in listar_clientes() if c['ready'] and c['pid']!=p['client_pid']]
 if len(outros)!=1:raise RuntimeError('Nao encontrei um unico segundo personagem pronto: '+str([(c['pid'],c['name']) for c in outros]))
 outro=outros[0];destino=Path(os.environ['APPDATA'])/'aika-caca-automatica-segundo';destino.mkdir(exist_ok=True)
 perfil=destino/'profile.json'
 if perfil.exists():
  perfil.with_name('profile_backup_'+time.strftime('%Y%m%d_%H%M%S')+'.json').write_bytes(perfil.read_bytes())
 p.update(client_pid=outro['pid'],client_hwnd=outro['hwnd'],base=[round(v) for v in outro['position']])
 perfil.write_text(json.dumps(validar(p),ensure_ascii=False,indent=2),encoding='utf-8')
 exe=raiz/'build/segundo-plano-retomada-local/win-unpacked/HuntingAitan.exe'
 proc=subprocess.Popen([str(exe),'--user-data-dir='+str(destino)],cwd=str(exe.parent))
 r=dict(ok=True,pid=proc.pid,cliente=outro['name'],cliente_pid=outro['pid'],dados=str(destino))
except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/segundo_hunting_resultado.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
