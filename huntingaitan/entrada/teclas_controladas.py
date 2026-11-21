"""Envio de teclas do motor: so com o Aika em foco, sem teclas presas e com liberacao garantida."""
import threading,time
from huntingaitan.entrada.entrada_segura import liberar_tecla

class TeclasControladas:
    """Mantem o conjunto de teclas seguradas e garante a liberacao ao parar, perder foco ou abrir modal."""
    def __init__(self,entrada,pressionar_sem_pausa,ativo,modal):
        self.entrada=entrada;self.pressionar_sem_pausa=pressionar_sem_pausa;self.ativo=ativo;self.modal=modal
        self.seg=set();self.lock=threading.RLock();self.ultima=[time.monotonic()]

    def soltar(self):
        with self.lock:
            for k in list(self.seg):
                if liberar_tecla(self.entrada,k) is not False:self.seg.discard(k)

    def liberar(self,k):
        with self.lock:
            if k in self.seg and liberar_tecla(self.entrada,k) is not False:self.seg.discard(k)

    def segurar(self,k):
        with self.lock:
            if not self.ativo() or self.modal.is_set():return False
            if k not in self.seg:
                if self.pressionar_sem_pausa(k) is False:return False
                self.seg.add(k)
            return True

    def esperar(self,s):
        ate=time.monotonic()+s
        while self.ativo():
            restante=ate-time.monotonic()
            if restante<=0:break
            time.sleep(min(.005,restante))

    def pulso(self,k,s=.045):
        if not k or not self.ativo():return False
        if not self.segurar(k):return False
        try:self.esperar(s)
        finally:self.liberar(k)
        return True

    def vigiar(self,fim):
        """Thread de seguranca: solta tudo se a caca parar, o foco sair, um modal abrir ou o laco travar."""
        while not fim.wait(.03):
            if not self.ativo() or self.modal.is_set() or time.monotonic()-self.ultima[0]>.5:self.soltar()
