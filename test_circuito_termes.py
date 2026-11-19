import copy,hashlib,json,math,sys,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from circuito_termes import CircuitoTermes,dentro_regiao,plano,conferir_arquivos
from perfil_hunt import validar,DEFAULT
from hunt_native import alvo_permitido
from test_navegacao_grade import grade


class CircuitoTermesTeste(unittest.TestCase):
    def test_perfil_antigo_preserva_caca_na_base_e_circuito_fixa_penza(self):
        self.assertEqual(validar({})['patrol_mode'],'base')
        self.assertEqual(validar(dict(patrol_mode='termes_penza',target='qualquer'))['target'],'penza')
        with self.assertRaises(ValueError):validar(dict(patrol_mode='desconhecido'))

    def test_penza_na_faixa_pode_ficar_longe_da_base_original(self):
        p=validar(dict(patrol_mode='termes_penza',radius=50))
        player=dict(position=(2584,650),height=0)
        mob=dict(position=(2584,712),height=0,hp=100,hostile=True,name='Penza Poderosa Mutante')
        # Distancia ao player >50: nao deve tentar selecionar.
        self.assertFalse(alvo_permitido(mob,player,(2584,587),p))
        player['position']=(2584,690)
        self.assertTrue(alvo_permitido(mob,player,(2584,587),p))
        mob['name']='Verit Mutante';self.assertFalse(alvo_permitido(mob,player,(2584,587),p))
        mob.update(name='Penza Poderosa Mutante',position=(2640,690))
        self.assertFalse(alvo_permitido(mob,dict(position=(2640,680),height=0),(2584,587),p))

    def test_tracado_tem_ida_volta_e_celulas_dentro_da_regiao(self):
        d=plano();self.assertEqual([t['ate'] for t in d['trechos']],[5,4,7,8,9,8,7,4,5,6])
        for t in d['trechos']:
            self.assertTrue(all(dentro_regiao(p) for p in t['caminho']))
            self.assertTrue(all(math.dist(a,b)<=math.sqrt(2)+1e-6 for a,b in zip(t['caminho'],t['caminho'][1:])))

    def test_espera_cinco_segundos_e_fecha_volta_sem_reiniciar_no_combate(self):
        c=CircuitoTermes((2584,587));agora=0
        for i in range(len(plano()['trechos'])):
            fim=plano()['trechos'][i]['caminho'][-1]
            self.assertEqual(c.destino(fim,agora)['estado'],'aguardar')
            self.assertEqual(c.destino(fim,agora+4.9)['estado'],'aguardar')
            c.destino(fim,agora+5)
            self.assertEqual(c.trecho,(i+1)%len(plano()['trechos']));agora+=6
        self.assertEqual(c.voltas,1)
        c=CircuitoTermes((2585,654));trecho=c.trecho
        c.destino((2580,665),10)  # deslocamento durante uma luta
        self.assertEqual(c.trecho,trecho)
        self.assertGreater(c.destino((2580,665),11)['destino'][1],654)

    def test_recusa_inicio_fora_da_regiao(self):
        with self.assertRaises(RuntimeError):CircuitoTermes((2785,837))

    def test_pausa_nao_consome_os_cinco_segundos_de_busca(self):
        c=CircuitoTermes((2584,587));fim=plano()['trechos'][0]['caminho'][-1]
        c.destino(fim,0);c.pausar(10)
        self.assertEqual(c.destino(fim,12)['estado'],'aguardar')
        self.assertEqual(c.trecho,0)
        c.destino(fim,15);self.assertEqual(c.trecho,1)

    def test_deslocamento_para_tras_reencontra_mesmo_trecho(self):
        c=CircuitoTermes((2584,610));trecho=c.trecho
        c.destino((2584,640),0)
        for t in range(5):
            passo=c.destino((2590,638),t+1)
            self.assertEqual(c.trecho,trecho)
            self.assertEqual(passo['estado'],'andar')
            self.assertTrue(dentro_regiao(passo['destino']))

    def test_colisao_respeita_limite_de_corredor(self):
        g=grade(9,7,[(4,y) for y in range(4)])
        rota=g.caminho((1.5,2.5),(7.5,2.5),limite=lambda p:1<=p[1]<=5)
        self.assertTrue(rota)
        self.assertTrue(all(1<=p[1]<=5 for p in rota))
        self.assertTrue(all(g.passagem(g.celula(a),g.celula(b)) for a,b in zip(rota,rota[1:])))
        self.assertIsNone(g.caminho((1.5,2.5),(7.5,2.5),limite=lambda p:1<=p[1]<=3))

    def test_arquivos_alterados_invalidam_tracado(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'terreno';p.write_bytes(b'original')
            with patch('circuito_termes.plano',return_value=dict(fontes={'terreno':hashlib.sha256(b'original').hexdigest()})):
                conferir_arquivos(td)
                p.write_bytes(b'alterado')
                with self.assertRaises(RuntimeError):conferir_arquivos(td)

    def executar_motor(self,bloqueado=False):
        import hunt_native as h
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='termes_penza',radius=50,buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        ctrl=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];pos=[(2584.5,587.5)];hp=[100];selecionado=[False];eventos=[];navs=[];inputs=[]
        def mob():return dict(ref=1,id=4093,name='Penza Poderosa Mutante',position=(2584.5,607.5),height=0,hp=hp[0],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob() if selecionado[0] else None)
            def listar_mobs(self,*args):return [mob()] if pos[0][1]>=600 and hp[0]>0 else []
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kw):
                destino=args[3];navs.append((tempo[0],destino,hp[0]))
                if bloqueado:return dict(estado='sem_caminho',w=False)
                pos[0]=destino
                if hp[0]==0 and pos[0][1]>673:ctrl.stop.set()
                return dict(estado='andando',w=True,erro=0,pontos=5)
        def down(k):
            inputs.append((tempo[0],k,hp[0]))
            if k=='tab':selecionado[0]=True
            if k=='1' and selecionado[0]:hp[0]=max(0,hp[0]-50)
        def dormir(t):
            tempo[0]+=max(t,.001)
            if tempo[0]>30:ctrl.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_arquivos'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):
            h.main(p,eventos.append,ctrl)
        return eventos,navs,inputs,hp[0]

    def test_motor_percorre_mata_penza_e_continua_sem_tab_durante_luta(self):
        eventos,navs,inputs,hp=self.executar_motor()
        self.assertEqual(hp,0)
        self.assertTrue(any(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos))
        self.assertTrue(any(dest[1]>673 and vida==0 for _,dest,vida in navs))
        self.assertEqual(sum(k=='tab' for _,k,_ in inputs),1)
        self.assertFalse(any(k=='tab' and 0<vida<100 for _,k,vida in inputs))

    def test_motor_nao_pula_ponto_nem_envia_movimento_sem_passagem(self):
        eventos,navs,inputs,hp=self.executar_motor(bloqueado=True)
        self.assertTrue(navs)
        self.assertEqual(len(set(dest for _,dest,_ in navs)),1)
        self.assertFalse(inputs)
        self.assertTrue(any(e.get('message','').startswith('Passagem do circuito indisponivel') for e in eventos))
        self.assertTrue(all(e.get('ponto')==5 for e in eventos if 'ponto' in e))


if __name__=='__main__':unittest.main()
