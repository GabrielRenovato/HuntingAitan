import unittest,copy,threading,sys
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.combate.hunt_native import ProgressoNativo

class ReaproximacaoTeste(unittest.TestCase):
 def test_reproduz_log_do_verit_ferido_a_3_22(self):
  alvo=dict(ref=1,id=7980,name='Verit Mutante',hp=121527)
  p=ProgressoNativo(alvo,0);p.observar(dict(alvo,hp=22726),10)
  self.assertTrue(p.precisa_aproximar(21.5,3.22))
  self.assertFalse(p.precisa_aproximar(21.5,2.0))
  self.assertFalse(p.aproximacao_falhou(21.5,17,dict(no_damage_seconds=5,radius=30)))
 def test_histerese_nao_movimenta_ao_receber_dano_recente(self):
  a=dict(ref=1,id=7980,name='Verit Mutante',hp=100);p=ProgressoNativo(a,0);p.observar(dict(a,hp=50),1)
  self.assertFalse(p.precisa_aproximar(1.3,2.6));self.assertTrue(p.precisa_aproximar(3,2.6))
 def test_motor_reaproxima_e_mata_o_mesmo_alvo_sem_tab(self):
  import huntingaitan.combate.hunt_native as h
  from huntingaitan.configuracao.perfil_hunt import DEFAULT
  perfil=copy.deepcopy(DEFAULT);perfil.update(buffs_enabled=False,minimize_on_start=False,cancel_normal=True,hp_keys=['','',''])
  for v in perfil['skills']:v['enabled']=False
  c=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
  t=[0.];hp=[100];pos=[(0,0)];mobpos=[(2,0)];teclas=[];eventos=[];navegacoes=[]
  def alvo():return dict(ref=1,id=7980,name='Verit Mutante',hp=hp[0],hp_max=100,mp=0,mp_max=0,position=mobpos[0],height=0,hostile=True)
  class Dados:
   hwnd=1
   def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo())
   def entidade(self,r):return alvo()
   def cena_validada(self):return 1
   def close(self):pass
  class Navegador:
   def invalidar(self):pass
   def suspender(self,*a):pass
   def planejar(self,*a,**kw):
    navegacoes.append(a);return dict(estado='andando',w=True,giro=None,pontos=2,erro=0)
  def down(k):
   teclas.append(k)
   if k=='1':
    hp[0]-=50
    if hp[0]==50:mobpos[0]=(3.22,0)
   if k=='w':pos[0]=(1.22,0)
  def dormir(v):
   t[0]+=max(.001,v)
   if t[0]>10:c.stop.set()
  def emitir(e):
   eventos.append(e)
   if e.get('message')=='Mob abatido; procurando o proximo.':c.stop.set()
  u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
  entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
  with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Navegador),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(perfil,emitir,c)
  self.assertTrue(navegacoes);self.assertEqual(teclas.count('tab'),1);self.assertEqual(teclas.count('1'),2)
  self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),1)
  self.assertTrue(any(e.get('message','').startswith('Alvo saiu do alcance;') for e in eventos))
  self.assertFalse(any(e.get('message','').startswith('Cancelamento experimental apos dano:') for e in eventos))

if __name__=='__main__':unittest.main()
