"""Fecha os avisos autorizados enquanto o painel esta aberto e a caca parada."""
import ctypes,threading,time,json
from ctypes import wintypes as w

def main(emitir,entrada_controle):
    import mss,pydirectinput as entrada
    from captura_aika import CapturaAika
    from avisos_hunt import DetectorAvisos,reconfirmar
    from entrada_segura import liberar_mouse
    fim=threading.Event();entrada.PAUSE=0
    u=ctypes.windll.user32;u.GetForegroundWindow.restype=w.HWND
    def foco():
        t=ctypes.create_unicode_buffer(256);u.GetWindowTextW(u.GetForegroundWindow(),t,256)
        return t.value=='AikaClient'
    def comandos():
        try:
            for linha in entrada_controle:
                try:d=json.loads(linha)
                except ValueError:continue
                if d.get('command')=='stop':break
        finally:fim.set()
    threading.Thread(target=comandos,daemon=True).start()
    det=DetectorAvisos();ultima_acao=-100.;aviso_erro=-100.
    emitir(dict(event='watcher',message='Monitor de convites e conversas ativo.'))
    try:
        with (getattr(mss,'MSS',None) or mss.mss)() as captura:
            cap=CapturaAika(captura)
            while not fim.wait(.35):
                if not foco() or time.monotonic()-ultima_acao<.7:continue
                try:
                    aviso=det.localizar(cap.capturar())
                    if not aviso:continue
                    ponto=reconfirmar(aviso)
                    if not ponto or fim.is_set() or not foco():continue
                    entrada.moveTo(*ponto)
                    if fim.is_set() or not foco():continue
                    entrada.mouseDown()
                    try:fim.wait(.045)
                    finally:liberar_mouse(entrada)
                    ultima_acao=time.monotonic()
                    emitir(dict(event='watcher',message='Convite CTE/Elter: Cancelar clicado.' if aviso['tipo']=='cte_elter' else 'Janela de mensagem de amigo fechada.',tipo=aviso['tipo']))
                except Exception as e:
                    if time.monotonic()-aviso_erro>=5:
                        emitir(dict(event='watcher',message='Monitor aguardando imagem valida.',detail=str(e)));aviso_erro=time.monotonic()
    finally:
        fim.set();emitir(dict(event='watcher',message='Monitor de janelas encerrado.'))
