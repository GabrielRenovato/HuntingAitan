import unittest
from types import SimpleNamespace
from huntingaitan.combate.caca_templaria import CacaTemplaria
from huntingaitan.rotas.navegacao_grade import Grade
from huntingaitan.rotas.circuito_verit_leste import CircuitoVeritLeste

class TemplariaTeste(unittest.TestCase):
    def test_regiao_vazia_nao_le_grade_nem_calcula_caminhos(self):
        t=CacaTemplaria()
        self.assertEqual(t.ordenar(None,None,(0,0),[],0,None),[])

    def test_prefere_caminho_curto_em_vez_de_distancia_atraves_de_parede(self):
        flags=bytearray(20*20)
        for y in range(2,20):flags[y*20+4]=1
        g=Grade((0,0),(0,0),20,20,bytes(flags),(0,)*400,1)
        nav=SimpleNamespace(grade=g,grade_em=0)
        perto=dict(id=1,position=(6.5,10.5));longe=dict(id=2,position=(2.5,18.5))
        t=CacaTemplaria();r=t.ordenar(None,nav,(2.5,10.5),[perto,longe],0,lambda p:True)
        self.assertEqual([m['id'] for m in r],[2,1])

    def test_candidato_isolado_nao_e_selecionado(self):
        flags=bytearray(20*20)
        for y in range(20):flags[y*20+4]=1
        g=Grade((0,0),(0,0),20,20,bytes(flags),(0,)*400,1)
        t=CacaTemplaria();nav=SimpleNamespace(grade=g,grade_em=0)
        self.assertEqual(t.ordenar(None,nav,(2.5,10.5),[dict(id=1,position=(8.5,10.5))],0,lambda p:True),[])

    def test_ref_trocada_recupera_so_o_id_e_nome_originais(self):
        alvo=dict(id=8,name='Verit Mutante',ref=44)
        dados=SimpleNamespace(entidade=lambda ref:dict(id=9),listar_mobs=lambda *args:[dict(id=9,name='Verit Mutante'),alvo])
        t=CacaTemplaria();p=SimpleNamespace(ref=20,id=8,nome_original='Verit Mutante')
        self.assertIs(t.recuperar(dados,p,(0,0),50,{}),alvo)
        p.nome_original='Outro';self.assertIsNone(t.recuperar(dados,p,(0,0),50,{}))

    def test_selecao_sem_confirmacao_nao_tenta_o_mesmo_id_para_sempre(self):
        t=CacaTemplaria()
        self.assertTrue(t.tentar_selecao(1,0));self.assertFalse(t.tentar_selecao(1,2))
        self.assertTrue(t.tentar_selecao(2,2))

    def criar(self):
        c=CircuitoVeritLeste((2957,825));c.inteligente=True
        return c,tuple(c.trechos[c.trecho]['caminho'][-1])

    def test_primeira_visita_vazia_aguarda_e_revisita_fresca_nao_repete_cinco_segundos(self):
        c,pos=self.criar();trecho=c.trecho;c.observar([],pos,0)
        self.assertEqual(c.destino(pos,0)['estado'],'aguardar')
        c.observar([],pos,5);c.destino(pos,5);self.assertNotEqual(c.trecho,trecho)
        c.trecho=trecho;c.espera_ate=None;c.observar([],pos,10)
        self.assertEqual(c.destino(pos,10)['estado'],'andar')

    def test_leitura_velha_nao_libera_parada_conhecida(self):
        c,pos=self.criar();i=c.trechos[c.trecho]['ate'];c.limpos[i]=0;c.observar([],pos,0)
        self.assertEqual(c.destino(pos,2)['estado'],'aguardar')

    def test_reaparecimento_apaga_estado_vazio_e_mede_intervalo_sem_inventar_morte(self):
        c,pos=self.criar();i=c.trechos[c.trecho]['ate']
        c.abate(dict(position=pos),pos,0);c.limpos[i]=0;c.observar([],pos,1)
        c.observar([dict(id=99,position=pos)],pos,25)
        self.assertNotIn(i,c.limpos);self.assertEqual(c.reaparecimentos[i],[25])
        self.assertNotIn(i,c.ultimo_abate)
