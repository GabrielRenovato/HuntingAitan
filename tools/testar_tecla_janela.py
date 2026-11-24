"""Teste isolado: WM_KEYDOWN/UP somente no HWND selecionado, sem SendInput."""
import os,sys,time,json,ctypes
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
pasta=Path.home()/'AppData/Roaming/aika-caca-automatica'
p=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(p['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos
saida=raiz/'build/teste_tecla_janela_resultado.json';d=None;pressionada=False;resultado={};janela=None
saida.write_text(json.dumps(dict(state='iniciando',inicio=time.time())),encoding='utf-8')
try:
 ultima=max((pasta/'app_sessions').glob('run_*.jsonl'),key=lambda f:f.stat().st_mtime,default=None)
 if ultima:
  linhas=ultima.read_text(encoding='utf-8').splitlines()
  if linhas and json.loads(linhas[-1]).get('event')!='finished':raise RuntimeError('Teste nao iniciado: pare a caca antes do teste isolado')
 d=DadosInternos();u=d.u
 u.GetForegroundWindow.restype=w.HWND
 u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.PostMessageW.restype=w.BOOL
 u.MapVirtualKeyW.argtypes=[w.UINT,w.UINT];u.MapVirtualKeyW.restype=w.UINT
 u.GetAsyncKeyState.argtypes=[ctypes.c_int];u.GetAsyncKeyState.restype=ctypes.c_short
 antes=d.snapshot()['player'];cd=d.recargas_atalhos().get('7')
 resultado.update(recarga_inicial=cd,mp_inicial=antes['mp'],hp_inicial=antes['hp'],hp_max=antes['hp_max'])
 if antes['hp']<=0:raise RuntimeError('Teste nao iniciado: personagem sem vida')
 if not cd:raise RuntimeError('Teste nao iniciado: tecla 7 nao mapeada')
 limite=time.monotonic()+180;ultimo_aviso=0
 while not cd.get('ready') and time.monotonic()<limite:
  if u.GetAsyncKeyState(0x7b)&0x8000:raise RuntimeError('Teste cancelado por F12')
  if time.monotonic()-ultimo_aviso>=1:
   saida.write_text(json.dumps(dict(resultado,state='aguardando_recarga',recarga_atual=cd)),encoding='utf-8');ultimo_aviso=time.monotonic()
  time.sleep(.2);cd=d.recargas_atalhos().get('7') or {}
 if not cd.get('ready'):raise RuntimeError('Teste nao iniciado: tecla 7 continua em recarga')
 antes=d.snapshot()['player']
 if d.estados_controle().get('casting'):raise RuntimeError('Teste nao iniciado: personagem ja esta usando habilidade')
 import tkinter as tk
 janela=tk.Tk();janela.title('Teste de teclas em segundo plano');janela.geometry('390x110+120+100')
 tk.Label(janela,text='Verificando uma cura 7 somente no Aika.\nO foco deve permanecer nesta janela.',padx=12,pady=15).pack()
 cancelado=[False]
 tk.Button(janela,text='Cancelar teste',command=lambda:cancelado.__setitem__(0,True)).pack()
 janela.protocol('WM_DELETE_WINDOW',lambda:cancelado.__setitem__(0,True))
 janela.update();janela.lift();janela.focus_force();time.sleep(.5);janela.update()
 frente=u.GetForegroundWindow()
 if not frente or frente==d.hwnd:raise RuntimeError('Teste nao iniciado: janela de diagnostico nao obteve foco')
 if cancelado[0]:raise RuntimeError('Teste cancelado')
 if any(u.GetAsyncKeyState(k)&0x8000 for k in (0x10,0x11,0x12,0x37,0x7b)):raise RuntimeError('Teste nao iniciado: tecla modificadora ou controle pressionado')
 scan=u.MapVirtualKeyW(0x37,0);lp=1|(scan<<16)
 resultado.update(dict(pid=d.pid,hwnd=d.hwnd,frente_antes=int(frente or 0),mp_antes=antes['mp'],recarga_antes=cd,amostras=[]))
 if not u.PostMessageW(d.hwnd,0x100,0x37,lp):raise RuntimeError('Mensagem de tecla recusada pelo Windows')
 pressionada=True;time.sleep(.16)
 if not u.PostMessageW(d.hwnd,0x101,0x37,lp|0xc0000000):raise RuntimeError('Mensagem de liberacao recusada')
 pressionada=False
 for _ in range(35):
  janela.update()
  if cancelado[0]:raise RuntimeError('Teste cancelado')
  pl=d.snapshot()['player'];r=d.recargas_atalhos().get('7');ctrl=d.estados_controle()
  resultado['amostras'].append(dict(mp=pl['mp'],recarga=r,cast=ctrl.get('casting_skill'),casting=ctrl.get('casting'),frente=int(u.GetForegroundWindow() or 0)))
  time.sleep(.06)
 resultado['acao_confirmada']=any(a['mp']<antes['mp'] or (a['recarga'] and not a['recarga']['ready']) or (a['casting'] and a['cast']==cd['skill']) for a in resultado['amostras'])
 resultado['foco_preservado']=all(a['frente']==int(frente or 0) for a in resultado['amostras'])
 resultado['ok']=True
 resultado['segundo_plano_confirmado']=resultado['acao_confirmada'] and resultado['foco_preservado']
except Exception as e:resultado.update(ok=False,erro=str(e))
finally:
 if janela:
  try:janela.destroy()
  except Exception:pass
 if d:
  if pressionada:d.u.PostMessageW(d.hwnd,0x101,0x37,1|(d.u.MapVirtualKeyW(0x37,0)<<16)|0xc0000000)
  d.close()
 saida.write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')
