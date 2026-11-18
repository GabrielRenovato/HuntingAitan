"""Recuperacao limitada da selecao; nao infere morte por desaparecimento."""
class RecuperacaoAlvo:
    def __init__(self,prazo=5.,tentativas=8,intervalo=.5):
        self.prazo=prazo;self.limite=tentativas;self.intervalo=intervalo
        self.reiniciar()
    def reiniciar(self):
        self.desde=None;self.ultima=None;self.tentativas=0
    def pausar(self,duracao):
        if self.desde is not None:self.desde+=duracao
        if self.ultima is not None:self.ultima+=duracao
    def decidir(self,agora):
        if self.desde is None:self.desde=agora
        if agora-self.desde>=self.prazo:return 'indisponivel'
        if self.ultima is not None and agora-self.ultima<self.intervalo:return 'aguardar'
        if self.tentativas>=self.limite:return 'indisponivel'
        self.tentativas+=1;self.ultima=agora
        return 'tab'
