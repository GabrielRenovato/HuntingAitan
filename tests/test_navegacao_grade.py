import unittest
from navegacao_grade import Grade

def grade(w,h,bloqueios=(),alturas=None):
 f=bytearray(w*h)
 for x,y in bloqueios:f[y*w+x]=1
 return Grade((0,0),(0,0),w,h,bytes(f),tuple(alturas or [0]*(w*h)),1)

class GradeTeste(unittest.TestCase):
 def test_desvia_de_arvore_em_vez_de_cruzar_bloqueio(self):
  g=grade(9,9,[(4,y) for y in range(7)])
  r=g.caminho((1.5,2.5),(7.5,2.5));self.assertIsNotNone(r)
  self.assertTrue(any(p[1]>7 for p in r));self.assertFalse(g.linha_livre((1,2),(7,2)))
  for a,b in zip(r,r[1:]):self.assertTrue(g.passagem(g.celula(a),g.celula(b)))
 def test_nao_corta_quinas(self):
  g=grade(3,3,[(1,0),(0,1)])
  self.assertFalse(g.passagem((0,0),(1,1)));self.assertIsNone(g.caminho((.5,.5),(2.5,2.5)))
 def test_alvo_em_celula_bloqueada_pode_ser_alcancado_ao_redor(self):
  g=grade(8,8,[(5,5)])
  self.assertIsNone(g.caminho((1.5,1.5),(5.5,5.5)))
  r=g.caminho((1.5,1.5),(5.5,5.5),alcance=2)
  self.assertIsNotNone(r);self.assertTrue(g.livre(g.celula(r[-1])))
 def test_respeita_desnivel_do_original(self):
  g=grade(3,1,alturas=[0,13,0]);self.assertFalse(g.passagem((0,0),(1,0)))
  g=grade(3,1,alturas=[0,12,0]);self.assertTrue(g.passagem((0,0),(1,0)))
 def test_lookahead_nao_atravessa_parede(self):
  g=grade(9,9,[(4,y) for y in range(7)]);r=g.caminho((1.5,2.5),(7.5,2.5))
  a=g.proximo((1.5,2.5),r,20)
  self.assertTrue(g.linha_livre((1,2),g.celula(a)))
 def test_destino_fora_da_grade_nao_inventa_rota(self):
  self.assertIsNone(grade(3,3).caminho((1.5,1.5),(20,20)))

if __name__=='__main__':unittest.main()
