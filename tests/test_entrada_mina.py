import copy,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.rotas.entrada_mina import EntradaMina,PORTAL,passagem_estrada,bloqueadores_da_porta
from tests.test_navegacao_grade import grade
from huntingaitan.configuracao.perfil_hunt import DEFAULT


def percurso(rota=None):
    m=EntradaMina.__new__(EntradaMina)
    m.rota=rota or [(2708.,1611.),PORTAL];m.bloqueadores=set();m.bloqueio_em=-float('inf')
    m.trechos=[dict(ate='entrada',caminho=m.rota)];m.trecho=0;m.voltas=0;m.indice=0
    m.trilha=[tuple(m.rota[0])];m.obstaculos=[];m.recuo=None;m.revisao=0
    return m


class EntradaTeste(unittest.TestCase):
    def mob(self,id_,pos):return dict(id=id_,position=pos)

    def test_mob_na_porta_e_hostil_vivo_proximo_sem_exigir_dano(self):
        mobs=[dict(id=1,position=(2716,1612),hostile=True,hp=100),dict(id=2,position=(2716,1612),hostile=False,hp=100),dict(id=3,position=(2716,1612),hostile=True,hp=0),dict(id=4,position=(2716,1620),hostile=True,hp=100)]
        self.assertEqual(bloqueadores_da_porta(mobs,(2716,1614)),{1})
        self.assertEqual(bloqueadores_da_porta(mobs,(2716,1640)),set())

    def test_rota_se_afasta_do_ponto_real_das_caixas(self):
        self.assertFalse(passagem_estrada((2713.124,1682.123)))
        self.assertTrue(passagem_estrada((2697.5,1682.5)))
        self.assertFalse(passagem_estrada((2711.5,1682.5)))
        m=percurso([(2695.5,1686.5),(2697.5,1680.5),(2700.5,1677.5)])
        self.assertFalse(m.contem((2713.124,1682.123)))
        self.assertTrue(m.contem((2697.5,1682.5)))

    def test_trajeto_pela_caixa_dagua_nao_e_barrado_pela_estrada_antiga(self):
        self.assertTrue(passagem_estrada((2704.5,1711.5)))
        self.assertTrue(passagem_estrada((2702.5,1684.5)))
        self.assertFalse(passagem_estrada((2713.124,1682.123)))

    def test_ja_preso_nas_caixas_recuar_para_o_lado_livre(self):
        m=percurso([(2710.5,1686.5),(2711.5,1680.5),(2713.5,1677.5)])
        a=m.destino((2713.124,1682.123),0)
        self.assertEqual(a['chave'][1],'recuo_entrada')
        self.assertLess(a['destino'][0],2712)
        self.assertGreater(a['destino'][1],1682.123)

    def test_colisao_real_recuar_e_planejar_rota_diferente(self):
        m=percurso([(1.5,4.5),(17.5,4.5)]);m.grade=grade(20,12);m.trilha=[(1.5,4.5),(2.5,4.5),(4.5,4.5)]
        with patch('huntingaitan.rotas.entrada_mina.PORTAL',(17.5,4.5)):
            self.assertTrue(m.observar_navegacao((4.5,4.5),2,dict(estado='replanejar',ponto=(10.5,4.5))))
            self.assertEqual(m.recuo,(2.5,4.5));self.assertEqual(m.revisao,1)
            self.assertTrue(all(m.passagem(p) for p in m.rota))
            self.assertFalse(m.passagem((6.3,4.5)))
            self.assertEqual(m.destino((4.5,4.5),3)['destino'],(2.5,4.5))
            self.assertEqual(m.destino((2.5,4.5),4)['chave'],('circuito','entrada',1))

    def test_parado_sem_tentativa_de_andar_nao_cria_obstaculo(self):
        m=percurso();m.grade=grade(20,12)
        self.assertFalse(m.observar_navegacao((4.5,4.5),2,dict(estado='andando',w=False,ponto=(10.5,4.5))))
        self.assertEqual(m.obstaculos,[])

    def test_ignora_mobs_no_caminho_mesmo_se_navegacao_bloquear(self):
        m=percurso();pos=(2670,1700);m.observar_navegacao(pos,10,dict(estado='bloqueado'))
        self.assertEqual(m.filtrar_mobs([self.mob(1,pos)],pos,10),[])

    def test_proximidade_do_portal_nao_autoriza_caca(self):
        m=percurso();pos=(2711,1611);m.observar_navegacao(pos,10,dict(estado='andando'))
        self.assertEqual(m.filtrar_mobs([self.mob(1,(2712,1611))],pos,10),[])

    def test_bloqueio_confirmado_so_seleciona_mob_na_passagem(self):
        m=percurso();pos=(2711,1611);m.observar_navegacao(pos,10,dict(estado='replanejar'))
        mobs=[self.mob(1,(2712,1611)),self.mob(2,(2711,1614)),self.mob(3,(2716,1611))]
        self.assertEqual([v['id'] for v in m.filtrar_mobs(mobs,pos,10)],[1])
        self.assertFalse(m.permite_combate(1,(2700,1611),mobs[0]))
        self.assertFalse(m.permite_combate(1,pos,self.mob(1,(2727,1611))))

    def test_bloqueio_antigo_nao_autoriza_novos_alvos(self):
        m=percurso();pos=(2711,1611);m.observar_navegacao(pos,0,dict(estado='replanejar'))
        self.assertEqual(m.filtrar_mobs([self.mob(1,(2712,1611))],pos,4),[])

    def test_chegada_aceita_centro_da_ultima_celula(self):
        self.assertEqual(percurso().destino((2713.5,1613.5),0)['estado'],'concluido')

    def test_chegada_nao_fica_parada_a_um_metro_da_ultima_celula(self):
        m=percurso([(2712.5,1620.5),(2716.5,1614.5)])
        self.assertEqual(m.destino((2716.0198,1615.1052),0)['estado'],'concluido')
        self.assertEqual(m.destino((2716,1618),0)['estado'],'andar')

    def test_motor_nao_usa_tab_ou_ataque_com_hostil_selecionado_no_trajeto(self):
        import huntingaitan.combate.hunt_native as h
        m=percurso([(2700.,1611.),PORTAL]);pos=[(2700.,1611.)];tempo=[0.];teclas=[];eventos=[]
        alvo=dict(ref=1,id=17,name='Hostil do caminho',position=(2701,1611),height=0,hp=100,hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo)
            def recargas_grupos(self):return [0.]*43
            def listar_mobs(self,*a):return [alvo]
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):pos[0]=PORTAL;return dict(estado='andando',w=True,erro=0,pontos=2)
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),cycle_context=True)
        from huntingaitan.combate.hunt_core import AgendaBuffs
        agenda=AgendaBuffs(0,['ctrl+1','f3'],ativo=True)
        control.buff_agenda=agenda
        def sleep(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>5:control.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1;u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=lambda k:teclas.append(k),keyUp=lambda k:None)
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=True,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''],reacoes=[dict(nome='Sangue Sagrado',tecla='3',tipo='buff',skill_id=1146,mp_min=0,intervalo_s=3)])
        for skill in p['skills']:skill['enabled']=False
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',sleep):
            h.main(p,eventos.append,control,percurso=m)
        self.assertEqual(control.reason,'entrada_alcancada')
        self.assertNotIn('tab',teclas);self.assertNotIn('1',teclas)
        self.assertNotIn('ctrl',teclas);self.assertNotIn('f3',teclas);self.assertNotIn('3',teclas)
        self.assertIs(control.buff_agenda,agenda)
        self.assertEqual(agenda.vencimentos,{'ctrl+1':0,'f3':0})
        self.assertEqual(agenda.proximo(tempo[0],True),'ctrl+1')


if __name__=='__main__':unittest.main()
