import unittest
from cancelamento_normal import CancelamentoNormal,executar_cancelamento
from perfil_hunt import validar

class CancelamentoTeste(unittest.TestCase):
 def preparar(self):
  c=CancelamentoNormal(True);a=dict(id=42,hp=100,position=(0,1))
  c.observar(0,a,(0,0),42);c.acao(True,0,0)
  return c,a
 def test_so_envia_depois_do_dano_e_nao_reenvia_mesmo_hp(self):
  c,a=self.preparar()
  self.assertFalse(c.observar(.2,a,(0,0),42))
  a['hp']=90;self.assertFalse(c.observar(.3,a,(0,0),42))
  self.assertTrue(c.observar(.37,a,(0,0),42))
  self.assertFalse(c.observar(.8,a,(0,0),42))
 def test_nao_interrompe_skill_nem_aproximacao(self):
  c,a=self.preparar();c.acao(False,.1,1.5);a['hp']=90
  self.assertFalse(c.observar(.3,a,(0,0),42))
  self.assertFalse(c.observar(.4,a,(0,0),42))
  c,a=self.preparar();a.update(hp=90,position=(0,8))
  self.assertFalse(c.observar(.3,a,(0,0),42))
  self.assertFalse(c.observar(.4,a,(0,0),42))
 def test_stun_perda_alvo_movimento_morte(self):
  for alteracao in ['ausente','outro','morto','movendo']:
   c,a=self.preparar();a['hp']=90;c.observar(.3,a,(0,0),42)
   pos=(0,0)
   if alteracao=='ausente':a=None
   elif alteracao=='outro':a['id']=99
   elif alteracao=='morto':a['hp']=0
   else:pos=(1,0)
   self.assertFalse(c.observar(.4,a,pos,42),alteracao)
 def test_sem_novo_dano_desativa_para_esse_alvo(self):
  c,a=self.preparar();a['hp']=90;c.observar(.3,a,(0,0),42)
  self.assertTrue(c.observar(.4,a,(0,0),42))
  c.acao(True,2.3,2.8);self.assertFalse(c.observar(2.5,a,(0,0),42))
  a['hp']=80;self.assertFalse(c.observar(2.6,a,(0,0),42));self.assertTrue(c.suspenso)
 def test_cancelamento_nao_envia_w_na_borda_do_alcance(self):
  c,a=self.preparar();a.update(position=(2.3,0),hp=90)
  self.assertFalse(c.observar(.3,a,(0,0),42));self.assertFalse(c.observar(.4,a,(0,0),42))
 def test_suspensao_por_distancia_dura_ate_trocar_de_mob(self):
  c,a=self.preparar();c.suspender_alvo(42);a['hp']=90
  self.assertFalse(c.observar(.3,a,(0,0),42));self.assertTrue(c.suspenso)
  a['id']=43;c.observar(.4,a,(0,0),43);self.assertFalse(c.suspenso)
 def test_foco_perdido_entre_w_e_ataque(self):
  chamadas=[];foco=[True]
  def pulso(k,d=.045):chamadas.append(k);foco[0]=False;return True
  self.assertFalse(executar_cancelamento(pulso,lambda:foco[0],'1'))
  self.assertEqual(chamadas,['w'])
 def test_perfil_opt_in(self):
  self.assertFalse(validar({})['cancel_normal'])
  self.assertTrue(validar({'cancel_normal':True})['cancel_normal'])
  with self.assertRaises(ValueError):validar({'cancel_normal':'true'})

if __name__=='__main__':unittest.main()
