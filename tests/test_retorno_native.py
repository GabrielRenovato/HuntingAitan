import unittest,copy,sys,threading
from unittest.mock import patch,MagicMock
from types import SimpleNamespace

class RetornoTeste(unittest.TestCase):
 def simular(self,afastado):
  import hunt_native as h
  from perfil_hunt import DEFAULT
  p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''])
  for v in p['skills']:v['enabled']=False
  controle=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
  t=[0.];teclas=[];eventos=[]
  class Dados:
   hwnd=1
   def snapshot(self):
    pos=(10,0) if afastado and t[0]>.1 else (0,0)
    return dict(player=dict(position=pos,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=None)
   def close(self):pass
  def dormir(s):
   t[0]+=max(.001,s)
   if t[0]>16:controle.stop.set()
  def down(k):
   teclas.append(k)
   if afastado and k in ['w','a','d']:controle.stop.set()
  u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
  entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
  with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):
   h.main(p,eventos.append,controle)
  return teclas,eventos
 def test_sem_mob_na_base_nao_recuar_nem_fingir_retorno(self):
  teclas,eventos=self.simular(False)
  self.assertTrue(teclas);self.assertEqual(set(teclas),{'tab'})
  msgs=[e.get('message') for e in eventos]
  self.assertEqual(msgs.count('Na base sem alvo valido; aguardando novos mobs.'),1)
  self.assertNotIn('Retornou a base.',msgs)
 def test_retorno_confere_direcao_com_movimento_atual(self):
  teclas,eventos=self.simular(True)
  navegacao=[k for k in teclas if k in ['w','a','d']]
  self.assertTrue(navegacao);self.assertEqual(navegacao[0],'w')

if __name__=='__main__':unittest.main()
