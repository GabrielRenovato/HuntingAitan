import unittest
from huntingaitan.combate.reacoes import Reacoes,validar_regra,grupo_de_recarga

class BuffContinuoTest(unittest.TestCase):
    def setUp(self):
        self.r=validar_regra(dict(nome='Sangue Sagrado',tecla='3',tipo='buff',skill_id=1146,mp_min=284,intervalo_s=3))
        self.m=Reacoes([self.r]);self.cd=[0.]*43

    def escolher(self,t=0,mp=1000,cd=None,**kw):
        return self.m.escolher(t,1.,1.,mp,False,[],self.cd if cd is None else cd,alvo=None,**kw)

    def test_usa_com_hp_cheio_sem_alvo_e_sem_combate(self):
        self.assertIs(self.escolher(),self.r)

    def test_recarga_real_libera_sem_esperar_120_segundos(self):
        self.m.enviada(self.r,0);grupo=grupo_de_recarga(1146);self.cd[grupo]=.5
        self.assertIsNone(self.escolher(30))
        self.cd[grupo]=0
        self.assertIs(self.escolher(30),self.r)

    def test_aguarda_mana_e_agenda_de_buffs(self):
        self.assertIsNone(self.escolher(mp=283))
        self.assertIsNone(self.escolher(buffs_liberados=False))

    def test_nao_inventa_recarga_quando_leitura_falha(self):
        self.assertIsNone(self.m.escolher(0,1.,1.,1000,False,[],None))

    def test_efeito_ativo_impede_repeticao_e_libera_apos_sumir(self):
        self.m.atualizar_efeitos([1146]);self.assertIsNone(self.escolher())
        self.m.atualizar_efeitos([]);self.assertIs(self.escolher(),self.r)

    def test_efeito_ativo_nao_bloqueia_cura(self):
        r=validar_regra(dict(nome='Cura',tecla='7',tipo='cura',skill_id=1088))
        m=Reacoes([r]);m.atualizar_efeitos([1088])
        self.assertIs(m.escolher(0,.3,1.,1000,False,[],self.cd),r)

    def test_motor_envia_sem_alvo_mas_reduz_repeticoes_sem_resposta(self):
        from tests.test_reacoes_motor import perfil,sessao,teclas
        from huntingaitan.leitura.replay import reproduzir
        t=reproduzir(sessao(),perfil(self.r),limite_segundos=7)
        self.assertIsNone(t['erro']);usos=teclas(t,'3')
        self.assertEqual(len(usos),1)
        self.assertTrue(any(e.get('event')=='reaction_result' and e.get('ok') is False for e in t['eventos']))
