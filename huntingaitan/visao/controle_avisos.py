"""Monitor recuperavel; a ausencia de janela precisa de duas capturas validas."""
import threading,time

def preparar_runtime_visual():
    # Inicializa extensoes nativas antes dos hooks de teclado e das threads
    # de leitura. No binario Windows, a ordem inversa pode bloquear o loader.
    import numpy,cv2

class ObservadorAvisos:
    def __init__(self,fim,ativo,log,bloqueio=None,detector=None,relogio=time.monotonic,janela=None):
        self.fim=fim;self.ativo=ativo;self.log=log;self.bloqueio=bloqueio or threading.Event()
        self.detector=detector;self.relogio=relogio;self.lock=threading.Lock()
        self.janela=janela;self.area=None
        self.ultimo=None;self.erro=None;self.livres=0;self.log_em=-100.;self.ultima_tela=None

    def preparar(self):
        # O carregador do OpenCV no executavel congelado nao pode disputar
        # sua primeira importacao entre a thread do monitor e a de interface.
        if self.detector is None:
            preparar_runtime_visual()
            from huntingaitan.visao.avisos_hunt import DetectorAvisos
            self.detector=DetectorAvisos()

    def iniciar(self):
        self.preparar()
        tarefa=threading.Thread(target=self.executar,daemon=True)
        tarefa.start()
        return tarefa

    def observar(self,tela):
        aviso=self.detector.localizar(tela,ao_bloquear=self.bloqueio.set)
        with self.lock:
            self.ultima_tela=tela
            self.erro=None
            self.ultimo=dict(aviso,capturado=self.relogio()) if aviso else None
            if aviso:self.livres=0;self.bloqueio.set()
            else:
                self.livres+=1
                if self.livres>=2:self.bloqueio.clear()

    def falhou(self,erro):
        with self.lock:
            self.erro=str(erro);self.ultimo=None;self.livres=0;self.bloqueio.set()
        if self.relogio()-self.log_em>=5:
            self.log('Monitor de janelas: captura indisponivel; entradas suspensas ate reconfirmar.',detail=str(erro))
            self.log_em=self.relogio()

    def atual(self):
        with self.lock:return self.ultimo.copy() if self.ultimo else None

    def salvar_diagnostico(self,caminho):
        """Grava somente o ultimo quadro do cliente escolhido, quando ha bloqueio."""
        from pathlib import Path
        import cv2
        with self.lock:tela=self.ultima_tela
        if tela is None:return False
        caminho=Path(caminho);caminho.parent.mkdir(parents=True,exist_ok=True)
        ok,imagem=cv2.imencode('.png',tela)
        if not ok:return False
        caminho.write_bytes(imagem.tobytes());return True

    def reconfirmar(self,aviso):
        from huntingaitan.visao.avisos_hunt import reconfirmar_imagem
        with self.lock:
            atual=self.ultimo;imagem=self.ultima_tela;area=self.area
            if not atual or not area or imagem is None or atual['tipo']!=aviso['tipo'] or self.relogio()-atual['capturado']>1:return None
            imagem=imagem.copy()
        return reconfirmar_imagem(aviso,imagem,area)

    def executar(self):
        from contextlib import ExitStack
        while not self.fim.is_set():
            try:
                if self.detector is None:self.preparar()
                with ExitStack() as pilha:
                    if self.janela:
                        from huntingaitan.visao.captura_janela import CapturaJanela
                        cap=pilha.enter_context(CapturaJanela(*self.janela))
                    else:
                        import mss
                        from huntingaitan.visao.captura_aika import CapturaAika
                        sct=pilha.enter_context((getattr(mss,'MSS',None) or mss.mss)())
                        cap=CapturaAika(sct)
                    while not self.fim.wait(.2):
                        if not self.ativo():continue
                        try:
                            imagem=cap.capturar()
                            with self.lock:self.area=cap.area
                            self.observar(imagem)
                        except Exception as e:
                            self.falhou(e);break
            except Exception as e:self.falhou(e)
            self.fim.wait(.3)
