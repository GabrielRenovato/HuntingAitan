import unittest,subprocess,sys,json
from pathlib import Path

class TesteInicializacao(unittest.TestCase):
 def test_importacao_nativa_nao_carrega_stack_visual(self):
  r=subprocess.run([sys.executable,'-c',"import sys,json; import hunt_native; print(json.dumps({n:n in sys.modules for n in ['cv2','numpy','rapidocr_onnxruntime']}))"],cwd=Path(__file__).parent,capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(r.stdout),{'cv2':False,'numpy':False,'rapidocr_onnxruntime':False})
 def test_nucleo_mantem_recargas_e_travamento(self):
  from hunt_core import CadenciaCombate,VerificadorMovimento
  c=CadenciaCombate({});c.registrar('2',0);self.assertIsNone(c.escolher(.5,True,True,1))
  v=VerificadorMovimento(3);self.assertFalse(v.observar((0,0),0,True));self.assertTrue(v.observar((0,0),3,True))

if __name__=='__main__':unittest.main()
