"""A/B isolado; nao altera o perfil nem habilita o combo na caca."""
import ctypes,json,os,subprocess,sys,time,math
from ctypes import wintypes as w
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.entrada.entrada_motor import EntradaMotor
from huntingaitan.combate.teste_cancelamento import condicao_teste,sequencia,avaliar
dest=raiz/'build'/('comparacao_combo_'+time.strftime('%Y%m%d_%H%M%S'));dest.mkdir()
r=dict(fase='leitura',rodadas=[]);d=None;e=None;fechadas=[];antigo=None;exe=None
u=ctypes.WinDLL('user32');k=ctypes.WinDLL('kernel32')
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
k.CloseHandle.argtypes=[w.HANDLE]
def salvar(): (dest/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    perfil=Path(os.environ['APPDATA'])/'aika-caca-automatica'
    p=json.loads((perfil/'profile.json').read_text(encoding='utf-8'))
    j=next(j for j in enumerar_clientes() if j['pid']==p['client_pid'] and j['hwnd']==p['client_hwnd'])
    d=DadosInternos(janela=j);s=d.snapshot();cc=d.estados_controle();t=s.get('target')
    r.update(personagem=s['player']['name'],hp=s['player']['hp']/s['player']['hp_max'],posicao=s['player']['position'],alvo=t)
    if d.caca_original_ativa():raise RuntimeError('Caca original ligada; experimento nao iniciou')
    if r['hp']<.85:raise RuntimeError('HP abaixo de 85%; experimento nao iniciou e a caca existente foi preservada')
    limite=time.monotonic()+25
    while not (t and t['name']=='Verit Mutante' and t['hp']>.5*t['hp_max'] and condicao_teste(s,cc,t['id'])) and time.monotonic()<limite:
        if s['player']['hp']/s['player']['hp_max']<.85:break
        if u.GetAsyncKeyState(0x7b)&0x8000:break
        time.sleep(.15);s=d.snapshot();cc=d.estados_controle();t=s.get('target')
    if not t or t['name']!='Verit Mutante' or t['hp']<=.5*t['hp_max'] or not condicao_teste(s,cc,t['id']):raise RuntimeError('Sem janela de teste: preciso de Verit proximo com mais de metade da vida, sem conjuracao/stun e player saudavel')
    if cc.get('normal_skill')!=961:raise RuntimeError('Ataque da templaria diferente do contrato deste teste')
    id_=t['id'];antigo=json.loads((raiz/'build/ativar_verit_leste.json').read_text(encoding='utf-8'))
    cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @cb
    def visitar(hwnd,_):
        global exe
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value!=antigo['pid']:return True
        h=k.OpenProcess(0x1000,False,pid.value)
        if not h:return True
        try:
            b=ctypes.create_unicode_buffer(32768);n=w.DWORD(len(b))
            if k.QueryFullProcessImageNameW(h,0,b,ctypes.byref(n)):
                caminho=Path(b.value).resolve()
                if caminho.name.lower()=='huntingaitan.exe' and raiz/'build' in caminho.parents:
                    exe=caminho;u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        finally:k.CloseHandle(h)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    if not fechadas:raise RuntimeError('Painel ativo nao confirmado; teste nao iniciou')
    fim=time.monotonic()+15
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<fim:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Painel ainda fechando; teste nao iniciou')
    e=EntradaMotor(d.hwnd,d.pid);e.conectar(d)
    def permitido():
        return not (u.GetAsyncKeyState(0x7b)&0x8000) and condicao_teste(d.snapshot(),d.estados_controle(),id_)
    e.permitido=permitido
    r['fase']='comparando';salvar()
    for modo in ('normal','sequencia','sequencia','normal')*2:
        if not permitido():break
        s=d.snapshot();inicio=time.monotonic();hp_anterior=s['target']['hp'];pos=s['player']['position'];dano=0;proximo=0.;comandos=[];ok=True
        rodada=dict(modo=modo,duracao=0.,dano=0,valida=False);r['rodadas'].append(rodada)
        while time.monotonic()-inicio<6:
            if not permitido():ok=False;rodada['interrupcao']='vida, controle, alvo ou F12';break
            s=d.snapshot();agora=time.monotonic();hp=s['target']['hp'];dano+=max(0,hp_anterior-hp);hp_anterior=hp
            if math.dist(pos,s['player']['position'])>.7:ok=False;rodada['interrupcao']='deslocamento indesejado';break
            if agora>=proximo:
                antes=time.perf_counter();envios=sequencia(e,permitido,modo=='sequencia')
                comandos.append(dict(duracao_ms=(time.perf_counter()-antes)*1000,envios=envios));proximo=time.monotonic()+.15
            time.sleep(.04)
        aceitos=sum(tecla=='1' and recebido is True for comando in comandos for tecla,recebido in comando['envios'])
        rodada.update(duracao=time.monotonic()-inicio,dano=dano,valida=ok and aceitos>0,ataques_aceitos=aceitos,comandos=comandos);salvar()
        if not ok:break
    r['comparacao']=avaliar(r['rodadas'])
except Exception as ex:r['erro']=str(ex)
finally:
    if e and e.ponte:
        try:
            try:
                for tecla in ('1','r','w'):e.keyUp(tecla)
                time.sleep(.15);e.ponte.mover(*d.snapshot()['player']['position'])
            finally:e.finalizar()
            r['ponte_removida']=e.ponte is None
        except Exception as ex:r['erro_limpeza']=str(ex)
    if d:d.close()
    if exe and fechadas and not any(u.IsWindow(h) for h in fechadas):
        proc=subprocess.Popen([str(exe),'--user-data-dir='+str(perfil)],cwd=exe.parent)
        antigo['pid']=proc.pid;(raiz/'build/ativar_verit_leste.json').write_text(json.dumps(antigo),encoding='utf-8')
        r['app_reaberto_pid']=proc.pid
    r['fase']='encerrado';salvar()
