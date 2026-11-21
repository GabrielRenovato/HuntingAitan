import threading,unittest
from types import SimpleNamespace
from teclas_controladas import TeclasControladas

class EntradaFalsa:
    def __init__(self):self.pressionadas=[];self.soltas=[]
    def keyDown(self,k):self.pressionadas.append(k)
    def keyUp(self,k):self.soltas.append(k)

def criar(ativo=True,modal=False):
    entrada=EntradaFalsa()
    estado=SimpleNamespace(ativo=ativo,modal=modal)
    evento_modal=threading.Event()
    if modal:evento_modal.set()
    t=TeclasControladas(entrada,lambda k:entrada.keyDown(k),lambda:estado.ativo,evento_modal)
    return t,entrada,estado,evento_modal

class TeclasControladasTest(unittest.TestCase):
    def test_segurar_registra_e_soltar_libera_tudo(self):
        t,entrada,_,_=criar()
        self.assertTrue(t.segurar('w'))
        self.assertTrue(t.segurar('d'))
        self.assertEqual(t.seg,{'w','d'})
        t.soltar()
        self.assertEqual(t.seg,set())
        self.assertEqual(sorted(entrada.soltas),['d','w'])

    def test_segurar_nao_repete_tecla_ja_presa(self):
        t,entrada,_,_=criar()
        t.segurar('w');t.segurar('w')
        self.assertEqual(entrada.pressionadas,['w'])

    def test_sem_foco_ou_com_modal_nao_pressiona(self):
        t,entrada,_,_=criar(ativo=False)
        self.assertFalse(t.segurar('w'))
        t2,entrada2,_,_=criar(modal=True)
        self.assertFalse(t2.segurar('w'))
        self.assertEqual(entrada.pressionadas+entrada2.pressionadas,[])

    def test_pulso_solta_mesmo_se_esperar_falhar(self):
        t,entrada,_,_=criar()
        def quebrar(s):raise RuntimeError('falha simulada')
        t.esperar=quebrar
        with self.assertRaises(RuntimeError):t.pulso('w')
        self.assertEqual(t.seg,set())
        self.assertIn('w',entrada.soltas)

    def test_pulso_sem_tecla_ou_sem_foco_retorna_falso(self):
        t,_,_,_=criar()
        self.assertFalse(t.pulso(None))
        t2,_,_,_=criar(ativo=False)
        self.assertFalse(t2.pulso('w'))

    def test_vigiar_solta_quando_modal_abre(self):
        t,entrada,estado,evento_modal=criar()
        t.segurar('w')
        evento_modal.set()
        fim=threading.Event()
        th=threading.Thread(target=t.vigiar,args=(fim,));th.start()
        for _ in range(100):
            if not t.seg:break
            fim.wait(.02)
        fim.set();th.join(2)
        self.assertEqual(t.seg,set())
        self.assertIn('w',entrada.soltas)

if __name__=='__main__':unittest.main()
