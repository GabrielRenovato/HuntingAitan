import sys,threading,unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock,Mock,patch
from huntingaitan.rotas.operacoes_mina import sair_grupo,entrar_jardim
from huntingaitan.rotas.jardim_aereo import dentro_jardim
from huntingaitan.rotas.entrada_jardim import PORTAL

class JardimSegundoPlanoTeste(unittest.TestCase):
    def test_carregamento_exige_thread_responsiva_e_mapa_estavel(self):
        from huntingaitan.rotas.ciclo_jardim import aguardar_cliente_jardim
        tempo=[0.];c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),background_keys=True)
        d=SimpleNamespace(hwnd=10,u=MagicMock(),snapshot=lambda:dict(player=dict(hp=100)),cena_validada=lambda:100)
        d.u32=Mock(side_effect=[1,1,2,2]);d.u.SendMessageTimeoutW.side_effect=[0,1,1,1]
        self.assertTrue(aguardar_cliente_jardim(d,c,lambda e:None,relogio=lambda:tempo[0],dormir=lambda v:tempo.__setitem__(0,tempo[0]+v)))
        self.assertEqual(d.u.SendMessageTimeoutW.call_count,4)
        self.assertFalse(c.stop.is_set())

    def test_cliente_que_nao_responde_nao_libera_a_instalacao_do_motor(self):
        from huntingaitan.rotas.ciclo_jardim import aguardar_cliente_jardim
        tempo=[0.];c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),background_keys=True)
        d=SimpleNamespace(hwnd=10,u=MagicMock(),snapshot=lambda:dict(player=dict(hp=100)),cena_validada=lambda:100,u32=lambda p:1)
        d.u.SendMessageTimeoutW.return_value=0
        self.assertFalse(aguardar_cliente_jardim(d,c,lambda e:None,limite=.5,relogio=lambda:tempo[0],dormir=lambda v:tempo.__setitem__(0,tempo[0]+v)))
        self.assertTrue(c.stop.is_set())
    def preparar(self,pilha,posicoes):
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),background_keys=True)
        dados=SimpleNamespace(hwnd=10,pid=20,u=MagicMock())
        dados.u.GetForegroundWindow.return_value=999
        dados.snapshot=Mock(side_effect=[dict(player=dict(position=p,hp=100,hp_max=100)) for p in posicoes])
        dados.listar_mobs=Mock(return_value=[])
        cap=SimpleNamespace(area=dict(left=100,top=200),capturar=Mock(return_value=object()))
        wgc=pilha.enter_context(patch('huntingaitan.visao.captura_janela.CapturaJanela'))
        wgc.return_value.__enter__.return_value=cap
        entrada=pilha.enter_context(patch('huntingaitan.entrada.entrada_janela.EntradaJanela')).return_value
        entrada.disponivel.return_value=True;entrada.mover_sem_cursor.return_value=True
        global_=MagicMock();global_.mouseDown.side_effect=AssertionError('Mouse global usado')
        mss=MagicMock();mss.MSS.side_effect=AssertionError('Captura global usada')
        pilha.enter_context(patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=global_,mss=mss))
        pilha.enter_context(patch('huntingaitan.rotas.operacoes_mina.mover_cursor_fisico',side_effect=AssertionError('Cursor global usado')))
        pilha.enter_context(patch('huntingaitan.rotas.operacoes_mina.time.sleep'))
        avisos=pilha.enter_context(patch('huntingaitan.visao.avisos_hunt.DetectorAvisos')).return_value
        avisos.localizar.return_value=None
        return control,dados,entrada,wgc

    def test_sai_do_grupo_com_clique_na_janela_sem_foco(self):
        with ExitStack() as pilha:
            c,d,e,wgc=self.preparar(pilha,[(3351,3295)]+[(1800,1100)]*3)
            ui=pilha.enter_context(patch('huntingaitan.rotas.operacoes_mina.InterfaceMina')).return_value
            ui.saida.return_value=dict(acao='abrir_grupo',ponto=(30,40),botao='right')
            self.assertTrue(sair_grupo(d,c,lambda e:None,dentro=dentro_jardim,nome='Jardim'))
            wgc.assert_called_once_with(10,20)
            e.mover_sem_cursor.assert_called_once_with(130,240)
            e.mouseDown.assert_called_once_with(button='right')
            d.u.GetForegroundWindow.assert_not_called()

    def test_entra_e_confirma_dificil_por_captura_da_janela(self):
        with ExitStack() as pilha:
            c,d,e,wgc=self.preparar(pilha,[PORTAL,(3351,3295),(3351,3295)])
            ui=pilha.enter_context(patch('huntingaitan.rotas.interface_jardim.InterfaceJardim')).return_value
            ui.entrada.return_value=ui.reconfirmar.return_value=dict(acao='abrir_portal',ponto=(30,40),duplo=True)
            v=pilha.enter_context(patch('huntingaitan.rotas.interface_mina.VerificadorElite')).return_value
            v.confirmar.return_value=True;v.diagnostico={}
            pilha.enter_context(patch('huntingaitan.rotas.interacao_altar.localizar_altar_clicavel',return_value=dict(ponto=(130,240),altar=dict(ref=123))))
            pilha.enter_context(patch('huntingaitan.rotas.interacao_altar.altar_sob_cursor',return_value=dict(ref=123,id=2258)))
            self.assertTrue(entrar_jardim(d,c,lambda e:None))
            e.mover_sem_cursor.assert_called_once_with(130,240)
            self.assertEqual(e.mouseDown.call_count,2)
            e.mouseDown.assert_any_call(duplo=True)
            self.assertEqual(v.confirmar.call_count,2)
            d.u.GetForegroundWindow.assert_not_called()

    def test_dificuldade_inicial_nao_captura_desktop_quando_ao_fundo(self):
        from huntingaitan.rotas.jardim_aereo import conferir_dificil
        with ExitStack() as pilha:
            _,_,_,wgc=self.preparar(pilha,[])
            v=pilha.enter_context(patch('huntingaitan.rotas.interface_mina.VerificadorElite')).return_value
            v.confirmar.return_value=True;v.diagnostico={}
            pilha.enter_context(patch('huntingaitan.rotas.jardim_aereo.salvar_diagnostico_dificuldade',return_value='recorte.png'))
            self.assertTrue(conferir_dificil(janela=(10,20),ativo=lambda:True,parar=lambda:False))
            wgc.assert_called_once_with(10,20)

    def test_altar_nao_confirmado_nao_recebe_clique(self):
        with ExitStack() as pilha:
            c,d,e,wgc=self.preparar(pilha,[PORTAL,(3351,3295),(3351,3295)])
            ui=pilha.enter_context(patch('huntingaitan.rotas.interface_jardim.InterfaceJardim')).return_value
            ui.entrada.return_value=ui.reconfirmar.return_value=dict(acao='abrir_portal',ponto=(30,40),duplo=True)
            v=pilha.enter_context(patch('huntingaitan.rotas.interface_mina.VerificadorElite')).return_value
            v.confirmar.return_value=True;v.diagnostico={}
            pilha.enter_context(patch('huntingaitan.rotas.interacao_altar.localizar_altar_clicavel',return_value=None))
            self.assertTrue(entrar_jardim(d,c,lambda e:None))
            e.mouseDown.assert_not_called()

    def test_objeto_que_mudou_antes_do_down_nao_recebe_clique(self):
        with ExitStack() as pilha:
            c,d,e,wgc=self.preparar(pilha,[PORTAL,(3351,3295),(3351,3295)])
            ui=pilha.enter_context(patch('huntingaitan.rotas.interface_jardim.InterfaceJardim')).return_value
            ui.entrada.return_value=ui.reconfirmar.return_value=dict(acao='abrir_portal',ponto=(30,40),duplo=True)
            v=pilha.enter_context(patch('huntingaitan.rotas.interface_mina.VerificadorElite')).return_value
            v.confirmar.return_value=True;v.diagnostico={}
            pilha.enter_context(patch('huntingaitan.rotas.interacao_altar.localizar_altar_clicavel',return_value=dict(ponto=(130,240),altar=dict(ref=123))))
            pilha.enter_context(patch('huntingaitan.rotas.interacao_altar.altar_sob_cursor',side_effect=[dict(ref=123,id=2258),None]))
            self.assertTrue(entrar_jardim(d,c,lambda e:None))
            e.mouseDown.assert_not_called()
