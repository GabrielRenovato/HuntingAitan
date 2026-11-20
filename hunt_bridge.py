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
        elif modo=='selftest-monitor':
            # Executado em processo novo para detectar a disputa de imports
            # que bloqueava a entrada/saida no executavel congelado.
            from controle_avisos import ObservadorAvisos
            fim=threading.Event()
            monitor=ObservadorAvisos(fim,lambda:False,lambda *a,**k:None)
            tarefa=monitor.iniciar()
            try:
                import keyboard
                keyboard.is_pressed('f12')
                from interface_mina import InterfaceMina
                InterfaceMina()
            finally:fim.set();tarefa.join(timeout=3)
            if tarefa.is_alive():raise RuntimeError('Monitor nao encerrou apos preparar a interface')
            r=dict(monitor=True,interface=True)
        elif modo=='selftest':
            import keyboard,pydirectinput,mss,hunt_native
            from avisos_hunt import DetectorAvisos
            DetectorAvisos()
            from dialogos_evento import DetectorEventos,tipo_convite
            detector=DetectorEventos();detector.preparar_ocr()
            import cv2,numpy as np
            teste=np.zeros((160,430,3),np.uint8)
            cv2.putText(teste,'Arena Elter',(15,50),cv2.FONT_HERSHEY_SIMPLEX,.9,(255,255,255),2)
            cv2.putText(teste,'Tempo restante: 111 seg',(15,105),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
            linhas,_=detector.ocr(teste)
            if tipo_convite([(l[1],float(l[2])) for l in linhas or []])!='arena_elter':raise RuntimeError('OCR empacotado nao reconheceu a amostra de teste')
            from circuito_termes import plano,dentro_regiao
            if len(plano()['trechos'])!=2*(len(plano()['pontos'])-1) or not dentro_regiao((2585,654)):raise RuntimeError('Circuito nao incluido no motor')
            from mina_lenfer import plano_mina,dentro_mina
            if not plano_mina()['trechos'] or not dentro_mina((2850,3344)):raise RuntimeError('Rota da Mina nao incluida no motor')
            from interface_mina import InterfaceMina
            from ciclo_mina import CicloMina
            InterfaceMina()
            from geometria_entrada import plano_geometria
            if not plano_geometria()['objetos']:raise RuntimeError('Geometria externa nao incluida no motor')
            from jardim_aereo import plano_jardim,dentro_jardim
            if not plano_jardim()['trechos'] or not dentro_jardim((3351,3295)):raise RuntimeError('Rota do Jardim nao incluida no motor')
            r=dict(backend=True,templates=True,ocr=True,circuito=True,mina=True)
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
    emitir(dict(event='status',state='initializing',message='Preparando reconhecimento antes dos controles de teclado.'))
    from controle_avisos import preparar_runtime_visual
    preparar_runtime_visual()
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
        if perfil['patrol_mode']=='mina_lenfer' and perfil['mina_repeat']:
            from ciclo_mina import main as executar
        elif perfil['patrol_mode']=='jardim_aereo':
            from ciclo_jardim import main as executar
        else:
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
