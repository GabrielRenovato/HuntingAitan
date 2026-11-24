"""Reproduz recargas sempre prontas, cura recusada e alvo sem dano."""
import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.combate.hunt_core import CadenciaCombate
from huntingaitan.combate.vigia_ataque import VigiaAtaque

class RegressaoPenzaTeste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()

    def test_skills_sempre_prontas_nao_excluem_normal(self):
        c=CadenciaCombate({'recargas':{'2':150,'3':150,'4':15,'5':17,'6':46,'8':93}})
        reais={k:dict(ready=True) for k in c.recargas};envios=[]
        for i in range(50):
            agora=i*.75;k=c.escolher(agora,True,False,.9,True,reais)
            if k:c.registrar(k,agora);envios.append((agora,k))
        normais=[t for t,k in envios if k=='1']
        self.assertGreater(len(normais),10)
        self.assertLessEqual(max(b-a for a,b in zip(normais,normais[1:])),2.5)
        self.assertEqual(set(k for _,k in envios),set(reais)|{'1'})

    def test_normal_em_recarga_nao_bloqueia_skills(self):
        c=CadenciaCombate({'recargas':{'2':1}});c.registrar('1',0)
        self.assertEqual(c.escolher(5,True,True,1,True,{'2':dict(ready=True)},normal_disponivel=False),'2')

    def test_tres_recuperacoes_sem_dano_esgotam_alvo(self):
        v=VigiaAtaque();v.observar(dict(id=7,hp=122649),0)
        for t in [3,6,9]:
            v.enviado();v.enviado();self.assertTrue(v.iniciar(t,2));v.suspender(t)
        v.enviado();v.enviado();self.assertTrue(v.esgotado(12,2))
        v.observar(dict(id=7,hp=122000),12);self.assertEqual(v.recuperacoes,0)

    def test_motor_recupera_com_skills_e_cura_falhando_sem_fingir_abate(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.configuracao.perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''],hp_percent=70,cancel_normal=False)
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];eventos=[];pos=[(0,0)];ignorado_em=[None]
        def alvo():return dict(ref=1,id=7271,name='Penza Poderosa Mutante',hp=125000 if tempo[0]<5 else 122649,hp_max=138888,position=(2.25,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=50,hp_max=100,mp=100,mp_max=100),target=alvo())
            def estados_controle(self):return dict(stunned=False,casting=False,normal_ready=True,normal_skill=1)
            def recargas_atalhos(self):return {str(i):dict(skill=49 if i==7 else i,ready=True,cooldown=0.) for i in range(1,9)}
            def entidade(self,r):return alvo()
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):
                pos[0]=(.8,0);return dict(estado='chegou',w=False)
        def dormir(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>40 or ignorado_em[0] is not None and tempo[0]>ignorado_em[0]+3:c.stop.set()
        def emitir(e):
            eventos.append(dict(e,sim_t=tempo[0]))
            if e.get('message','').startswith('Alvo sem dano apos tres recuperacoes;'):ignorado_em[0]=tempo[0]
        u=MagicMock();u.GetForegroundWindow.return_value=1;u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=lambda k:None,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,c)
        self.assertTrue(any(e.get('kind')=='normal' for e in eventos))
        self.assertTrue(any(e.get('kind')=='skill' for e in eventos))
        self.assertTrue(any(e.get('message','').startswith('Cura sem efeito confirmado') for e in eventos))
        ignorado=next(e for e in eventos if e.get('message','').startswith('Alvo sem dano apos tres recuperacoes;'))
        self.assertLess(ignorado['sim_t'],35)
        self.assertFalse(any(e.get('message')=='Alvo confirmado por dados internos.' for e in eventos if e['sim_t']>ignorado['sim_t']))
        self.assertFalse(any(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos))
        envios=[e for e in eventos if e.get('event')=='action']
        for i,e in enumerate(envios):
            if e.get('kind')=='heal' and i+1<len(envios):self.assertGreaterEqual(envios[i+1]['sim_t']-e['sim_t'],1.99)

if __name__=='__main__':unittest.main()
