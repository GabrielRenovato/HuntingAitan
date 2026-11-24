import unittest
from huntingaitan.rotas.navegador_local import NavegadorLocal
from tests.test_navegacao_grade import grade

class NavegadorTeste(unittest.TestCase):
 def test_bloqueio_quase_reto_exclui_aresta_real_em_vez_de_diagonal_inventada(self):
  n=NavegadorLocal(lambda d,p:grade(20,20))
  pos=(3.5,8.5);destino=(16.5,6.5)
  anterior=n.planejar(None,pos,90,destino,'croshu',0,controle_interno=True)
  bloqueio=n.planejar(None,pos,90,destino,'croshu',2.1,controle_interno=True)
  self.assertFalse(n.grade.linha_livre(n.grade.celula(pos),n.grade.celula(anterior['ponto'])))
  novo=n.replanejar_agora(None,pos,90,destino,'croshu',2.1,bloqueio,controle_interno=True)
  self.assertNotEqual(novo.get('ponto'),anterior['ponto'])
 def test_giros_sem_avanco_nao_reiniciam_prazo_indefinidamente(self):
  n=NavegadorLocal(lambda d,p:grade(14,14))
  for t,heading in [(0,41.2),(1,64.9),(2,41.2),(3,64.9)]:
   self.assertEqual(n.planejar(None,(1.5,1.5),heading,(10.5,1.5),'mob',t)['estado'],'andando')
  r=n.planejar(None,(1.5,1.5),41.2,(10.5,1.5),'mob',4.1)
  self.assertEqual(r['estado'],'bloqueado');self.assertEqual(r['motivo'],'alinhamento_sem_progresso')
 def test_alinhamento_que_melhora_e_pausa_por_stun_nao_disparam_bloqueio(self):
  n=NavegadorLocal(lambda d,p:grade(14,14))
  for t,heading in [(0,0),(2,15),(4,30),(6,45),(8,60)]:
   self.assertEqual(n.planejar(None,(1.5,1.5),heading,(10.5,1.5),'mob',t)['estado'],'andando')
  n.suspender((1.5,1.5),20)
  self.assertEqual(n.planejar(None,(1.5,1.5),60,(10.5,1.5),'mob',20.1)['estado'],'andando')
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
  n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0,controle_interno=True)
  for t in [2.1,4.2]:self.assertEqual(n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',t,controle_interno=True)['estado'],'replanejar')
  self.assertEqual(n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',6.3,controle_interno=True)['estado'],'bloqueado')

 def test_passagem_falha_e_excluida_do_desvio_e_expira(self):
  g=grade(12,12);n=NavegadorLocal(lambda d,p:g)
  n.planejar(None,(1.5,1.5),0,(9.5,1.5),'a',0,controle_interno=True)
  r=n.planejar(None,(1.5,1.5),0,(9.5,1.5),'a',2.1,controle_interno=True)
  a,b=r['passagem_bloqueada'];self.assertFalse(n.grade.passagem(a,b))
  n.planejar(None,(1.5,1.5),0,(9.5,1.5),'a',2.2,controle_interno=True)
  self.assertNotIn((n.grade.mundo(a),n.grade.mundo(b)),list(zip(n.rota,n.rota[1:])))
  n.suspender((2.5,2.5),24)
  n.planejar(None,(2.5,2.5),0,(9.5,1.5),'a',24.1,controle_interno=True)
  self.assertTrue(n.grade.passagem(a,b));self.assertFalse(g.arestas_bloqueadas)

 def test_motor_interno_nao_aguarda_giro_de_teclado_para_se_deslocar(self):
  n=NavegadorLocal(lambda d,p:grade(12,12))
  r=n.planejar(None,(1.5,1.5),0,(9.5,1.5),'a',0,controle_interno=True)
  self.assertTrue(r['w']);self.assertIsNone(r['giro'])
 def test_rota_nao_ultrapassa_area_configurada(self):
  n=NavegadorLocal(lambda d,p:grade(12,12));r=n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0,limite=((1.5,1.5),3))
  self.assertEqual(r['estado'],'sem_caminho')
 def test_pausa_por_stun_nao_conta_como_colisao(self):
  n=NavegadorLocal(lambda d,p:grade(12,12));n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',0)
  n.suspender((1.5,1.5),10)
  self.assertEqual(n.planejar(None,(1.5,1.5),90,(9.5,1.5),'a',10.1)['estado'],'andando')

if __name__=='__main__':unittest.main()
