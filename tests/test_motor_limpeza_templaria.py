import copy,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.configuracao.perfil_hunt import DEFAULT
from huntingaitan.rotas.navegacao_grade import Grade

class MotorLimpezaTeste(unittest.TestCase):
    def executar(self,negar_ate=0,modo='termes_verit_leste'):
        import huntingaitan.combate.hunt_native as h
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode=modo,background_keys=True,client_pid=20,client_hwnd=10,
            buffs_enabled=False,extra_buffs_enabled=False,f3_enabled=False,heal_enabled=False,hp_keys=['','',''],reacoes=[])
        for v in p['skills']:v['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];alvo=[None];eventos=[];golpes=[];movimentos=[]
        cinzas=modo=='cinzenta_croshu_trio'
        pos=(2882.5,1154.5) if cinzas else (2903.5,820.5)
        def mob(id_,x,tipo):return dict(id=id_,ref=id_,name='Verit Mutante' if tipo==1378 else 'Banzul Dentes Flamejantes',template_id=tipo,position=(x,820.5),height=0,hp=100,hp_max=100,hostile=True)
        mobs=[mob(8001,2904,1244),mob(8002,2905,1244),mob(8003,2905.5,1378)]
        if cinzas:
            for i,m in enumerate(mobs):m.update(name='Croshu Mutante das Cinzas',template_id=1376,position=(2883.5+i*.4,1154.5))
        class Dados:
            pid=20;hwnd=10;caminho=Path('AIKACL.exe');tipos_atalhos={}
            def snapshot(self):return dict(player=dict(name='Templaria',position=pos,heading=0,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo[0])
            def estados_controle(self):return dict(normal_skill=1 if cinzas else 961,normal_ready=True)
            def recargas_atalhos(self):return {'1':dict(skill=1 if cinzas else 961,cooldown=0,ready=True)}
            def listar_mobs(self,*args):return [m.copy() for m in mobs if m['hp']>0]
            def entidade(self,ref):return next((m.copy() for m in mobs if m['id']==ref),None)
            def caca_original_ativa(self):return False
            def close(self):pass
        class Entrada:
            PAUSE=0
            def __init__(self,*a):self.ultima_resposta={}
            def conectar(self,*a):pass
            def validar_regras(self,*a):return []
            def disponivel(self):return True
            def recuperar_alvo(self,m):alvo[0]=next(x for x in mobs if x['id']==m['id']);return True
            def keyDown(self,k,_pause=False):
                if k=='1' and alvo[0] and alvo[0]['id']==8003 and tempo[0]<negar_ate:
                    self.ultima_resposta=dict(motivo='recusado_pelo_cliente');return False
                if k=='1' and alvo[0] and alvo[0]['hp']>0:
                    golpes.append(alvo[0]['id']);alvo[0]['hp']=max(0,alvo[0]['hp']-50)
                return True
            def keyUp(self,*a):return True
            def mover_para(self,*a):
                movimentos.append([m['hp'] for m in mobs]);c.stop.set();return True
            def parar_movimento(self):pass
            def finalizar(self):pass
        grade=Grade((2860,1130) if cinzas else (2880,800),(0,0),60,60,bytes(3600),(0,)*3600,1)
        class Nav:
            def __init__(self,**kw):self.grade=grade;self.grade_em=1000;self.leitor=lambda *a:grade
            def invalidar(self):pass
            def suspender(self,*a):pass
            def planejar(self,*a,**kw):
                if a[4][0]=='recuperar_ataque':return dict(estado='chegou',w=False)
                return dict(estado='andando',w=True,ponto=pos,pontos=2,erro=0)
        class Monitor:
            def __init__(self,*a,**kw):self.b=kw['bloqueio']
            def iniciar(self):self.b.clear()
            def atual(self):return None
        def dormir(t):
            tempo[0]+=max(t,.001)
            if tempo[0]>60:c.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=99
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=SimpleNamespace(keyDown=lambda k:None)),\
            patch('huntingaitan.entrada.entrada_motor.EntradaMotor',Entrada),patch.object(h,'DadosInternos',Dados),\
            patch.object(h,'NavegadorLocal',Nav),patch.object(h,'ObservadorAvisos',Monitor),patch.object(h,'conferir_leste'),patch.object(h,'conferir_cinzas'),\
            patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),\
            patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):
            h.main(p,eventos.append,c)
        self.assertTrue(golpes);self.assertEqual(golpes[0],8001 if cinzas else 8003)
        self.assertEqual({m['id'] for m in mobs if m['hp']==0},{8001,8002,8003})
        self.assertTrue(movimentos);self.assertTrue(all(hp==0 for hp in movimentos[0]))
        self.assertEqual(next(e for e in eventos if e['event']=='session_summary')['abates'],3)
        return eventos

    def test_mata_mutante_primeiro_limpa_os_proximos_e_so_entao_avanca(self):self.executar()

    def test_verit_proximo_recusado_por_doze_segundos_nao_e_abandonado(self):
        eventos=self.executar(12)
        self.assertFalse(any('ignorad' in e.get('message','') or 'Alvo sem dano; procurando' in e.get('message','') for e in eventos))

    def test_proximo_alvo_e_selecionado_no_ciclo_da_morte_confirmada(self):
        eventos=self.executar()
        trocas=[e for e in eventos if e['event']=='target_handoff']
        self.assertEqual(len(trocas),2)
        self.assertEqual({e['target_id'] for e in trocas},{8001,8002})
        self.assertTrue(all(e['latencia_ms']<1 for e in trocas))

    def test_croshus_usam_as_mesmas_trocas_sem_ativar_limpeza_da_templaria(self):
        eventos=self.executar(modo='cinzenta_croshu_trio')
        self.assertEqual(len([e for e in eventos if e['event']=='target_handoff']),2)
        self.assertFalse(any(e.get('message','').startswith('Limpeza curta') for e in eventos))
