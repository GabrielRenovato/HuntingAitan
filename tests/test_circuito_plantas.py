import copy,math,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.combate.hunt_native import alvo_permitido
from huntingaitan.rotas.circuito_plantas import CircuitoPlantas,plano_plantas,dentro_plantas


class CircuitoPlantasTest(unittest.TestCase):
    def test_perfil_fixa_especie_e_preserva_conta_skills_cura(self):
        original=copy.deepcopy(DEFAULT)
        p=validar(dict(original,patrol_mode='ungor_plantas',client_pid=200,client_hwnd=20,target='qualquer',data_source='visual'))
        self.assertEqual((p['target'],p['data_source'],p['base'],p['radius'],p['auto_base']),('planta','native',[2440,1360],50,False))
        self.assertEqual((p['client_pid'],p['client_hwnd']),(200,20))
        for k in ['skills','heal_key','hp_percent','buff_keys']:self.assertEqual(p[k],original[k])
        self.assertEqual(original,DEFAULT)

    def test_filtro_exclui_outras_plantas_e_outras_especies(self):
        p=validar(dict(patrol_mode='ungor_plantas'));player=dict(position=(2440,1360),height=0)
        pontos=[(1957,1435),(1972,1423),(2108,1396),(2146,1346),(2179,1261),(2274,1235),(2430,1367),(2450,1378),(2457,1350),(2426,1346)]
        def mob(pos,nome='Planta Carnívora Mutante'):return dict(position=pos,height=0,hp=100,hostile=True,name=nome)
        self.assertEqual([i+1 for i,pos in enumerate(pontos) if alvo_permitido(mob(pos),player,p['base'],p)],[7,8,9,10])
        self.assertFalse(alvo_permitido(mob((2440,1360),'Buto Mutante'),player,p['base'],p))
        self.assertFalse(alvo_permitido(dict(mob((2440,1360)),hostile=False),player,p['base'],p))

    def test_circuito_fechado_comeca_perto_e_repete_volta(self):
        plano=plano_plantas();self.assertEqual([(t['de'],t['ate']) for t in plano['trechos']],[(7,8),(8,9),(9,10),(10,7)])
        self.assertEqual(plano['registro_mob'],1373)
        self.assertTrue(dentro_plantas((2440,1360)))
        with self.assertRaisesRegex(RuntimeError,'2440'):CircuitoPlantas((2711,1292))
        c=CircuitoPlantas((2430,1367));agora=0.;visitados=[]
        for _ in range(4):
            t=c.trechos[c.trecho];fim=t['caminho'][-1]
            self.assertEqual(c.destino(fim,agora)['estado'],'aguardar');visitados.append(t['ate'])
            c.destino(fim,agora+5.1);agora+=6
        self.assertEqual(visitados,[8,9,10,7]);self.assertEqual(c.voltas,1)

    def test_motor_mata_quatro_percorre_volta_e_mata_respawn_sem_trocar_vivo(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='ungor_plantas',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];pos=[(2430.,1367.)]
        hp=[100]*4;sel=[None];onda=[0];eventos=[];trocas_vivo=[];navegacao=[]
        locais=[tuple(p['pos']) for p in plano_plantas()['pontos']]
        def mob(i):return dict(ref=0x100000+i,id=9000+onda[0]*4+i,name='Planta Carnívora Mutante',position=locais[i],height=0,hp=hp[i],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob(sel[0]) if sel[0] is not None else None)
            def listar_mobs(self,*args):return [mob(i) for i in range(4) if hp[i]>0]
            def entidade(self,ref):return mob(ref-0x100000)
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kw):
                pos[0]=tuple(args[3]);navegacao.append((pos[0],sum(hp)))
                return dict(estado='chegou',w=False)
        def down(k):
            if k=='tab':
                if sel[0] is not None and hp[sel[0]]>0:trocas_vivo.append(sel[0])
                sel[0]=next((i for i in range(4) if hp[i]>0),None)
            if k=='1' and sel[0] is not None:hp[sel[0]]=max(0,hp[sel[0]]-50)
        def dormir(s):
            tempo[0]+=max(.001,s)
            if onda[0]==0 and any(e.get('patrol_laps',0)>=1 for e in eventos if e.get('event')=='telemetry'):
                onda[0]=1;hp[:]=[100]*4;sel[0]=None
            if sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos)>=8 or tempo[0]>90:control.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_plantas'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,control)
        self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),8)
        self.assertFalse(trocas_vivo);self.assertEqual(onda[0],1)
        for local in locais:self.assertTrue(any(math.dist(destino,local)<=2 and vida==0 for destino,vida in navegacao),local)
        self.assertTrue(any(e.get('patrol_laps',0)>=1 for e in eventos if e.get('event')=='telemetry'))


if __name__=='__main__':unittest.main()
