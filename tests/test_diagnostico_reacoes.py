import copy,unittest
from huntingaitan.combate.reacoes import Reacoes,validar_regra

class DiagnosticoReacoesTest(unittest.TestCase):
    def test_motivo_e_decisao_usam_as_mesmas_condicoes(self):
        r=validar_regra(dict(nome='Area',tecla='4',tipo='ataque',mp_min=788,mobs_min=2,mobs_raio_m=4,alcance_m=4))
        m=Reacoes([r]);args=(10,1.,1.,500,True,[2,3],[0]*43)
        d=m.diagnostico(*args,alvo=dict(hp_pct=100,dist=2))[0]
        self.assertEqual(d['motivo'],'Mana insuficiente');self.assertFalse(d['condicoes']['mp'])
        self.assertIsNone(m.escolher(*args,alvo=dict(hp_pct=100,dist=2)))
        args=(10,1.,1.,2000,True,[2],[0]*43)
        d=m.diagnostico(*args,alvo=dict(hp_pct=100,dist=2))[0]
        self.assertFalse(d['condicoes']['mobs']);self.assertIn('hostis',d['motivo'])

    def test_indice_do_painel_preservado_apos_ordenar_prioridade(self):
        regras=[validar_regra(dict(nome='Ataque',tecla='4',tipo='ataque')),
                validar_regra(dict(nome='Cura',tecla='f2',tipo='cura',hp_max_pct=70)),
                validar_regra(dict(nome='Inativa',tecla='',tipo='cura',ativa=False))]
        m=Reacoes(regras);args=(10,.5,1.,5000,True,[],[0]*43)
        alvo=dict(hp_pct=100,dist=2);escolhida=m.escolher(*args,alvo=alvo)
        d=m.diagnostico(*args,alvo=alvo,escolhida=escolhida)
        self.assertEqual([v['index'] for v in d],[1,0])
        self.assertTrue(d[0]['escolhida']);self.assertEqual(d[1]['motivo'],'Aguardando prioridade')

    def test_diagnostico_nao_consumiu_skill_e_respeita_intervalo(self):
        r=validar_regra(dict(nome='Cura',tecla='f2',tipo='cura',intervalo_s=3));m=Reacoes([r])
        args=(10,.4,1.,5000,True,[],[0]*43);antes=copy.deepcopy(m.proximo_em)
        self.assertTrue(m.diagnostico(*args)[0]['pronta']);self.assertEqual(m.proximo_em,antes)
        self.assertIs(m.escolher(*args),r);m.enviada(r,10)
        d=m.diagnostico(11,.4,1.,5000,True,[],[0]*43)[0]
        self.assertFalse(d['condicoes']['pronta']);self.assertIn('recarga',d['motivo'])

    def test_agenda_bloqueia_ofensiva_sem_bloquear_cura(self):
        r=[validar_regra(dict(nome='Ataque',tecla='4',tipo='ataque')),validar_regra(dict(nome='Cura',tecla='f2',tipo='cura'))]
        m=Reacoes(r);d=m.diagnostico(10,.4,1.,5000,True,[],[0]*43,alvo=dict(hp_pct=100,dist=2),ofensivas_liberadas=False)
        por_indice={v['index']:v for v in d};self.assertFalse(por_indice[0]['pronta']);self.assertTrue(por_indice[1]['pronta'])

    def test_motor_emite_motivo_para_o_editor_sem_enviar_ataque_em_area(self):
        from tests.test_reacoes_motor import sessao,perfil,mob
        from huntingaitan.leitura.replay import reproduzir
        alvo=mob(1,12.)
        regra=dict(nome='Area',tecla='4',tipo='ataque',mobs_min=2,mobs_raio_m=4,alcance_m=4)
        t=reproduzir(sessao(alvo=alvo,mobs=[alvo]),perfil(regra),limite_segundos=3)
        self.assertIsNone(t['erro'])
        leituras=[e for e in t['eventos'] if e.get('event')=='reaction_state']
        self.assertTrue(leituras)
        self.assertTrue(all(e['regras'][0]['index']==0 and not e['regras'][0]['condicoes']['mobs'] for e in leituras))
        self.assertFalse(any(e.get('event')=='action' and e.get('kind')=='reacao' for e in t['eventos']))
