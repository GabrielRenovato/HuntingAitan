import copy,hashlib,json,math,sys,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from circuito_verit import CircuitoVerit,dentro_verit,plano_verit,conferir_verit
from perfil_hunt import validar,DEFAULT
from hunt_native import alvo_permitido

class CircuitoVeritTeste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()

    def test_perfil_forca_verit_sem_alterar_modo_antigo(self):
        p=validar(dict(patrol_mode='termes_verit',target='qualquer',data_source='visual'))
        self.assertEqual((p['target'],p['data_source']),('verit','native'))
        self.assertEqual(validar({})['patrol_mode'],'base')
        self.assertEqual(validar(dict(patrol_mode='termes_penza'))['target'],'penza')

    def test_loop_contem_so_os_oito_pontos_marcados(self):
        d=plano_verit();self.assertEqual([p['id'] for p in d['pontos']],[1,5,20,18,4,19,2,3])
        self.assertEqual([t['ate'] for t in d['trechos']],[5,20,18,4,19,2,3,1])
        for i,t in enumerate(d['trechos']):
            self.assertLessEqual(math.dist(t['caminho'][0],d['pontos'][i]['pos']),1)
            self.assertLessEqual(math.dist(t['caminho'][-1],d['pontos'][(i+1)%8]['pos']),1)
            self.assertTrue(all(dentro_verit(p) for p in t['caminho']))
            self.assertTrue(all(math.dist(a,b)<=math.sqrt(2)+1e-6 for a,b in zip(t['caminho'],t['caminho'][1:])))

    def test_fecha_duas_voltas_com_paradas_e_retomada(self):
        c=CircuitoVerit((2748,833));agora=0
        for _ in range(2):
            for i,t in enumerate(plano_verit()['trechos']):
                fim=t['caminho'][-1]
                self.assertEqual(c.destino(fim,agora)['estado'],'aguardar')
                self.assertEqual(c.destino(fim,agora+4.9)['estado'],'aguardar')
                c.destino(fim,agora+5);self.assertEqual(c.trecho,(i+1)%8);agora+=6
        self.assertEqual(c.voltas,2)
        c=CircuitoVerit((2748,833));fim=c.trechos[0]['caminho'][-1]
        c.destino(fim,0);c.pausar(10)
        self.assertEqual(c.destino(fim,14)['estado'],'aguardar')
        c.destino(fim,15);self.assertEqual(c.trecho,1)

    def test_entrada_perto_de_qualquer_trecho_sem_voltar_ao_primeiro(self):
        for t in plano_verit()['trechos']:
            pos=t['caminho'][len(t['caminho'])//2];c=CircuitoVerit(pos)
            self.assertEqual(c.trechos[c.trecho]['ate'],t['ate'])
        with self.assertRaises(RuntimeError):CircuitoVerit((2584,587))

    def test_filtro_exclui_penza_npc_verit_distante_e_fora_da_rota(self):
        p=validar(dict(patrol_mode='termes_verit',radius=50));player=dict(position=(2748,833),height=0)
        m=dict(position=(2779,844),height=0,hp=100,hostile=True,name='Verit Mutante')
        self.assertTrue(alvo_permitido(m,player,(0,0),p))
        for campos in [dict(name='Penza Poderosa Mutante'),dict(hostile=False),dict(hp=0),dict(height=8),dict(position=(2864,821)),dict(position=(2705,922))]:
            self.assertFalse(alvo_permitido(dict(m,**campos),player,(0,0),p))

    def test_hashes_recusam_arquivos_alterados(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'terreno';p.write_bytes(b'original')
            with patch('circuito_verit.plano_verit',return_value=dict(fontes={'terreno':hashlib.sha256(b'original').hexdigest()})):
                conferir_verit(td);p.write_bytes(b'mudou')
                with self.assertRaises(RuntimeError):conferir_verit(td)

    def motor(self,bloqueado=False):
        import hunt_native as h
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='termes_verit',radius=50,buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];pos=[(2748.5,833.5)];hp=[100];selecionado=[False];eventos=[];navs=[];inputs=[]
        def mob():return dict(ref=1,id=4093,name='Verit Mutante',position=(2779.5,844.5),height=0,hp=hp[0],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob() if selecionado[0] else None)
            def listar_mobs(self,*args):return [mob()] if math.dist(pos[0],(2748.5,833.5))>5 and hp[0]>0 else []
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kw):
                destino=args[3];navs.append((tempo[0],destino,hp[0]))
                if bloqueado:return dict(estado='sem_caminho',w=False)
                pos[0]=destino
                if hp[0]==0:c.stop.set()
                return dict(estado='andando',w=True,erro=0,pontos=5)
        def down(k):
            inputs.append((tempo[0],k,hp[0]))
            if k=='tab':selecionado[0]=True
            if k=='1' and selecionado[0]:hp[0]=max(0,hp[0]-50)
        def dormir(t):
            tempo[0]+=max(t,.001)
            if tempo[0]>30:c.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_verit'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,c)
        return eventos,navs,inputs,hp[0]

    def test_motor_percorre_mata_verit_e_retoma_com_alvo_mantido(self):
        eventos,navs,inputs,hp=self.motor()
        self.assertEqual(hp,0)
        self.assertTrue(any(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos))
        self.assertTrue(any(vida==0 for _,_,vida in navs))
        self.assertEqual(sum(k=='tab' for _,k,_ in inputs),1)
        self.assertFalse(any(k=='tab' and 0<vida<100 for _,k,vida in inputs))
        self.assertTrue(any(e.get('target')=='Verit Mutante' for e in eventos))

    def test_motor_nao_avanca_ponto_sem_passagem(self):
        eventos,navs,inputs,hp=self.motor(True)
        self.assertTrue(navs);self.assertEqual(len(set(d for _,d,_ in navs)),1)
        self.assertFalse(inputs)
        self.assertTrue(all(e['ponto']==5 for e in eventos if 'ponto' in e))

if __name__=='__main__':unittest.main()
