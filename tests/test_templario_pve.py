import copy,unittest
from huntingaitan.configuracao.perfil_hunt import DEFAULT
from huntingaitan.configuracao.perfil_templario import ajustar_pve,ESPERADAS
from huntingaitan.combate.reacoes import Reacoes,grupo_de_recarga

class TemplarioPVETest(unittest.TestCase):
    def preparar(self):
        slots=[dict(tecla=k,skill_id=v,nome=k,mana=1497 if k=='ctrl+3' else 100,recarga_s=120) for k,v in ESPERADAS.items()]
        p=copy.deepcopy(DEFAULT);p.update(client_pid=123,client_hwnd=456,patrol_mode='termes_penza')
        p['reacoes']=[dict(nome='Pocao',tecla='f4',tipo='item_hp',hp_max_pct=50),dict(nome='Item extra',tecla='ctrl+4',tipo='defesa',hp_max_pct=50)]
        return p,slots,ajustar_pve(p,slots)
    def test_uma_penza_libera_area_e_recarga_real_decide_reuso(self):
        _,_,p=self.preparar();m=Reacoes(p['reacoes']);cd=[1.]*43;cd[grupo_de_recarga(1258)]=0
        args=(0,1.,1.,5000,True,[2.],[*cd]);alvo=dict(hp_pct=70,dist=2.)
        r=m.escolher(*args,alvo=alvo);self.assertEqual(r['skill_id'],1258)
        m.enviada(r,0);self.assertIsNone(m.escolher(.8,1,1,5000,True,[2],cd,alvo=alvo))
        self.assertEqual(m.escolher(1.3,1,1,5000,True,[2],cd,alvo=alvo)['skill_id'],1258)
        cd[grupo_de_recarga(1258)]=.1
        self.assertIsNone(m.escolher(3,1,1,5000,True,[2],cd,alvo=alvo))
    def test_reserva_mana_da_cura_e_pocao_precede_conjuracao(self):
        _,_,p=self.preparar();m=Reacoes(p['reacoes'])
        self.assertEqual(m.escolher(0,.3,1,5000,True,[2],[0]*43,alvo=dict(hp_pct=80,dist=2))['tecla'],'f4')
        r=next(r for r in p['reacoes'] if r['skill_id']==1258)
        self.assertEqual(r['mp_min'],1597)
        self.assertIsNone(Reacoes([r]).escolher(0,1,1,1000,True,[2],[0]*43,alvo=dict(hp_pct=80,dist=2)))
    def test_preserva_rota_conta_e_item_extra_sem_mudar_original(self):
        original,_,p=self.preparar()
        self.assertEqual((p['client_pid'],p['client_hwnd'],p['patrol_mode']),(123,456,'termes_penza'))
        self.assertEqual(next(r for r in p['reacoes'] if r['tecla']=='ctrl+4')['hp_max_pct'],50)
        self.assertEqual(original['reacoes'][0]['tipo'],'item_hp')
        self.assertEqual(p['action_gap'],.6)
