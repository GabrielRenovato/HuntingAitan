import unittest
from navegador_local import NavegadorLocal
from tests.test_navegacao_grade import grade

class NavegadorTeste(unittest.TestCase):
 def test_bloqueio_informa_o_ponto_para_planejar_desvio(self):
  n=NavegadorLocal(lambda d,p:grade(14,14))
  n.planejar(None,(1.5,1.5),90,(10.5,1.5),'a',0)
  r=n.planejar(None,(1.5,1.5),90,(10.5,1.5),'a',2.1)
  self.assertEqual(r['estado'],'replanejar');self.assertGreater(r['ponto'][0],1.5)
 def test_posicao_descentrada_na_quina_nao_para_sem_comando(self):
  n=NavegadorLocal(lambda d,p:grade(12,12,[(9,8)]))
  r=n.planejar(None,(8.978854,8.449965),14.2632,(10.5,10.5),'a',0)
  self.assertTrue(r['w'] or r['giro'] is not None)
 def test_perto_da_parede_corrige_angulo_pequeno_em_vez_de_ficar_parado(self):
  n=NavegadorLocal(lambda d,p:grade(14,14,[(3,2)]))
  r=n.planejar(None,(1.5,1.99),88,(10.5,1.5),'a',0)
  self.assertFalse(r['w']);self.assertIsNotNone(r['giro'])
 def test_curva_suave_mantem_avanco_sem_reiniciar_na_variacao_do_angulo(self):
  n=NavegadorLocal(lambda d,p:grade(14,14))
  self.assertTrue(n.planejar(None,(1.5,1.5),90,(10.5,1.5),'a',0)['w'])
  r=n.planejar(None,(1.5,1.5),62,(10.5,1.5),'a',.1)
  self.assertTrue(r['w']);self.assertEqual(r['giro'],'d')
  n.suspender((1.5,1.5),.2)
  self.assertFalse(n.planejar(None,(1.5,1.5),62,(10.5,1.5),'a',.3)['w'])
 def test_curva_em_movimento_nao_corta_obstaculo_a_frente(self):
  n=NavegadorLocal(lambda d,p:grade(14,14,[(2,2)]))
  n.planejar(None,(1.5,1.5),90,(10.5,1.5),'a',0)
  self.assertFalse(n.planejar(None,(1.5,1.5),60,(10.5,1.5),'a',.1)['w'])
 def test_curva_em_movimento_respeita_limite_da_area(self):
  n=NavegadorLocal(lambda d,p:grade(14,14));limite=lambda p:p[1]<1.9
  n.planejar(None,(1.5,1.5),90,(10.5,1.5),'a',0,limite=limite)
  self.assertFalse(n.planejar(None,(1.5,1.5),70,(10.5,1.5),'a',.1,limite=limite)['w'])
 def test_correcao_curta_aguarda_resposta_e_nao_oscila_por_erro_pequeno(self):
  n=NavegadorLocal(lambda d,p:grade(14,14))
  r=n.planejar(None,(1.5,1.5),80,(10.5,1.5),'a',0)
  self.assertLess(r['tempo'],.04);self.assertEqual(r['giro'],'d')
  self.assertIsNone(n.planejar(None,(1.5,1.5),80,(10.5,1.5),'a',.04)['giro'])
  self.assertIsNone(n.planejar(None,(1.5,1.5),94,(10.5,1.5),'a',.1)['giro'])
 def test_obstaculo_depois_da_meta_nao_impede_aproximar_da_meta(self):
  n=NavegadorLocal(lambda d,p:grade(8,8,[(4,1)]))
  self.assertTrue(n.planejar(None,(2.1,1.5),90,(3.5,1.5),'a',0)['w'])
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
