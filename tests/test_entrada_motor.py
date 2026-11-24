import unittest,math,subprocess,sys,importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from tests.test_segundo_plano import User32
from huntingaitan.entrada.entrada_motor import EntradaMotor
from huntingaitan.entrada.ponte_camera import validar_angulos

class PonteFake:
    def __init__(self,d):self.d=d;self.acoes=[];self.resultado=1;self.fechada=False;self.instalada=True;self.incerta=False
    def usar(self,id_):self.acoes.append(('skill',id_));return dict(resultado=self.resultado)
    def selecionar(self):self.acoes.append(('selecionar',))
    def focar(self,alvo):self.acoes.append(('focar',alvo['id']));return dict(resultado=1)
    def girar(self,a):self.acoes.append(('girar',a));self.d.yaw+=math.degrees(a)
    def mover(self,x,y):self.acoes.append(('mover',x,y))
    def close(self):self.fechada=True;self.instalada=False

class DadosFake:
    pid=20;hwnd=10;yaw=0.
    def __init__(self):self.ready=True
    def recargas_atalhos(self):return {'f4':dict(skill=1088,ready=self.ready)}
    def camera_regional(self):return dict(yaw=self.yaw,position=(0,0))
    def snapshot(self):return dict(player=dict(position=(3,4)))

class EntradaTeste(unittest.TestCase):
    def criar(self):
        u=User32();d=DadosFake();e=EntradaMotor(10,20,u);e.conectar(d,PonteFake);return e,d,u
    def test_skill_e_tab_usam_motor_sem_teclas_globais_ou_mensagens_de_teclado(self):
        e,d,u=self.criar();self.assertTrue(e.keyDown('f4'));e.keyUp('f4');e.keyDown('tab');e.keyUp('tab')
        self.assertEqual(e.ponte.acoes,[('skill',1088),('selecionar',)]);self.assertFalse(u.envios)
    def test_recarga_ou_recusa_nao_conta_como_envio(self):
        e,d,u=self.criar();d.ready=False;self.assertFalse(e.keyDown('f4'));self.assertFalse(e.ponte.acoes)
        d.ready=True;e.ponte.resultado=0;self.assertFalse(e.keyDown('f4'))
    def test_item_continua_destinado_apenas_ao_hwnd(self):
        e,d,u=self.criar();e.keyDown('f9');e.keyUp('f9')
        self.assertEqual([x[:3] for x in u.envios],[(10,0x100,120),(10,0x101,120)])
    def test_orienta_por_angulo_lido_e_respeita_parada(self):
        e,d,u=self.criar()
        with patch('huntingaitan.entrada.entrada_motor.time.sleep'):
            self.assertTrue(e.orientar_para((0,10)))
        self.assertLessEqual(abs(d.yaw-90),8);self.assertTrue(all(abs(a[1])<=.15 for a in e.ponte.acoes))
        n=len(e.ponte.acoes);self.assertFalse(e.orientar_para((10,0),lambda:False));self.assertEqual(len(e.ponte.acoes),n)
    def test_finalizar_para_movimento_e_remove_a_ponte(self):
        e,d,u=self.criar();p=e.ponte;e.mover_para((5,4),0);self.assertFalse(e.mover_para((5,4),.1));e.finalizar()
        self.assertEqual(p.acoes,[('mover',5,4),('mover',3,4)]);self.assertTrue(p.fechada);self.assertIsNone(e.ponte)
    def test_clientes_diferentes_sao_recusados(self):
        e=EntradaMotor(10,20,User32());d=DadosFake();d.pid=30
        with self.assertRaisesRegex(RuntimeError,'diferentes'):e.conectar(d,PonteFake)
    def test_angulos_invalidos_sao_recusados(self):
        for a in (float('nan'),float('inf'),.16,-.16):
            with self.assertRaises(ValueError):validar_angulos(a,0)

    def test_recupera_exatamente_o_id_travado_sem_ciclar_tab(self):
        e,d,u=self.criar();self.assertTrue(e.recuperar_alvo(dict(id=2049)))
        self.assertEqual(e.ponte.acoes,[('focar',2049)]);self.assertFalse(u.envios)

    def test_barreira_de_modal_e_parada_bloqueia_todas_as_novas_acoes(self):
        e,d,u=self.criar();e.permitido=lambda:False
        self.assertFalse(e.keyDown('f4'));self.assertFalse(e.keyDown('tab'))
        self.assertFalse(e.orientar_para((1,0)));self.assertFalse(e.recuperar_alvo(dict(id=2049)))
        self.assertFalse(e.mover_para((5,4),1));self.assertFalse(e.ponte.acoes);self.assertFalse(u.envios)

    def test_movimento_em_andamento_nao_e_reiniciado_por_pontos_semelhantes(self):
        e,d,u=self.criar();e.mover_para((10,4),0)
        self.assertFalse(e.mover_para((11,4),.5));self.assertEqual(len(e.ponte.acoes),1)
        self.assertTrue(e.mover_para((11,4),1.6))

    def test_alternativa_validada_pode_substituir_destino_sem_aguardar_timer_antigo(self):
        e,d,u=self.criar();e.mover_para((10,4),0)
        self.assertFalse(e.mover_para((11,4),.5))
        self.assertTrue(e.mover_para((11,4),.5,forcar=True))
        self.assertEqual(e.ponte.acoes,[('mover',10,4),('mover',11,4)])

    def test_validacao_recusa_regra_de_outra_habilidade(self):
        e,d,u=self.criar()
        p=dict(attack_key='f4',reacoes=[dict(ativa=True,skill_id=170,tecla='f4',nome='Buff errado')],buff_keys=[])
        with self.assertRaisesRegex(ValueError,'Buff errado em f4'):e.validar_regras(p)
        self.assertFalse(e.ponte.acoes)

    def test_validacao_atualiza_nivel_da_mesma_habilidade(self):
        e,d,u=self.criar()
        p=dict(attack_key='f4',reacoes=[dict(ativa=True,skill_id=1073,tecla='f4',nome='Cura')],buff_keys=[])
        self.assertEqual(e.validar_regras(p),[])
        self.assertEqual(p['reacoes'][0]['skill_id'],1088)

    def test_buff_vazio_nao_e_contado_como_enviado(self):
        e,d,u=self.criar();d.tipos_atalhos={'f5':0}
        p=dict(attack_key='f4',reacoes=[],buff_keys=['f5'])
        self.assertIn('f5 vazio',e.validar_regras(p)[0]);self.assertEqual(p['buff_keys'],[''])
        self.assertFalse(e.keyDown('f5'));self.assertEqual(e.ultima_resposta['motivo'],'slot_vazio')
        self.assertFalse(u.envios);self.assertFalse(e.ponte.acoes)

@unittest.skipUnless(importlib.util.find_spec('unicorn') and importlib.util.find_spec('keystone'),'Emulador x86 opcional nao instalado')
class EmulacaoTeste(unittest.TestCase):
    def test_ponte_preserva_estado_e_restaura_procedimento_original(self):
        raiz=Path(__file__).resolve().parents[1]
        r=subprocess.run([sys.executable,str(raiz/'tools/testar_ponte_emulador.py')],cwd=raiz,capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
