"""Regressao: o prazo antigo nao pode mandar voltar antes da leitura apos aproximar."""
import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import MagicMock,patch


class PrazoAproximacaoTest(unittest.TestCase):
    def test_pool_some_por_meio_segundo_e_alvo_e_selecionado_sem_retorno_prematuro(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.configuracao.perfil_hunt import DEFAULT
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(no_damage_seconds=3,radius=40,buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for v in p['skills']:v['enabled']=False
        controle=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        tempo=[0.];pos=[(0.,0.)];aproximou=[None];hp=[100];selecionado=[False];eventos=[]
        def mob():return dict(ref=1,id=9001,name='Croshu Mutante das Cinzas',position=(0.,20.),height=0,hp=hp[0],hp_max=100,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=pos[0],heading=0,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob() if selecionado[0] else None)
            def listar_mobs(self,*args):
                if aproximou[0] is not None and tempo[0]-aproximou[0]<.5:return []
                return [mob()] if hp[0]>0 else []
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kwargs):
                if args[4][0]=='busca':pos[0]=(0.,18.);aproximou[0]=tempo[0]
                return dict(estado='chegou',w=False)
        def down(k):
            if k=='tab' and aproximou[0] is not None and tempo[0]-aproximou[0]>=.6:selecionado[0]=True
            if k=='1' and selecionado[0]:hp[0]=max(0,hp[0]-50)
        def dormir(s):
            tempo[0]+=max(.001,s)
            if any(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos) or tempo[0]>20:controle.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,controle)
        self.assertIsNotNone(aproximou[0]);self.assertGreater(aproximou[0],3)
        self.assertEqual(hp[0],0)
        self.assertFalse(any(e.get('message')=='Sem alvo proximo; retornando a base.' for e in eventos))
