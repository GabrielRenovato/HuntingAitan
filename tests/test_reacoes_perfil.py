import unittest
from huntingaitan.configuracao.perfil_hunt import validar

def com(tecla,**perfil):
    return validar(dict(reacoes=[dict(nome='r',tecla=tecla,tipo='cura')],**perfil))

class TeclasReservadasTest(unittest.TestCase):
    def test_buffs_por_tempo_reservam_ctrl_1_a_5(self):
        for t in ('ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5'):
            with self.subTest(t=t),self.assertRaisesRegex(ValueError,'repetido'):com(t,buffs_enabled=True)

    def test_sem_buffs_por_tempo_a_tecla_fica_livre(self):
        self.assertEqual(com('ctrl+3',buffs_enabled=False)['reacoes'][0]['tecla'],'ctrl+3')

    def test_buffs_adicionais_e_f3_automatico(self):
        for t in ('ctrl+6','ctrl+8'):
            with self.subTest(t=t):
                with self.assertRaisesRegex(ValueError,'repetido'):com(t,extra_buffs_enabled=True)
                self.assertEqual(com(t,extra_buffs_enabled=False)['reacoes'][0]['tecla'],t)
        with self.assertRaisesRegex(ValueError,'repetido'):com('f3',f3_enabled=True)
        self.assertEqual(com('f3',f3_enabled=False)['reacoes'][0]['tecla'],'f3')

    def test_f2_do_remediar_nao_conflita_com_o_padrao(self):
        self.assertEqual(com('f2')['reacoes'][0]['tecla'],'f2')

    def test_regra_inativa_nao_reserva_nem_conflita(self):
        p=validar(dict(reacoes=[dict(nome='r',tecla='ctrl+3',tipo='cura',ativa=False)]))
        self.assertFalse(p['reacoes'][0]['ativa'])

if __name__=='__main__':unittest.main()
