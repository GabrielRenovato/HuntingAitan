"""Contrato das rotas de caca usado pelo motor.

Uma rota decide onde o personagem pode estar (contem), para onde andar (destino)
e como tratar mobs e pausas. Os metodos opcionais tem padrao neutro, para que
modos sem esses recursos nao precisem implementa-los.
"""

class Rota:
    contem=staticmethod(lambda pos,margem=0:False)

    def conferir(self,pasta):return None
    def pausar(self,duracao):return None
    def combate_ativo(self):return None
    def filtrar_mobs(self,mobs,pos,raio,defendendo=False):return mobs
    def atingiu_limite(self,pos):return False
    def lazapa_proximo(self,mobs,pos):return None
    def replanejar_passagem(self,pos):return False

    def destino(self,pos,agora):
        raise NotImplementedError(f'{type(self).__name__} precisa implementar destino()')
