import copy,unittest
from unittest.mock import patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.leitura.clientes import listar_clientes


class SeletorClienteTest(unittest.TestCase):
    def test_perfil_persiste_par_pid_hwnd_e_preserva_perfil_antigo(self):
        p=validar(dict(client_pid=123,client_hwnd=456))
        self.assertEqual((p['client_pid'],p['client_hwnd']),(123,456))
        self.assertEqual((validar({})['client_pid'],validar({})['client_hwnd']),(0,0))

    def test_identificacao_incompleta_ou_invalida_e_recusada(self):
        for dados in [dict(client_pid=123),dict(client_hwnd=456),dict(client_pid=True,client_hwnd=456),dict(client_pid=-1,client_hwnd=456),dict(client_pid='123',client_hwnd=456)]:
            with self.subTest(dados=dados),self.assertRaises(ValueError):validar(dados)

    def test_lista_mostra_personagem_e_nao_o_alvo_de_outra_conta(self):
        janelas=[dict(pid=100,hwnd=10,caminho=r'C:\Aika\AIKACL.exe'),dict(pid=200,hwnd=20,caminho=r'C:\Aika\AIKACL-multiinstancia-teste.exe')]
        fechados=[];abertos=[]
        class Dados:
            def __init__(self,janela):self.janela=janela;abertos.append(janela['pid'])
            def snapshot(self):
                nome='DilmaRusef' if self.janela['pid']==100 else 'Domination'
                return dict(player=dict(name=nome,position=(2711,1292)),target=dict(name='Buto Mutante'))
            def close(self):fechados.append(self.janela['pid'])
        with patch('huntingaitan.leitura.clientes.enumerar_clientes',return_value=janelas),patch('huntingaitan.leitura.clientes.DadosInternos',Dados):
            r=listar_clientes()
        self.assertEqual([c['name'] for c in r],['DilmaRusef','Domination'])
        self.assertTrue(all(c['ready'] for c in r));self.assertEqual(abertos,fechados)

    def test_falha_em_um_cliente_nao_esconde_o_outro_e_fecha_leitor(self):
        janelas=[dict(pid=100,hwnd=10,caminho=r'C:\Aika\AIKACL.exe'),dict(pid=200,hwnd=20,caminho=r'C:\Aika\AIKACL-multiinstancia-teste.exe')]
        fechados=[]
        class Dados:
            def __init__(self,janela):self.pid=janela['pid']
            def snapshot(self):
                if self.pid==100:raise RuntimeError('Personagem carregando')
                return dict(player=dict(name='Domination',position=(2711,1292)))
            def close(self):fechados.append(self.pid)
        with patch('huntingaitan.leitura.clientes.enumerar_clientes',return_value=janelas),patch('huntingaitan.leitura.clientes.DadosInternos',Dados):r=listar_clientes()
        self.assertFalse(r[0]['ready']);self.assertIn('carregando',r[0]['error'])
        self.assertTrue(r[1]['ready']);self.assertEqual(fechados,[100,200])
