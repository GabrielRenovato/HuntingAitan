"""Verifica se Ctrl enviado por mensagens altera o modificador reconhecido pelo cliente."""
import sys,os,json,time,ctypes,tkinter as tk
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz));pasta=Path.home()/'AppData/Roaming/aika-caca-automatica'
p=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
r={};d=None;root=None;enviadas=[]
try:
 f=max((pasta/'app_sessions').glob('run_*.jsonl'),key=lambda f:f.stat().st_mtime)
 if json.loads(f.read_text(encoding='utf-8').splitlines()[-1]).get('event')!='finished':raise RuntimeError('Caca ainda ativa')
 d=DadosInternos();u=d.u;u.GetForegroundWindow.restype=w.HWND
 u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.PostMessageW.restype=w.BOOL
 u.MapVirtualKeyW.argtypes=[w.UINT,w.UINT];u.MapVirtualKeyW.restype=w.UINT
 u.GetAsyncKeyState.restype=ctypes.c_short
 if u.GetAsyncKeyState(0x11)&0x8000:raise RuntimeError('Ctrl fisico pressionado')
 root=tk.Tk();root.title('Teste Ctrl em segundo plano');root.geometry('360x95+120+100');tk.Label(root,text='Verificando Ctrl apenas na janela do Aika.\\nEste teste nao usa teclado global.',pady=15).pack();root.update();root.lift();root.focus_force();time.sleep(.4);root.update()
 frente=int(u.GetForegroundWindow() or 0)
 if not frente or frente==d.hwnd:raise RuntimeError('Diagnostico nao obteve foco')
 gerente=d.u32(d.base+d.cfg('bar_manager_rva'))
 r=dict(frente=frente,modificador_antes=d.u32(gerente+0x62c),teclas=[],controle_global=bool(u.GetAsyncKeyState(0x11)&0x8000))
 for vk in (0x11,):
  lp=1|(u.MapVirtualKeyW(vk,0)<<16)
  if not u.PostMessageW(d.hwnd,0x100,vk,lp):raise RuntimeError('Mensagem recusada')
  enviadas.append(vk);time.sleep(.06);root.update();r['teclas'].append(dict(vk=vk,modificador=d.u32(gerente+0x62c),frente=int(u.GetForegroundWindow() or 0)))
 r['ctrl_reconhecido']=r['teclas'][-1]['modificador']==3
 r['foco_preservado']=all(a['frente']==frente for a in r['teclas']);r['ok']=True
except Exception as e:r.update(ok=False,erro=str(e))
finally:
 if d:
  for vk in reversed(enviadas):d.u.PostMessageW(d.hwnd,0x101,vk,1|(d.u.MapVirtualKeyW(vk,0)<<16)|0xc0000000)
  d.close()
 if root:root.destroy()
 (raiz/'build/teste_ctrl_janela_resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
