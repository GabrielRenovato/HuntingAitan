import copy,unittest
from huntingaitan.configuracao.perfil_hunt import DEFAULT
from huntingaitan.leitura.replay import reproduzir
from huntingaitan.leitura.sessao import para_json

def sessao(hp=100,mp=2000,grupos=None,n=600,alvo=None,mobs=()):
    """Jogador parado, sem alvo, com a vida e a mana pedidas; recargas por grupo todas prontas por padrao."""
    jogador=dict(ref=1,id=1,name='Heroi',position=(10.,20.),height=0.,heading=90.,hp=hp,hp_max=100,mp=mp,mp_max=3000,hostile=False)
    snap=para_json(dict(source='native',player=jogador,target=alvo))
    reg=[dict(m='snapshot',r=snap) for _ in range(n)]
    reg+=[dict(m='listar_mobs',r=para_json(list(mobs))) for _ in range(n)]
    reg+=[dict(m='estados_controle',r=para_json(dict(stunned=False,paralyzed=False,frozen=False,casting=False,effects={73:0,219:0,235:0}))) for _ in range(n)]
    reg+=[dict(m='recargas_atalhos',r=para_json({})) for _ in range(n)]
    reg+=[dict(m='recargas_grupos',r=list(grupos or [0.]*43)) for _ in range(n)]
    reg+=[dict(m='caca_original_ativa',r=False) for _ in range(n)]
    return reg

REMEDIAR=dict(nome='Remediar',tecla='f2',tipo='cura',skill_id=1088,hp_max_pct=40,mp_min=1497,intervalo_s=2.5)

def perfil(*reacoes,**extra):
    p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,hp_keys=['','',''],reacoes=list(reacoes));p.update(extra)
    for s in p['skills']:s['enabled']=False
    return p

def teclas(traco,tecla):
    return [t for t,tipo,k in traco['teclas'] if k==tecla and tipo=='down']

class RemediarA40PorCentoTest(unittest.TestCase):
    def rodar(self,hp=100,mp=2000,grupos=None,*reacoes,segundos=6):
        return reproduzir(sessao(hp,mp,grupos),perfil(*(reacoes or (REMEDIAR,))),limite_segundos=segundos)

    def test_usa_com_40_por_cento_e_nao_com_41(self):
        t40=self.rodar(40);t41=self.rodar(41)
        self.assertIsNone(t40['erro']);self.assertGreaterEqual(len(teclas(t40,'f2')),1)
        self.assertEqual(teclas(t41,'f2'),[])

    def test_vida_cheia_nao_usa(self):
        self.assertEqual(self.rodar(100)['teclas'],[])

    def test_respeita_o_intervalo_entre_usos(self):
        usos=teclas(self.rodar(30,segundos=8),'f2')
        self.assertGreaterEqual(len(usos),2)
        self.assertTrue(all(b-a>=2.5 for a,b in zip(usos,usos[1:])),usos)

    def test_sem_mana_suficiente_nao_usa(self):
        self.assertEqual(teclas(self.rodar(30,mp=1000),'f2'),[])   # Remediar custa 1497

    def test_recarga_real_do_cliente(self):
        em_recarga=[0.]*43;em_recarga[7]=1.0          # grupo de Remediar (id 1088)
        self.assertEqual(teclas(self.rodar(30,2000,em_recarga),'f2'),[])
        self.assertGreaterEqual(len(teclas(self.rodar(30,2000,[0.]*43),'f2')),1)

    def test_tecla_com_modificador(self):
        t=self.rodar(30,2000,None,dict(REMEDIAR,tecla='ctrl+3'))
        self.assertIn('ctrl',[k for _,_,k in t['teclas']]);self.assertGreaterEqual(len(teclas(t,'3')),1)

    def test_substitui_a_cura_antiga_da_tecla_unica(self):
        # heal_key padrao e '7': com reacao de cura configurada ela nao deve ser usada.
        t=self.rodar(20)
        self.assertEqual(teclas(t,'7'),[])

    def test_sem_reacoes_a_cura_antiga_continua(self):
        t=reproduzir(sessao(30),perfil(),limite_segundos=6)
        self.assertGreaterEqual(len(teclas(t,'7')),1)

def mob(id_,x,hp=80):
    return dict(ref=1000+id_,id=id_,name='Verit Mutante',position=(x,20.),height=0.,heading=0.,hp=hp,hp_max=100,mp=0,mp_max=0,hostile=True,slot=id_)

class CombateTest(unittest.TestCase):
    EMISSAO=dict(nome='Emision',tecla='4',tipo='ataque',skill_id=1258,mobs_min=2,mobs_raio_m=6,alcance_m=6,intervalo_s=12)
    THYMOS=dict(nome='Thymos',tecla='5',tipo='buff_combate',skill_id=1320,intervalo_s=180)

    def rodar(self,mobs,*reacoes,hp=100,mp=2000,segundos=5):
        alvo=mob(1,12.)
        return reproduzir(sessao(hp,mp,None,alvo=alvo,mobs=mobs),perfil(*reacoes),limite_segundos=segundos)

    def test_ataque_em_area_so_com_dois_ou_mais_mobs_perto(self):
        um=self.rodar([mob(1,12.)],self.EMISSAO);dois=self.rodar([mob(1,12.),mob(2,13.)],self.EMISSAO)
        self.assertIsNone(um['erro']);self.assertEqual(teclas(um,'4'),[])
        self.assertGreaterEqual(len(teclas(dois,'4')),1)

    def test_mob_fora_do_raio_nao_conta(self):
        self.assertEqual(teclas(self.rodar([mob(1,12.),mob(2,40.)],self.EMISSAO),'4'),[])

    def test_buff_de_combate_so_lutando_e_respeita_intervalo(self):
        t=self.rodar([mob(1,12.)],self.THYMOS,segundos=8)
        usos=teclas(t,'5');self.assertEqual(len(usos),1)       # 180 s de intervalo: uma vez na janela
        sem_alvo=reproduzir(sessao(100,2000),perfil(self.THYMOS),limite_segundos=5)
        self.assertEqual(teclas(sem_alvo,'5'),[])

    def test_pocao_de_mana_por_limite_de_mana(self):
        pocao=dict(nome='Pocao',tecla='ctrl+6',tipo='item_mp',mp_max_pct=30,intervalo_s=5)
        livre=dict(extra_buffs_enabled=False)      # ctrl+6 e reservado aos buffs adicionais do app
        baixa=reproduzir(sessao(100,600),perfil(pocao,**livre),limite_segundos=4);cheia=reproduzir(sessao(100,2500),perfil(pocao,**livre),limite_segundos=4)
        self.assertGreaterEqual(len(teclas(baixa,'6')),1);self.assertEqual(teclas(cheia,'6'),[])      # 600/3000=20%

    def test_cura_continua_acima_do_ataque_em_combate(self):
        t=self.rodar([mob(1,12.),mob(2,13.)],self.EMISSAO,REMEDIAR,hp=30,segundos=4)
        primeiras=[k for _,tipo,k in t['teclas'] if tipo=='down' and k in ('f2','4')]
        self.assertEqual(primeiras[0],'f2')

    def test_reacoes_ofensivas_respeitam_intervalo_e_intercalam_normal(self):
        regras=[dict(nome=f'ataque{k}',tecla=str(k),tipo='ataque',intervalo_s=.5,alcance_m=3) for k in (2,3,4)]
        t=self.rodar([mob(1,12.)],*regras,segundos=7)
        self.assertIsNone(t['erro'])
        ataques=[(s,k) for s,tipo,k in t['teclas'] if tipo=='down' and k in ('1','2','3','4')]
        self.assertGreater(len(ataques),4)
        ofensivas=[s for s,k in ataques if k!='1']
        self.assertTrue(all(b-a>=.7 for a,b in zip(ofensivas,ofensivas[1:])),ofensivas)
        sequencia=0
        for _,k in ataques:
            sequencia=0 if k=='1' else sequencia+1
            self.assertLessEqual(sequencia,2)

    def test_npc_e_morto_nao_disparam_ataque_em_area(self):
        npc=dict(mob(2,13.),hostile=False)
        morto=mob(3,13.,hp=0)
        t=self.rodar([mob(1,12.),npc,morto],self.EMISSAO)
        self.assertIsNone(t['erro']);self.assertEqual(teclas(t,'4'),[])

if __name__=='__main__':unittest.main()
