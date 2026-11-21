import unittest
from huntingaitan.rotas.base import Rota
from huntingaitan.rotas.circuito_termes import CircuitoTermes,dentro_regiao
from huntingaitan.rotas.circuito_verit import CircuitoVerit,dentro_verit
from huntingaitan.rotas.mina_lenfer import MinaLenfer,dentro_mina
from huntingaitan.rotas.jardim_aereo import JardimAereo,dentro_jardim

class ContratoRotasTest(unittest.TestCase):
    def test_rotas_de_caca_implementam_o_contrato(self):
        for classe in (CircuitoTermes,CircuitoVerit,MinaLenfer,JardimAereo):
            with self.subTest(classe=classe.__name__):
                self.assertTrue(issubclass(classe,Rota))
                self.assertTrue(callable(classe.contem))
                self.assertTrue(callable(classe.destino))

    def test_contem_de_cada_rota_e_sua_area(self):
        self.assertIs(CircuitoTermes.contem,dentro_regiao)
        self.assertIs(CircuitoVerit.contem,dentro_verit)
        self.assertIs(MinaLenfer.contem,dentro_mina)
        self.assertIs(JardimAereo.contem,dentro_jardim)

    def test_padroes_neutros_nao_mudam_comportamento(self):
        r=Rota()
        self.assertIsNone(r.conferir('x'))
        self.assertIsNone(r.pausar(1.))
        self.assertIsNone(r.combate_ativo())
        mobs=[1,2]
        self.assertIs(r.filtrar_mobs(mobs,(0,0),3),mobs)
        self.assertFalse(r.atingiu_limite((0,0)))
        self.assertIsNone(r.lazapa_proximo(mobs,(0,0)))
        self.assertFalse(r.replanejar_passagem((0,0)))
        self.assertFalse(Rota.contem((0,0)))

    def test_destino_sem_implementacao_falha_com_mensagem_clara(self):
        with self.assertRaises(NotImplementedError):Rota().destino((0,0),0.)

if __name__=='__main__':unittest.main()
