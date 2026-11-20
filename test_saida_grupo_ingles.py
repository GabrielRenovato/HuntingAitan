import unittest
import numpy as np
from interface_mina import InterfaceMina


class SaidaInglesTeste(unittest.TestCase):
    def saida(self,textos):
        def ocr(im):
            linhas=[]
            for texto,x,y,w,h,score in textos:
                caixa=np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h]],float)*1.25
                linhas.append([caixa,texto,score])
            return linhas,None
        return InterfaceMina(ocr=ocr).saida_texto(np.zeros((720,1280,3),np.uint8))

    def test_menu_leave_party(self):
        a=self.saida([('Leave Party',65,550,110,14,.99)])
        self.assertEqual(a['acao'],'sair_grupo')

    def test_confirmar_exige_pergunta_da_mesma_janela(self):
        a=self.saida([('Leave the party?',550,300,200,15,.99),('Confirm',540,350,80,15,.99),('Cancel',660,350,80,15,.99)])
        self.assertEqual(a['acao'],'confirmar_saida')
        self.assertLess(a['ponto'][0],660)
        self.assertEqual(self.saida([('Confirm',540,350,80,15,.99)])['acao'],'aguardar_saida')

    def test_texto_ambigio_ou_baixa_confianca_nao_e_clicado(self):
        for texto,score in [('Leave Party',.5),('Delete Party',.99),('Party Invite',.99)]:
            self.assertEqual(self.saida([(texto,65,550,110,14,score)])['acao'],'aguardar_saida')

    def test_abre_menu_com_direito_no_quadro_de_grupo(self):
        a=self.saida([('Party Information Active',0,500,130,14,.99)])
        self.assertEqual(a['acao'],'abrir_menu_grupo');self.assertEqual(a['botao'],'right')
        self.assertGreater(a['ponto'][1],514)


if __name__=='__main__':unittest.main()
