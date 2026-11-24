"""Teste interativo de numeros por mensagens; nao altera perfil nem atalhos."""
import sys,os,json,time,ctypes,tkinter as tk
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
pasta=Path.home()/'AppData/Roaming/aika-caca-automatica';perfil=json.loads((pasta/'profile.json').read_text(encoding='utf-8-sig'))
for k in ('pid','hwnd'):os.environ['AIKA_CLIENT_'+k.upper()]=str(perfil['client_'+k])
from huntingaitan.leitura.dados_internos import DadosInternos

def main():
 d=DadosInternos();u=d.u
 u.GetForegroundWindow.restype=w.HWND
 u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.PostMessageW.restype=w.BOOL
 u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
 u.GetAsyncKeyState.restype=ctypes.c_short
 root=tk.Tk();root.title('Aika · teste 1 a 9 em segundo plano');root.geometry('510x265+140+120')
 info=tk.StringVar(value='Selecione um mob no Aika e volte a esta janela.');status=tk.StringVar(value='Pronto. Somente numeros 1 a 9; F12 interrompe.')
 tk.Label(root,text='Teste de teclado em segundo plano',font=('Segoe UI',13,'bold'),pady=10).pack()
 tk.Label(root,text='Uma passagem de 1 a 9. O perfil e a barra ficam preservados.\nUse outra janela enquanto o teste roda. Sem Ctrl, TAB ou WASD.',wraplength=480).pack()
 tk.Label(root,textvariable=info,wraplength=480,pady=8).pack();tk.Label(root,textvariable=status,wraplength=480,pady=8).pack()
 registro=dict(inicio=time.time(),pid=d.pid,hwnd=d.hwnd,teclas=[],estado='pronto');saida=raiz/'build/teste_numeros_segundo_plano.json'
 estado=dict(rodando=False,tecla=None,numero=1,liberar_em=0.,proxima=0.,fim=0.,base=None)
 def gravar():saida.write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding='utf-8')
 def validar_janela():
  pid=w.DWORD();u.GetWindowThreadProcessId(d.hwnd,ctypes.byref(pid))
  if not u.IsWindow(d.hwnd) or pid.value!=d.pid:raise RuntimeError('Cliente selecionado foi fechado ou mudou')
 def enviar(vk,soltar=False):
  validar_janela();lp=1|(u.MapVirtualKeyW(vk,0)<<16)
  if soltar:lp|=0xc0000000
  if not u.PostMessageW(d.hwnd,0x101 if soltar else 0x100,vk,lp):raise RuntimeError('Windows recusou a mensagem de teclado')
 def parar(motivo='Interrompido pelo usuario'):
  if estado['tecla'] is not None:
   try:enviar(estado['tecla'],True)
   finally:estado['tecla']=None
  estado['rodando']=False;registro['estado']='encerrado';registro['motivo']=motivo;registro['fim']=time.time();gravar();status.set(motivo);botao.config(state='normal')
 def comecar():
  try:
   f=max((pasta/'app_sessions').glob('run_*.jsonl'),key=lambda f:f.stat().st_mtime,default=None)
   if f and json.loads(f.read_text(encoding='utf-8').splitlines()[-1]).get('event')!='finished':raise RuntimeError('Clique Parar no app de caca antes deste teste')
   snap=d.snapshot();alvo=snap.get('target')
   if alvo and alvo.get('hp',0)>0 and not alvo.get('hostile'):raise RuntimeError('O alvo selecionado e amistoso/NPC. Selecione um mob para testar.')
   if snap['player']['hp']<=0:raise RuntimeError('Personagem sem vida')
   estado.update(rodando=True,tecla=None,numero=1,proxima=time.monotonic()+.5,fim=time.monotonic()+60,base=snap['player']['position'])
   registro.update(estado='rodando',teclas=[],iniciado=time.time());gravar();botao.config(state='disabled');status.set('Executando somente na janela do Aika...')
  except Exception as e:status.set(str(e))
 linha=tk.Frame(root);linha.pack(pady=8);botao=tk.Button(linha,text='Comecar teste 1 a 9',command=comecar,width=23);botao.pack(side='left',padx=6)
 tk.Button(linha,text='Parar',command=parar,width=12).pack(side='left',padx=6)
 def fechar():
  try:parar('Janela de teste fechada')
  finally:d.close();root.destroy()
 root.protocol('WM_DELETE_WINDOW',fechar)
 def tick():
  try:
   if estado['rodando']:
    agora=time.monotonic();frente=int(u.GetForegroundWindow() or 0)
    if u.GetAsyncKeyState(0x7b)&0x8000:parar('Interrompido por F12')
    elif agora>=estado['fim']:parar('Tempo maximo do teste atingido')
    elif estado['tecla'] is not None and (agora>=estado['liberar_em'] or frente==d.hwnd):
     vk=estado['tecla'];enviar(vk,True);estado['tecla']=None
     gerente=d.u32(d.base+d.cfg('bar_manager_rva'));item=registro['teclas'][-1]
     item.update(liberada=time.time(),estado_tecla_depois=d.u32(gerente+0x30+vk*4),frente_ao_soltar=frente)
     estado['numero']+=1;estado['proxima']=agora+.8;gravar()
    elif frente==d.hwnd or not frente:status.set('Deixe outra janela em primeiro plano para testar ao fundo.')
    elif estado['tecla'] is None and agora>=estado['proxima']:
     if estado['numero']>9:
      registro['todos_recebidos']=all(x.get('estado_tecla_durante')==1 for x in registro['teclas'])
      registro['foco_nao_foi_para_aika']=all(x['frente_ao_enviar']!=d.hwnd and x.get('frente_ao_soltar')!=d.hwnd for x in registro['teclas'])
      parar('Teste concluido: confira as acoes no Aika.')
     elif any(u.GetAsyncKeyState(k)&0x8000 for k in (0x10,0x11,0x12)):
      status.set('Aguardando voce soltar Ctrl, Alt ou Shift...')
     else:
      snap=d.snapshot();pl=snap['player'];alvo=snap.get('target')
      if pl['hp']<=0:raise RuntimeError('Personagem sem vida; teste interrompido')
      if alvo and alvo.get('hp',0)>0 and not alvo.get('hostile'):raise RuntimeError('Alvo amistoso selecionado; teste interrompido')
      import math
      if math.dist(pl['position'],estado['base'])>8:raise RuntimeError('Personagem se afastou do inicio; teste interrompido')
      ctrl=d.estados_controle()
      if ctrl.get('casting'):status.set('Aguardando terminar a habilidade atual...')
      else:
       n=estado['numero'];vk=0x30+n;estado['tecla']=vk;estado['liberar_em']=agora+.16
       registro['teclas'].append(dict(numero=n,enviada=time.time(),frente_ao_enviar=frente,mp_antes=pl['mp'],hp_antes=pl['hp'],alvo_hp=alvo.get('hp') if alvo else None,recarga_antes=d.recargas_atalhos().get(str(n))))
       enviar(vk);status.set('Tecla '+str(n)+' enviada somente ao Aika.');gravar()
   elif time.monotonic()%2<.15:
    pl=d.snapshot()['player'];info.set(pl.get('name','Aika')+' · HP '+str(pl['hp'])+'/'+str(pl['hp_max']))
   if estado['rodando'] and estado['tecla'] is not None:
    gerente=d.u32(d.base+d.cfg('bar_manager_rva'));r=registro['teclas'][-1];r['estado_tecla_durante']=d.u32(gerente+0x30+estado['tecla']*4)
  except Exception as e:
   try:parar(str(e))
   except Exception:status.set(str(e));estado['rodando']=False
  root.after(50,tick)
 gravar();root.after(50,tick);root.mainloop()
if __name__=='__main__':
 try:main()
 except Exception as e:(raiz/'build/teste_numeros_segundo_plano.json').write_text(json.dumps(dict(estado='erro',erro=str(e))),encoding='utf-8')
