import unittest
from huntingaitan.rotas.renovacao_giovanni import CompraGiovanni,pode_usar_cidade,opcao_favor,opcao_gratuita

class RenovacaoTeste(unittest.TestCase):
    def test_gratuita_nao_confunde_com_favor_pago_e_exige_saldo_preservado(self):
        self.assertTrue(opcao_gratuita('Bendición de Giovanni'))
        self.assertFalse(opcao_gratuita('Favor de Giovanni [50000 Oro]'))
        self.assertFalse(opcao_gratuita('Bendicion de Giovanni [50000 Oro]'))
        c=CompraGiovanni(100000,[],custo=0)
        self.assertEqual(c.conferir(100000,[8500]),8500)
        self.assertIsNone(c.conferir(50000,[8500]))
    def test_nome_e_preco_aceitam_so_confusao_ocr_entre_zero_e_o(self):
        for texto in ('Favor de Giovanni [50000 Oro]','Favor de Giovanni [500o0 Oro]'):
            self.assertTrue(opcao_favor(texto))
        for texto in ('Favor de Giovanni [50050 Oro]','Favor de Giovanni [5000 Oro]',
                      'Favor de Giovanni [500000 Oro]','Bendicion de Giovanni [50000 Oro]'):
            self.assertFalse(opcao_favor(texto))
    def test_compra_exige_saldo_e_efeito_novo(self):
        c=CompraGiovanni(100000,[9001])
        self.assertIsNone(c.conferir(100000,[9001,8500]))
        self.assertIsNone(c.conferir(50000,[9001]))
        self.assertIsNone(c.conferir(50000,[8500,8501]))
        self.assertEqual(c.conferir(50000,[9001,9607]),9607)

    def test_nao_compra_de_novo_ou_sem_saldo(self):
        for ouro,efeitos in ((49999,[]),(100000,[8500])):
            with self.assertRaises(ValueError):CompraGiovanni(ouro,efeitos)

    def test_pergaminho_exige_leitura_sem_mobs_e_controle_livre(self):
        p=dict(position=(100,100),hp=100,hp_max=100)
        self.assertTrue(pode_usar_cidade(p,[],{}))
        self.assertFalse(pode_usar_cidade(p,None,{}))
        self.assertFalse(pode_usar_cidade(p,[dict(position=(110,100),hp=1)],{}))
        for k in ('casting','stunned','paralyzed','frozen'):
            self.assertFalse(pode_usar_cidade(p,[],{k:True}))
