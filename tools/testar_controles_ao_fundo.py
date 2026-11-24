import ctypes,sys,os,time,json,math,tkinter as tk
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.visao.controle_avisos import preparar_runtime_visual
u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32');u.GetForegroundWindow.restype=w.HWND;u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND];k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
r={};root=None
try:
 for hwnd in (7014614,33425404):
  if not u.IsWindow(hwnd):continue
  pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));h=k.OpenProcess(0x1000,False,pid.value)
  if not h:raise RuntimeError('Nao consegui conferir Hunting aberto')
  try:
   buf=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(buf))
   if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise RuntimeError('Caminho indisponivel')
   if Path(buf.value).resolve()!=(raiz/'build/segundo-plano-retomada-local/win-unpacked/HuntingAitan.exe').resolve():raise RuntimeError('Janela Hunting mudou')
  finally:k.CloseHandle(h)
  u.PostMessageW(hwnd,0x10,0,0)
 for _ in range(100):
  if not any(u.IsWindow(h) for h in (7014614,33425404)):break
  time.sleep(.1)
 if any(u.IsWindow(h) for h in (7014614,33425404)):raise RuntimeError('Hunting ainda fechando; nao testei')
 preparar_runtime_visual();root=tk.Tk();root.title('HuntingAitan - verificando comandos ao fundo');root.geometry('420x95+100+100');tk.Label(root,text='Comparando TAB e movimento sem foco.\nOs dois macros estao parados.',pady=18).pack();root.update();root.lift();root.focus_force();time.sleep(.3);root.update();frente=u.GetForegroundWindow()
 r['testes']=[]
 for j in enumerar_clientes():
  d=DadosInternos(janela=j);e=EntradaJanela(d.hwnd,d.pid)
  try:
   teste=dict(pid=d.pid,nome=d.snapshot()['player']['name'],fases=[])
   for fase in ('mensagens_normais','notificacao_ativacao'):
    if u.GetForegroundWindow()!=frente:raise RuntimeError('Foco mudou; teste interrompido')
    if d.snapshot()['player']['hp']/d.snapshot()['player']['hp_max']<.65:break
    if fase=='notificacao_ativacao':
     u.PostMessageW(d.hwnd,0x1c,1,0);u.PostMessageW(d.hwnd,6,1,0);u.PostMessageW(d.hwnd,7,0,0);time.sleep(.2)
    antes=d.snapshot();e.keyDown('tab');time.sleep(.08);e.keyUp('tab');time.sleep(.35);alvo=d.snapshot()['target']
    pos=d.snapshot()['player']['position'];e.keyDown('w');time.sleep(.35);e.keyUp('w');time.sleep(.3);apos=d.snapshot()
    f=dict(fase=fase,tab_antes=antes['target']['id'] if antes['target'] else None,tab_depois=alvo['id'] if alvo else None,deslocamento=math.dist(pos,apos['player']['position']),foco_preservado=u.GetForegroundWindow()==frente)
    if alvo and alvo['hostile'] and alvo['hp']>0 and math.dist(apos['player']['position'],alvo['position'])<3:
     cds=[];e.keyDown('1');time.sleep(.08);e.keyUp('1')
     for _ in range(20):
      root.update();time.sleep(.1);cds.append(d.estados_controle().get('normal_cooldown',0))
     f['recarga_ataque_max']=max(cds);f['alvo_hp_antes']=alvo['hp'];f['alvo_apos']=d.snapshot()['target']
    teste['fases'].append(f);root.update()
   r['testes'].append(teste)
  finally:
   e.keyUp('w');e.keyUp('1');e.keyUp('tab');d.close()
 r['ok']=True
except Exception as ex:r.update(ok=False,erro=str(ex))
finally:
 if root:root.destroy()
 (raiz/'build/teste_controles_ao_fundo.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
