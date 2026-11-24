import unittest
from huntingaitan.combate.destravar_colisao import DestravarColisao


class DestravarTeste(unittest.TestCase):
    def test_tecla_por_personagem_e_confirmacao_por_deslocamento(self):
        for tecla in ('4',"'"):
            d=DestravarColisao();envios=[]
            cc={'recargas_atalhos':{tecla:dict(skill=33,ready=True)}}
            r=d.tentar(0,(10,10),tecla,cc,lambda k:envios.append(k) or True)
            self.assertTrue(r['aceito']);self.assertEqual(envios,[tecla])
            self.assertFalse(d.observar((10.1,10)));self.assertTrue(d.observar((11,10)))
            self.assertFalse(d.observar((12,10)))

    def test_nao_disputa_stun_cast_recarga_ou_binding_ausente(self):
        for cc in ({},{'recargas_atalhos':{'4':dict(skill=1258,ready=False)}},
                   *[{'recargas_atalhos':{'4':dict(skill=1258,ready=True)},k:True}
                     for k in ('casting','stunned','paralyzed','frozen')]):
            d=DestravarColisao()
            self.assertIsNone(d.tentar(0,(0,0),'4',cc,lambda _:self.fail('Envio indevido')))

    def test_recusa_nao_confirma_e_tentativas_nao_sao_spam(self):
        d=DestravarColisao();cc={'recargas_atalhos':{"'":dict(skill=33,ready=True)}}
        self.assertFalse(d.tentar(0,(0,0),"'",cc,lambda _:False)['aceito'])
        self.assertFalse(d.observar((5,0)))
        self.assertIsNone(d.tentar(2,(0,0),"'",cc,lambda _:self.fail('Spam')))
