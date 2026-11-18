"""Ponte JSON local entre o painel Electron e o motor de caca."""
import sys,json,threading,traceback,time,os
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8')

DIARIO=None
LOCK=threading.Lock()
def emitir(d):
    with LOCK:
        if DIARIO:
            DIARIO.write(json.dumps(dict(t=time.time(),**d),ensure_ascii=False)+'\n');DIARIO.flush()
        print(json.dumps(d,ensure_ascii=False),flush=True)

def main():
    from perfil_hunt import DEFAULT,validar,importar_nativo
    modo=sys.argv[1]
    if modo=='watch':
        from vigiar_janelas import main as vigiar
        vigiar(emitir,sys.stdin);return
    if modo!='run':
        d=json.loads(sys.stdin.read() or '{}')
        if modo=='defaults':r=DEFAULT
        elif modo=='selftest':
            import keyboard,pydirectinput,mss,hunt_native
            from avisos_hunt import DetectorAvisos
            DetectorAvisos()
            r=dict(backend=True,templates=True)
        elif modo=='validate':r=validar(d)
        elif modo=='position':
            from dados_internos import DadosInternos
            leitor=DadosInternos()
            try:
                snap=leitor.snapshot();p=snap['player'];r=dict(position=p['position'],hp=p['hp']/p['hp_max'],mp=p['mp']/p['mp_max'] if p['mp_max'] else None,source='native',target=snap['target']['name'] if snap['target'] else None)
            finally:leitor.close()
        elif modo=='native':r=importar_nativo(d['path'],d.get('profile'))
        else:raise ValueError('Comando desconhecido')
        emitir(dict(ok=True,data=r));return
    global DIARIO
    pasta=Path(os.environ.get('AIKA_DATA_DIR',str(Path(__file__).resolve().parent)))/'app_sessions';pasta.mkdir(exist_ok=True)
    DIARIO=(pasta/('run_'+time.strftime('%Y%m%d_%H%M%S')+'.jsonl')).open('w',encoding='utf-8')
    perfil=validar(json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))
    emitir(dict(event='status',state='initializing',message='Inicializando motor '+perfil['data_source'],source=perfil['data_source']))
    control=type('Control',(),{'stop':threading.Event(),'pause':threading.Event()})()
    def comandos():
        try:
            for linha in sys.stdin:
                d=json.loads(linha)
                if d.get('command')=='stop':control.reason='botao_parar';control.stop.set()
                elif d.get('command')=='pause':control.pause.set();emitir(dict(event='status',state='paused',message='Pausado pelo painel.'))
                elif d.get('command')=='resume':control.pause.clear()
        finally:
            if not control.stop.is_set():control.reason='canal_do_painel_fechado'
            emitir(dict(event='log',message='Canal de controle encerrado.',reason=getattr(control,'reason','desconhecido')))
            control.stop.set()
    threading.Thread(target=comandos,daemon=True).start()
    if perfil['data_source']=='native':
        from hunt_native import main as executar
        executar(perfil,emitir,control)
    else:
        raise RuntimeError('Esta distribuicao oferece apenas o motor por dados internos.')

if __name__=='__main__':
    try:main()
    except Exception as e:
        emitir(dict(event='error',ok=False,message=str(e)))
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
