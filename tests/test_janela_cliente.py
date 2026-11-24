import unittest
from types import SimpleNamespace
from threading import Event
from huntingaitan.leitura.janela_cliente import escolher_janela,janela_em_foco
from huntingaitan.entrada.teclas_controladas import TeclasControladas


class JanelaClienteTest(unittest.TestCase):
    def test_escolha_explicita_ignora_outra_janela_em_primeiro_plano(self):
        original=dict(hwnd=10,pid=100,caminho=r'C:\GoLevel\AikaOnline\AIKACL.exe')
        copia=dict(hwnd=20,pid=200,caminho=r'C:\GoLevel\AikaOnline\AIKACL-multiinstancia-teste.exe')
        self.assertEqual(escolher_janela([copia,original],20,100,10),original)
        self.assertEqual(escolher_janela([copia,original],10,200,20),copia)

    def test_duas_instancias_originais_exigem_identificacao_em_primeiro_plano(self):
        a=dict(hwnd=10,pid=100,caminho=r'C:\Aika\AIKACL.exe')
        b=dict(hwnd=20,pid=200,caminho=r'D:\Aika\AIKACL.exe')
        self.assertEqual(escolher_janela([a,b],20),b)
        with self.assertRaisesRegex(RuntimeError,'primeiro plano'):escolher_janela([a,b],99)

    def test_executavel_nao_reconhecido_e_recusado_antes_de_ler_memoria(self):
        with self.assertRaisesRegex(RuntimeError,'compativel'):
            escolher_janela([dict(hwnd=20,pid=200,caminho=r'C:\Aika\outro.exe')],20)

    def test_cliente_fechado_nao_cai_para_a_outra_conta(self):
        original=dict(hwnd=10,pid=100,caminho=r'C:\Aika\AIKACL.exe')
        with self.assertRaisesRegex(RuntimeError,'fechado'):escolher_janela([original],10,200,20)
        with self.assertRaisesRegex(RuntimeError,'fechado'):escolher_janela([original],10,100,20)

    def test_outra_janela_aika_nao_autoriza_tab_ataque_ou_movimento(self):
        foco=[10];enviadas=[]
        u=SimpleNamespace(GetForegroundWindow=lambda:foco[0])
        e=SimpleNamespace(keyUp=lambda k:enviadas.append(('up',k)))
        teclas=TeclasControladas(e,lambda k:enviadas.append(('down',k)),lambda:janela_em_foco(u,10),Event())
        self.assertTrue(teclas.segurar('w'))
        foco[0]=20
        self.assertFalse(janela_em_foco(u,10))
        for k in ['w','tab','1']:self.assertFalse(teclas.segurar(k))
        teclas.soltar()
        self.assertEqual(enviadas,[('down','w'),('up','w')]);self.assertFalse(teclas.seg)


if __name__=='__main__':unittest.main()
