import unittest,copy
from hunt_core import AgendaBuffs,executar_buff
from perfil_hunt import DEFAULT,validar
K=['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5']

class TesteRebuff(unittest.TestCase):
 def test_buffs_no_inicio_e_repeticao_em_nove_minutos(self):
  a=AgendaBuffs(0,K)
  for i,k in enumerate(K):
   t=i*2
   self.assertEqual(a.proximo(t,True),k)
   a.confirmar(t)
   if i<4:self.assertIsNone(a.proximo(t+.5,True))
  self.assertFalse(a.em_andamento)
  self.assertIsNone(a.proximo(539,True));self.assertEqual(a.proximo(540,True),'ctrl+1')
 def test_nao_inicia_antes_do_foco_e_nao_reinicia_sequencia(self):
  a=AgendaBuffs(10,K)
  self.assertIsNone(a.proximo(9,True))
  self.assertIsNone(a.proximo(10,False))
  self.assertEqual(a.proximo(11,True),'ctrl+1');a.confirmar(11)
  self.assertIsNone(a.proximo(12,True))
  self.assertEqual(a.proximo(13,True),'ctrl+2')
 def test_aguarda_fim_da_luta(self):
  a=AgendaBuffs(0,K)
  self.assertIsNone(a.proximo(600,False));self.assertEqual(a.proximo(610,True),'ctrl+1')
 def test_desativado_nao_envia(self):
  self.assertIsNone(AgendaBuffs(0,K,ativo=False).proximo(9999,True))
 def test_ctrl_segurado_so_durante_cada_atalho(self):
  e=[]
  self.assertTrue(executar_buff('ctrl+3',lambda k:e.append(('down',k)),lambda k:e.append(('up',k)),lambda s:None,lambda:True))
  self.assertEqual(e,[('down','ctrl'),('down','3'),('up','3'),('up','ctrl')])
 def test_perda_de_foco_libera_ctrl(self):
  e=[];n=[0]
  def permitido():n[0]+=1;return n[0]<2
  self.assertFalse(executar_buff('ctrl+1',lambda k:e.append(('down',k)),lambda k:e.append(('up',k)),lambda s:None,permitido))
  self.assertEqual(e,[('down','ctrl'),('up','ctrl')])
 def test_erro_libera_modificador(self):
  e=[]
  def esperar(s):raise RuntimeError('erro')
  with self.assertRaises(RuntimeError):executar_buff('ctrl+1',lambda k:e.append(('down',k)),lambda k:e.append(('up',k)),esperar,lambda:True)
  self.assertEqual(e[-1],('up','ctrl'))
 def test_perfil_persiste_cinco_atalhos(self):
  p=validar(DEFAULT);self.assertTrue(p['buffs_enabled']);self.assertEqual(p['buff_minutes'],9);self.assertEqual(p['buff_keys'],K)
  p['buff_keys']=['ctrl+1']*5
  with self.assertRaises(ValueError):validar(p)

if __name__=='__main__':unittest.main()
