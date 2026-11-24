import unittest,threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from huntingaitan.rotas.servico_npc import TransacaoNPC,avaliar_equipamento,inteiro_moeda,RotaLuis,durabilidade,nome_corresponde,normalizar
from huntingaitan.rotas.ciclo_jardim import CicloJardim
from huntingaitan.configuracao.perfil_hunt import DEFAULT

DESC=['Espada de Termes','Classe: Guerreiro','Durabilidade: 8/151']

class TransacaoTeste(unittest.TestCase):
    def test_nome_com_uma_letra_perdida_exige_destino_sem_ambiguidade(self):
        alvo='Globo terraqueo Tijia'
        self.assertTrue(nome_corresponde('Globo terraqueo Tiia',alvo,[alvo,'Espada de Termes']))
        self.assertFalse(nome_corresponde('Globo terraqueo Tiia',alvo,[alvo,'Globo terraqueo Tiia']))
        self.assertFalse(nome_corresponde('Globo terraqueo Xixa',alvo,[alvo]))
        self.assertFalse(nome_corresponde('Pocao','PocaoX'))

    def test_variacao_ocr_de_durabilidade_sem_aceitar_numeros_soltos(self):
        for texto in ('Durabilidade: 66/66','Durabiidade: 66/66','Durabilidad: 66/66'):
            self.assertEqual(durabilidade([texto]),(66,66))
        for texto in ('66/66','Durabilidade: 1000/1000','Durabilidade: 70/66'):
            self.assertIsNone(durabilidade([texto]))
    def test_venda_exige_reparo_e_confirmacao_por_saldo(self):
        t=TransacaoNPC();self.assertFalse(t.preparar_venda('Espada de Termes',59597,DESC,1000000)[0])
        self.assertTrue(t.preparar_reparo(1712564,102220))
        self.assertFalse(t.confirmar_reparo(1712564,True))
        self.assertTrue(t.confirmar_reparo(1610344,True))
        self.assertTrue(t.preparar_venda('Espada de Termes',59597,DESC,1610344)[0])
        self.assertFalse(t.mesma_venda('Pocao',59597));self.assertFalse(t.mesma_venda('Espada de Termes',1))
        self.assertFalse(t.confirmar_venda(1610344,True));self.assertFalse(t.confirmar_venda(1669941,False))
        self.assertTrue(t.confirmar_venda(1669941,True));self.assertEqual(t.vendidos,1)
        self.assertFalse(t.confirmar_venda(1669941,True))

    def test_reparo_sem_dinheiro_ou_com_erro_bloqueia_venda(self):
        t=TransacaoNPC();self.assertFalse(t.preparar_reparo(20,100));self.assertFalse(t.reparado)
        self.assertTrue(t.preparar_reparo(100,20));self.assertFalse(t.confirmar_reparo(80,True,erro=True))

    def test_protege_equipados_refinados_vinculados_e_itens_sem_tipo(self):
        self.assertTrue(avaliar_equipamento('Espada de Termes',DESC)[0])
        for linhas in [[],['Pocao'],['Espada de Termes +7']+DESC[1:],DESC+['Equiped Item'],DESC+['Item vinculado'],['Outra Espada']+DESC[1:]]:
            self.assertFalse(avaliar_equipamento('Espada de Termes',linhas)[0],linhas)
        self.assertEqual(inteiro_moeda('1,610,344'),1610344);self.assertIsNone(inteiro_moeda('46/60'))

    def test_ciclo_passa_no_npc_antes_de_voltar_ao_portal(self):
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        contexto=dict(position=(1892,1067),hp=1,pasta='jogo');servico=Mock(return_value=True)
        ciclo=CicloJardim(DEFAULT,c,lambda e:None,lambda:contexto,Mock(),Mock(),Mock(),servico=servico)
        ciclo.passo();self.assertEqual(ciclo.etapa,'jardim_npc_servico')
        ciclo.passo();servico.assert_called_once();self.assertEqual(ciclo.etapa,'jardim_retornar')
        self.assertFalse(c.stop.is_set())
        servico.return_value=False;ciclo.etapa='jardim_npc_servico';ciclo.passo()
        self.assertTrue(c.stop.is_set());self.assertEqual(c.reason,'servico_npc_nao_confirmado')

    def test_caminho_real_ate_luis_mandez(self):
        p=Path(r'C:\GoLevel\AikaOnline')
        if not p.exists():self.skipTest('Cliente local indisponivel')
        rota=RotaLuis(p,(1856.4,1082.4));self.assertEqual(rota.portal,(1892,1066))
        self.assertEqual(rota.destino(rota.rota[-1],0)['estado'],'concluido')
        self.assertTrue(all(rota.grade.passagem(rota.grade.celula(a),rota.grade.celula(b)) for a,b in zip(rota.rota,rota.rota[1:])))

    def test_chegada_nao_insiste_nos_ultimos_centimetros_do_npc(self):
        rota=RotaLuis.__new__(RotaLuis);rota.portal=(1892,1066)
        self.assertEqual(rota.destino((1888.7706,1067.7712),0)['estado'],'concluido')
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        motor=Mock();contexto=dict(position=(1888.7706,1067.7712),hp=1,pasta='jogo')
        ciclo=CicloJardim(DEFAULT,c,lambda e:None,lambda:contexto,motor,Mock(),Mock(),servico=Mock(return_value=True))
        ciclo.passo();self.assertEqual(ciclo.etapa,'jardim_npc_servico');motor.assert_not_called()

class CapturasTeste(unittest.TestCase):
    def test_venda_rembrandt_com_zero_no_rotulo_do_preco(self):
        import numpy as np
        from huntingaitan.rotas.interface_npc import InterfaceNPC
        # Reproduz a saida do OCR sem distribuir a captura inteira com chat.
        ui=InterfaceNPC();im=np.zeros((400,600,3),np.uint8)
        ui.achar_npc=Mock(return_value=dict(ponto=(300,100),escala=1.))
        ui.achar=Mock(return_value=dict(ponto=(250,180)))
        ui.ler=Mock(return_value=[dict(texto='Botas Rembrandt',nome='botasrembrandt',ponto=(300,120)),
                                 dict(texto='Prec0: 15,846',nome='prec015846',ponto=(300,150)),
                                 dict(texto='Cancelar',nome='cancelar',ponto=(350,180))])
        venda=ui.dialogo(im,'venda')
        self.assertIsNotNone(venda)
        self.assertEqual(normalizar(venda['nome']),'botasrembrandt')
        self.assertEqual(venda['preco'],15846)

    def test_confirmacao_por_imagem_recusa_texto_alterado(self):
        import cv2
        from huntingaitan.rotas.interface_npc import InterfaceNPC
        ui=InterfaceNPC();im=cv2.imread(str(Path(__file__).parent/'fixtures/npc_venda.png'))
        venda=ui.dialogo(im,'venda');self.assertTrue(ui.confirmacao_estavel(im,venda))
        (x,y,_,_),_=venda['conferencia'];outra=im.copy()
        outra[y+2,x+2]=255 if im[y+2,x+2].mean()<100 else 0
        self.assertFalse(ui.confirmacao_estavel(outra,venda))

    def test_quantidade_35_ao_fundo_nao_vira_nome_da_bota(self):
        import cv2,numpy as np
        from huntingaitan.rotas.interface_npc import InterfaceNPC
        ui=InterfaceNPC();im=np.zeros((1080,1920,3),np.uint8)
        # Marca de Classe generica; os textos simulam o OCR da regressao real.
        tpl=ui.tpl['npc_classe'];h,w=tpl.shape
        im[530:530+h,1100:1100+w]=cv2.cvtColor(tpl,cv2.COLOR_GRAY2BGR)
        linhas=[('35',1100,450),('zapatos tijie',1100,480),('Classe: Santo',1100,530),
                ('Durabilidade: 66/66',1100,600)]
        ui.ler=Mock(return_value=[dict(texto=t,nome=normalizar(t),ponto=(x+30,y+7),caixa=(x,y,x+100,y+14)) for t,x,y in linhas])
        item=ui.equipamento_sob_cursor(im,(1045,549),1.,'zapatos tijie')
        self.assertIsNotNone(item);self.assertEqual(item[0],'zapatos tijie')
        self.assertEqual(durabilidade(item[1]),(66,66))
        self.assertNotIn('35',item[1])

    def test_menu_tienda_por_imagem_sem_ocr(self):
        import cv2,numpy as np
        from huntingaitan.rotas.interface_npc import InterfaceNPC
        ui=InterfaceNPC();tpl=ui.tpl['npc_tienda'];h,w=tpl.shape
        tela=np.zeros((400,600,3),np.uint8)
        tela[150:150+h,200:200+w]=cv2.cvtColor(tpl,cv2.COLOR_GRAY2BGR)
        ui.ler=Mock(side_effect=AssertionError('Menu conhecido nao deve chamar OCR'))
        self.assertEqual(ui.menu(tela,'loja',False),(200+w//2,150+h//2))

    def test_clique_no_corpo_do_npc_em_vez_do_nome_flutuante(self):
        import numpy as np
        from huntingaitan.rotas.interface_npc import InterfaceNPC
        ui=InterfaceNPC.__new__(InterfaceNPC)
        ui.ler=lambda *_: [dict(nome='luismandez',ponto=(500,100),caixa=(460,94,540,106))]
        self.assertEqual(ui.npc(np.zeros((500,800,3),np.uint8)),(500,142))
        ui.ler=lambda *_: [dict(nome='luismandez',ponto=(500,480),caixa=(460,474,540,486))]
        self.assertIsNone(ui.npc(np.zeros((500,800,3),np.uint8)))

    def test_interface_nas_capturas_do_usuario(self):
        import cv2
        from huntingaitan.rotas.interface_npc import InterfaceNPC
        ui=InterfaceNPC();p=Path(__file__).parent/'fixtures'
        reparo=ui.dialogo(cv2.imread(str(p/'npc_reparo.png')),'reparo')
        self.assertIsNotNone(reparo);self.assertEqual(reparo['custo'],102220)
        venda=ui.dialogo(cv2.imread(str(p/'npc_venda.png')),'venda')
        self.assertIsNotNone(venda);self.assertEqual((venda['nome'],venda['preco']),('Espada de Termes',59597))
        loja=ui.loja(cv2.imread(str(p/'npc_loja.png')))
        self.assertIsNotNone(loja);self.assertEqual(loja['ouro'],1610344);self.assertEqual(len(loja['paginas']),3)
        eq=ui.equipamento_sob_cursor(cv2.imread(str(p/'npc_tooltip.png')))
        self.assertIsNotNone(eq);self.assertEqual(eq[0],'Personal de Almagest')

if __name__=='__main__':unittest.main()
