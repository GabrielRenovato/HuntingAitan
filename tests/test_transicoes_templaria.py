import unittest
from huntingaitan.rotas.circuito_verit_leste import CircuitoVeritLeste
from huntingaitan.rotas.navegacao_grade import Grade
from huntingaitan.rotas.navegador_local import NavegadorLocal
from huntingaitan.combate.confirmacao_reacao import ConfirmacaoReacao
from huntingaitan.combate.reacoes import validar_regra,grupo_de_recarga

class TransicoesTeste(unittest.TestCase):
    def test_ponto_conhecido_vazio_transiciona_antes_de_chegar_e_parar(self):
        c=CircuitoVeritLeste((2957,825));c.inteligente=True;t=c.trecho
        fim=c.trechos[t]['caminho'][-1];pos=(fim[0],fim[1]-3)
        c.limpos[c.trechos[t]['ate']]=0;c.observar([],pos,1)
        r=c.destino(pos,1)
        self.assertEqual(r['estado'],'andar');self.assertNotEqual(c.trecho,t)

    def test_primeira_visita_nao_e_tratada_como_ponto_ja_conferido(self):
        c=CircuitoVeritLeste((2957,825));c.inteligente=True;t=c.trecho
        fim=c.trechos[t]['caminho'][-1];c.observar([],fim,1)
        self.assertEqual(c.destino(fim,1)['estado'],'aguardar');self.assertEqual(c.trecho,t)

    def test_duas_leituras_vazias_frescas_liberam_primeira_visita_sem_cinco_segundos(self):
        c=CircuitoVeritLeste((2957,825));c.inteligente=True;t=c.trecho
        fim=c.trechos[t]['caminho'][-1]
        c.observar([],fim,1);self.assertEqual(c.destino(fim,1)['estado'],'aguardar')
        c.observar([],fim,1.4);r=c.destino(fim,1.4)
        self.assertEqual(r['estado'],'andar');self.assertNotEqual(c.trecho,t)

    def test_leitura_antiga_ou_mob_reaparecendo_impede_pular_primeira_visita(self):
        for caso in ('atraso','mob'):
            c=CircuitoVeritLeste((2957,825));c.inteligente=True;t=c.trecho;fim=c.trechos[t]['caminho'][-1]
            c.observar([],fim,1)
            if caso=='atraso':c.observar([],fim,2)
            else:c.observar([dict(id=1,position=fim)],fim,1.4)
            self.assertEqual(c.destino(fim,2 if caso=='atraso' else 1.4)['estado'],'aguardar')
            self.assertEqual(c.trecho,t)

    def test_confere_ponto_vazio_durante_aproximacao_sem_parar_no_centro(self):
        c=CircuitoVeritLeste((2957,825));c.inteligente=True;t=c.trecho;fim=c.trechos[t]['caminho'][-1]
        c.observar([],(fim[0],fim[1]-7),1)
        c.observar([],(fim[0],fim[1]-5),1.4)
        pos=(fim[0],fim[1]-3.2)
        r=c.destino(pos,1.7)
        self.assertEqual(r['estado'],'andar');self.assertNotEqual(c.trecho,t)

    def test_recalcula_alternativa_no_mesmo_instante_do_bloqueio(self):
        g=Grade((0,0),(0,0),8,8,bytes(64),(0,)*64,1)
        n=NavegadorLocal(leitor=lambda *args:g);pos=(3.5,1.5);dest=(3.5,6.5)
        op=dict(controle_interno=True)
        n.planejar(None,pos,0,dest,'rota',0,**op)
        bloqueio=n.planejar(None,pos,0,dest,'rota',2.1,**op)
        self.assertIn('passagem_bloqueada',bloqueio)
        novo=n.replanejar_agora(None,pos,0,dest,'rota',2.1,bloqueio,**op)
        self.assertEqual(novo['estado'],'andando');self.assertTrue(novo['replanejado_imediato'])
        self.assertTrue(all(n.grade.passagem(n.grade.celula(a),n.grade.celula(b)) for a,b in zip(n.rota,n.rota[1:])))

    def test_cura_concluida_pelo_cliente_nao_espera_margem_extra(self):
        r=validar_regra(dict(nome='Cura',tecla='f4',tipo='cura',skill_id=1088,mp_min=10))
        player=dict(hp=50,hp_max=100,mp=100,position=(0,0))
        cds=[0.]*43;cc=dict(recargas_grupos=cds)
        c=ConfirmacaoReacao();c.enviada(r,0,player,cc)
        self.assertIsNone(c.observar(.5,player,dict(cc,casting=True,casting_skill=1088),resposta_cliente=True))
        cds[grupo_de_recarga(1088)]=1
        fim=c.observar(.55,dict(player,mp=90),dict(cc,casting=False),resposta_cliente=True)
        self.assertTrue(fim['ok'])

    def test_cast_ativo_continua_bloqueando_mesmo_no_modo_rapido(self):
        r=validar_regra(dict(nome='Cura',tecla='f4',tipo='cura',skill_id=1088))
        p=dict(hp=50,hp_max=100,mp=100,position=(0,0));cc=dict(recargas_grupos=[0.]*43)
        c=ConfirmacaoReacao();c.enviada(r,0,p,cc)
        self.assertIsNone(c.observar(1,dict(p,mp=80),dict(cc,casting=True,casting_skill=1088),resposta_cliente=True))
