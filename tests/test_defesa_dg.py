import copy,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.combate.defesa_dg import DefesaDG
from huntingaitan.rotas.mina_lenfer import MinaLenfer
from huntingaitan.configuracao.perfil_hunt import DEFAULT
from tests.test_navegacao_grade import grade


class DefesaTeste(unittest.TestCase):
    def test_dano_residual_com_vida_cheia_nao_prende_rota_na_defesa(self):
        d=DefesaDG();d.observar(0,1,{})
        # Alternancia observada na Mina: poucos pontos de dano e regeneracao.
        for i in range(1,301):
            hp=[1.,.99983352,.99958380,.99995838,.99970866,.99954218][i%6]
            self.assertFalse(d.observar(i*.1,hp,{}),(i,hp))

    def test_dano_em_varios_golpes_pequenos_ainda_aciona_defesa(self):
        d=DefesaDG();d.observar(0,1,{})
        for i in range(1,10):self.assertFalse(d.observar(i*.2,1-i*.001,{}))
        self.assertTrue(d.observar(2.,.99,{}))

    def test_danos_antigos_nao_acumulam_indefinidamente(self):
        d=DefesaDG();d.observar(0,1,{})
        for i in range(1,30):self.assertFalse(d.observar(i*4,1-i*.001,{}))

    def test_inimigo_a_dez_unidades_entra_na_busca_defensiva(self):
        d=DefesaDG();d.observar(0,.5,{})
        mobs=[dict(id=1,position=(10,0)),dict(id=2,position=(20,0))]
        self.assertEqual(d.candidatos(mobs,(0,0)),mobs[:1])

    def test_dano_e_stun_travam_avanco_ate_quatro_segundos_de_sossego(self):
        d=DefesaDG()
        self.assertFalse(d.observar(0,1,{}))
        self.assertTrue(d.observar(1,.9,{}))
        self.assertTrue(d.observar(4,.9,dict(stunned=True)))
        self.assertTrue(d.observar(7.9,.9,{}))
        self.assertFalse(d.observar(8,.9,{}))

    def test_vida_baixa_nao_libera_novo_grupo_so_porque_parou_de_tomar_dano(self):
        d=DefesaDG()
        d.observar(0,1,{})
        self.assertTrue(d.observar(1,.4,{}))
        self.assertTrue(d.observar(101,.4,{}))
        self.assertFalse(d.observar(102,.8,{}))

    def test_defesa_nao_persegue_chefe_distante_nem_descarta_hostil_colado(self):
        m=MinaLenfer((2850,3344));m.grade=grade(30,8)
        m.rota_planejada=[(1.5,1.5),(28.5,1.5)]
        mobs=[dict(id=1,name='Soldado',position=(3.5,1.5)),dict(id=2,name='Malik',position=(20.5,1.5))]
        self.assertEqual([v['id'] for v in m.filtrar_mobs(mobs,(1.5,1.5),50,True)],[1])
        # A grade continua excluindo uma entidade sem passagem.
        m.grade=grade(30,8,[(5,y) for y in range(8)]);m.custo_origem=None
        mobs[1].update(position=(8.5,1.5))
        self.assertEqual([v['id'] for v in m.filtrar_mobs(mobs,(1.5,1.5),50,True)],[1])

    def test_motor_nao_avanca_apos_timeout_de_selecao_enquanto_ferido(self):
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        import huntingaitan.combate.hunt_native as h
        pos=(2850.5,3344.5)
        plano=dict(limites=[2816,3328,3072,3584],entrada=pos,
                   pontos=[dict(id=0,pos=(2860.5,3344.5),chefe='malik',espera=15)],
                   trechos=[dict(ate=0,caminho=[pos,(2860.5,3344.5)])])
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='mina_lenfer',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for skill in p['skills']:skill['enabled']=False
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        t=[0.];events=[];movimentos=[]
        mob=dict(ref=1,id=3000,name='Soldado',position=(2855.5,3344.5),height=0,hp=100,hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):
                hp=100 if t[0]<.1 or t[0]>=8 else 60
                return dict(player=dict(position=pos,heading=90,height=0,hp=hp,hp_max=100,mp=100,mp_max=100),target=None)
            def cena_validada(self):return 1
            def u32(self,*a):return 30005
            def listar_mobs(self,*a):return [mob]
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):
                movimentos.append((t[0],a[4]))
                return dict(estado='chegou')
        def sleep(v):
            t[0]+=max(.001,v)
            if t[0]>16:control.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=lambda k:None,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch('huntingaitan.rotas.mina_lenfer.plano_mina',return_value=plano),patch.object(MinaLenfer,'conferir'),patch.object(MinaLenfer,'filtrar_mobs',side_effect=lambda mobs,*a:mobs),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',sleep):
            h.main(p,events.append,control)
        self.assertTrue(any(.1<=tempo<8 and chave[0]=='busca' for tempo,chave in movimentos),movimentos)
        self.assertFalse(any(.1<=tempo<8 and chave[0]=='circuito' for tempo,chave in movimentos),movimentos)
        self.assertTrue(any(tempo>=8 and chave[0]=='circuito' for tempo,chave in movimentos),movimentos)
        self.assertFalse(any(e.get('event')=='dungeon_complete' for e in events))


if __name__=='__main__':unittest.main()
