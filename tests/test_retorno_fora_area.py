import math,unittest,copy,sys,threading
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from navegacao_grade import Grade
from navegador_local import NavegadorLocal


def janela(pos,raio=48,bloqueios=()):
    x,y=math.floor(pos[0]),math.floor(pos[1]);canto=(x-raio,y-raio);w=raio*2+1;f=bytearray(w*w)
    for bx,by in bloqueios:
        if canto[0]<=bx<canto[0]+w and canto[1]<=by<canto[1]+w:f[(by-canto[1])*w+bx-canto[0]]=1
    return Grade((0,0),canto,w,w,bytes(f),(0,)*(w*w),1)


class RetornoForaAreaTeste(unittest.TestCase):
    def test_reproduz_posicao_final_log_e_grade_insuficiente(self):
        pos=(2760.906,727.832);base=(2708.627,737.507);g=janela(pos)
        self.assertIsNone(g.caminho(pos,base,alcance=2,limite=(base,32)))
        raio=max(32,math.dist(pos,base)+2)
        r=g.caminho(pos,base,alcance=2,limite=(base,raio),parcial=True)
        self.assertTrue(r);self.assertLess(math.dist(r[-1],base),math.dist(pos,base))
        for a,b in zip(r,r[1:]):self.assertTrue(g.passagem(g.celula(a),g.celula(b)))

    def test_final_do_trecho_rele_grade_e_continua_ate_base(self):
        base=(2708.627,737.507);pos=(2760.906,727.832);leituras=[]
        def ler(d,p):leituras.append(p);return janela(p)
        n=NavegadorLocal(ler)
        for t in range(4):
            r=n.planejar(None,pos,270,base,('base',base),t,alcance=2,limite=(base,max(32,math.dist(pos,base)+2)),parcial=True)
            if r['estado']=='chegou':break
            self.assertTrue(n.rota);pos=n.rota[-1]
        self.assertEqual(r['estado'],'chegou');self.assertGreaterEqual(len(leituras),2)
        self.assertLessEqual(math.dist(pos,base),2)

    def test_rota_parcial_nao_atravessa_parede(self):
        pos=(10.5,10.5);dest=(40.5,10.5)
        g=janela(pos,8,[(15,y) for y in range(3,16)])
        r=g.caminho(pos,dest,parcial=True)
        self.assertTrue(r)
        for a,b in zip(r,r[1:]):self.assertTrue(g.passagem(g.celula(a),g.celula(b)))

    def test_area_de_caca_normal_continua_restrita(self):
        pos=(10.5,10.5);dest=(30.5,10.5);g=janela(pos)
        self.assertIsNone(g.caminho(pos,dest,limite=(pos,10)))

    def test_motor_prioriza_retorno_e_permite_reentrada(self):
        import hunt_native as h
        from perfil_hunt import DEFAULT
        perfil=copy.deepcopy(DEFAULT);perfil.update(buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''],radius=30)
        for s in perfil['skills']:s['enabled']=False
        controle=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];passos=[];teclas=[];eventos=[]
        base=(2708.627,737.507);pos=(2760.906,727.832)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=base if tempo[0]<.1 else pos,heading=270,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=None)
            def cena_validada(self):return 1
            def close(self):pass
        class Navegador:
            def invalidar(self):pass
            def planejar(self,*args,**kw):
                passos.append((args,kw));controle.stop.set()
                return dict(estado='andando',w=True,giro=None,pontos=10,erro=0)
        def dormir(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>2:controle.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=lambda k:teclas.append(k),keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Navegador),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(perfil,eventos.append,controle)
        self.assertTrue(passos);args,kw=passos[0]
        self.assertEqual(args[4],('base',base));self.assertTrue(kw['parcial'])
        self.assertGreaterEqual(kw['limite'][1],math.dist(pos,base))
        self.assertIn('s',teclas)


if __name__=='__main__':unittest.main()
