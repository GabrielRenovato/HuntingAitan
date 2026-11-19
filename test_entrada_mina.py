import copy,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from entrada_mina import EntradaMina,PORTAL
from perfil_hunt import DEFAULT


def percurso(rota=None):
    m=EntradaMina.__new__(EntradaMina)
    m.rota=rota or [(2708.,1611.),PORTAL];m.bloqueadores=set();m.bloqueio_em=-float('inf')
    m.trechos=[dict(ate='entrada',caminho=m.rota)];m.trecho=0;m.voltas=0;m.indice=0
    return m


class EntradaTeste(unittest.TestCase):
    def mob(self,id_,pos):return dict(id=id_,position=pos)

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

    def test_motor_nao_usa_tab_ou_ataque_com_hostil_selecionado_no_trajeto(self):
        import hunt_native as h
        m=percurso([(2700.,1611.),PORTAL]);pos=[(2700.,1611.)];tempo=[0.];teclas=[];eventos=[]
        alvo=dict(ref=1,id=17,name='Hostil do caminho',position=(2701,1611),height=0,hp=100,hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo)
            def listar_mobs(self,*a):return [alvo]
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):pos[0]=PORTAL;return dict(estado='andando',w=True,erro=0,pontos=2)
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        def sleep(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>5:control.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=lambda k:teclas.append(k),keyUp=lambda k:None)
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',sleep):
            h.main(p,eventos.append,control,percurso=m)
        self.assertEqual(control.reason,'entrada_alcancada')
        self.assertNotIn('tab',teclas);self.assertNotIn('1',teclas)


if __name__=='__main__':unittest.main()
