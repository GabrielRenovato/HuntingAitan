import ctypes,unittest
from types import SimpleNamespace
import numpy as np
from huntingaitan.visao.captura_aika import CapturaAika


class DpiTeste(unittest.TestCase):
    def captura(self,falhar=False,rejeitar_v2=False):
        chamadas=[];contexto=[91]
        def ajustar(valor):
            v=valor.value if isinstance(valor,ctypes.c_void_p) else valor
            chamadas.append(v)
            if rejeitar_v2 and v==ctypes.c_void_p(-4).value:return None
            anterior=contexto[0];contexto[0]=v;return anterior
        cap=CapturaAika.__new__(CapturaAika);cap.u=SimpleNamespace(SetThreadDpiAwarenessContext=ajustar)
        area=dict(left=-1366,top=0,width=1366,height=768)
        def regiao():
            self.assertIn(contexto[0],[ctypes.c_void_p(-4).value,ctypes.c_void_p(-3).value]);return area
        def grab(recebida):
            self.assertEqual(recebida,area);regiao()
            if falhar:raise ValueError('falha de captura')
            return np.zeros((768,1366,4),np.uint8)
        cap._regiao=regiao;cap.sct=SimpleNamespace(grab=grab)
        return cap,chamadas,contexto

    def test_area_e_grab_usam_pixels_fisicos_e_restauram_contexto(self):
        cap,c,ctx=self.captura();im=cap.capturar()
        self.assertEqual(im.shape,(768,1366,3));self.assertEqual(ctx[0],91)
        self.assertEqual(c,[ctypes.c_void_p(-4).value,91])

    def test_restaura_contexto_mesmo_se_captura_falhar(self):
        cap,c,ctx=self.captura(falhar=True)
        with self.assertRaisesRegex(ValueError,'falha de captura'):cap.capturar()
        self.assertEqual(ctx[0],91)

    def test_windows_sem_v2_usa_contexto_por_monitor_anterior(self):
        cap,c,ctx=self.captura(rejeitar_v2=True);cap.capturar()
        self.assertEqual(c,[ctypes.c_void_p(-4).value,ctypes.c_void_p(-3).value,91])

    def test_api_ausente_preserva_captura_existente(self):
        cap=CapturaAika.__new__(CapturaAika);cap.u=SimpleNamespace()
        cap._regiao=lambda:dict(left=0,top=0,width=640,height=480)
        cap.sct=SimpleNamespace(grab=lambda area:np.zeros((480,640,4),np.uint8))
        self.assertEqual(cap.capturar().shape,(480,640,3))


if __name__=='__main__':unittest.main()
