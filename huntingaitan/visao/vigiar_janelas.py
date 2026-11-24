"""Fecha somente os avisos autorizados com o painel ocioso."""
import ctypes,threading,time,json
from ctypes import wintypes as w
from huntingaitan.visao.controle_avisos import ObservadorAvisos
from huntingaitan.leitura.janela_cliente import localizar_cliente,janela_em_foco


def main(emitir,entrada_controle):
    import pydirectinput as entrada
    from huntingaitan.visao.avisos_hunt import reconfirmar
    from huntingaitan.entrada.entrada_segura import liberar_mouse
    fim=threading.Event();entrada.PAUSE=0
    u=ctypes.windll.user32;u.GetForegroundWindow.restype=w.HWND
    def foco():
        try:return janela_em_foco(u,localizar_cliente(u=u)['hwnd'])
        except RuntimeError:return False
    def log(msg,**extra):emitir(dict(event='watcher',message=msg,**extra))
    def comandos():
        try:
            for linha in entrada_controle:
                try:d=json.loads(linha)
                except ValueError:continue
                if d.get('command')=='stop':break
        finally:fim.set()
    threading.Thread(target=comandos,daemon=True).start()
    monitor=ObservadorAvisos(fim,foco,log);monitor.iniciar()
    proximo_clique=0.;clicou=False;erro_em=-100.
    log('Monitor de convites e conversas ativo.')
    try:
        while not fim.wait(.1):
            if not foco():continue
            aviso=monitor.atual();agora=time.monotonic()
            if not monitor.bloqueio.is_set():
                if clicou:log('Fechamento do aviso confirmado em duas capturas.');clicou=False
                continue
            if not aviso or aviso['tipo'] not in ('cte_elter','arena_elter','conversa_amigo'):continue
            if agora<proximo_clique or agora-aviso['capturado']>1.:continue
            proximo_clique=agora+.6
            try:
                ponto=reconfirmar(aviso)
                if not ponto or fim.is_set() or not foco():continue
                entrada.moveTo(*ponto)
                if fim.is_set() or not foco():continue
                entrada.mouseDown()
                try:fim.wait(.045)
                finally:liberar_mouse(entrada)
                clicou=True
                log('Clique de fechamento enviado; aguardando desaparecer.',tipo=aviso['tipo'])
            except Exception as e:
                if agora-erro_em>=5:log('Monitor aguardando reconfirmacao do aviso.',detail=str(e));erro_em=agora
    finally:
        fim.set();log('Monitor de janelas encerrado.')
