import copy,math,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.combate.hunt_native import alvo_permitido
from huntingaitan.rotas.circuito_croshu import CircuitoCroshu,plano_croshu,dentro_croshu
from huntingaitan.rotas.circuito_termes import distancia_segmento
from huntingaitan.rotas.evitar_mobs import aplicar_zonas
from huntingaitan.rotas.navegacao_grade import Grade


class CircuitoCroshuTest(unittest.TestCase):
    def test_perfil_fixa_especie_sem_mudar_cliente_ou_atalhos(self):
        p=validar(dict(patrol_mode='ungor_croshu',client_pid=200,client_hwnd=20))
        self.assertEqual((p['target'],p['base'],p['auto_base'],p['radius']),('croshu_ungor',[1895,1155],False,50))
        self.assertEqual((p['client_pid'],p['client_hwnd']),(200,20));self.assertEqual(p['skills'],DEFAULT['skills'])

    def test_trechos_fecham_volta_sem_cinco_e_afastam_menores(self):
        d=plano_croshu();self.assertEqual([(t['de'],t['ate']) for t in d['trechos']],[(6,3),(3,7),(7,6)])
        centros=[m['pos'] for m in d['menores']];self.assertEqual(len(centros),31)
        for t in d['trechos']:
            for a,b in zip(t['caminho'],t['caminho'][1:]):
                self.assertLessEqual(math.dist(a,b),math.sqrt(2)+1e-6)
                self.assertTrue(all(distancia_segmento(c,a,b)>10 for c in centros))
        with self.assertRaisesRegex(RuntimeError,'ponto 5'):CircuitoCroshu((1933,1183))
        c=CircuitoCroshu((1895,1155));visitados=[]
        for i in range(3):
            t=c.trechos[c.trecho];fim=t['caminho'][-1];visitados.append(t['ate'])
            self.assertEqual(c.destino(fim,i*6)['estado'],'aguardar');c.destino(fim,i*6+5.1)
        self.assertEqual(visitados,[3,7,6]);self.assertEqual(c.voltas,1)

    def test_so_tres_mutantes_elegiveis_sem_menores_e_sem_ponto_cinco(self):
        p=validar(dict(patrol_mode='ungor_croshu'))
        pontos=[(1954,1138),(1934,1152),(1901,1166),(1952,1186),(1933,1183),(1895,1155),(1950,1127)]
        def alvo(pos,nome='Cão Mutante Croshu'):return dict(position=pos,height=0,hp=100,hostile=True,name=nome)
        aceitos=[i+1 for i,pos in enumerate(pontos) if alvo_permitido(alvo(pos),dict(position=pos,height=0),p['base'],p)]
        self.assertEqual(aceitos,[3,6,7])
        for nome in ['Croshu Cinzento','Croshu Canino','Croshu Mutante das Cinzas']:
            self.assertFalse(alvo_permitido(alvo((1895,1155),nome),dict(position=(1895,1155),height=0),p['base'],p))

    def test_mascara_nao_apaga_colisao_nativa_e_bloqueia_menor_movel(self):
        flags=bytearray(40*40);flags[39*40+39]=1
        grade=Grade((0,0),(0,0),40,40,bytes(flags),tuple([0]*1600),1)
        nova=aplicar_zonas(grade,[(20,20)],5,saida=(2,2))
        self.assertTrue(grade.livre((20,20)));self.assertFalse(nova.livre((20,20)))
        self.assertFalse(nova.livre((39,39)));self.assertTrue(nova.livre((2,2)))
        c=CircuitoCroshu((1895,1155));self.assertTrue(c.permite((1895,1155)))
        c.atualizar_menores([dict(name='Croshu Canino',position=(1895,1155),hp=100)])
        self.assertFalse(c.permite((1895,1155)))
        c.atualizar_menores([]);self.assertTrue(c.permite((1895,1155)))

    def test_motor_circula_mata_respawn_e_aplica_desvio_ao_planejamento(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='ungor_croshu',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];pos=[(1895.,1155.)]
        hp=[100]*3;sel=[None];onda=[0];eventos=[];trocas_vivo=[];mascaras=[]
        locais=[tuple(p['pos']) for p in plano_croshu()['pontos']]
        menor=dict(ref=99,id=8800,name='Croshu Canino',position=(1876,1140),height=0,hp=100,hp_max=100,hostile=True)
        def mob(i):return dict(ref=0x100000+i,id=9000+onda[0]*3+i,name='Cão Mutante Croshu',position=locais[i],height=0,hp=hp[i],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob(sel[0]) if sel[0] is not None else None)
            def listar_mobs(self,*args):return [menor]+[mob(i) for i in range(3) if hp[i]>0]
            def entidade(self,ref):return mob(ref-0x100000)
            def cena_validada(self):return 1
            def close(self):pass
        grade=Grade((0,0),(1830,1080),180,180,bytes(180*180),tuple([0]*(180*180)),1)
        class Nav:
            def __init__(self,leitor=None):self.leitor=leitor
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,dados,atual,heading,destino,chave,agora,**kw):
                g=self.leitor(dados,atual);mascaras.append(not g.livre(g.celula(menor['position'])))
                if not kw['limite'](destino):return dict(estado='sem_caminho',w=False)
                pos[0]=tuple(destino);return dict(estado='chegou',w=False)
        def down(k):
            if k=='tab':
                if sel[0] is not None and hp[sel[0]]>0:trocas_vivo.append(sel[0])
                sel[0]=next((i for i in range(3) if hp[i]>0),None)
            if k=='1' and sel[0] is not None:hp[sel[0]]=max(0,hp[sel[0]]-50)
        def dormir(s):
            tempo[0]+=max(.001,s)
            if onda[0]==0 and any(e.get('patrol_laps',0)>=1 for e in eventos if e.get('event')=='telemetry'):
                onda[0]=1;hp[:]=[100]*3;sel[0]=None
            if sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos)>=6 or tempo[0]>100:control.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1;entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_croshu'),patch('huntingaitan.rotas.navegacao_grade.ler_grade',return_value=grade),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,control)
        self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),6)
        self.assertFalse(trocas_vivo);self.assertTrue(mascaras);self.assertTrue(all(mascaras))
        self.assertTrue(any(e.get('patrol_laps',0)>=1 for e in eventos if e.get('event')=='telemetry'))
