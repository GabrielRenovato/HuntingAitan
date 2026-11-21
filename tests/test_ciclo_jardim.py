import threading,unittest,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch,MagicMock
from huntingaitan.rotas.ciclo_jardim import executar_trecho
from huntingaitan.combate.hunt_native import alvo_permitido
from huntingaitan.configuracao.perfil_hunt import DEFAULT


class TrechoTeste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
    def setUp(self):
        self.control=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='jardim_limite_lazapas')
        self.eventos=[]
        def motor(p,emitir,control):
            emitir(dict(event='jardim_limit'));emitir(dict(event='finished'))
        self.motor=Mock(side_effect=motor)

    def test_saida_e_confirmada_antes_de_finalizar_sem_contar_dg(self):
        sair=Mock(side_effect=[False,True])
        with patch('huntingaitan.rotas.ciclo_jardim.time.sleep'):executar_trecho({},self.eventos.append,self.control,self.motor,sair)
        self.assertEqual(sair.call_count,2)
        self.assertEqual(self.control.reason,'jardim_trecho_encerrado')
        self.assertEqual(len([e for e in self.eventos if e['event']=='finished']),1)
        self.assertFalse(any(e['event']=='dungeon_complete' for e in self.eventos))
        self.assertTrue(any(e.get('state')=='jardim_saida_confirmada' for e in self.eventos))

    def test_nao_sai_se_motor_parou_antes_do_limite(self):
        sair=Mock();motor=Mock(side_effect=lambda p,e,c:e(dict(event='finished')))
        executar_trecho({},self.eventos.append,self.control,motor,sair)
        sair.assert_not_called()

    def test_parar_cancela_saida_sem_confirmacao_falsa(self):
        sair=Mock(side_effect=lambda:self.control.stop.set() or False)
        executar_trecho({},self.eventos.append,self.control,self.motor,sair)
        self.assertFalse(any(e.get('state')=='jardim_saida_confirmada' for e in self.eventos))

    def test_filtro_bloqueia_lazapa_final_e_seridunn_mas_preserva_primeiros(self):
        p=dict(DEFAULT,patrol_mode='jardim_aereo',radius=50,target='qualquer')
        player=dict(position=(3757,3146),height=0)
        alvo=dict(name='Lazapa Tempestuosa',position=(3758,3146),height=0,hp=100,hostile=True)
        self.assertFalse(alvo_permitido(alvo,player,player['position'],p))
        self.assertFalse(alvo_permitido(dict(alvo,name='Seridunn'),player,player['position'],p))
        player['position']=(3522,3235);alvo.update(name='Lazapa da Furia',position=(3523,3235))
        self.assertTrue(alvo_permitido(alvo,player,player['position'],p))

    def test_motor_interrompe_antes_de_qualquer_tab_ou_ataque_no_lazapa_final(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.rotas.jardim_aereo import JardimAereo
        from tests.test_navegacao_grade import grade
        pos=(3750.5,3140.5);teclas=[];t=[0.];eventos=[]
        mob=dict(ref=1,id=2408,name='Lazapa Tempestuosa',position=(3757.5,3142.5),height=0,hp=100,hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos,heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob)
            def cena_validada(self):return 1
            def u32(self,*a):return 30005
            def listar_mobs(self,*a):return [mob]
            def close(self):pass
        def conferir(j,pasta):j.grade=grade(40,40);j.grade.origem=(3740,3120)
        def sleep(v):
            t[0]+=max(.001,v)
            if t[0]>10:self.control.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=teclas.append,keyUp=lambda k:None)
        p=dict(DEFAULT,patrol_mode='jardim_aereo',buffs_enabled=False,minimize_on_start=False)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch('huntingaitan.rotas.jardim_aereo.conferir_dificil',return_value=True),patch.object(JardimAereo,'conferir',conferir),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',sleep):
            h.main(p,eventos.append,self.control)
        self.assertEqual(self.control.reason,'jardim_limite_lazapas')
        self.assertEqual(teclas,[])
        self.assertTrue(any(e['event']=='jardim_limit' for e in eventos))
        self.assertFalse(any(e['event']=='action' for e in eventos))

    def test_saida_do_jardim_nao_e_confundida_com_estar_fora_da_mina(self):
        from huntingaitan.rotas.operacoes_mina import sair_grupo
        from huntingaitan.rotas.jardim_aereo import dentro_jardim
        estados=[(3351,3295),(2700,1700),(2700,1700),(2700,1700)]
        d=SimpleNamespace(hwnd=1,u=MagicMock());d.u.GetForegroundWindow.return_value=1
        d.snapshot=Mock(side_effect=[dict(player=dict(position=q,hp=100,hp_max=100)) for q in estados])
        class MSS:
            def __enter__(self):return self
            def __exit__(self,*a):pass
        cap=SimpleNamespace(capturar=lambda:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=MagicMock(),mss=SimpleNamespace(MSS=MSS)),patch('huntingaitan.visao.captura_aika.CapturaAika',return_value=cap),patch('huntingaitan.rotas.operacoes_mina.InterfaceMina') as ui,patch('huntingaitan.visao.avisos_hunt.DetectorAvisos') as avisos,patch('huntingaitan.rotas.operacoes_mina.time.sleep'):
            ui.return_value.saida.return_value=dict(acao='aguardar_saida');avisos.return_value.localizar.return_value=None
            self.assertTrue(sair_grupo(d,self.control,self.eventos.append,dentro=dentro_jardim,nome='Jardim'))
        self.assertEqual(d.snapshot.call_count,4)


if __name__=='__main__':unittest.main()
