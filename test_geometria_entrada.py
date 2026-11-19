import base64,json,math,struct,unittest,zlib
from unittest.mock import patch
from pathlib import Path
from geometria_entrada import GeometriaEntrada,plano_geometria
from tools.validar_entrada_mina import ler_ms3,transformar,ocupa,recortar_y
from test_navegacao_grade import grade

class GeometriaTeste(unittest.TestCase):
    def geometria(self):
        with patch.object(GeometriaEntrada,'conferir'):return GeometriaEntrada(Path('cliente'))

    def test_ponto_real_das_pedras_ocupado_e_estrada_livre(self):
        g=self.geometria()
        self.assertFalse(g.livre((2683.2029,1714.4978)))
        self.assertTrue(g.livre((2696.5,1714.5)))
        self.assertTrue(g.livre((2698.5,1682.5)))
        self.assertTrue(g.livre((2628.4,1792.4)))
        self.assertTrue(g.livre((2716,1611)))
        self.assertFalse(g.livre((0,0)))

    def test_inventario_cobre_modelos_sem_formatos_ignorados(self):
        d=plano_geometria();self.assertFalse(d['ignorados']);self.assertGreater(len(d['objetos']),300)
        self.assertTrue(any(o['modelo'].endswith('nlafarm076.MS3') for o in d['objetos']))

    def test_mascara_completa_corrompida_nao_e_aceita(self):
        d=dict(plano_geometria(),mascara=base64.b64encode(zlib.compress(b'')).decode())
        with patch('geometria_entrada.plano_geometria',return_value=d):
            with self.assertRaisesRegex(RuntimeError,'invalida'):GeometriaEntrada('cliente')

    def test_extensao_da_grade_bloqueia_a_celula_das_pedras(self):
        g=grade(12,12);g.origem=(2678,1708)
        nova=self.geometria().aplicar(g)
        self.assertFalse(nova.livre(nova.celula((2683.2,1714.5))))
        self.assertEqual(nova.alturas,g.alturas)

    def test_rotacao_yaw_converte_plano_xz_para_mundo_xy(self):
        import numpy as np
        v=transformar(np.array([[1.,0.,0.]]),(10,20,3),(math.pi/2,0,0),2)
        self.assertAlmostEqual(v[0][0],10);self.assertAlmostEqual(v[0][1],3);self.assertAlmostEqual(v[0][2],18)

    def test_intersecao_considera_altura_do_personagem(self):
        p=[(0.,0.,0.),(0.,2.,0.),(0.,0.,3.)]
        cortado=recortar_y(recortar_y(p,.35,True),1.8,False)
        self.assertTrue(ocupa(cortado,(.3,1.)))
        self.assertFalse(ocupa(cortado,(2.,1.)))

    def test_parser_ms3_rejeita_tamanho_e_indices_invalidos(self):
        with self.assertRaises(ValueError):ler_ms3(b'errado')
        raw=bytearray(116+3*32+6+40+2);struct.pack_into('<I',raw,0,2222);struct.pack_into('<I',raw,28,1);struct.pack_into('<3I',raw,84,3,3,1)
        struct.pack_into('<3H',raw,116+3*32,0,1,9)
        with self.assertRaisesRegex(ValueError,'invalida'):ler_ms3(raw)

if __name__=='__main__':unittest.main()
