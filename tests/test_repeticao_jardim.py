import threading,unittest,sys
from types import SimpleNamespace
from unittest.mock import Mock,patch,MagicMock
import numpy as np
from huntingaitan.rotas.ciclo_jardim import CicloJardim
from huntingaitan.rotas.interface_jardim import InterfaceJardim
from huntingaitan.configuracao.perfil_hunt import validar,DEFAULT


class CicloTeste(unittest.TestCase):
    def preparar(self,**perfil):
        self.control=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        self.pos=[3351,3295];self.eventos=[];self.contador=0
        def motor(p,e,c,**kw):
            if kw:self.pos[:]=[1840,1092];c.reason='entrada_alcancada'
            else:self.pos[:]=[3779,3130];e(dict(event='jardim_limit'));c.reason='jardim_limite_lazapas'
            e(dict(event='finished'))
        def sair():self.pos[:]=[1856.4,1082.4];return True
        def entrar():self.pos[:]=[3351,3295];return True
        self.motor=Mock(side_effect=motor);self.sair=Mock(side_effect=sair);self.entrar=Mock(side_effect=entrar)
        self.rota=Mock(return_value=object())
        return CicloJardim(dict(DEFAULT,**({'jardim_goal':'antes_shiraz'}|perfil)),self.control,self.eventos.append,
            lambda:dict(position=self.pos[:],hp=1,pasta='jogo'),self.motor,self.sair,self.entrar,self.rota)

    def test_duas_passagens_com_saida_reentrada_e_sem_falso_abate(self):
        c=self.preparar(jardim_cycles=2)
        for _ in range(12):
            if self.control.stop.is_set():break
            c.passo()
        self.assertTrue(self.control.stop.is_set());self.assertEqual(c.trechos,2)
        self.assertEqual(self.sair.call_count,2);self.assertEqual(self.entrar.call_count,1)
        self.assertEqual(self.rota.call_count,1)
        self.assertFalse(any(e['event'] in ('finished','dungeon_complete') for e in self.eventos))
        self.assertEqual(self.control.reason,'jardim_trecho_encerrado')
        self.assertTrue(all(call.args[0]['duration_minutes']==0 for call in self.motor.call_args_list))

    def test_entrada_sem_dificuldade_confirmada_sai_e_retenta_sem_contar(self):
        c=self.preparar();self.pos[:]=[1840,1092]
        self.entrar.side_effect=lambda:self.pos.__setitem__(slice(None),[3351,3295]) or False
        c.passo();c.passo();self.assertEqual(c.etapa,'jardim_corrigir_entrada')
        c.passo();self.assertEqual(c.etapa,'jardim_retornar');self.assertEqual(c.trechos,0)
        self.assertEqual(self.motor.call_count,0)

    def test_sem_repeticao_e_morte_preservadas(self):
        c=self.preparar(jardim_repeat=False);c.passo();c.passo()
        self.assertTrue(self.control.stop.is_set());self.entrar.assert_not_called()
        c=self.preparar();c.ler=lambda:dict(position=[3351,3295],hp=0)
        c.passo();self.assertEqual(self.control.reason,'personagem_sem_vida');self.motor.assert_not_called()

    def test_portal_bloqueado_passa_ids_so_para_liberacao(self):
        c=self.preparar();self.pos[:]=[1840,1092];self.control.bloqueadores_portal={17}
        self.entrar.side_effect=None;self.entrar.return_value=False
        c.passo();c.passo();self.assertEqual(c.etapa,'jardim_liberar_entrada')
        c.passo();self.assertEqual(self.rota.call_args.kwargs['bloqueadores'],{17})

    def test_perfil_valida_opcoes(self):
        p=validar(dict(DEFAULT,patrol_mode='jardim_aereo'))
        self.assertTrue(p['jardim_repeat']);self.assertFalse(p['mina_repeat'])
        for n in [-1,1.5,True,10000]:
            with self.assertRaises(ValueError):validar(dict(DEFAULT,jardim_cycles=n))


class InterfaceTeste(unittest.TestCase):
    def test_painel_real_reconhece_botoes_sem_ocr_e_reconfirma_sem_reler_tela(self):
        from pathlib import Path
        import cv2
        painel=cv2.imread(str(Path(__file__).parent/'fixtures/jardim_painel_entrada.png'))
        tela=np.zeros((1080,1920,3),np.uint8);tela[355:725,710:1210]=painel
        ui=InterfaceJardim(ocr=Mock(side_effect=AssertionError('Nao deve executar OCR no painel conhecido')))
        for selecionado,nome,ponto in [(False,'selecionar_dificil',(818,535)),(True,'confirmar_calabouco',(773,686))]:
            acao=ui.entrada(tela,selecionado)
            self.assertEqual(acao['acao'],nome);self.assertEqual(acao['ponto'],ponto)
            self.assertEqual(ui.reconfirmar(tela,acao,selecionado)['ponto'],ponto)
            alterada=tela.copy();x,y=ponto;alterada[y-15:y+15,x-42:x+42]=0
            self.assertNotIn('ponto',ui.reconfirmar(alterada,acao,selecionado))
        ui.ocr.assert_not_called()

    def setUp(self):
        self.ui=InterfaceJardim(ocr=lambda t:([],None));self.tela=np.zeros((1080,1920,3),np.uint8)
        self.ui.achar=Mock(return_value=None)

    def test_dificil_somente_dentro_painel_e_enter_depois_da_selecao(self):
        self.ui.achar.side_effect=lambda t,n,*args,**kw:dict(ponto=(700,100),escala=1) if n=='titulo_calabouco' else None
        self.ui.textos_regiao=lambda t,roi:[dict(nome='hard',ponto=(1750,300)),dict(nome='dificil',ponto=(650,200)),dict(nome='entrar',ponto=(650,500))]
        self.assertEqual(self.ui.entrada(self.tela)['acao'],'selecionar_dificil')
        self.assertEqual(self.ui.entrada(self.tela,True)['acao'],'confirmar_calabouco')

    def test_hard_hud_nao_e_botao_e_portal_exige_nome_correto(self):
        self.ui.textos_regiao=lambda t,roi:[dict(nome='hard',ponto=(1750,300)),dict(nome='minaabandonada',ponto=(700,200))]
        self.assertEqual(self.ui.entrada(self.tela)['acao'],'aguardar_portal')
        self.ui.textos_regiao=lambda t,roi:[dict(nome='altardaascensao',ponto=(700,200))]
        self.assertTrue(self.ui.entrada(self.tela)['duplo'])

    def test_grupo_por_texto_tem_prioridade_sobre_altar_ao_fundo(self):
        self.ui.achar.side_effect=lambda t,n,*a,**k:dict(ponto=(1000,300)) if n=='jardim_altar_bin' else None
        self.ui.textos_regiao=lambda t,roi:[dict(nome='grupodemazmorra',ponto=(900,200)),dict(nome='entrar',ponto=(820,700)),dict(nome='altardaascensao',ponto=(1000,300))]
        self.assertEqual(self.ui.entrada(self.tela,True),dict(acao='entrar_grupo_mazmorra',ponto=(820,700)))

    def test_grupo_sem_botao_nao_clica_no_altar_atras_da_janela(self):
        self.ui.textos_regiao=lambda t,roi:[dict(nome='grupodemazmorra',ponto=(900,200)),dict(nome='altardaascensao',ponto=(1000,300))]
        self.assertEqual(self.ui.entrada(self.tela,True)['acao'],'aguardar_mazmorra')

    def test_entrada_confirma_dificil_duas_vezes_e_nao_usa_spawn_da_mina(self):
        from huntingaitan.rotas.operacoes_mina import entrar_jardim
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        d=SimpleNamespace(hwnd=1,u=MagicMock());d.u.GetForegroundWindow.return_value=1
        d.snapshot=Mock(return_value=dict(player=dict(position=(3351,3295),hp=100,hp_max=100)))
        eventos=[]
        class MSS:
            def __enter__(self):return self
            def __exit__(self,*a):pass
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=MagicMock(),mss=SimpleNamespace(MSS=MSS)),patch('huntingaitan.visao.captura_aika.CapturaAika') as cap,patch('huntingaitan.rotas.interface_mina.VerificadorElite') as ver,patch('huntingaitan.rotas.operacoes_mina.time.sleep'):
            cap.return_value.capturar.return_value=self.tela
            ver.return_value.confirmar.side_effect=[False,True,True]
            ver.return_value.diagnostico={}
            self.assertTrue(entrar_jardim(d,control,eventos.append))
            self.assertEqual(ver.call_args.kwargs['dificuldade'],'dificil')
            self.assertEqual(ver.return_value.confirmar.call_count,3)
        self.assertTrue(any(e.get('state')=='dificil_confirmado' for e in eventos))


class ArquivosTeste(unittest.TestCase):
    def test_retorno_real_respeita_terreno_e_objetos(self):
        from pathlib import Path
        from huntingaitan.rotas.entrada_jardim import EntradaJardim,PORTAL
        import math
        raiz=Path(r'C:\GoLevel\AikaOnline')
        if not raiz.exists():self.skipTest('Cliente local indisponivel; geometria coberta pelos dados empacotados.')
        rota=EntradaJardim(raiz,(1856.4,1082.4))
        self.assertLessEqual(math.dist(rota.rota[-1],PORTAL),4)
        self.assertTrue(all(rota.grade.passagem(rota.grade.celula(a),rota.grade.celula(b)) for a,b in zip(rota.rota,rota.rota[1:])))
        self.assertTrue(all(rota.geometria.livre(p) for p in rota.rota))
        self.assertEqual(rota.filtrar_mobs([dict(id=2,position=(1855,1082))],(1856,1082),0),[])
        # Posicao real em que a versao anterior encerrava a aproximacao cedo.
        self.assertEqual(rota.destino((1841.4917,1091.1141),0)['estado'],'andar')
        self.assertEqual(rota.destino(rota.rota[-1],0)['estado'],'concluido')
        # Quina real: o alvo antigo ficava dentro da tolerancia do motor.
        pos=(1853.961181640625,1085.73193359375)
        plano=rota.destino(pos,1)
        self.assertEqual(plano['estado'],'andar')
        self.assertGreaterEqual(math.dist(pos,plano['destino']),1.5)
        self.assertTrue(rota.grade.linha_livre(rota.grade.celula(pos),rota.grade.celula(plano['destino'])))


class CursorTeste(unittest.TestCase):
    def test_clique_confere_pixels_fisicos_em_monitor_a_esquerda(self):
        import ctypes
        from ctypes import wintypes as w
        from huntingaitan.entrada.entrada_segura import mover_cursor_fisico
        class Usuario:
            def GetSystemMetrics(self,i):return {76:-1920,77:0,78:3840,79:1080}[i]
            def SendInput(self,n,ptr,tamanho):
                e=ptr._obj.uniao.mouse
                self.flags=e.flags
                self.pos=(-1920+int(e.dx*3840/65536),int(e.dy*1080/65536))
                return 1
            def GetCursorPos(self,ptr):
                p=ctypes.cast(ptr,ctypes.POINTER(w.POINT)).contents;p.x,p.y=self.pos;return 1
        u=Usuario();entrada=SimpleNamespace(failSafeCheck=Mock())
        self.assertTrue(mover_cursor_fisico(entrada,-956,172,u))
        self.assertEqual(u.flags,0xc001)
        self.assertEqual(u.pos,(-956,172));entrada.failSafeCheck.assert_called_once()
        u.GetCursorPos=lambda ptr:0
        self.assertFalse(mover_cursor_fisico(entrada,970,121,u))
        u.SendInput=lambda *a:0
        self.assertFalse(mover_cursor_fisico(entrada,970,121,u))


if __name__=='__main__':unittest.main()
