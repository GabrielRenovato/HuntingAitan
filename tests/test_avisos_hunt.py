import unittest
from pathlib import Path
import cv2,numpy as np
from huntingaitan.visao.avisos_hunt import DetectorAvisos
P=Path(__file__).parent

class AvisosTeste(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=DetectorAvisos();cls.chat=cv2.imread(str(P/'fixtures'/'fixture_conversa_social.png'))
  cls.elter=cv2.imread(str(Path(__file__).parent/'fixtures'/'fixture_elter.png'))
 def test_conversa_fecha_x_externo(self):
  a=self.d.localizar(self.chat)
  self.assertEqual(a['tipo'],'conversa_amigo')
  self.assertLess(abs(a['ponto'][0]-343),3);self.assertLess(abs(a['ponto'][1]-15),3)
 def test_conversa_em_outra_posicao_e_escala(self):
  for escala in [1.,.8,1.25]:
   im=cv2.resize(self.chat,None,fx=escala,fy=escala)
   tela=np.zeros((1080,1920,3),np.uint8);h,w=im.shape[:2];tela[210:210+h,330:330+w]=im
   a=self.d.localizar(tela)
   self.assertIsNotNone(a,escala);self.assertEqual(a['tipo'],'conversa_amigo')
   self.assertLess(abs(a['ponto'][0]-(330+343*escala)),4)
 def test_social_sem_conversa_nao_fecha(self):
  im=self.chat.copy();im[40:62,60:170]=0
  self.assertIsNone(self.d.localizar(im))
 def test_sem_x_confirmado_nao_clica(self):
  im=self.chat.copy();im[2:27,330:360]=0
  self.assertIsNone(self.d.localizar(im))
 def test_cte_elter_cancelar(self):
  a=self.d.localizar(self.elter)
  self.assertEqual(a['tipo'],'cte_elter')
  self.assertTrue(245<a['ponto'][0]<331 and 241<a['ponto'][1]<267)
 def test_sem_dialogos_nao_clica(self):
  self.assertIsNone(self.d.localizar(np.zeros((1080,1920,3),np.uint8)))

if __name__=='__main__':unittest.main()
