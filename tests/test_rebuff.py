import unittest,copy
from huntingaitan.combate.hunt_core import AgendaBuffs,executar_buff
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
K=['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5']

class TesteRebuff(unittest.TestCase):
 def test_slots_vazios_nao_suspendem_percurso_nem_enviam_buffs(self):
  a=AgendaBuffs(0,K)
  tipos={k:0 for k in K}
  for t in (0,30,60):
   self.assertIsNone(a.proximo(t,True,tipos))
   self.assertFalse(a.em_andamento)
  tipos['ctrl+3']=2
  self.assertEqual(a.proximo(61,True,tipos),'ctrl+3')
  a.confirmar(61)
  self.assertFalse(a.em_andamento)
 def test_filtro_de_slots_preserva_itens_e_leitura_desconhecida(self):
  a=AgendaBuffs(0,['f3','f7'])
  self.assertEqual(a.proximo(0,True,{'f3':6}),'f3');a.confirmar(0)
  self.assertEqual(a.proximo(2,True,{'f3':6}),'f7')
 def test_f3_trinta_minutos_e_sem_ctrl(self):
  a=AgendaBuffs(0,['f3'],periodos={'f3':1800})
  self.assertEqual(a.proximo(0,True),'f3');a.confirmar(0)
  self.assertIsNone(a.proximo(1799,True));self.assertEqual(a.proximo(1800,True),'f3')
  e=[]
  self.assertTrue(executar_buff('f3',lambda k:e.append(('down',k)),lambda k:e.append(('up',k)),lambda s:None,lambda:True))
  self.assertEqual(e,[('down','f3'),('up','f3')])
 def test_f3_libera_tecla_em_falha(self):
  e=[]
  def esperar(s):raise RuntimeError('erro')
  with self.assertRaises(RuntimeError):executar_buff('f3',lambda k:None,lambda k:e.append(k),esperar,lambda:True)
  self.assertEqual(e,['f3'])
 def test_buffs_adicionais_renovam_em_onze_minutos(self):
  teclas=K+['ctrl+6','ctrl+8']
  a=AgendaBuffs(0,teclas,periodos={'ctrl+6':660,'ctrl+8':660})
  for i,k in enumerate(teclas):
   self.assertEqual(a.proximo(i*2,True),k);a.confirmar(i*2)
  self.assertEqual(a.vencimentos['ctrl+1'],540)
  self.assertEqual(a.vencimentos['ctrl+6'],670)
  self.assertEqual(a.vencimentos['ctrl+8'],672)
  for i,k in enumerate(K):
   self.assertEqual(a.proximo(540+i*2,True),k);a.confirmar(540+i*2)
  self.assertIsNone(a.proximo(669,True))
  self.assertEqual(a.proximo(670,True),'ctrl+6');a.confirmar(670)
  self.assertTrue(a.em_andamento)
  self.assertIsNone(a.proximo(671,True))
  self.assertEqual(a.proximo(672,True),'ctrl+8');a.confirmar(672)
  self.assertFalse(a.em_andamento)
  self.assertEqual(a.vencimentos['ctrl+6'],1330)
  self.assertEqual(a.vencimentos['ctrl+8'],1332)
 def test_perfil_adicionais_evita_atalhos_duplicados(self):
  p=validar({});self.assertTrue(p['extra_buffs_enabled']);self.assertEqual(p['extra_buff_minutes'],11)
  p['buff_keys'][-1]='ctrl+6'
  with self.assertRaises(ValueError):validar(p)
  p['extra_buffs_enabled']=False;validar(p)
 def test_buffs_no_inicio_e_repeticao_em_nove_minutos(self):
  a=AgendaBuffs(0,K)
  for i,k in enumerate(K):
   t=i*2
   self.assertEqual(a.proximo(t,True),k)
   a.confirmar(t)
   if i<4:self.assertIsNone(a.proximo(t+.5,True))
  self.assertFalse(a.em_andamento)
  self.assertIsNone(a.proximo(539,True));self.assertEqual(a.proximo(540,True),'ctrl+1')
 def test_renovacao_mantem_ciclo_entre_vencimentos_individuais(self):
  a=AgendaBuffs(0,K,intervalo=3)
  for i,k in enumerate(K):
   self.assertEqual(a.proximo(i*3,True),k);a.confirmar(i*3)
  for i,k in enumerate(K):
   self.assertEqual(a.proximo(540+i*3,True),k);a.confirmar(540+i*3)
   if i<4:
    self.assertTrue(a.em_andamento)
    self.assertIsNone(a.proximo(541+i*3,True))
    self.assertTrue(a.em_andamento)
  self.assertFalse(a.em_andamento)
 def test_falha_nao_remove_buff_pendente(self):
  a=AgendaBuffs(0,K)
  self.assertEqual(a.proximo(0,True),'ctrl+1')
  self.assertIsNone(a.proximo(1,False))
  self.assertTrue(a.em_andamento)
  self.assertEqual(a.proximo(2,True),'ctrl+1')
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
