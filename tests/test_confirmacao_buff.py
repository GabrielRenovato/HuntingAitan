import unittest
from huntingaitan.combate.confirmacao_buff import ConfirmacaoBuff
from huntingaitan.combate.hunt_core import AgendaBuffs
from huntingaitan.combate.vigia_ataque import VigiaAtaque
from huntingaitan.combate.reacoes import grupo_de_recarga

def cc(ativos=(),casting=False,cd=0):
    cds=[0.]*43;cds[grupo_de_recarga(1135)]=cd
    return dict(active_skill_ids=list(ativos),casting=casting,casting_skill=1135 if casting else None,recargas_grupos=cds)

class BuffTeste(unittest.TestCase):
    def test_mana_e_recarga_nao_substituem_efeito_quando_a_lista_existe(self):
        v=ConfirmacaoBuff();v.iniciar('f3',1135,0,dict(mp=1000),cc())
        self.assertIsNone(v.observar(1,dict(mp=250),cc(cd=1)))
        r=v.observar(6,dict(mp=250),cc(cd=.5));self.assertFalse(r['ok']);self.assertEqual(r['repetir_em'],2)
    def test_aguarda_fim_da_conjuracao_e_confirma_efeito(self):
        v=ConfirmacaoBuff();v.iniciar('f3',1135,0,dict(mp=1000),cc())
        self.assertIsNone(v.observar(2,dict(mp=250),cc([1135],True,1)))
        self.assertTrue(v.observar(3,dict(mp=250),cc([1135],False,.5))['ok'])
    def test_stun_nao_marca_buff_como_aplicado(self):
        v=ConfirmacaoBuff();v.iniciar('f3',1135,0,dict(mp=1000),cc())
        r=v.observar(1,dict(mp=1000),dict(cc(),stunned=True))
        self.assertIsNone(r['ok']);self.assertFalse(v.pendente)
    def test_pausa_nao_consume_o_prazo(self):
        v=ConfirmacaoBuff();v.iniciar('f3',1135,0,dict(mp=1000),cc());v.pausar(20)
        self.assertIsNone(v.observar(25,dict(mp=1000),cc()))
        self.assertFalse(v.observar(26,dict(mp=1000),cc())['ok'])
    def test_adiar_buff_falho_libera_a_sequencia_e_respeita_nova_tentativa(self):
        a=AgendaBuffs(0,['f3','f8'],540,2,True)
        self.assertEqual(a.proximo(0,True),'f3');a.adiar(0,5)
        self.assertEqual(a.proximo(.3,True),'f8');a.confirmar(.3)
        self.assertIsNone(a.proximo(3,True));self.assertEqual(a.proximo(5,True),'f3')
    def test_regeneracao_do_mob_nao_conta_como_sucesso_de_ataque(self):
        v=VigiaAtaque();v.observar(dict(id=1,hp=50),0);v.enviado();v.enviado()
        v.observar(dict(id=1,hp=60),2)
        self.assertTrue(v.iniciar(3,2))
