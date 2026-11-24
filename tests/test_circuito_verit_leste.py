import math,unittest
from huntingaitan.rotas.circuito_verit_leste import CircuitoVeritLeste,dentro_leste,plano_leste
from huntingaitan.rotas.circuito_verit import plano_verit
from huntingaitan.configuracao.perfil_hunt import validar
from huntingaitan.combate.hunt_native import alvo_permitido

class CircuitoLesteTeste(unittest.TestCase):
    def test_exclui_spawns_misturados_sem_alterar_o_oeste(self):
        d=plano_leste();ids={p['id'] for p in d['pontos']}
        self.assertEqual(ids,{6,7,11,14,15,16,17})
        self.assertEqual(len(d['trechos']),7)
        self.assertEqual([p['id'] for p in plano_verit()['pontos']],[1,5,20,18,4,19,2,3])
        for i,t in enumerate(d['trechos']):
            self.assertLessEqual(math.dist(t['caminho'][0],d['pontos'][i]['pos']),1)
            self.assertLessEqual(math.dist(t['caminho'][-1],d['pontos'][(i+1)%7]['pos']),1)
            self.assertTrue(all(dentro_leste(p) for p in t['caminho']))
            self.assertTrue(all(math.dist(a,b)<=math.sqrt(2)+1e-6 for a,b in zip(t['caminho'],t['caminho'][1:])))

    def test_trajeto_e_filtro_respeitam_afastamento_dos_normais(self):
        d=plano_leste()
        self.assertEqual({p['id'] for p in d['excluidos']},{9,8,10,12,13})
        for p in d['excluidos']:self.assertFalse(dentro_leste(p['pos']))
        for t in d['trechos']:
            for pos in t['caminho']:
                self.assertTrue(all(math.dist(pos,m['pos'])>d['raio_normais'] for m in d['normais']))

    def test_retorna_duas_voltas_sem_pular_paradas(self):
        c=CircuitoVeritLeste((2957,825));agora=0
        for _ in range(2):
            for t in plano_leste()['trechos']:
                fim=t['caminho'][-1];r=c.destino(fim,agora)
                self.assertEqual((r['estado'],r['ponto']),('aguardar',t['ate']))
                self.assertEqual(c.destino(fim,agora+4.9)['estado'],'aguardar')
                c.destino(fim,agora+5);agora+=6
        self.assertEqual(c.voltas,2)

    def test_filtro_aceita_verit_leste_e_recusa_outros_mobs(self):
        p=validar(dict(patrol_mode='termes_verit_leste',target='qualquer',radius=50))
        self.assertEqual(p['target'],'verit')
        player=dict(position=(2864,821),height=0)
        m=dict(name='Verit Mutante',position=(2905,820),height=0,hp=100,hostile=True)
        self.assertTrue(alvo_permitido(m,player,(2864,821),p))
        self.assertFalse(alvo_permitido(dict(m,name='Tet das Chamas'),player,(2864,821),p))
        self.assertFalse(dentro_leste((2748,833)))
        with self.assertRaises(RuntimeError):CircuitoVeritLeste((2748,833))

    def test_entra_perto_de_qualquer_trecho(self):
        for t in plano_leste()['trechos']:
            pos=t['caminho'][len(t['caminho'])//2]
            c=CircuitoVeritLeste(pos)
            self.assertEqual(c.trechos[c.trecho]['ate'],t['ate'])
