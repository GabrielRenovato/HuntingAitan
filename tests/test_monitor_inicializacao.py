import json,subprocess,sys,threading,unittest,tempfile,os
from pathlib import Path
from unittest.mock import patch,Mock
from huntingaitan.visao.controle_avisos import ObservadorAvisos


class InicializacaoMonitorTeste(unittest.TestCase):
    def test_detector_e_carregado_antes_da_thread(self):
        ordem=[];detector=object()
        with patch('huntingaitan.visao.avisos_hunt.DetectorAvisos',side_effect=lambda:ordem.append('detector') or detector),patch('huntingaitan.visao.controle_avisos.threading.Thread') as thread:
            thread.return_value.start.side_effect=lambda:ordem.append('thread')
            m=ObservadorAvisos(threading.Event(),lambda:False,Mock());m.iniciar()
        self.assertEqual(ordem,['detector','thread']);self.assertIs(m.detector,detector)

    def test_falha_de_carregamento_nao_fica_escondida_na_thread(self):
        with patch('huntingaitan.visao.avisos_hunt.DetectorAvisos',side_effect=RuntimeError('modelo ausente')),patch('huntingaitan.visao.controle_avisos.threading.Thread') as thread:
            with self.assertRaisesRegex(RuntimeError,'modelo ausente'):
                ObservadorAvisos(threading.Event(),lambda:False,Mock()).iniciar()
            thread.assert_not_called()

    def test_detector_injetado_nao_e_substituido(self):
        detector=object()
        with patch('huntingaitan.visao.avisos_hunt.DetectorAvisos') as fabrica,patch('huntingaitan.visao.controle_avisos.threading.Thread'):
            m=ObservadorAvisos(threading.Event(),lambda:False,Mock(),detector=detector);m.iniciar()
            fabrica.assert_not_called();self.assertIs(m.detector,detector)

    def test_monitor_e_interface_carregam_em_processo_novo(self):
        r=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'hunt_bridge.py'),'selftest-monitor'],input='{}',capture_output=True,text=True,timeout=20,check=True)
        self.assertEqual(json.loads(r.stdout)['data'],dict(monitor=True,interface=True))

    def test_run_prepara_extensoes_antes_de_criar_threads_de_controle(self):
        import hunt_bridge as b,huntingaitan.combate.hunt_native as h
        ordem=[]
        with tempfile.TemporaryDirectory() as temp:
            cfg=Path(temp)/'perfil.json';cfg.write_text('{}',encoding='utf-8')
            with patch.dict(os.environ,AIKA_DATA_DIR=temp),patch.object(sys,'argv',['backend','run',str(cfg)]),patch.object(b,'DIARIO',None),patch.object(b,'emitir'),patch('huntingaitan.visao.controle_avisos.preparar_runtime_visual',side_effect=lambda:ordem.append('visao')),patch.object(b.threading,'Thread') as tarefa,patch.object(h,'main',side_effect=lambda *a:ordem.append('motor')):
                tarefa.return_value.start.side_effect=lambda:ordem.append('thread')
                try:b.main()
                finally:
                    if b.DIARIO:b.DIARIO.close()
        self.assertEqual(ordem,['visao','thread','motor'])


if __name__=='__main__':unittest.main()
