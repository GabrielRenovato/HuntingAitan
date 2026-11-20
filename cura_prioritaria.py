"""Cura separada da fila ofensiva; um envio nao comprova uso da habilidade."""


class CuraPrioritaria:
    def __init__(self, tecla, limite, intervalo_fallback):
        self.tecla=tecla
        self.limite=limite
        self.intervalo_fallback=intervalo_fallback
        self.tentar_em=0.
        self.fallback_em=0.
        self.pendente=None
        self.falhas=0;self.recuperar=False

    def observar(self, agora, hp, real):
        if self.pendente is None:return None
        inicio,hp_antes=self.pendente
        if real is not None and not real['ready']:
            self.pendente=None
            self.fallback_em=inicio+self.intervalo_fallback
            self.falhas=0;self.recuperar=False
            return 'recarga_confirmada'
        if hp>hp_antes+.03:
            self.pendente=None
            self.fallback_em=inicio+self.intervalo_fallback
            self.falhas=0;self.recuperar=False
            return 'hp_recuperado'
        if agora-inicio>=2:
            self.pendente=None
            self.falhas+=1
            if self.falhas>=2:
                self.recuperar=True;self.tentar_em=max(self.tentar_em,agora+3)
            return 'sem_confirmacao'
        return None

    def necessaria(self, agora, hp, real):
        if not self.tecla or not 0<hp<=self.limite or agora<self.tentar_em:return False
        if real is not None:return real['ready']
        return agora>=self.fallback_em

    def enviada(self, agora, hp):
        self.pendente=(agora,hp)
        self.tentar_em=agora+2.

    def aguardando_inicio(self, agora):
        # Nenhuma skill ofensiva deve interromper a janela de confirmacao.
        return self.pendente is not None
