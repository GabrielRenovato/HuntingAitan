import copy,math,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.rotas.circuito_cinzas import plano_cinzas,dentro_cinzas
from huntingaitan.rotas.circuito_cinzas_sul import CircuitoCinzasSul,plano_cinzas_sul,dentro_cinzas_sul
from huntingaitan.combate.hunt_native import alvo_permitido

class CircuitoSulTeste(unittest.TestCase):
    def test_modos_independentes_preservam_perfil_e_rota_anterior(self):
        original=copy.deepcopy(DEFAULT)
        p=validar(dict(original,patrol_mode='cinzenta_croshu_sul',client_pid=55,client_hwnd=66))
        self.assertEqual((p['base'],p['target'],p['radius'],p['auto_base']),([2955,1311],'croshu',50,False))
        for k in ('skills','buff_keys','heal_key','hp_percent','client_pid','client_hwnd'):
            self.assertEqual(p[k],dict(original,client_pid=55,client_hwnd=66)[k])
        self.assertEqual([x['id'] for x in plano_cinzas()['pontos']],[7,8,9,11,10])
        self.assertFalse(dentro_cinzas((2955,1311)));self.assertFalse(dentro_cinzas_sul((2882,1154)))
        with self.assertRaises(RuntimeError):CircuitoCinzasSul((2882,1154))

    def test_seis_pontos_sao_elegiveis_sem_aceitar_especie_errada(self):
        p=validar(dict(patrol_mode='cinzenta_croshu_sul'))
        self.assertEqual([x['id'] for x in plano_cinzas_sul()['pontos']],[6,2,1,3,5,4])
        for ponto in plano_cinzas_sul()['pontos']:
            player=dict(position=ponto['pos'],height=0)
            alvo=dict(position=ponto['pos'],height=0,hp=10,hostile=True,name='Croshu Mutante das Cinzas')
            self.assertTrue(alvo_permitido(alvo,player,p['base'],p))
            self.assertFalse(alvo_permitido(dict(alvo,name='Croshu das Cinzas'),player,p['base'],p))
            self.assertFalse(alvo_permitido(dict(alvo,hostile=False),player,p['base'],p))

    def test_duas_voltas_conferem_os_seis_pontos_antes_de_repetir(self):
        c=CircuitoCinzasSul((2955,1311));visitados=[]
        for i in range(12):
            t=c.trechos[c.trecho];fim=t['caminho'][-1];visitados.append(t['ate'])
            self.assertEqual(c.destino(fim,i*6)['estado'],'aguardar')
            c.destino(fim,i*6+5.1)
        self.assertEqual(visitados,[2,1,3,5,4,6]*2);self.assertEqual(c.voltas,2)

    def test_motor_visita_e_abate_os_seis_pela_ponte_sem_teclado_global(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='cinzenta_croshu_sul',background_keys=True,client_pid=20,client_hwnd=1,buffs_enabled=False,extra_buffs_enabled=False,f3_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for skill in p['skills']:skill['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        tempo=[0.];pos=[(2955.,1311.)];hp=[100]*6;sel=[None];eventos=[];movimentos=[]
        locais=[x['pos'] for x in plano_cinzas_sul()['pontos']]
        def mob(i):return dict(ref=0x100000+i,id=9000+i,name='Croshu Mutante das Cinzas',position=locais[i],height=0,hp=hp[i],hp_max=100,hostile=True)
        def visivel(i):return hp[i]>0 and math.dist(pos[0],locais[i])<15
        class Dados:
            pid=20;hwnd=1;caminho=Path('AIKACL.exe');tipos_atalhos={}
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob(sel[0]) if sel[0] is not None else None)
            def listar_mobs(self,*args):return [mob(i) for i in range(6) if visivel(i)]
            def entidade(self,ref):return mob(ref-0x100000)
            def cena_validada(self):return 1
            def caca_original_ativa(self):return False
            def estados_controle(self):return dict(normal_skill=961,normal_ready=True)
            def recargas_atalhos(self):return {'1':dict(skill=961,cooldown=0,ready=True)}
            def close(self):pass
        class Entrada:
            PAUSE=0
            def __init__(self,*a):self.ultima_resposta={}
            def conectar(self,*a):pass
            def validar_regras(self,*a):return []
            def disponivel(self):return True
            def recuperar_alvo(self,m):sel[0]=m['ref']-0x100000;return True
            def keyDown(self,k,_pause=False):
                if k=='1' and sel[0] is not None:hp[sel[0]]=max(0,hp[sel[0]]-50)
                return True
            def keyUp(self,*a):return True
            def mover_para(self,ponto,*a,**kw):movimentos.append(ponto);pos[0]=tuple(ponto);return True
            def parar_movimento(self):pass
            def finalizar(self):pass
        from huntingaitan.rotas.navegacao_grade import Grade
        grade=Grade((2840,1290),(0,0),220,140,bytes(220*140),(0,)*(220*140),1)
        class Nav:
            def __init__(self,**kw):self.grade=grade;self.grade_em=1000;self.leitor=lambda *a:grade
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kwargs):return dict(estado='andando',w=True,ponto=tuple(args[3]),pontos=2,erro=0)
        class Monitor:
            def __init__(self,*a,**kw):self.b=kw['bloqueio']
            def iniciar(self):self.b.clear()
            def atual(self):return None
        def dormir(s):
            tempo[0]+=max(.001,s)
            if sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos)==6 or tempo[0]>240:c.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=99
        global_bloqueado=SimpleNamespace(keyDown=lambda *a,**kw:self.fail('Teclado global acionado no circuito por threads'))
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=global_bloqueado),patch('huntingaitan.entrada.entrada_motor.EntradaMotor',Entrada),patch.object(h,'ObservadorAvisos',Monitor),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_cinzas_sul'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,c)
        self.assertEqual(hp,[0]*6);self.assertTrue(movimentos)
        self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),6)
