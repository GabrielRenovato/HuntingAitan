import sys,os,json,time,shutil
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
pasta=Path.home()/'AppData/Roaming/aika-caca-automatica';p=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.skills_cliente import ler_slots,descrever_barra
from huntingaitan.visao.controle_avisos import preparar_runtime_visual
r={}
try:
 preparar_runtime_visual();d=DadosInternos()
 try:
  r=dict(ok=True,pid=d.pid,hwnd=d.hwnd,player=d.snapshot()['player'],slots=list(ler_slots(d)),barra=descrever_barra(d),profile=p)
  gestor=d.u32(d.base+d.cfg('bar_manager_rva'));r['hotkeys']=list(d.read(gestor+0x430,468))
  import cv2,mss
  from huntingaitan.visao.captura_aika import CapturaAika
  with mss.MSS() as sct:
   cap=CapturaAika(sct);cv2.imwrite(str(raiz/'build/barra_atual_segundo_plano.png'),cap.capturar());r['area']=cap.area
 finally:d.close()

except Exception as e:r=dict(ok=False,erro=str(e))
(raiz/'build/barra_atual_segundo_plano.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
