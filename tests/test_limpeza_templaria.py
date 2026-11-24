import unittest
from types import SimpleNamespace
from huntingaitan.combate.caca_templaria import CacaTemplaria
from huntingaitan.combate.identidade_mob import verit_mutante
from huntingaitan.combate.hunt_native import ProgressoNativo,alvo_permitido
from huntingaitan.configuracao.perfil_hunt import validar
from huntingaitan.rotas.navegacao_grade import Grade

def mob(id_,x=1,y=0,template=1244,**kw):
    return dict(id=id_,ref=id_*100,name='Outro nome',template_id=template,position=(x,y),height=0,hp=100,hp_max=100,hostile=True,**kw)

class IdentidadeTeste(unittest.TestCase):
    def test_especie_manda_no_filtro_mesmo_com_nome_diferente(self):
        self.assertTrue(verit_mutante(mob(1,template=1378)))
        m=mob(1);m['name']='Verit Mutante';self.assertFalse(verit_mutante(m))
        p=validar(dict(patrol_mode='termes_verit_leste',radius=50))
        m=mob(1,x=2905,y=820,template=1378)
        self.assertTrue(alvo_permitido(m,dict(position=(2903,820),height=0),(0,0),p))

    def test_id_da_instancia_nao_substitui_codigo_da_especie(self):
        self.assertFalse(verit_mutante(mob(1378,template=1251)))

    def test_nome_localizado_nao_perde_alvo_mas_troca_de_especie_sim(self):
        m=mob(1,template=1378);p=ProgressoNativo(m,0);m['name']='Nome traduzido'
        self.assertEqual(p.observar(m,1),'mesmo')
        m['template_id']=1251;self.assertEqual(p.observar(m,2),'outro')

class LimpezaTeste(unittest.TestCase):
    def setUp(self):self.t=CacaTemplaria();self.player=dict(height=0)
    def test_tres_hostis_disparam_limpeza_e_um_distante_nao_entra(self):
        lista=[mob(1),mob(2,x=2),mob(3,x=3),mob(4,x=8)]
        self.assertEqual(self.t.atualizar_limpeza(lista,(0,0),self.player,0),'iniciada')
        self.assertEqual(self.t.limpeza_ids,{1,2,3})
        self.assertFalse(self.t.permite_limpeza(lista[3],(0,0),self.player))

    def test_dupla_nao_dispara_e_npc_nao_conta(self):
        npc=mob(3);npc['hostile']=False
        self.assertIsNone(self.t.atualizar_limpeza([mob(1),mob(2),npc],(0,0),self.player,0))
        self.assertIsNone(self.t.limpeza_centro)

    def test_mantem_limpeza_do_ultimo_hostil_sem_exigir_tres_novamente(self):
        lista=[mob(1),mob(2,x=2),mob(3,x=3)]
        self.t.atualizar_limpeza(lista,(0,0),self.player,0)
        self.t.atualizar_limpeza([lista[2]],(0,0),self.player,1)
        self.assertTrue(self.t.permite_limpeza(lista[2],(0,0),self.player))
        self.t.atualizar_limpeza([],(0,0),self.player,2)
        self.assertEqual(self.t.atualizar_limpeza([],(0,0),self.player,2.5),'concluida')

    def test_ancora_impede_encadear_limpeza_ate_outro_spot(self):
        self.t.atualizar_limpeza([mob(1),mob(2),mob(3)],(0,0),self.player,0)
        self.assertFalse(self.t.permite_limpeza(mob(4,x=7),(3,0),self.player))
        alto=mob(5);alto['height']=5
        self.assertFalse(self.t.permite_limpeza(alto,(0,0),self.player))

    def test_parede_nao_prende_limpeza_para_sempre_nem_registra_abate(self):
        self.t.atualizar_limpeza([mob(1),mob(2),mob(3)],(0,0),self.player,0)
        self.assertTrue(self.t.aguardar_limpeza(0,False))
        self.assertFalse(self.t.aguardar_limpeza(2.1,False))
        self.assertIsNone(self.t.limpeza_centro)
        self.assertIsNone(self.t.atualizar_limpeza([mob(1),mob(2),mob(3)],(0,0),self.player,3))

    def test_mutante_tem_prioridade_mesmo_com_oito_outros_mobs_mais_perto(self):
        g=Grade((0,0),(0,0),30,30,bytes(900),(0,)*900,1)
        nav=SimpleNamespace(grade=g,grade_em=0)
        lista=[mob(i,x=11,y=10) for i in range(1,9)]+[mob(99,x=18,y=10,template=1378)]
        r=self.t.ordenar(None,nav,(10.5,10.5),lista,0,lambda p:True)
        self.assertEqual(r[0]['id'],99)

    def test_verit_na_borda_da_janela_tem_trecho_em_vez_de_ser_ignorado(self):
        g=Grade((0,0),(0,0),20,20,bytes(400),(0,)*400,1)
        nav=SimpleNamespace(grade=g,grade_em=0)
        r=self.t.ordenar(None,nav,(10.5,10.5),[mob(1,x=22,y=10,template=1378)],0,lambda p:True)
        self.assertEqual([m['id'] for m in r],[1])
