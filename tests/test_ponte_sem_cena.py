import struct,threading,unittest
from types import SimpleNamespace
from huntingaitan.entrada.ponte_camera import PonteCamera

class PonteSemCenaTeste(unittest.TestCase):
    def test_probe_e_remocao_nao_dependem_da_cena_destruida_no_teleporte(self):
        for op in (1,3):
            p=PonteCamera.__new__(PonteCamera)
            p.seq=0;p.lock=threading.Lock();p.instalada=True;p.incerta=False;p.pid=7;p.thread=8;p.hwnd=9;p.msg=10;p.token=11;p.d=1000
            def thread(hwnd,pid):pid._obj.value=7;return 8
            def cena():self.fail('Probe/remocao acessou cena em carregamento')
            p.dados=SimpleNamespace(cena_validada=cena,read=lambda a,n:struct.pack('<4I',1,1,op,1),u32=lambda a:0)
            p.u=SimpleNamespace(GetWindowThreadProcessId=thread,SendMessageTimeoutW=lambda *args:1)
            escritas=[];p.escrever=lambda a,b:escritas.append((a,b))
            self.assertEqual(p.pedir(op)['status'],1)
            cab=struct.unpack('<6I2f',escritas[0][1])
            self.assertEqual(cab[4:6],(0,0))
            self.assertEqual(p.instalada,op!=3)
