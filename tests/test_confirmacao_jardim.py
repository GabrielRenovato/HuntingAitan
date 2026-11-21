import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from jardim_aereo import conferir_dificil,salvar_diagnostico_dificuldade


class ConfirmacaoTeste(unittest.TestCase):
    def executar(self,resultados,ativo=None,parar=None,erro_salvar=None):
        eventos=[];capturar=Mock(return_value=np.zeros((768,1366,3),np.uint8))
        class MSS:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        v=Mock();v.confirmar.side_effect=resultados;v.diagnostico=dict(resolucao=[1366,768],indicador=None)
        v.resumo.return_value='esperado dificil; indicador ilegivel; tela 1366x768'
        with patch.dict('sys.modules',mss=SimpleNamespace(MSS=MSS)),patch('captura_aika.CapturaAika',return_value=SimpleNamespace(capturar=capturar)),patch('interface_mina.VerificadorElite',return_value=v),patch('jardim_aereo.time.sleep'),patch('jardim_aereo.salvar_diagnostico_dificuldade',return_value='recorte.png',side_effect=erro_salvar) as salvar:
            resultado=conferir_dificil(emitir=eventos.append,ativo=ativo,parar=parar)
        return resultado,capturar,eventos,salvar

    def test_frames_transitorios_nao_encerram_antes_do_jogo_desenhar(self):
        ok,cap,eventos,salvar=self.executar([False,False,True,True])
        self.assertTrue(ok);self.assertEqual(cap.call_count,4)
        self.assertEqual(salvar.call_args.kwargs['etapa'],'confirmado')
        self.assertTrue(any('duas capturas' in e.get('message','') for e in eventos))

    def test_um_acerto_isolado_nao_libera_dificuldade(self):
        with self.assertRaisesRegex(RuntimeError,'nao confirmada'):self.executar([True,False,True,False])

    def test_espera_foco_antes_de_capturar(self):
        ativo=Mock(side_effect=[False,True,True,True,True,True,True])
        ok,cap,eventos,_=self.executar([True,True],ativo=ativo)
        self.assertTrue(ok);self.assertEqual(cap.call_count,2)
        self.assertTrue(any(e.get('state')=='paused' for e in eventos))

    def test_parada_do_usuario_cancela_sem_capturar(self):
        ok,cap,_,salvar=self.executar([],parar=lambda:True)
        self.assertFalse(ok);cap.assert_not_called();salvar.assert_not_called()

    def test_falha_ao_salvar_nao_esconde_erro_de_dificuldade(self):
        with self.assertRaisesRegex(RuntimeError,'dificuldade Dificil nao confirmada'):
            self.executar([False]*4,erro_salvar=OSError('sem permissao'))

    def test_diagnostico_salva_recorte_real_e_dados_de_leitura(self):
        import cv2
        tela=np.zeros((768,1366,3),np.uint8);tela[20,1360]=[10,100,220]
        leituras=[dict(resolucao=[1366,768],indicador=None)]*4
        with tempfile.TemporaryDirectory() as pasta,patch.dict('os.environ',AIKA_DATA_DIR=pasta):
            arquivo=Path(salvar_diagnostico_dificuldade(tela,leituras))
            recorte=cv2.imread(str(arquivo));self.assertEqual(recorte.shape,(576,546,3))
            self.assertEqual(recorte[20,540].tolist(),[10,100,220])
            self.assertEqual(json.loads(arquivo.with_suffix('.json').read_text(encoding='utf-8'))['leituras'],leituras)

    def test_mesmo_recorte_e_atualizado_sem_criar_um_arquivo_por_frame(self):
        tela=np.zeros((768,1366,3),np.uint8)
        with tempfile.TemporaryDirectory() as pasta,patch.dict('os.environ',AIKA_DATA_DIR=pasta):
            arquivo=Path(salvar_diagnostico_dificuldade(tela,[],etapa='antes_ocr'))
            novo=salvar_diagnostico_dificuldade(tela,[dict(indicador='dificil')],arquivo=arquivo,etapa='confirmado')
            self.assertEqual(str(arquivo),novo)
            self.assertEqual(len(list(arquivo.parent.glob('jardim_dificuldade_*'))),2)
            self.assertEqual(json.loads(arquivo.with_suffix('.json').read_text(encoding='utf-8'))['etapa'],'confirmado')

    def test_png_existe_antes_do_primeiro_ocr_mesmo_se_ele_falhar(self):
        class MSS:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with tempfile.TemporaryDirectory() as pasta,patch.dict('os.environ',AIKA_DATA_DIR=pasta):
            def ocr(tela):
                arquivos=list((Path(pasta)/'app_sessions').glob('jardim_dificuldade_*.png'))
                self.assertEqual(len(arquivos),1)
                dados=json.loads(arquivos[0].with_suffix('.json').read_text(encoding='utf-8'))
                self.assertEqual(dados['etapa'],'antes_ocr')
                self.assertEqual(dados['leituras'],[])
                raise RuntimeError('OCR interrompido')
            v=Mock();v.confirmar.side_effect=ocr
            cap=SimpleNamespace(capturar=lambda:np.zeros((768,1366,3),np.uint8))
            with patch.dict('sys.modules',mss=SimpleNamespace(MSS=MSS)),patch('captura_aika.CapturaAika',return_value=cap),patch('interface_mina.VerificadorElite',return_value=v),patch('jardim_aereo.time.sleep'):
                with self.assertRaisesRegex(RuntimeError,'OCR interrompido'):conferir_dificil()
            self.assertTrue(list((Path(pasta)/'app_sessions').glob('jardim_dificuldade_*.png')))


if __name__=='__main__':unittest.main()
