import unittest,sys,threading,copy
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.combate.recuperacao_alvo import RecuperacaoAlvo

class RecuperacaoTeste(unittest.TestCase):
 def test_id_sumido_nao_produz_tab_infinito(self):
  r=RecuperacaoAlvo();acoes=[r.decidir(i*.1) for i in range(150)]
  self.assertEqual(acoes.count('tab'),8)
  self.assertIn('indisponivel',acoes[:51])
  self.assertNotIn('tab',acoes[51:])
 def test_retorno_original_reinicia_tentativas(self):
  r=RecuperacaoAlvo();r.decidir(0);r.decidir(1);r.reiniciar()
  self.assertEqual(r.decidir(100),'tab');self.assertEqual(r.tentativas,1)
 def test_pausa_nao_consume_prazo(self):
  r=RecuperacaoAlvo();r.decidir(0);r.pausar(100)
  self.assertEqual(r.decidir(100.5),'tab')
  self.assertEqual(r.decidir(105),'indisponivel')
 def test_motor_abandona_id_irrecuperavel_e_ataca_selecionado(self):
  import huntingaitan.combate.hunt_native as h
  from huntingaitan.configuracao.perfil_hunt import DEFAULT
  p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''])
  for v in p['skills']:v['enabled']=False
  control=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
  relogio=[0.];eventos=[];teclas=[];adotado=[False]
  def entidade(id,hp):return dict(ref=id,id=id,name='Tet das Chamas',position=(0,1),height=0,hp=hp,hp_max=200,mp=0,mp_max=0,hostile=True)
  class Dados:
   hwnd=1
   def snapshot(self):
    alvo=entidade(8062,150 if relogio[0]>.3 else 200) if relogio[0]<1 else entidade(7683,200)
    return dict(player=dict(position=(0,0),height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo)
   def entidade(self,ref):raise RuntimeError('Entidade removida')
   def close(self):pass
  def evento(e):
   eventos.append(e)
   if e.get('message')=='Atacando o alvo proximo ja selecionado.':adotado[0]=True
  def down(k):
   teclas.append((relogio[0],k))
   if adotado[0] and k=='1':control.stop.set()
  def dormir(t):
   relogio[0]+=max(.001,t)
   if relogio[0]>12:control.stop.set()
  u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
  entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
  with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:relogio[0]),patch.object(h.time,'sleep',dormir):
   h.main(p,evento,control)
  recuperacoes=[e for e in eventos if e.get('message')=='Recuperando somente o alvo travado.']
  self.assertEqual(len(recuperacoes),8)
  self.assertTrue(adotado[0]);self.assertLess(relogio[0],8)
  self.assertFalse(any(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos))
  self.assertTrue(any(k=='1' and t>4 for t,k in teclas))

if __name__=='__main__':unittest.main()
