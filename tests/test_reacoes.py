import unittest
from huntingaitan.combate.reacoes import Reacoes,grupo_de_recarga,validar_reacoes,validar_regra

def r(**k):
    base=dict(nome='x',tecla='f2',tipo='cura',hp_max_pct=60,skill_id=0,intervalo_s=2.5)
    base.update(k);return base

PRONTAS=[0.]*43

class ValidarTest(unittest.TestCase):
    def test_teclas_com_modificador_e_funcao(self):
        for t in ['f2','ctrl+3','shift+f4','alt+q','7',"'"]:self.assertEqual(validar_regra(r(tecla=t.upper()))['tecla'],t)

    def test_teclas_invalidas(self):
        for t in ['f12','ctrl+ctrl','ctrl+','','espaco','win+1']:
            with self.subTest(t=t),self.assertRaises(ValueError):validar_regra(r(tecla=t))

    def test_tipo_e_limites(self):
        for ruim in [dict(tipo='xyz'),dict(hp_max_pct=0),dict(hp_max_pct=101),dict(intervalo_s=.1),dict(skill_id=12000),dict(mobs_min=-1),dict(ativa='sim')]:
            with self.subTest(ruim=ruim),self.assertRaises(ValueError):validar_regra(r(**ruim))

    def test_tecla_repetida_entre_regras_e_com_reservadas(self):
        with self.assertRaises(ValueError):validar_reacoes([r(nome='a',tecla='f2'),r(nome='b',tecla='f2')])
        with self.assertRaises(ValueError):validar_reacoes([r(tecla='3')],reservadas={'3'})
        self.assertEqual(len(validar_reacoes([r(nome='a',tecla='f2'),r(nome='b',tecla='f2',ativa=False)])),2)

    def test_grupo_de_recarga_segue_a_formula_do_cliente(self):
        self.assertEqual((grupo_de_recarga(1088),grupo_de_recarga(1073),grupo_de_recarga(1)),(7,7,0))
        self.assertIsNone(grupo_de_recarga(0));self.assertIsNone(grupo_de_recarga(12000))

class EscolherTest(unittest.TestCase):
    def reacoes(self,*regras):return Reacoes([validar_regra(x) for x in regras])

    def test_prioridade_por_tipo_e_depois_pela_ordem(self):
        m=self.reacoes(r(nome='cura',tecla='f2'),r(nome='emerg',tecla='ctrl+2',tipo='emergencia',hp_max_pct=30),r(nome='def',tecla='f3',tipo='defesa',hp_max_pct=50))
        self.assertEqual(m.escolher(0,.25,1,2000,True,1,PRONTAS)['nome'],'emerg')
        self.assertEqual(m.escolher(0,.45,1,2000,True,1,PRONTAS)['nome'],'def')
        self.assertEqual(m.escolher(0,.55,1,2000,True,1,PRONTAS)['nome'],'cura')
        self.assertIsNone(m.escolher(0,.65,1,2000,True,1,PRONTAS))

    def test_vida_cheia_ou_morto_nao_reage(self):
        m=self.reacoes(r())
        self.assertIsNone(m.escolher(0,1,1,0,True,1,PRONTAS));self.assertIsNone(m.escolher(0,0,1,0,True,1,PRONTAS))

    def test_mana_minima_pula_para_a_proxima_regra(self):
        m=self.reacoes(r(nome='grande',tecla='f2',mp_min=1497),r(nome='pequena',tecla='f3',hp_max_pct=60))
        self.assertEqual(m.escolher(0,.4,.1,500,True,1,PRONTAS)['nome'],'pequena')
        self.assertEqual(m.escolher(0,.4,.9,2000,True,1,PRONTAS)['nome'],'grande')

    def test_so_em_combate_e_mobs_minimos(self):
        m=self.reacoes(r(nome='d',tecla='f3',tipo='defesa',so_em_combate=True,mobs_min=2,hp_max_pct=50))
        self.assertIsNone(m.escolher(0,.4,1,0,False,[1,2,3],PRONTAS))
        self.assertIsNone(m.escolher(0,.4,1,0,True,[1],PRONTAS))
        self.assertIsNone(m.escolher(0,.4,1,0,True,None,PRONTAS))
        self.assertIsNotNone(m.escolher(0,.4,1,0,True,[1,5],PRONTAS))
        self.assertIsNone(m.escolher(0,.4,1,0,True,[1,9],PRONTAS))     # o segundo esta fora do raio de 6 m

    def test_item_de_mana_usa_o_limite_de_mana(self):
        m=self.reacoes(r(nome='pocao',tecla='ctrl+6',tipo='item_mp',mp_max_pct=30))
        self.assertIsNone(m.escolher(0,.2,.5,1,True,0,PRONTAS))
        self.assertEqual(m.escolher(0,1,.2,1,True,0,PRONTAS)['nome'],'pocao')

    def test_recarga_real_do_cliente_bloqueia_e_libera(self):
        m=self.reacoes(r(skill_id=1088))
        em_recarga=[0.]*43;em_recarga[7]=1.5
        self.assertIsNone(m.escolher(0,.4,1,2000,True,1,em_recarga))
        self.assertIsNotNone(m.escolher(0,.4,1,2000,True,1,PRONTAS))
        self.assertIsNotNone(m.escolher(0,.4,1,2000,True,1,None))     # sem leitura: so o intervalo vale

    def test_intervalo_minimo_entre_usos(self):
        m=self.reacoes(r(intervalo_s=3))
        regra=m.escolher(10,.4,1,0,True,1,PRONTAS);self.assertIsNotNone(regra);m.enviada(regra,10)
        self.assertIsNone(m.escolher(12.9,.4,1,0,True,1,PRONTAS));self.assertIsNotNone(m.escolher(13.1,.4,1,0,True,1,PRONTAS))

    def test_regra_inativa_e_ignorada_e_lista_vazia_e_falsa(self):
        self.assertFalse(self.reacoes());self.assertFalse(self.reacoes(r(ativa=False,tecla='')))
        self.assertTrue(self.reacoes(r()).tem_cura())

def c(**k):
    d=dict(nome='x',tecla='f2',tipo='ataque',intervalo_s=2.5);d.update(k);return d

class TiposDeCombateTest(unittest.TestCase):
    def reacoes(self,*regras):return Reacoes([validar_regra(x) for x in regras])
    ALVO=dict(hp_pct=80,dist=2.)


    def test_buff_de_combate_nao_depende_da_vida_e_exige_combate(self):
        m=self.reacoes(c(nome='thymos',tecla='5',tipo='buff_combate',skill_id=1320,intervalo_s=180))
        self.assertEqual(m.escolher(0,1.0,1,2000,True,[],PRONTAS)['nome'],'thymos')
        self.assertEqual(m.escolher(0,.2,1,2000,True,[],PRONTAS)['nome'],'thymos')
        self.assertIsNone(m.escolher(0,1.0,1,2000,False,[],PRONTAS))

    def test_ataque_exige_alvo_vivo_alcance_e_faixa_de_vida(self):
        m=self.reacoes(c(nome='emissao',tecla='4',tipo='ataque',alcance_m=6,alvo_hp_min_pct=10,alvo_hp_max_pct=100))
        self.assertIsNone(m.escolher(0,1,1,2000,True,[],PRONTAS,alvo=None))
        self.assertIsNone(m.escolher(0,1,1,2000,True,[],PRONTAS,alvo=dict(hp_pct=80,dist=7)))
        self.assertIsNone(m.escolher(0,1,1,2000,True,[],PRONTAS,alvo=dict(hp_pct=10,dist=2)))   # no minimo, nao conta
        self.assertEqual(m.escolher(0,1,1,2000,True,[],PRONTAS,alvo=self.ALVO)['nome'],'emissao')

    def test_ataque_so_com_varios_mobs_perto(self):
        m=self.reacoes(c(nome='area',tecla='4',tipo='ataque',mobs_min=2,mobs_raio_m=5))
        self.assertIsNone(m.escolher(0,1,1,2000,True,[3],PRONTAS,alvo=self.ALVO))
        self.assertIsNotNone(m.escolher(0,1,1,2000,True,[3,4],PRONTAS,alvo=self.ALVO))
        self.assertEqual(m.raio_mobs(),5.)

    def test_prioridade_sobrevivencia_vem_antes_do_combate(self):
        m=self.reacoes(c(nome='ataque',tecla='4',tipo='ataque'),c(nome='buff',tecla='5',tipo='buff_combate'),c(nome='cura',tecla='f2',tipo='cura',hp_max_pct=40))
        self.assertEqual(m.escolher(0,.3,1,2000,True,[],PRONTAS,alvo=self.ALVO)['nome'],'cura')
        self.assertEqual(m.escolher(0,.9,1,2000,True,[],PRONTAS,alvo=self.ALVO)['nome'],'buff')

    def test_padrao_de_vida_por_tipo(self):
        self.assertEqual([validar_regra(dict(tecla='1',tipo=t))['hp_max_pct'] for t in ('emergencia','defesa','cura','buff_combate','ataque')],[30.,50.,60.,100.,100.])
        self.assertEqual(validar_regra(dict(tecla='1',tipo='cura',hp_max_pct=40))['hp_max_pct'],40.)

    def test_faixa_de_vida_do_alvo_invalida(self):
        with self.assertRaises(ValueError):validar_regra(r(alvo_hp_min_pct=50,alvo_hp_max_pct=50))

    def test_sem_regra_com_mobs_min_nao_precisa_contar(self):
        self.assertEqual(self.reacoes(c()).raio_mobs(),0.)

if __name__=='__main__':unittest.main()
