import unittest
from types import SimpleNamespace
from huntingaitan.entrada.entrada_segura import liberar_tecla,liberar_mouse

class EntradaTeste(unittest.TestCase):
 def test_canto_bloqueia_novas_acoes_mas_permite_soltar(self):
  eventos=[]
  def keyup(k):raise RuntimeError('fail-safe do canto')
  keyup.__wrapped__=lambda k:eventos.append(('up',k))
  entrada=SimpleNamespace(keyUp=keyup)
  with self.assertRaises(RuntimeError):entrada.keyUp('w')
  liberar_tecla(entrada,'w');liberar_tecla(entrada,'ctrl')
  self.assertEqual(eventos,[('up','w'),('up','ctrl')])
 def test_mouse_tambem_e_liberado(self):
  eventos=[]
  def up():raise RuntimeError('fail-safe')
  up.__wrapped__=lambda:eventos.append('mouse-up')
  liberar_mouse(SimpleNamespace(mouseUp=up));self.assertEqual(eventos,['mouse-up'])
 def test_sem_wrapper_preserva_entrada(self):
  eventos=[];liberar_tecla(SimpleNamespace(keyUp=lambda k:eventos.append(k)),'a')
  self.assertEqual(eventos,['a'])

if __name__=='__main__':unittest.main()
