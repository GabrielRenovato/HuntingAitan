import unittest
from types import SimpleNamespace
from huntingaitan.combate.teste_cancelamento import condicao_teste,sequencia,avaliar

class ComparacaoTeste(unittest.TestCase):
    def test_cura_stun_distancia_e_identidade_bloqueiam_o_experimento(self):
        s=dict(player=dict(hp=100,hp_max=100,position=(0,0)),target=dict(id=1,hp=100,hostile=True,position=(1,0)))
        self.assertTrue(condicao_teste(s,{},1));self.assertFalse(condicao_teste(s,{},2))
        self.assertFalse(condicao_teste(s,dict(stunned=True),1))
        s['player']['hp']=50;self.assertFalse(condicao_teste(s,{},1))
        s['player']['hp']=100;s['target']['position']=(4,0);self.assertFalse(condicao_teste(s,{},1))

    def test_ordem_e_liberacao_sem_esperas_programadas(self):
        a=[];e=SimpleNamespace(keyDown=lambda k:a.append(('down',k)),keyUp=lambda k:a.append(('up',k)))
        sequencia(e,lambda:True,True)
        self.assertEqual([k for tipo,k in a if tipo=='down'],list('1rr1ww'))
        self.assertEqual([k for tipo,k in a if tipo=='up'],list('1rr1ww'))

    def test_recusa_do_primeiro_ataque_nao_envia_movimento(self):
        a=[];e=SimpleNamespace(keyDown=lambda k:False,keyUp=lambda k:a.append(k))
        self.assertEqual(sequencia(e,lambda:True,True),[('1',False)]);self.assertEqual(a,['1'])

    def test_poucas_amostras_nao_habilitam_macro_mesmo_com_ganho_aparente(self):
        r=[dict(modo='normal',valida=True,dano=10,duracao=1),dict(modo='sequencia',valida=True,dano=100,duracao=1)]
        a=avaliar(r);self.assertFalse(a['evidencia_suficiente']);self.assertFalse(a['ativar_automaticamente'])

    def test_recarga_no_segundo_ataque_nao_apaga_os_dois_w_da_sequencia(self):
        a=[];n=[0]
        def down(k):
            a.append(k)
            if k=='1':n[0]+=1
            return not(k=='1' and n[0]==2)
        sequencia(SimpleNamespace(keyDown=down,keyUp=lambda k:None),lambda:True,True)
        self.assertEqual(a,list('1rr1ww'))

    def test_rodadas_interrompidas_nao_entram_na_comparacao(self):
        r=[dict(modo='normal',valida=False,dano=100,duracao=1)]
        self.assertIsNone(avaliar(r)['taxas_observadas']['normal'])
