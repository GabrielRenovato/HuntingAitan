import unittest
from huntingaitan.combate.aproximacao_janela import AproximacaoJanela

class AproximacaoTeste(unittest.TestCase):
    def test_repetir_ataque_nao_esconde_falta_de_deslocamento(self):
        a=AproximacaoJanela()
        self.assertEqual(a.decidir(1,(0,0),0),'atacar')
        self.assertEqual(a.decidir(1,(0,0),.1),'aguardar')
        self.assertEqual(a.decidir(1,(0,0),1),'atacar')
        self.assertEqual(a.decidir(1,(0,0),3),'bloqueado')

    def test_movimento_real_novo_alvo_e_stun_reiniciam_prazo(self):
        a=AproximacaoJanela();a.decidir(1,(0,0),0)
        self.assertEqual(a.decidir(1,(1,0),2),'atacar')
        self.assertNotEqual(a.decidir(1,(1,0),4),'bloqueado')
        self.assertEqual(a.decidir(2,(1,0),5),'atacar')
        a.reiniciar();self.assertEqual(a.decidir(2,(1,0),20),'atacar')
