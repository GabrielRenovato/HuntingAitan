import copy,threading,unittest
from types import SimpleNamespace
from unittest.mock import Mock
import cv2,numpy as np
from ciclo_mina import CicloMina
from interface_mina import InterfaceMina,VerificadorElite
from perfil_hunt import DEFAULT,validar


class CicloTeste(unittest.TestCase):
    def setUp(self):
        self.p=copy.deepcopy(DEFAULT);self.p.update(patrol_mode='mina_lenfer',mina_repeat=True)
        self.ctrl=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        self.pos=[2850,3344];self.hp=1;self.eventos=[]
        self.ler=lambda:dict(position=self.pos,hp=self.hp,pasta='cliente')
        self.motor=Mock();self.sair=Mock(return_value=False);self.entrar=Mock(return_value=False);self.rota=Mock(return_value=object())
        self.c=CicloMina(self.p,self.ctrl,self.eventos.append,self.ler,self.motor,self.sair,self.entrar,self.rota)

    def test_ciclo_conta_somente_abate_confirmado_e_nao_finaliza_painel_por_etapa(self):
        def dg(p,emitir,control):
            emitir(dict(event='dungeon_complete'));emitir(dict(event='finished',reason='mina_finalizada'))
        self.motor.side_effect=dg;self.c.passo()
        self.assertEqual(self.c.concluidas,1);self.assertEqual(self.c.etapa,'sair')
        self.assertFalse(any(e['event']=='finished' for e in self.eventos))
        self.c.passo();self.c.passo() # falha de saida nao reinicia a DG
        self.assertEqual(self.motor.call_count,1);self.assertEqual(self.c.concluidas,1)
        self.pos=[2628,1792];self.c.passo();self.assertEqual(self.c.etapa,'retornar')

    def test_encerramento_sem_abate_nao_conta_dg(self):
        self.c.passo()
        self.assertEqual(self.c.concluidas,0);self.assertTrue(self.ctrl.stop.is_set())

    def test_depois_de_chegar_ao_portal_entra_no_elite_antes_de_nova_dg(self):
        self.pos=[2716,1611];self.c.passo();self.assertEqual(self.c.etapa,'entrar')
        self.c.passo();self.assertEqual(self.c.etapa,'retornar');self.assertEqual(self.motor.call_count,0)
        self.c.passo();self.entrar.return_value=True;self.pos=[2716,1611];self.c.passo()
        self.assertEqual(self.c.etapa,'dg');self.assertEqual(self.c.concluidas,0)

    def test_dificuldade_nao_confirmada_sai_sem_contar_abate(self):
        self.c.etapa='entrar';self.c.passo()
        self.assertEqual(self.c.etapa,'corrigir_entrada');self.assertEqual(self.c.concluidas,0)
        self.c.passo();self.assertEqual(self.motor.call_count,0)

    def test_entrada_bloqueada_so_autoriza_ids_reportados_pela_interacao(self):
        self.pos=[2716,1611];self.c.etapa='entrar';self.ctrl.bloqueadores_portal={17}
        self.c.passo();self.assertEqual(self.c.etapa,'liberar_entrada')
        def liberar(p,emitir,control,percurso):control.reason='entrada_alcancada'
        self.motor.side_effect=liberar;self.c.passo()
        self.rota.assert_called_once_with('cliente',self.pos,bloqueadores={17})
        self.assertEqual(self.c.etapa,'entrar');self.assertEqual(self.c.concluidas,0)

    def test_limite_de_voltas_termina_apos_sair(self):
        self.c.perfil['mina_cycles']=1;self.c.concluidas=1;self.c.etapa='sair'
        self.sair.return_value=True;self.c.passo()
        self.assertTrue(self.ctrl.stop.is_set());self.assertEqual(self.ctrl.reason,'ciclos_concluidos')

    def test_retorno_usa_posicao_do_save_e_rota_externa(self):
        self.pos=[2628,1792]
        def ir(p,emitir,control,percurso):control.reason='entrada_alcancada'
        self.motor.side_effect=ir;self.c.passo()
        self.rota.assert_called_once_with('cliente',self.pos)
        self.assertEqual(self.c.etapa,'entrar');self.assertEqual(self.c.concluidas,0)

    def test_morte_nao_envia_cliques_de_saida_ou_entrada(self):
        self.hp=0;self.c.passo()
        self.assertTrue(self.ctrl.stop.is_set());self.sair.assert_not_called();self.entrar.assert_not_called();self.motor.assert_not_called()

    def test_perfil_rejeita_ciclos_fracionarios_e_repeat_invalido(self):
        for n in [-1,1.5,True,'2']:
            with self.assertRaises(ValueError):validar(dict(mina_cycles=n))
        with self.assertRaises(ValueError):validar(dict(mina_repeat='sim'))
        self.assertEqual(validar(dict(mina_cycles=2))['mina_cycles'],2)


class InterfaceTeste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ui=InterfaceMina()
    def tela(self):return np.zeros((700,900,3),np.uint8)
    def colar(self,tela,nome,x,y):
        t=self.ui.tpl[nome];h,w=t.shape;tela[y:y+h,x:x+w]=cv2.cvtColor(t,cv2.COLOR_GRAY2BGR)

    def test_desconhecido_nao_gera_clique(self):
        self.assertNotIn('ponto',self.ui.saida(self.tela()))
        self.assertNotIn('ponto',self.ui.entrada(self.tela()))

    def test_confirmar_solitario_nao_autoriza_saida(self):
        tela=self.tela();self.colar(tela,'confirmar',200,200)
        self.assertNotIn('ponto',self.ui.saida(tela))

    def test_pergunta_precisa_do_botao_confirmar_da_mesma_janela(self):
        tela=self.tela();self.colar(tela,'pergunta',300,200);self.colar(tela,'confirmar',40,500)
        self.assertEqual(self.ui.saida(tela)['acao'],'aguardar_confirmacao')
        self.colar(tela,'confirmar',275,250)
        self.assertEqual(self.ui.saida(tela)['acao'],'confirmar_saida')

    def test_elite_so_e_confirmado_por_texto_exato_e_confiavel(self):
        tela=self.tela()
        for texto,score,ok in [('Elite',.95,True),('Normal',.99,False),('Elite',.5,False),('Entrar Elite',.99,False)]:
            ocr=lambda im:([[None,texto,score]],None)
            self.assertEqual(VerificadorElite(ocr).confirmar(tela),ok)


if __name__=='__main__':unittest.main()
