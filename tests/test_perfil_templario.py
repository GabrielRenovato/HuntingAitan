import copy,unittest
from huntingaitan.configuracao.perfil_hunt import DEFAULT
from huntingaitan.configuracao.perfil_templario import preparar,ESPERADAS
from huntingaitan.combate.reacoes import Reacoes

class PerfilTemplarioTest(unittest.TestCase):
    def barra(self):
        return [dict(tecla=k,skill_id=v,nome=k,mana=100,recarga_s=12) for k,v in ESPERADAS.items()]
    def test_aplica_sem_trocar_cliente_rota_ou_mudar_original(self):
        p=copy.deepcopy(DEFAULT);p.update(client_pid=123,client_hwnd=456,hp_percent=70)
        novo=preparar(p,self.barra())
        self.assertEqual(novo['reacoes'][0]['tecla'],'ctrl+3')
        self.assertEqual(novo['reacoes'][0]['hp_max_pct'],70)
        self.assertEqual((novo['client_pid'],novo['client_hwnd']),(123,456))
        self.assertEqual(novo['patrol_mode'],p['patrol_mode'])
        self.assertEqual(novo['buff_keys'],['ctrl+1','ctrl+2','','',''])
        self.assertFalse(any(s['enabled'] for s in novo['skills']))
        self.assertEqual(p['reacoes'],[])
    def test_recusa_barra_trocada(self):
        barra=self.barra();barra[0]['skill_id']=5002
        with self.assertRaisesRegex(ValueError,'Barra diferente'):preparar(DEFAULT,barra)
    def test_area_exige_dois_hostis_e_cura_fica_disponivel_entre_ataques(self):
        p=preparar(dict(copy.deepcopy(DEFAULT),hp_percent=70),self.barra())
        m=Reacoes(p['reacoes'])
        r=m.escolher(0,.5,1,5000,True,[2,3],[0]*43,dict(hp_pct=100,dist=2),ofensivas_liberadas=False)
        self.assertEqual(r['tecla'],'ctrl+3')
        areas=Reacoes([r for r in p['reacoes'] if r['tecla'] in ('4','6','8')])
        self.assertIsNone(areas.escolher(0,1,1,5000,True,[2],[0]*43,dict(hp_pct=100,dist=2)))
        self.assertIsNotNone(areas.escolher(0,1,1,5000,True,[2,3],[0]*43,dict(hp_pct=100,dist=2)))
