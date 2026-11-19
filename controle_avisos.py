"""Monitor recuperavel; a ausencia de janela precisa de duas capturas validas."""
import threading,time

def preparar_runtime_visual():
    # Inicializa extensoes nativas antes dos hooks de teclado e das threads
    # de leitura. No binario Windows, a ordem inversa pode bloquear o loader.
    import numpy,cv2

class ObservadorAvisos:
    def __init__(self,fim,ativo,log,bloqueio=None,detector=None,relogio=time.monotonic):
        self.fim=fim;self.ativo=ativo;self.log=log;self.bloqueio=bloqueio or threading.Event()
        self.detector=detector;self.relogio=relogio;self.lock=threading.Lock()
        self.ultimo=None;self.erro=None;self.livres=0;self.log_em=-100.

    def preparar(self):
        # O carregador do OpenCV no executavel congelado nao pode disputar
        # sua primeira importacao entre a thread do monitor e a de interface.
        if self.detector is None:
            preparar_runtime_visual()
            from avisos_hunt import DetectorAvisos
            self.detector=DetectorAvisos()

    def iniciar(self):
        self.preparar()
        tarefa=threading.Thread(target=self.executar,daemon=True)
        tarefa.start()
        return tarefa

    def observar(self,tela):
        aviso=self.detector.localizar(tela,ao_bloquear=self.bloqueio.set)
        with self.lock:
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

    def executar(self):
        while not self.fim.is_set():
            try:
                import mss
                from captura_aika import CapturaAika
                from avisos_hunt import DetectorAvisos
                if self.detector is None:self.detector=DetectorAvisos()
                with (getattr(mss,'MSS',None) or mss.mss)() as sct:
                    cap=CapturaAika(sct)
                    while not self.fim.wait(.2):
                        if not self.ativo():continue
                        try:self.observar(cap.capturar())
                        except Exception as e:
                            self.falhou(e);break
            except Exception as e:self.falhou(e)
            self.fim.wait(.3)
