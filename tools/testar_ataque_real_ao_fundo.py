import sys,json,time,math,tkinter as tk,ctypes
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.visao.controle_avisos import preparar_runtime_visual
r=dict(testes=[]);root=None
try:
 preparar_runtime_visual();root=tk.Tk();root.title('Teste real de ataque sem foco');root.geometry('420x100+150+120');tk.Label(root,text='Medindo ataque nas duas janelas ao fundo.\nNao envia buffs nem ativa o Aika.',pady=20).pack();root.update();root.lift();root.focus_force();time.sleep(.4)
 u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND;frente=u.GetForegroundWindow()
 for j in enumerar_clientes():
  d=DadosInternos(janela=j);e=EntradaJanela(d.hwnd,d.pid);t=dict(pid=d.pid,quadros=[]);r['testes'].append(t)
  try:
   t['nome']=d.snapshot()['player']['name']
   for i in range(60):
    root.update()
    if u.GetForegroundWindow()==d.hwnd:raise RuntimeError('Aika ganhou foco; teste sem foco interrompido')
    s=d.snapshot();p=s['player'];a=s['target'];t['quadros'].append(dict(t=time.time(),pos=p['position'],heading=p['heading'],hp=p['hp']/p['hp_max'],alvo=a))
    if p['hp']/p['hp_max']<.65:t['parou']='vida baixa';break
    if i in (0,10,20):
     if not a or not a['hostile'] or a['hp']<=0:e.keyDown('tab');time.sleep(.07);e.keyUp('tab')
    if i==25:e.keyDown('a')
    if i==30:e.keyUp('a')
    if i==35:e.keyDown('w')
    if i==40:e.keyUp('w')
    if i%6==0:e.keyDown('1');time.sleep(.07);e.keyUp('1')
    time.sleep(.1)
   t['aika_permaneceu_sem_foco']=u.GetForegroundWindow()!=d.hwnd
  finally:e.keyUp('a');e.keyUp('w');e.keyUp('1');e.keyUp('tab');d.close()
 r['ok']=True
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if root:root.destroy()
 (raiz/'build/teste_ataque_real_ao_fundo.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
