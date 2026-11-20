import unittest
from unittest.mock import patch
import numpy as np
from interface_mina import VerificadorElite
from perfil_hunt import validar


class EscalaTeste(unittest.TestCase):
    def test_hard_em_ingles_equivale_a_dificil_sem_aceitar_normal_ou_elite(self):
        for texto,esperado in [('Hard',True),('HARD',True),('Difícil',True),('Normal',False),('Elite',False),('Easy',False),('Hard Mode',False)]:
            with self.subTest(texto=texto):
                v=VerificadorElite(self.ocr(texto),dificuldade='dificil')
                self.assertEqual(v.confirmar(self.tela()),esperado)
                if esperado:
                    self.assertEqual(v.diagnostico['indicador'],'dificil')
                    self.assertEqual(v.diagnostico['texto_indicador'],[texto])

    def test_ocr_do_hud_nao_gira_texto_em_180_graus(self):
        with patch('rapidocr_onnxruntime.RapidOCR',return_value=self.ocr('Hard')) as criar:
            self.assertTrue(VerificadorElite(dificuldade='dificil').confirmar(self.tela()))
            self.assertIs(criar.call_args.kwargs['use_cls'],False)

    def tela(self,w=3840,h=2160,y=620,altura=24):
        im=np.zeros((h,w,3),np.uint8);im[y:y+altura,w-240:w-140,1]=255
        return im

    def ocr(self,texto='Difícil',score=.98):
        def ler(im):
            y,x=np.where(im[:,:,1]>240)
            if not len(x):return [],None
            caixa=[[int(x.min()),int(y.min())],[int(x.max()),int(y.min())],
                   [int(x.max()),int(y.max())],[int(x.min()),int(y.max())]]
            return [[caixa,texto,score]],None
        return ler

    def test_hud_ampliado_4k_encontra_indicador_fora_do_recorte_antigo(self):
        v=VerificadorElite(self.ocr(),dificuldade='dificil')
        self.assertTrue(v.confirmar(self.tela()))
        self.assertEqual(v.diagnostico['tentativas'],2)
        self.assertAlmostEqual(v.diagnostico['escala_texto'],2,delta=.25)

    def test_opcao_desativada_preserva_leitura_fixa(self):
        v=VerificadorElite(self.ocr(),dificuldade='dificil',auto_escala=False)
        self.assertFalse(v.confirmar(self.tela()))
        self.assertEqual(v.diagnostico['tentativas'],1)

    def test_hud_pequeno_funciona_em_resolucao_alta_sem_ampliar_busca(self):
        v=VerificadorElite(self.ocr(),dificuldade='dificil')
        self.assertTrue(v.confirmar(self.tela(y=300,altura=12)))
        self.assertEqual(v.diagnostico['tentativas'],1)

    def test_indicador_deslocado_usa_busca_mais_ampla(self):
        im=self.tela(1920,1080,y=650,altura=18)
        v=VerificadorElite(self.ocr(),dificuldade='dificil')
        self.assertTrue(v.confirmar(im))
        self.assertGreater(v.diagnostico['recorte'][3],650)

    def test_ampliar_recorte_nao_aceita_dificuldade_errada_ou_baixa_confianca(self):
        for texto,score in [('Normal',.99),('Elite',.99),('Difícil',.5),('Entrar Difícil',.99)]:
            with self.subTest(texto=texto,score=score):
                v=VerificadorElite(self.ocr(texto,score),dificuldade='dificil')
                self.assertFalse(v.confirmar(self.tela()))

    def test_opcao_migra_ativa_e_preserva_desativacao(self):
        self.assertTrue(validar({})['auto_ui_scale'])
        self.assertFalse(validar(dict(auto_ui_scale=False))['auto_ui_scale'])
        with self.assertRaisesRegex(ValueError,'auto_ui_scale'):validar(dict(auto_ui_scale='false'))


if __name__=='__main__':unittest.main()
