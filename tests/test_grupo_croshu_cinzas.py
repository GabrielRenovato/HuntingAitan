import copy,math,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.combate.hunt_native import alvo_permitido


class GrupoCroshuCinzasTest(unittest.TestCase):
    def test_modo_fixa_grupo_sem_mudar_skills_cura_e_buffs(self):
        original=copy.deepcopy(DEFAULT)
        p=validar(dict(original,client_pid=200,client_hwnd=20,patrol_mode='cinzenta_croshu_trio',base=[1,2],auto_base=True,radius=50,target='qualquer',data_source='visual',mina_repeat=True))
        self.assertEqual((p['base'],p['radius'],p['target'],p['auto_base'],p['data_source'],p['mina_repeat']),([2882,1154],50,'croshu',False,'native',False))
        for k in ['skills','heal_key','hp_percent','buff_keys','buff_minutes']:
            self.assertEqual(p[k],original[k])
        self.assertEqual((p['client_pid'],p['client_hwnd']),(200,20))
        self.assertEqual(original,DEFAULT)

    def test_so_os_tres_spawns_estao_no_raio_e_npc_e_outras_especies_sao_excluidos(self):
        p=validar(dict(patrol_mode='cinzenta_croshu_trio'));player=dict(position=(2882,1154),height=0)
        pontos=[(2982,1338),(3009,1321),(2862,1387),(2866,1321),(2884,1350),(2955,1310),(2881,1189),(2881,1156),(2905,1143),(2686,1089),(2725,1102)]
        def alvo(pos,nome='Croshu Mutante das Cinzas',hostile=True):return dict(position=pos,height=0,hp=100,hostile=hostile,name=nome)
        aceitos=[i+1 for i,pos in enumerate(pontos) if alvo_permitido(alvo(pos),player,p['base'],p)]
        self.assertEqual(aceitos,[7,8,9])
        self.assertFalse(alvo_permitido(alvo((2881,1156),'Cão Mutante Croshu'),player,p['base'],p))
        self.assertFalse(alvo_permitido(alvo((2881,1156),hostile=False),player,p['base'],p))
        self.assertFalse(alvo_permitido(alvo((2955,1310)),dict(player,position=(2955,1310)),p['base'],p))

    def test_busca_fechada_visita_todos_os_pontos(self):
        from huntingaitan.rotas.circuito_cinzas import CircuitoCinzas,plano_cinzas
        c=CircuitoCinzas((2882,1154));visitados=[]
        for i in range(5):
            t=c.trechos[c.trecho];fim=t['caminho'][-1];visitados.append(t['ate'])
            self.assertEqual(c.destino(fim,i*6)['estado'],'aguardar');c.destino(fim,i*6+5.1)
        self.assertEqual(set(visitados),{7,8,9,10,11});self.assertEqual(c.voltas,1)
        self.assertEqual(len(plano_cinzas()['trechos']),5)

    def test_novo_grupo_e_elegivel_perto_da_coordenada_informada(self):
        from huntingaitan.rotas.circuito_cinzas import CircuitoCinzas,dentro_cinzas
        p=validar(dict(patrol_mode='cinzenta_croshu_trio'))
        player=dict(position=(2697,1106),height=0)
        self.assertTrue(dentro_cinzas(player['position']))
        c=CircuitoCinzas(player['position'])
        self.assertIn(c.trechos[c.trecho]['ate'],(7,10,11))
        for pos in ((2686,1089),(2725,1102)):
            mob=dict(position=pos,height=0,hp=100,hostile=True,name='Croshu Mutante das Cinzas')
            self.assertTrue(alvo_permitido(mob,player,p['base'],p))
            self.assertFalse(alvo_permitido(dict(mob,name='Croshu das Cinzas'),player,p['base'],p))

    def test_terceiro_ponto_visita_coordenada_informada_sem_parar_no_cadastro_antigo(self):
        from huntingaitan.rotas.circuito_cinzas import CircuitoCinzas,plano_cinzas
        d=plano_cinzas()
        self.assertEqual(next(p['pos'] for p in d['pontos'] if p['id']==7),[2885,1196])
        self.assertEqual(next(p['pos'] for p in d['pontos_cadastro'] if p['id']==7),[2881,1189])
        c=CircuitoCinzas((2905,1143))
        c.trecho=next(i for i,t in enumerate(c.trechos) if t['ate']==7);c.indice=0
        passo=c.destino((2881,1189),0)
        self.assertEqual(passo['estado'],'andar')
        self.assertEqual(passo['ponto'],7)
        self.assertEqual(c.destino((2885,1196),1)['estado'],'aguardar')

    def test_motor_procura_o_terceiro_invisivel_da_base(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='cinzenta_croshu_trio',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for skill in p['skills']:skill['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        tempo=[0.];pos=[(2882.,1154.)];hp=[100]*3;sel=[None];eventos=[];tabs_vivos=[];visitou_oculto=[False]
        locais=[(2881,1156),(2905,1143),(2885,1196)]
        def mob(i):return dict(ref=0x100000+i,id=9000+i,name='Croshu Mutante das Cinzas',position=locais[i],height=0,hp=hp[i],hp_max=100,hostile=True)
        def visivel(i):return hp[i]>0 and (i!=2 or math.dist(pos[0],locais[2])<3)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob(sel[0]) if sel[0] is not None else None)
            def listar_mobs(self,*args):return [mob(i) for i in range(3) if visivel(i)]
            def entidade(self,ref):return mob(ref-0x100000)
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kwargs):
                pos[0]=tuple(args[3])
                if hp[:2]==[0,0] and math.dist(pos[0],locais[2])<3:visitou_oculto[0]=True
                return dict(estado='chegou',w=False)
        def down(k):
            if k=='tab':
                if sel[0] is not None and hp[sel[0]]>0:tabs_vivos.append(sel[0])
                sel[0]=next((i for i in range(3) if visivel(i)),None)
            elif k=='1' and sel[0] is not None:hp[sel[0]]=max(0,hp[sel[0]]-50)
        def dormir(s):
            tempo[0]+=max(.001,s)
            if sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos)==3 or tempo[0]>60:c.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1;entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_cinzas'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,c)
        self.assertEqual(hp,[0,0,0]);self.assertTrue(visitou_oculto[0]);self.assertFalse(tabs_vivos)
        self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),3)
        self.assertFalse(any(e.get('message')=='Sem alvo proximo; retornando a base.' for e in eventos))

if __name__=='__main__':unittest.main()
