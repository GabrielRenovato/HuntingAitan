import unittest
from huntingaitan.leitura.escolha_cliente import descrever,escolher_cliente

A=dict(hwnd=10,pid=4360,caminho=r'C:\GoLevel\AikaOnline\AIKACL-multiinstancia-teste.exe')
B=dict(hwnd=20,pid=16672,caminho=r'C:\GoLevel\AikaOnline\AIKACL-multiinstancia-teste.exe')

class EscolherClienteTest(unittest.TestCase):
    def test_um_cliente_e_escolhido_sozinho(self):self.assertIs(escolher_cliente([A]),A)

    def test_pid_escolhe_entre_varios(self):
        self.assertIs(escolher_cliente([A,B],pid=16672),B)

    def test_varios_sem_pid_lista_os_pids(self):
        with self.assertRaises(RuntimeError) as e:escolher_cliente([A,B])
        msg=str(e.exception);self.assertIn('4360',msg);self.assertIn('16672',msg);self.assertIn('--pid',msg)

    def test_pid_inexistente_lista_os_abertos(self):
        with self.assertRaises(RuntimeError) as e:escolher_cliente([A,B],pid=1)
        self.assertIn('PID 1',str(e.exception));self.assertIn('4360',str(e.exception))

    def test_nenhum_cliente(self):
        with self.assertRaisesRegex(RuntimeError,'Nenhum cliente'):escolher_cliente([])

    def test_descrever(self):self.assertEqual(descrever(A),'PID 4360 (AIKACL-multiinstancia-teste.exe)')

if __name__=='__main__':unittest.main()
