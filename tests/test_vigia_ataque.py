import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.combate.vigia_ataque import VigiaAtaque


class VigiaAtaqueTeste(unittest.TestCase):
    def vigia(self):
        v=VigiaAtaque();v.observar(dict(id=4093,hp=5500),0);v.enviado();v.enviado();return v

    def test_detecta_log_ataques_a_2_25_sem_dano(self):
        v=self.vigia();self.assertFalse(v.iniciar(2.9,2.25));self.assertTrue(v.iniciar(3,2.25))
        self.assertEqual(v.recuperar_ate,4.5)

    def test_nao_confunde_morte_com_ataque_travado(self):
        v=self.vigia();v.observar(dict(id=4093,hp=0),1)
        v.enviado();v.enviado();self.assertFalse(v.iniciar(8,2))

    def test_dano_reinicia_a_verificacao(self):
        v=self.vigia();v.observar(dict(id=4093,hp=5000),2.9)
        self.assertFalse(v.iniciar(3,2))

    def test_stun_pausa_e_nao_dispara_recuperacao_ao_terminar(self):
        v=self.vigia();v.suspender(10)
        self.assertFalse(v.iniciar(10,2))

    def test_fora_do_alcance_deixa_navegacao_normal_cuidar(self):
        self.assertFalse(self.vigia().iniciar(5,13.59))

    def test_requer_ataques_realmente_enviados(self):
        v=VigiaAtaque();v.observar(dict(id=4093,hp=5500),0)
        self.assertFalse(v.iniciar(10,2))

    def test_motor_reposiciona_sem_tab_extra_e_so_registra_morte_com_hp_zero(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.configuracao.perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for skill in p['skills']:skill['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];hp=[5500];pos=[(0,0)];teclas=[];eventos=[];navs=[]
        def alvo():return dict(ref=1,id=4093,name='Verit Mutante',hp=hp[0],hp_max=5500,mp=0,mp_max=0,position=(2.25,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo())
            def entidade(self,r):return alvo()
            def cena_validada(self):return 1
            def close(self):pass
        class Navegador:
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):
                navs.append((tempo[0],kw['alcance']));pos[0]=(1,0)
                return dict(estado='andando',w=True,giro=None,pontos=2,erro=0)
        def down(k):
            teclas.append((tempo[0],k))
            if k=='1' and pos[0][0]>0:hp[0]=0
        def dormir(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>10:c.stop.set()
        def emitir(e):
            eventos.append(e)
            if e.get('message')=='Mob abatido; procurando o proximo.':c.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Navegador),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,c)
        self.assertTrue(navs);self.assertGreaterEqual(navs[0][0],3);self.assertEqual(navs[0][1],1.3)
        self.assertEqual([k for t,k in teclas].count('tab'),1)
        self.assertTrue(any(e.get('message','').startswith('Ataques sem dano por 3s;') for e in eventos))
        self.assertEqual(hp[0],0)
        self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),1)


if __name__=='__main__':unittest.main()
