"""Valida por 120s o circuito sul pelo motor interno, somente no perfil principal."""
import ctypes,json,os,re,subprocess,sys,time
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.escolha_cliente import abrir_leitor
from huntingaitan.leitura.skills_cliente import ler_skill
from huntingaitan.configuracao.perfil_hunt import validar
from huntingaitan.rotas.circuito_cinzas_sul import dentro_cinzas_sul

pasta=Path(os.environ['APPDATA'])/'aika-caca-automatica';dest=raiz/'build'/('croshu_sul_threads_'+time.strftime('%Y%m%d_%H%M%S'));dest.mkdir()
(raiz/'build/ultimo_croshu_sul_threads.txt').write_text(str(dest),encoding='utf-8')
u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.IsWindow.argtypes=[w.HWND]
r=dict(fase='preflight',ajustes=[]);d=None;proc=None;out=None;err=None;fechadas=[];exepainel=None
def salvar():(dest/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    p=json.loads((pasta/'profile.json').read_text(encoding='utf-8'));d=abrir_leitor(p['client_pid'])
    player=d.snapshot()['player'];r.update(nome=player['name'],posicao=player['position'],hp_inicial=player['hp']/player['hp_max'],sha256=d.sha256)
    if d.hwnd!=p['client_hwnd']:raise RuntimeError('Janela selecionada mudou; painel preservado')
    if player['name']!='Domination':raise RuntimeError('Cliente selecionado nao e a templaria esperada')
    if not dentro_cinzas_sul(player['position']):raise RuntimeError('Personagem fora do circuito sul; painel preservado')
    if r['hp_inicial']<.65:raise RuntimeError('Vida abaixo de 65%; painel preservado')
    if d.caca_original_ativa():raise RuntimeError('Caca original ligada; painel preservado')
    # O binario inteiro ja passou na lista de hashes do leitor. Registra as
    # rotinas existentes, sem instalar nem executar novos contratos.
    r['contratos']={nome:dict(rva=hex(rva),prefixo=d.read(d.base+rva,12).hex()) for nome,rva in (
        ('mover_destino',0x7d820),('selecionar_id',0x107270),('habilidade',0xee0d0),('camera',0x1b46a0))}
    cc=d.recargas_atalhos();tipos=dict(d.tipos_atalhos)
    r['barra']={k:dict(v,nome=ler_skill(d,v['skill'])['nome']) for k,v in cc.items()}
    cmd="[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); Get-CimInstance Win32_Process -Filter \"name='HuntingAitan.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    txt=subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,encoding='utf-8',check=True).stdout.strip();ps=json.loads(txt) if txt else []
    if isinstance(ps,dict):ps=[ps]
    alvos=[x for x in ps if '--type=' not in (x.get('CommandLine') or '') and (re.search(re.escape(str(pasta).lower())+r'(?![\w-])',(x.get('CommandLine') or '').lower()) or '--user-data-dir' not in (x.get('CommandLine') or '').lower())]
    ids={x['ProcessId'] for x in alvos}
    if alvos and alvos[0].get('ExecutablePath'):exepainel=Path(alvos[0]['ExecutablePath'])
    cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    @cb
    def visitar(hwnd,_):
        pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value in ids:u.PostMessageW(hwnd,0x10,0,0);fechadas.append(hwnd)
        return True
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.EnumWindows(visitar,0)
    prazo=time.monotonic()+20
    while any(u.IsWindow(h) for h in fechadas) and time.monotonic()<prazo:time.sleep(.1)
    if any(u.IsWindow(h) for h in fechadas):raise RuntimeError('Painel ainda encerrando; teste nao iniciou')
    time.sleep(1)
    arquivo=pasta/'profile.json';texto=arquivo.read_text(encoding='utf-8');p=json.loads(texto)
    (pasta/('profile.antes-threads-sul-'+time.strftime('%Y%m%d_%H%M%S')+'.json')).write_text(texto,encoding='utf-8')
    # Remover somente os buffs que o proprio cliente confirmou em slots vazios.
    for i,k in enumerate(p['buff_keys']):
        if k and tipos.get(k)==0:p['buff_keys'][i]='';r['ajustes'].append('Buff vazio ignorado: '+k)
    if all(tipos.get(k)==0 for k in p['extra_buff_keys']):
        p['extra_buffs_enabled']=False;r['ajustes'].append('Extras em slots vazios desativados')
    if 961<=cc.get(p['attack_key'],{}).get('skill',0)<=976:
        p['unstuck_key']='4'
        atual=r['barra'].get(p['heal_key'],{})
        if p['heal_enabled'] and 'remediar' not in atual.get('nome','').lower():
            curas=[k for k,v in r['barra'].items() if 'remediar' in v['nome'].lower() and '+' not in k]
            if len(curas)==1:p['heal_key']=curas[0];r['ajustes'].append('Cura alinhada a Remediar na barra: '+curas[0])
    p.update(patrol_mode='cinzenta_croshu_sul',background_keys=True)
    p=validar(p);arquivo.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    (dest/'profile.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    r['segundo_plano']=True;r['fase']='rodando';salvar()
    env=dict(os.environ,AIKA_DATA_DIR=str(dest),AIKA_CLIENT_PID=str(p['client_pid']),AIKA_CLIENT_HWND=str(p['client_hwnd']))
    out=(dest/'stdout.jsonl').open('w',encoding='utf-8');err=(dest/'stderr.txt').open('w',encoding='utf-8')
    proc=subprocess.Popen([sys.executable,'-u',str(raiz/'hunt_bridge.py'),'run',str(dest/'profile.json')],cwd=raiz,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True)
    limite=time.monotonic()+120;r['amostras_foco']=0;r['amostras_sem_foco']=0
    while proc.poll() is None and time.monotonic()<limite:
        s=d.snapshot()['player'];r['hp_minimo']=min(r.get('hp_minimo',1.),s['hp']/s['hp_max']);r['ultima_posicao']=s['position']
        r['amostras_foco']+=1;r['amostras_sem_foco']+=u.GetForegroundWindow()!=d.hwnd;salvar()
        if r['hp_minimo']<.65:r['parada']='vida abaixo de 65%';break
        if (dest/'PARAR').exists():r['parada']='pedido local';break
        time.sleep(.5)
except Exception as e:r['erro']=str(e)
finally:
    if proc and proc.poll() is None:
        try:proc.stdin.write('{"command":"stop"}\n');proc.stdin.flush();proc.wait(timeout=15)
        except Exception as e:r['erro_parada']=str(e)
    if out:out.close()
    if err:err.close()
    if d:d.close()
    r['codigo']=proc.returncode if proc else None;r['fase']='encerrado';salvar()
    # O painel sera reaberto apos a conferencia dos logs, sem reiniciar a caca.
