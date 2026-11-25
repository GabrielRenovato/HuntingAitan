import copy,sys,threading,unittest
import numpy,cv2
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.combate.confirmacao_reacao import ConfirmacaoReacao
from huntingaitan.combate.reacoes import validar_regra

def cura():return validar_regra(dict(nome='Remediar',tecla='f2',tipo='cura',skill_id=1088,hp_max_pct=70,mp_min=1497,intervalo_s=2.5))
def jogador(hp=50,mp=5000,pos=(0,0)):return dict(hp=hp,hp_max=100,mp=mp,mp_max=10000,position=pos)
def controles(cast=False,cd=0,**kw):
    grupos=[0.]*43;grupos[7]=cd
    return dict(casting=cast,casting_skill=1088 if cast else None,recargas_grupos=grupos,**kw)

class ConfirmacaoReacaoTest(unittest.TestCase):
    def test_revitalize_aplicado_confirma_mesmo_recebendo_mais_dano_que_cura(self):
        v=ConfirmacaoReacao()
        r=validar_regra(dict(nome='Revitalize',tecla='7',tipo='cura',skill_id=49,hp_max_pct=75))
        antes=controles(active_skill_ids=[170]);depois=controles(active_skill_ids=[49,170])
        depois['recargas_grupos'][3]=.99
        for i in range(2):
            v.enviada(r,i*300,jogador(72),antes)
            resultado=v.observar(i*300+.3,jogador(70,4990),depois)
            self.assertTrue(resultado['ok'])
            self.assertEqual(v.falhas_cura,0)
            self.assertFalse(v.recuperando)

    def test_efeito_antigo_ou_sem_inicio_de_recarga_nao_confirma_revitalize(self):
        r=validar_regra(dict(nome='Revitalize',tecla='7',tipo='cura',skill_id=49))
        for antigo,cd in ((True,.99),(False,0)):
            v=ConfirmacaoReacao()
            antes=controles(active_skill_ids=[49] if antigo else [])
            depois=controles(active_skill_ids=[49]);depois['recargas_grupos'][3]=cd
            v.enviada(r,0,jogador(),antes)
            self.assertIsNone(v.observar(.3,jogador(48),depois))

    def test_emergencia_preempta_confirmacao_de_buff_sem_cast_mas_nao_cura_em_execucao(self):
        v=ConfirmacaoReacao();buff=validar_regra(dict(nome='Buff',tecla='3',tipo='buff',skill_id=1146))
        v.enviada(buff,0,jogador(),controles())
        self.assertIsNone(v.interromper_por_emergencia(jogador(30),controles(True)))
        self.assertIsNone(v.interromper_por_emergencia(jogador(50),controles()))
        self.assertEqual(v.interromper_por_emergencia(jogador(30),controles())['motivo'],'cura_emergencial_priorizada')
        v.enviada(cura(),0,jogador(),controles())
        self.assertIsNone(v.interromper_por_emergencia(jogador(20),controles()))
        self.assertIsNotNone(v.pendente)
    def test_nao_libera_so_pelo_inicio_da_conjuracao(self):
        v=ConfirmacaoReacao();v.enviada(cura(),0,jogador(),controles())
        self.assertIsNone(v.observar(.9,jogador(),controles(True,1)))
        self.assertIsNone(v.observar(1.8,jogador(),controles(True,.5)))
        r=v.observar(2.1,jogador(80,3503),controles(False,.4))
        self.assertTrue(r['ok']);self.assertIsNone(v.pendente)

    def test_recarga_antiga_e_regeneracao_nao_confirmam_envio(self):
        v=ConfirmacaoReacao();v.enviada(cura(),0,jogador(),controles(cd=.5))
        r=v.observar(1.3,jogador(53),controles(cd=.5))
        self.assertFalse(r['ok']);self.assertTrue(v.proteger(.53))

    def test_stun_e_pausa_nao_sao_falsamente_tratados_como_input_perdido(self):
        v=ConfirmacaoReacao();v.enviada(cura(),0,jogador(),controles())
        v.pausar(10)
        self.assertIsNone(v.observar(10.8,jogador(),controles()))
        r=v.observar(11,jogador(),controles(stunned=True))
        self.assertIsNone(r['ok']);self.assertEqual(v.falhas_cura,0)

    def test_duas_recuperacoes_depois_bloqueia_ate_intervencao_confirmada(self):
        v=ConfirmacaoReacao();acoes=[]
        for i in range(6):
            v.enviada(cura(),i*3,jogador(30),controles())
            self.assertFalse(v.observar(i*3+1.3,jogador(30),controles())['ok'])
            a=v.recuperacao()
            if a:acoes.append(a)
        self.assertEqual(acoes,['revalidar','revalidar','manual']);self.assertTrue(v.manual)
        self.assertIsNone(v.observar(25,jogador(30,8000),controles()))
        self.assertTrue(v.observar(26,jogador(60,8000,(2,0)),controles())['ok'])
        self.assertFalse(v.manual)

    def test_motor_aguarda_cura_sem_interromper_com_w_tab_ou_buff(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.configuracao.perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,minimize_on_start=False,heal_enabled=False,hp_keys=['','',''],reacoes=[cura(),dict(nome='Sangue',tecla='3',tipo='buff',skill_id=1146,intervalo_s=3)])
        for sk in p['skills']:sk['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];inicio=[None];teclas=[];eventos=[]
        def hp():return 80 if inicio[0] is not None and t[0]>=inicio[0]+2.9 else 30
        mob=dict(ref=1,id=9000,name='Verit Mutante',hp=100,hp_max=100,hostile=True,position=(10,0),height=0)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(jogador(hp(),3503 if hp()==80 else 5000),heading=90,height=0),target=mob)
            def entidade(self,ref):return mob
            def listar_mobs(self,*a):return [mob]
            def estados_controle(self):
                passou=t[0]-inicio[0] if inicio[0] is not None else -1
                return controles(.9<=passou<2.9,1 if .9<=passou<5 else 0)
            def close(self):pass
        def down(k):
            teclas.append((t[0],k))
            if k=='f2' and inicio[0] is None:inicio[0]=t[0]
            elif k!='f2':c.stop.set()
        def dormir(dt):
            t[0]+=max(.001,dt)
            if t[0]>10:c.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)),patch.object(h,'DadosInternos',Dados),patch.object(h.threading,'Thread'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(p,eventos.append,c)
        self.assertIsNotNone(inicio[0]);self.assertEqual(teclas[0][1],'f2')
        posteriores=[s for s,k in teclas if k!='f2'];self.assertTrue(posteriores)
        self.assertTrue(all(s>=inicio[0]+2.9 for s in posteriores),teclas)
        self.assertTrue(any(e.get('event')=='reaction_result' and e.get('ok') is True for e in eventos))
