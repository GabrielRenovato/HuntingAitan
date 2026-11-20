import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock

class PrioridadeJanelaTeste(unittest.TestCase):
    def simular(self,morrer=False,buffs=False):
        import hunt_native as h
        import avisos_hunt  # Carrega OpenCV antes de simular o relogio do motor.
        from perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p["extra_buffs_enabled"]=False;p.update(buffs_enabled=buffs,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];hp=[100];eventos=[];teclas=[];mouse=[];clicou=[False]
        def alvo():return dict(ref=1,id=4093,name='Verit Mutante',hp=hp[0],hp_max=100,mp=0,mp_max=0,position=(2,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=(0,0),height=0,hp=0 if morrer and t[0]>=2 else 100,hp_max=100,mp=100,mp_max=100),target=alvo())
            def close(self):pass
        class Monitor:
            def __init__(self,*args,bloqueio=None,**kwargs):self.bloqueio=bloqueio
            def iniciar(self):pass
            def atual(self):
                if 1<=t[0]<3:
                    self.bloqueio.set();return dict(tipo='cte_elter',ponto=(100,100),capturado=t[0])
                self.bloqueio.clear();return None
        def down(k):
            teclas.append((t[0],k))
            if k=='1' and t[0]>=3:hp[0]=0
        def dormir(s):
            t[0]+=max(.001,s)
            if t[0]>15:c.stop.set()
        def emitir(e):
            eventos.append(e)
            if e.get('message')=='Mob abatido; procurando o proximo.':c.stop.set()
        def reconfirmar(a):return None if clicou[0] else (100,100)
        def clicar():clicou[0]=True;mouse.append(t[0])
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None,moveTo=lambda *p:None,mouseDown=clicar,mouseUp=lambda:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'ObservadorAvisos',Monitor),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir),patch('avisos_hunt.reconfirmar',reconfirmar):h.main(p,emitir,c)
        return eventos,teclas,mouse,hp[0]

    def test_motor_nao_ataca_apos_clique_ate_janela_sumir(self):
        eventos,teclas,mouse,hp=self.simular()
        self.assertEqual(len(mouse),1)
        self.assertFalse(any(1<=tempo<3 for tempo,key in teclas))
        self.assertTrue(any(tempo>=3 and key=='1' for tempo,key in teclas))
        self.assertEqual([k for tempo,k in teclas].count('tab'),1)
        self.assertTrue(any(e.get('message','').startswith('Fechamento confirmado em duas capturas;') for e in eventos))
        self.assertEqual(hp,0)

    def test_modal_interrompe_buffs_e_sequencia_retoma_antes_dos_ataques(self):
        eventos,teclas,mouse,hp=self.simular(buffs=True)
        self.assertEqual(len(mouse),1)
        self.assertFalse(any(1<=tempo<3 for tempo,key in teclas))
        self.assertEqual([e['atalho'] for e in eventos if e.get('message')=='Atalho de buff enviado.'],['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5'])
        fim=next(i for i,e in enumerate(eventos) if e.get('message')=='Ciclo de buffs concluido; combate liberado com a selecao preservada.')
        self.assertFalse(any(e.get('event')=='action' for e in eventos[:fim]))
        self.assertGreater(next(tempo for tempo,key in teclas if key=='tab'),max(tempo for tempo,key in teclas if key=='ctrl'))
        self.assertEqual(hp,0)

    def test_hp_e_morte_continuam_observados_enquanto_fecha_aviso(self):
        eventos,teclas,mouse,hp=self.simular(morrer=True)
        self.assertTrue(any(e.get('message')=='Personagem sem vida com janela bloqueante aberta; caca encerrada.' for e in eventos))
        self.assertTrue(any(e.get('state')=='aviso' and e.get('hp')==0 for e in eventos))
        self.assertFalse(any(tempo>=1 and key=='1' for tempo,key in teclas))

if __name__=='__main__':unittest.main()
