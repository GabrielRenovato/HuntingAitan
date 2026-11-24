import unittest
from huntingaitan.rotas.circuito_cinzas import CircuitoCinzas,plano_cinzas
from huntingaitan.rotas.circuito_verit_leste import CircuitoVeritLeste
from huntingaitan.rotas.visitas_circuito import VisitasCircuito
from huntingaitan.combate.escolha_por_caminho import EscolhaPorCaminho
from huntingaitan.combate.caca_templaria import CacaTemplaria

class CroshuTransicoesTeste(unittest.TestCase):
    def test_compartilha_componentes_sem_mudar_rota_dos_tres_croshus(self):
        self.assertTrue(issubclass(CircuitoCinzas,VisitasCircuito))
        self.assertTrue(issubclass(CircuitoVeritLeste,VisitasCircuito))
        self.assertTrue(issubclass(CacaTemplaria,EscolhaPorCaminho))
        self.assertEqual([(t['de'],t['ate']) for t in plano_cinzas()['trechos']],[(7,8),(8,9),(9,7)])

    def test_revisita_vazia_muda_de_trecho_sem_parar_no_ponto(self):
        c=CircuitoCinzas((2882,1154));c.inteligente=True;t=c.trecho
        fim=c.trechos[t]['caminho'][-1];pos=(fim[0],fim[1]-3)
        c.limpos[c.trechos[t]['ate']]=0;c.observar([],pos,1)
        r=c.destino(pos,1)
        self.assertEqual(r['estado'],'andar');self.assertNotEqual(c.trecho,t)

    def test_croshu_reaparecido_impede_usar_marca_de_vazio(self):
        c=CircuitoCinzas((2882,1154));c.inteligente=True;t=c.trecho
        fim=c.trechos[t]['caminho'][-1];c.limpos[c.trechos[t]['ate']]=0
        c.observar([dict(id=9000,position=fim)],fim,1)
        self.assertEqual(c.destino(fim,1)['estado'],'aguardar')
        self.assertEqual(c.trecho,t)

    def test_primeira_visita_continua_verificando_o_terceiro_ponto(self):
        c=CircuitoCinzas((2882,1154));c.inteligente=True;c.trecho=2;c.indice=0
        self.assertEqual(c.destino((2881,1189),0)['estado'],'andar')
        c.observar([],(2885,1196),1)
        self.assertEqual(c.destino((2885,1196),1)['estado'],'aguardar')
