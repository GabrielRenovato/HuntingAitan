import sys,os,json
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.clientes import listar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.skills_cliente import descrever_barra
from huntingaitan.leitura.recargas_barra import atalhos_slots
r=[]
for j in enumerar_clientes():
 d=None
 try:
  d=DadosInternos(janela=j);gestor=d.u32(d.base+d.cfg('bar_manager_rva'));m=atalhos_slots(d.read(gestor+0x430,468));barra=descrever_barra(d)
  for s in barra:s['tecla']=m.get(s['slot'],'')
  import cv2
  from huntingaitan.visao.captura_janela import CapturaJanela
  with CapturaJanela(d.hwnd,d.pid) as cap:cv2.imwrite(str(raiz/('build/cliente_'+str(d.pid)+'.png')),cap.capturar())
  snap=d.snapshot();mobs=d.listar_mobs(snap['player']['position'],50,snap['player'])
  r.append(dict(ok=True,mobs=mobs,pid=d.pid,hwnd=d.hwnd,snapshot=d.snapshot(),controle=d.estados_controle(),barra=barra,modificador=d.read(gestor+0x62c,1)[0]))
 except Exception as e:r.append(dict(ok=False,erro=str(e),pid=j['pid']))
 finally:
  if d:d.close()
(raiz/'build/inspecao_duas_barras.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
