import unittest
from huntingaitan.combate.reacoes import Reacoes,VigiaReacao,validar_regra
from huntingaitan.leitura.replay import reproduzir
from tests.test_reacoes_motor import sessao,perfil,REMEDIAR

def regra(**k):
    return validar_regra(dict(dict(nome='Remediar',tecla='ctrl+3',tipo='cura',skill_id=1088,hp_max_pct=60,intervalo_s=2.2),**k))

GRUPOS=[0.]*43
EM_RECARGA=[0.]*43;EM_RECARGA[7]=1.5          # grupo de Remediar (id 1088)

class VigiaReacaoTest(unittest.TestCase):
    def test_grupo_de_recarga_subindo_confirma_o_efeito(self):
        v=VigiaReacao();r=regra();v.enviada(r,10.,.5,2000)
        self.assertEqual(v.observar(10.5,.5,2000,3000,None,EM_RECARGA),[(r,True)]);self.assertEqual(v.falhas,0)

    def test_cliente_conjurando_a_skill_confirma(self):
        v=VigiaReacao();r=regra();v.enviada(r,10.,.5,2000)
        self.assertEqual(v.observar(10.2,.5,2000,3000,1088,GRUPOS),[(r,True)])

    def test_mana_gasta_ou_vida_subindo_confirmam(self):
        v=VigiaReacao();r=regra();v.enviada(r,10.,.5,2000)
        self.assertEqual(v.observar(11.,.5,1900,3000,None,GRUPOS),[(r,True)])    # caiu 100 = 3,3% de 3000
        v.enviada(r,20.,.5,2000)
        self.assertEqual(v.observar(21.,.55,2000,3000,None,GRUPOS),[(r,True)])   # vida +5 pontos

    def test_sem_sinal_dentro_da_janela_ainda_esta_pendente(self):
        v=VigiaReacao();v.enviada(regra(),10.,.5,2000)
        self.assertEqual(v.observar(12.,.5,2000,3000,None,GRUPOS),[])

    def test_sem_sinal_apos_a_janela_e_falha(self):
        v=VigiaReacao();r=regra();v.enviada(r,10.,.5,2000)
        self.assertEqual(v.observar(10.+VigiaReacao.JANELA,.5,2000,3000,None,GRUPOS),[(r,False)]);self.assertEqual(v.falhas,1)

    def test_sucesso_zera_a_sequencia(self):
        v=VigiaReacao();r=regra()
        for t in (0,5,10):v.enviada(r,t,.5,2000);v.observar(t+4,.5,2000,3000,None,GRUPOS)
        self.assertEqual(v.falhas,3)
        v.enviada(r,20.,.5,2000);v.observar(20.5,.5,2000,3000,None,EM_RECARGA)
        self.assertEqual(v.falhas,0)

    def test_item_e_ataque_nao_sao_verificados(self):
        v=VigiaReacao()
        v.enviada(regra(tipo='item_hp',skill_id=0),0.,.5,2000);v.enviada(regra(tipo='ataque',skill_id=1258,nome='E',tecla='4'),0.,.5,2000)
        self.assertEqual(v.observar(10.,.5,2000,3000,None,GRUPOS),[]);self.assertEqual(v.falhas,0)

    def test_niveis_alerta_e_abortar(self):
        v=VigiaReacao();r=regra()
        for i in range(VigiaReacao.ALERTA):v.enviada(r,i*5,.9,2000);v.observar(i*5+4,.9,2000,3000,None,GRUPOS)
        self.assertEqual(v.nivel(.9),'alerta');self.assertEqual(v.nivel(.9),'ok')           # avisa uma vez so
        for i in range(VigiaReacao.ALERTA,VigiaReacao.ABORTAR):v.enviada(r,i*5,.9,2000);v.observar(i*5+4,.9,2000,3000,None,GRUPOS)
        self.assertEqual(v.nivel(.9),'ok')                                                  # vida ainda alta: nao encerra
        self.assertEqual(v.nivel(.5),'abortar')

    def test_reenvio_dentro_da_janela_nao_perde_o_veredito(self):
        v=VigiaReacao();r=regra();v.enviada(r,0.,.5,2000);v.enviada(r,2.2,.5,2000)
        self.assertEqual(len(v.observar(3.6,.5,2000,3000,None,GRUPOS)),1);self.assertEqual(len(v.observar(5.8,.5,2000,3000,None,GRUPOS)),1)

class BackoffDeBuffTest(unittest.TestCase):
    def test_buff_sem_efeito_espera_cada_vez_mais_e_cura_nao(self):
        buff=regra(nome='Aegis',tipo='buff',tecla='7',skill_id=1334,hp_max_pct=100,intervalo_s=3);cura=regra()
        m=Reacoes([buff,cura]);m.enviada(buff,0.);m.resultado(buff,False,4.);m.resultado(buff,False,4.)
        self.assertEqual(m.proximo_em['Aegis'],4.+3*4)
        m.enviada(cura,0.);m.resultado(cura,False,4.);self.assertEqual(m.proximo_em['Remediar'],2.2)
        m.resultado(buff,True,30.);self.assertEqual(m.falhas['Aegis'],0)

class MotorCuraSemEfeitoTest(unittest.TestCase):
    def test_cura_sem_efeito_recupera_e_aguarda_controle_sem_abandonar_personagem(self):
        # Jogo "surdo": vida parada em 30%, mana e recargas intocadas. A cura e enviada e nada muda.
        t=reproduzir(sessao(30,2000,n=3000),perfil(REMEDIAR),limite_segundos=40)
        self.assertIsNone(t['erro'])
        fim=[e for e in t['eventos'] if e.get('event')=='finished']
        self.assertEqual([e.get('reason') for e in fim],['controle_de_parada'])
        recuperacoes=[e for e in t['eventos'] if e.get('event')=='input_recovery']
        self.assertEqual([e['state'] for e in recuperacoes],['attempt','attempt','waiting'])
        indice=next(i for i,e in enumerate(t['eventos']) if e.get('event')=='input_recovery' and e.get('state')=='waiting')
        self.assertFalse(any(e.get('event')=='action' for e in t['eventos'][indice+1:]))
        self.assertNotIn('esc',[k for _,tipo,k in t['teclas'] if tipo=='down'])

if __name__=='__main__':unittest.main()
