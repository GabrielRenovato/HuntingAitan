from pathlib import Path
import threading,unittest
from types import SimpleNamespace
from unittest.mock import patch
import cv2,numpy as np
from dialogos_evento import DetectorEventos,tipo_convite
from controle_avisos import ObservadorAvisos

P=Path(__file__).parent/'fixtures'

def ocr_arena(im):return [[None,'Arena Elter',.99],[None,'Arena Elter começará em breve.',.99]],None

class EventosTeste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.im=cv2.imread(str(P/'fixture_arena_elter.png'))

    def test_arena_requer_nome_e_texto_do_convite(self):
        self.assertEqual(tipo_convite([('Arena Elter começará em breve.',.99)]),'arena_elter')
        self.assertEqual(tipo_convite([('Escola de treinamento de Elter',.99),('Aguardando 111 segundos',.99)]),'cte_elter')
        self.assertIsNone(tipo_convite([('Arena Elter',.99)]))
        self.assertIsNone(tipo_convite([('Arena Elter começará em breve',.3)]))

    def test_detecta_arena_e_avisa_bloqueio_antes_do_ocr(self):
        bloqueio=[]
        def ocr(im):self.assertTrue(bloqueio);return ocr_arena(im)
        a=DetectorEventos(ocr).localizar(self.im,lambda:bloqueio.append(True))
        self.assertEqual(a['tipo'],'arena_elter');self.assertLess(abs(a['ponto'][0]-288),3)

    def test_cancelar_isolado_nao_dispara(self):
        im=self.im.copy();im[238:270,122:214]=0
        self.assertIsNone(DetectorEventos(ocr_arena).localizar(im))

    def test_titulo_sem_cancelar_nao_dispara(self):
        im=self.im.copy();im[238:275,240:335]=0
        self.assertIsNone(DetectorEventos(ocr_arena).localizar(im))

    def test_confirmar_em_outra_linha_nao_forma_convite(self):
        im=self.im.copy();botao=im[239:268,123:213].copy();im[239:268,123:213]=0;im[90:119,123:213]=botao
        self.assertIsNone(DetectorEventos(ocr_arena).localizar(im))

    def test_dialogo_generico_bloqueia_sem_autorizar_clique(self):
        d=DetectorEventos(lambda im:([[None,'Confirmar troca de itens?',.99]],None))
        a=d.localizar(self.im)
        self.assertEqual(a['tipo'],'janela_desconhecida');self.assertIsNone(d.reconfirmar(self.im,a))

    def test_reconfirma_janela_movida_sem_limite_artificial_de_quatro_pixels(self):
        d=DetectorEventos(ocr_arena);a=d.localizar(self.im)
        tela=np.zeros((1080,1920,3),np.uint8);h,w=self.im.shape[:2];tela[310:310+h,740:740+w]=self.im
        p=d.reconfirmar(tela,a)
        self.assertIsNotNone(p);self.assertLess(abs(p[0]-(740+a['ponto'][0])),3);self.assertLess(abs(p[1]-(310+a['ponto'][1])),3)

    def test_nao_reconfirma_depois_de_desaparecer(self):
        d=DetectorEventos(ocr_arena);a=d.localizar(self.im)
        self.assertIsNone(d.reconfirmar(np.zeros_like(self.im),a))

    def test_duas_escalas_e_resolucoes(self):
        for escala in [.8,1.25]:
            d=DetectorEventos(ocr_arena);im=cv2.resize(self.im,None,fx=escala,fy=escala)
            tela=np.zeros((768,1366,3),np.uint8);h,w=im.shape[:2];tela[100:100+h,330:330+w]=im
            a=d.localizar(tela)
            self.assertIsNotNone(a,escala);self.assertEqual(a['tipo'],'arena_elter')
            self.assertLess(abs(a['ponto'][0]-(330+288*escala)),5)

    def test_cache_evitar_recarregar_ocr_para_mesmo_convite(self):
        n=[]
        def ocr(im):n.append(1);return ocr_arena(im)
        d=DetectorEventos(ocr);d.localizar(self.im);d.localizar(self.im)
        self.assertEqual(len(n),1)

class MonitorTeste(unittest.TestCase):
    def monitor(self):
        class Detector:
            def localizar(self,tela,ao_bloquear=None):
                if isinstance(tela,Exception):raise tela
                if tela and ao_bloquear:ao_bloquear()
                return tela
        return ObservadorAvisos(threading.Event(),lambda:True,lambda *a,**k:None,detector=Detector(),relogio=lambda:0.)

    def test_um_frame_sem_janela_nao_libera_combate(self):
        m=self.monitor();m.observar(dict(tipo='cte_elter',ponto=(10,10)))
        self.assertTrue(m.bloqueio.is_set())
        m.observar(None);self.assertTrue(m.bloqueio.is_set())
        m.observar(None);self.assertFalse(m.bloqueio.is_set())

    def test_excecao_de_captura_pausa_e_recupera_com_duas_leituras(self):
        m=self.monitor();m.falhou(RuntimeError('captura temporaria'))
        self.assertTrue(m.bloqueio.is_set());self.assertIsNone(m.atual())
        m.observar(None);m.observar(None);self.assertFalse(m.bloqueio.is_set());self.assertIsNone(m.erro)

    def test_falha_entre_frames_livres_reinicia_a_confirmacao(self):
        m=self.monitor();m.observar(dict(tipo='arena_elter',ponto=(10,10)));m.observar(None)
        m.falhou(RuntimeError('falhou'));m.observar(None)
        self.assertTrue(m.bloqueio.is_set());m.observar(None);self.assertFalse(m.bloqueio.is_set())

    def test_loop_reabre_captura_apos_excecao_em_vez_de_morrer(self):
        m=self.monitor();chamadas=[];aberturas=[]
        class Fim:
            encerrado=False
            def is_set(self):return self.encerrado
            def wait(self,s):return self.encerrado
        m.fim=Fim()
        class Contexto:
            def __enter__(self):aberturas.append(1);return self
            def __exit__(self,*args):pass
        class Captura:
            def __init__(self,sct):pass
            def capturar(self):
                chamadas.append(1)
                if len(chamadas)==1:raise RuntimeError('primeira captura falhou')
                if len(chamadas)>=4:m.fim.encerrado=True
                return None
        with patch.dict('sys.modules',mss=SimpleNamespace(MSS=Contexto)),patch('captura_aika.CapturaAika',Captura):m.executar()
        self.assertGreaterEqual(len(aberturas),2);self.assertFalse(m.bloqueio.is_set())

if __name__=='__main__':unittest.main()
