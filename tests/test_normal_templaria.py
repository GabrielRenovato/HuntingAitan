import unittest
from huntingaitan.combate.normal_templaria import NormalTemplaria
from huntingaitan.combate.hunt_native import ProgressoNativo
from huntingaitan.combate.caca_templaria import CacaTemplaria

def alvo(hp=100,pos=(1,0)):
    return dict(id=8000,ref=1,name='Verit Mutante',template_id=1378,hp=hp,hp_max=100,hostile=True,height=0,position=pos)

class NormalTeste(unittest.TestCase):
    def test_movimento_do_mob_bloqueia_novo_ataque_ate_estabilizar(self):
        n=NormalTemplaria();n.observar(alvo(),0)
        self.assertFalse(n.permitir(.1));self.assertTrue(n.permitir(.2))
        n.observar(alvo(pos=(1.3,0)),.3);self.assertFalse(n.permitir(.6));self.assertTrue(n.permitir(.71))

    def test_dano_e_animacao_em_andamento_impedem_repetir_normal(self):
        n=NormalTemplaria();n.observar(alvo(),0);n.solicitado(.2)
        n.observar(alvo(80),2.9,dict(animation=8))
        self.assertFalse(n.permitir(3));self.assertTrue(n.permitir(4.8))

    def test_dano_da_pran_com_player_ocioso_nao_impede_retomar(self):
        n=NormalTemplaria();n.observar(alvo(),0);n.solicitado(.2)
        n.observar(alvo(80),3,dict(animation=2))
        self.assertTrue(n.permitir(3))

    def test_recusa_nao_causa_repeticao_de_comandos_em_cada_quadro(self):
        n=NormalTemplaria();n.observar(alvo(),0);n.solicitado(.2)
        self.assertFalse(n.permitir(1));self.assertFalse(n.permitir(2.6));self.assertTrue(n.permitir(2.8))

    def test_espera_saida_de_conjuracao(self):
        n=NormalTemplaria();n.observar(alvo(),0);n.apos_conjuracao(1)
        self.assertFalse(n.permitir(1.2));self.assertTrue(n.permitir(1.5))

    def test_conjuracao_nao_consume_prazo_sem_dano(self):
        p=ProgressoNativo(alvo(),0);p.pausar_confirmacao(2);p.pausar_confirmacao(8);p.retomar_confirmacao(12)
        self.assertFalse(p.aproximacao_falhou(14,1,dict(no_damage_seconds=5,radius=50)))
        self.assertTrue(p.aproximacao_falhou(16,1,dict(no_damage_seconds=5,radius=50)))

    def test_retencao_exige_mesmo_tipo_vivo_proximo(self):
        t=CacaTemplaria();player=dict(position=(0,0),height=0)
        self.assertTrue(t.reter_verit(alvo(),player))
        self.assertFalse(t.reter_verit(alvo(0),player));self.assertFalse(t.reter_verit(alvo(pos=(8,0)),player))
        m=alvo();m['template_id']=1251;self.assertFalse(t.reter_verit(m,player))
