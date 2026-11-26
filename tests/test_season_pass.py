import unittest
from pathlib import Path
from unittest.mock import Mock
import cv2
import numpy as np
from huntingaitan.visao.season_pass import DetectorSeasonPass, fechar_com_escape
from huntingaitan.visao.avisos_hunt import DetectorAvisos, reconfirmar_imagem
from huntingaitan.entrada.entrada_janela import codigo_tecla


class TesteSeasonPass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.im = cv2.imread(str(Path(__file__).parent/'fixtures/fixture_season_pass.png'))
        cls.detector = DetectorSeasonPass()

    def test_reconhece_passe_movido_e_escalado(self):
        for escala in (1., .8, 1.25):
            with self.subTest(escala=escala):
                recorte = cv2.resize(self.im, None, fx=escala, fy=escala)
                tela = np.zeros((900, 1500, 3), np.uint8)
                h, w = recorte.shape[:2]
                tela[90:90+h, 160:160+w] = recorte
                aviso = DetectorAvisos().localizar(tela)
                self.assertEqual(aviso['tipo'], 'season_pass')
                self.assertIsNotNone(reconfirmar_imagem(aviso, tela, {'left': 0, 'top': 0}))

    def test_so_titulo_nao_autoriza_escape(self):
        im = self.im.copy()
        im[99:128, 145:335] = 0
        self.assertIsNone(self.detector.localizar(im))

    def test_nao_reconfirma_se_o_passe_ja_fechou(self):
        self.assertIsNone(reconfirmar_imagem({'tipo':'season_pass'}, np.zeros_like(self.im), {'left':0, 'top':0}))

    def test_envia_e_libera_escape_sem_clique(self):
        entrada = Mock()
        self.assertTrue(fechar_com_escape(entrada, lambda:True, lambda _:None))
        entrada.keyDown.assert_called_once_with('esc')
        entrada.keyUp.assert_called_once_with('esc')
        entrada.mouseDown.assert_not_called()
        self.assertEqual(codigo_tecla('esc'), 27)

    def test_nao_envia_se_cliente_perdeu_disponibilidade(self):
        entrada = Mock()
        self.assertFalse(fechar_com_escape(entrada, lambda:False, lambda _:None))
        entrada.keyDown.assert_not_called()

    def test_libera_escape_apos_falha(self):
        entrada = Mock(); entrada.keyDown.side_effect = RuntimeError('falha')
        with self.assertRaises(RuntimeError):
            fechar_com_escape(entrada, lambda:True, lambda _:None)
        entrada.keyUp.assert_called_once_with('esc')
