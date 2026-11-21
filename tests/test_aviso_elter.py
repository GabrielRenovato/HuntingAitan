from pathlib import Path
import unittest,time
import cv2,numpy as np
from huntingaitan.visao.aviso_elter import DetectorElter

class TesteElter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.im=cv2.imread(str(Path(__file__).parent/'fixtures'/'fixture_elter.png'))
        cls.d=DetectorElter()
    def test_anexo_clica_cancelar(self):
        x,y=self.d.localizar(self.im)
        self.assertTrue(245<x<331 and 241<y<267)
    def test_captura_atual_do_usuario(self):
        im=cv2.imread(str(Path(__file__).parent/'fixtures'/'fixture_elter.png'))
        x,y=self.d.localizar(im)
        self.assertTrue(259<x<346 and 229<y<256)
    def test_posicao_da_janela_pode_mudar(self):
        tela=np.zeros((1080,1920,3),np.uint8);tela[300:632,800:1252]=self.im
        x,y=self.d.localizar(tela)
        self.assertTrue(1045<x<1131 and 541<y<567)
    def test_titulo_sem_cancelar_nao_clica(self):
        im=self.im.copy();im[235:275,239:338]=0
        self.assertIsNone(self.d.localizar(im))
    def test_tela_sem_convite_nao_clica(self):
        self.assertIsNone(self.d.localizar(np.zeros((1080,1920,3),np.uint8)))

if __name__=='__main__':unittest.main()
