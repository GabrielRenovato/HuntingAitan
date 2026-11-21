import unittest,copy
from huntingaitan.combate.hunt_core import CadenciaCombate
from huntingaitan.configuracao.perfil_hunt import validar,DEFAULT

class CadenciaRapidaTeste(unittest.TestCase):
 def test_abertura_normal_tem_prioridade_em_alcance_sem_ignorar_intervalo(self):
  c=CadenciaCombate({'recargas':{'2':150}})
  self.assertEqual(c.escolher(0,True,False,1,em_alcance=True,iniciar_normal=True),'1')
  c.registrar('1',0)
  self.assertIsNone(c.escolher(.1,True,False,1,em_alcance=True,iniciar_normal=True))
  self.assertEqual(c.escolher(.12,True,False,1,em_alcance=True,iniciar_normal=False),'2')
 def test_abertura_nao_ataca_alvo_morto_ou_invalido(self):
  c=CadenciaCombate({})
  self.assertIsNone(c.escolher(0,False,False,1,True,iniciar_normal=True))
  self.assertIsNone(c.escolher(0,True,False,0,True,iniciar_normal=True))
 def test_skill_em_alcance_nao_espera_primeiro_dano(self):
  c=CadenciaCombate({'recargas':{'4':15}})
  self.assertEqual(c.escolher(0,True,False,1,em_alcance=True),'4')
  self.assertEqual(c.escolher(0,True,False,1,em_alcance=False),'1')
 def test_fim_do_stun_nao_exige_novo_dano_para_usar_skill(self):
  c=CadenciaCombate({'recargas':{'4':15}})
  self.assertEqual(c.escolher(10,True,False,.6,em_alcance=True),'4')
 def test_recargas_individuais_e_intervalo_continuam_valendo(self):
  c=CadenciaCombate({'intervalo_skills':.7,'recargas':{'4':15,'5':17}})
  c.registrar('4',0)
  self.assertIsNone(c.escolher(.69,True,True,1,True))
  self.assertEqual(c.escolher(.7,True,True,1,True),'5')
  c.registrar('5',.7)
  self.assertNotIn(c.escolher(2,True,True,1,True),['4','5'])
  c.registrar('1',2)
  self.assertEqual(c.escolher(15,True,True,1,True),'1')
  c.registrar('1',15)
  self.assertEqual(c.escolher(15.13,True,True,1,True),'4')
 def test_ataque_normal_nao_acrescenta_meio_segundo_a_skill_pronta(self):
  c=CadenciaCombate({'recargas':{'4':15}});c.registrar('1',0)
  self.assertEqual(c.escolher(.12,True,False,1,True),'4')
 def test_migracao_da_janela_antiga_aplica_nova_cadencia(self):
  p=copy.deepcopy(DEFAULT);p.update(version=2,action_gap=1.4)
  r=validar(p);self.assertEqual(r['action_gap'],.7);self.assertEqual(r['skills'],p['skills'])
  p['action_gap']=2.;self.assertEqual(validar(p)['action_gap'],2.)
 def test_alvo_morto_ou_invalido_nao_recebe_skill(self):
  c=CadenciaCombate({})
  self.assertIsNone(c.escolher(0,False,True,1,True))
  self.assertIsNone(c.escolher(0,True,True,0,True))

if __name__=='__main__':unittest.main()
