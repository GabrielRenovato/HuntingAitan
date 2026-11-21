import unittest
from huntingaitan.combate.hunt_core import CadenciaCombate


class CadenciaCalibradaTeste(unittest.TestCase):
    def test_calibracao_respeita_170ms_entre_tentativas(self):
        c=CadenciaCombate({'recargas':{}})
        c.registrar('1',0,intervalo_normal=.17)
        self.assertIsNone(c.escolher(.16,True,True,1,True))
        self.assertEqual(c.escolher(.17,True,True,1,True),'1')

    def test_configuracao_sem_combo_mantem_cadencia_anterior(self):
        c=CadenciaCombate({'recargas':{}});c.registrar('1',0)
        self.assertIsNone(c.escolher(.17,True,True,1,True))
        self.assertEqual(c.escolher(1,True,True,1,True),'1')

    def test_intervalo_nao_pode_ficar_abaixo_do_medido(self):
        c=CadenciaCombate({'recargas':{}});c.registrar('1',0,intervalo_normal=0)
        self.assertEqual(c.normal_em,.17)


if __name__=='__main__':unittest.main()
