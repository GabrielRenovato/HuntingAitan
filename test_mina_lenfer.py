import copy,json,math,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from mina_lenfer import MinaLenfer,plano_mina,dentro_mina
from perfil_hunt import validar,DEFAULT
from test_navegacao_grade import grade

class MinaTeste(unittest.TestCase):
    def test_ulman_abatido_nao_conclui_objetivo_malik(self):
        m=MinaLenfer((2850,3344));pos=m.pontos[-1]['pos']
        self.assertIsNone(m.registrar_abate(1,'Ulman Super Fisico',pos,0))
        self.assertEqual(m.destino(pos,100)['estado'],'aguardar_chefe')
        self.assertFalse(m.concluida)

    def test_malik_recebe_prioridade_sobre_hostis_do_caminho(self):
        m=MinaLenfer((2850,3344));m.grade=grade(12,8);m.rota_planejada=[(1.5,1.5),(10.5,1.5)]
        mobs=[dict(id=1,name='Soldado',position=(3.5,1.5)),dict(id=2,name='Malik',position=(7.5,1.5))]
        self.assertEqual([v['id'] for v in m.filtrar_mobs(mobs,(1.5,1.5),10)],[2])

    def test_modo_fixa_dados_nativos_e_alvos_hostis(self):
        p=validar(dict(patrol_mode='mina_lenfer',target='verit',data_source='visual'))
        self.assertEqual((p['target'],p['data_source']),('qualquer','native'))

    def test_inicio_requer_primeira_area(self):
        MinaLenfer((2850.4,3344.4))
        MinaLenfer((2918,3386))
        for p in [(2585,674),(0,0)]:
            with self.assertRaises(RuntimeError):MinaLenfer(p)

    def test_rota_cobre_setores_e_passos_adjuntos(self):
        d=plano_mina();self.assertEqual(len(d['trechos']),1)
        self.assertEqual([p['chefe'] for p in d['pontos'] if p['chefe']],['malik'])
        for t in d['trechos']:
            self.assertTrue(all(dentro_mina(p) for p in t['caminho']))
            self.assertTrue(all(math.dist(a,b)<=math.sqrt(2)+1e-6 for a,b in zip(t['caminho'],t['caminho'][1:])))

    def test_chefe_ausente_nao_avanca_sala_nem_registra_conclusao(self):
        m=MinaLenfer((2850,3344));m.trecho=next(i for i,p in enumerate(m.pontos) if p['chefe']=='malik');p=m.pontos[m.trecho]
        for t in [0,60,600]:self.assertEqual(m.destino(p['pos'],t)['estado'],'aguardar_chefe')
        self.assertFalse(m.concluida)

    def test_fim_exige_malik_confirmado_e_area_final_limpa(self):
        m=MinaLenfer((2850,3344));m.trecho=len(m.pontos)-1;p=m.pontos[-1]['pos']
        self.assertEqual(m.registrar_abate(10,'Malik',p,0),'malik')
        self.assertEqual(m.destino(p,0)['estado'],'aguardar')
        m.combate_ativo()  # nova fase ou outro mob: recomeca a verificacao
        self.assertEqual(m.destino(p,10)['estado'],'aguardar')
        m.pausar(5)
        self.assertNotEqual(m.destino(p,29)['estado'],'concluido')
        self.assertEqual(m.destino(p,30)['estado'],'concluido')

    def test_outros_nomes_nao_confirmam_malik(self):
        m=MinaLenfer((2850,3344));p=m.pontos[-1]['pos']
        self.assertIsNone(m.registrar_abate(1,'Soldado',p,0))
        self.assertIsNone(m.registrar_abate(2,'Guarda-Costas do Malik',p,0))
        self.assertFalse(m.abates)

    def test_filtro_nao_puxa_mob_atras_de_parede_por_distancia_reta(self):
        m=MinaLenfer((2850,3344));m.grade=grade(12,8,[(5,y) for y in range(7)])
        m.rota_planejada=[(1.5,1.5),(10.5,1.5)]
        mobs=[dict(id=1,name='Soldado',position=(3.5,1.5)),dict(id=2,name='Soldado',position=(7.5,1.5))]
        self.assertEqual([v['id'] for v in m.filtrar_mobs(mobs,(1.5,1.5),8)],[1])

    def test_motor_confirma_abates_antes_de_finalizar(self):
        import hunt_native as h
        d=dict(limites=[2816,3328,3072,3584],entrada=[2850,3344],pontos=[],trechos=[])
        for i,(chefe,nome) in enumerate([('malik','Malik')]):
            pos=(2854.5+i*4,3344.5);d['pontos'].append(dict(id=i,pos=pos,chefe=chefe,espera=15));d['trechos'].append(dict(ate=i,caminho=[(2850.5,3344.5),pos]))
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='mina_lenfer',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];pos=[(2850.5,3344.5)];vida=[100];selecionado=[None];events=[];keys=[]
        def alvo(i):return dict(ref=i+1,id=3000+i,name=['Malik'][i],position=d['pontos'][i]['pos'],height=0,hp=vida[i],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo(selecionado[0]) if selecionado[0] is not None else None)
            def cena_validada(self):return 1
            def u32(self,*a):return 30005
            def listar_mobs(self,*a):return [alvo(i) for i in range(1) if vida[i]>0]
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):pos[0]=a[3];return dict(estado='andando',w=True,erro=0,pontos=5)
        def down(k):
            keys.append(k)
            if k=='tab':selecionado[0]=next((i for i in range(1) if vida[i]>0),None)
            if k=='1' and selecionado[0] is not None:vida[selecionado[0]]=0
        def sleep(v):
            t[0]+=max(.001,v)
            if t[0]>60:control.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch('mina_lenfer.plano_mina',return_value=d),patch.object(MinaLenfer,'conferir'),patch.object(MinaLenfer,'filtrar_mobs',side_effect=lambda mobs,*a:mobs),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',sleep):
            h.main(p,events.append,control)
        self.assertEqual(vida,[0]);self.assertEqual(keys.count('tab'),1)
        self.assertTrue(any(e.get('event')=='dungeon_complete' for e in events))
        self.assertEqual(len([e for e in events if e.get('message')=='Chefe da Mina abatido com vida zero confirmada.']),1)

if __name__=='__main__':unittest.main()
