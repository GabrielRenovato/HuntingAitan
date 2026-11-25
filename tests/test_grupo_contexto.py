import unittest
import numpy as np
from huntingaitan.rotas.interface_mina import InterfaceMina

class GrupoContextoTeste(unittest.TestCase):
    def detectar(self,nome='Domination',barras=True,y=340):
        tela=np.zeros((600,800,3),np.uint8)
        if barras:
            tela[y+8:y+11,40:100]=(0,0,255)
            tela[y+15:y+18,40:100]=(255,0,0)
        caixa=[[80,(y-5)*2],[160,(y-5)*2],[160,(y+5)*2],[80,(y+5)*2]]
        d=InterfaceMina(ocr=lambda im:([[caixa,nome,.99]],None));d.nome_personagem='Domination'
        return d.saida_texto(tela)

    def test_nome_exato_e_barras_reconhecem_grupo_sem_cabecalho_legivel(self):
        r=self.detectar();self.assertEqual(r['acao'],'abrir_menu_grupo')
        self.assertEqual(r['ponto'],(60,340));self.assertEqual(r['botao'],'right')

    def test_outro_personagem_nao_e_usado_como_ancora(self):
        self.assertEqual(self.detectar(nome='Outro')['acao'],'aguardar_saida')

    def test_nome_sem_as_barras_nao_autoriza_clique(self):
        self.assertEqual(self.detectar(barras=False)['acao'],'aguardar_saida')

    def test_nome_no_chat_nao_autoriza_clique(self):
        self.assertEqual(self.detectar(y=550)['acao'],'aguardar_saida')
