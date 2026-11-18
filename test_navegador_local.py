import unittest
from navegador_local import NavegadorLocal
from test_navegacao_grade import grade

class NavegadorTeste(unittest.TestCase):
 def test_reta_usa_w_sem_giro(self):
  n=NavegadorLocal(lambda d,p:grade(12,12));r=n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0)
  self.assertTrue(r['w']);self.assertIsNone(r['giro'])
 def test_grade_atualizada_nao_reinicia_rota_valida(self):
  g=grade(12,12);n=NavegadorLocal(lambda d,p:g)
  n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0);rota=n.rota
  n.planejar(None,(3.5,1.5),90,(9.5,1.5),'a',2.1)
  self.assertIs(n.rota,rota)
 def test_sem_heading_nao_move_as_cegas(self):
  n=NavegadorLocal();r=n.planejar(None,(1,1),None,(9,1),'a',0)
  self.assertFalse(r['w']);self.assertEqual(r['estado'],'sem_orientacao')
 def test_desvio_reorienta_antes_de_correr_contra_parede(self):
  g=grade(9,9,[(4,y) for y in range(7)]);n=NavegadorLocal(lambda d,p:g)
  r=n.planejar(None,(3.5,2.5),90,(7.5,2.5),'a',0)
  self.assertFalse(r['w']);self.assertIsNotNone(r['giro'])
 def test_bloqueio_fisico_replaneja_e_limita_tentativas(self):
  n=NavegadorLocal(lambda d,p:grade(12,12))
  n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0)
  for t in [2.1,4.2]:self.assertEqual(n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',t)['estado'],'replanejar')
  self.assertEqual(n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',6.3)['estado'],'bloqueado')
 def test_rota_nao_ultrapassa_area_configurada(self):
  n=NavegadorLocal(lambda d,p:grade(12,12));r=n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0,limite=((1.5,1.5),3))
  self.assertEqual(r['estado'],'sem_caminho')
 def test_pausa_por_stun_nao_conta_como_colisao(self):
  n=NavegadorLocal(lambda d,p:grade(12,12));n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0)
  n.suspender((1.5,1.5),10)
  self.assertEqual(n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',10.1)['estado'],'andando')

if __name__=='__main__':unittest.main()
