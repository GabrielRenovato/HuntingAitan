import copy,json,math,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from huntingaitan.leitura.sessao import DadosGravador,DadosReplay,de_json,ler_registros,para_json
from huntingaitan.leitura.replay import comparar,reproduzir

def sessao_sintetica(n=400,hp=100):
    jogador=dict(ref=1,id=1,name='Heroi',position=(10.,20.),height=0.,heading=90.,hp=hp,hp_max=100,mp=100,mp_max=100,hostile=False)
    reg=[dict(m='snapshot',r=para_json(dict(source='native',player=jogador,target=None))) for _ in range(n)]
    reg+=[dict(m='listar_mobs',r=[]) for _ in range(n)]
    reg+=[dict(m='estados_controle',r=para_json(dict(stunned=False,paralyzed=False,frozen=False,casting=False,effects={73:0,219:0,235:0}))) for _ in range(n)]
    reg+=[dict(m='caca_original_ativa',r=False) for _ in range(n)]
    reg+=[dict(m='recargas_atalhos',r=para_json({'2':dict(skill=1,ready=True,cooldown=0.)})) for _ in range(n)]
    return reg

class CodecTest(unittest.TestCase):
    def test_ida_e_volta_preserva_tipos(self):
        original={'pos':(1.5,2.5),'efeitos':{73:0,219:1},'lista':[(1,2),{'a':None}],'nan':float('nan'),'bytes':b'\x01\xff','txt':'ação'}
        volta=de_json(json.loads(json.dumps(para_json(original))))
        self.assertEqual(volta['pos'],(1.5,2.5));self.assertIsInstance(volta['pos'],tuple)
        self.assertEqual(volta['efeitos'],{73:0,219:1})
        self.assertEqual(volta['lista'],[(1,2),{'a':None}])
        self.assertTrue(math.isnan(volta['nan']));self.assertEqual(volta['bytes'],b'\x01\xff');self.assertEqual(volta['txt'],'ação')

    def test_chave_textual_reservada_nao_confunde_o_decodificador(self):
        original={'__t__':1,'x':2}
        self.assertEqual(de_json(json.loads(json.dumps(para_json(original)))),original)

class GravadorReplayTest(unittest.TestCase):
    class Real:
        hwnd=7
        def __init__(self):self.fechado=False
        def snapshot(self):return dict(player=dict(position=(1,2)))
        def estados_controle(self):raise RuntimeError('indisponivel')
        def close(self):self.fechado=True

    def test_gravador_repassa_grava_erro_e_fecha(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo=Path(pasta)/'sub'/'s.jsonl';real=self.Real();g=DadosGravador(real,arquivo,relogio=lambda:5.)
            self.assertEqual(g.hwnd,7)
            self.assertEqual(g.snapshot()['player']['position'],(1,2))
            with self.assertRaises(RuntimeError):g.estados_controle()
            g.close();self.assertTrue(real.fechado)
            regs=ler_registros(arquivo)
            self.assertEqual([r['m'] for r in regs],['snapshot','estados_controle'])
            self.assertEqual(regs[1]['erro'],'indisponivel')

    def test_replay_devolve_em_ordem_repete_ultimo_e_pede_parada(self):
        regs=[dict(m='snapshot',r=1),dict(m='snapshot',r=2),dict(m='estados_controle',erro='falhou')]
        paradas=[];d=DadosReplay(regs,ao_acabar=lambda:paradas.append(1))
        self.assertEqual((d.snapshot(),d.snapshot()),(1,2));self.assertEqual(paradas,[])
        self.assertEqual(d.snapshot(),2);self.assertEqual(paradas,[1])
        with self.assertRaises(RuntimeError):d.estados_controle()
        with self.assertRaises(RuntimeError):d.recargas_atalhos()
        self.assertTrue(hasattr(d,'listar_mobs'));self.assertFalse(hasattr(d,'inexistente'))

class ReproduzirTest(unittest.TestCase):
    def test_motor_reproduz_sessao_sem_erro_e_e_deterministico(self):
        a=reproduzir(sessao_sintetica(),limite_segundos=4);b=reproduzir(sessao_sintetica(),limite_segundos=4)
        self.assertIsNone(a['erro']);self.assertGreater(a['duracao'],1)
        self.assertTrue(any(e.get('event')=='status' for e in a['eventos']))
        self.assertIsNone(comparar(a,b))

    def test_fim_da_gravacao_encerra_o_motor(self):
        t=reproduzir(sessao_sintetica(n=40),limite_segundos=600)
        self.assertIsNone(t['erro']);self.assertLess(t['duracao'],600)
        self.assertEqual(t['eventos'][-1].get('event'),'finished')

    def test_comparar_aponta_primeira_divergencia(self):
        a=dict(eventos=[{'x':1}],teclas=[(0,'down','1')],erro=None)
        b=dict(eventos=[{'x':1}],teclas=[(0,'down','2')],erro=None)
        self.assertIn('teclas[0]',comparar(a,b))
        self.assertIsNone(comparar(a,copy.deepcopy(a)))
        c=dict(a,eventos=[{'x':1},{'x':2}]);self.assertIn('eventos tem 1',comparar(a,c))

    def test_gravar_e_reproduzir_de_novo_da_o_mesmo_traco(self):
        # Grava a sessao sintetica pelo gancho do motor e reproduz a gravacao resultante.
        with tempfile.TemporaryDirectory() as pasta,patch.dict(os.environ,{'AIKA_GRAVAR_SESSAO':'1','AIKA_DATA_DIR':pasta}):
            primeiro=reproduzir(sessao_sintetica(),limite_segundos=3)
            arquivos=list((Path(pasta)/'app_sessions').glob('leituras_*.jsonl'));self.assertEqual(len(arquivos),1)
            os.environ.pop('AIKA_GRAVAR_SESSAO')
            segundo=reproduzir(str(arquivos[0]),limite_segundos=3)
        sem_log=lambda t:dict(t,eventos=[e for e in t['eventos'] if 'reproducao offline' not in str(e.get('message',''))])
        self.assertIsNone(sem_log(primeiro)['erro']);self.assertIsNone(comparar(sem_log(primeiro),sem_log(segundo)))

if __name__=='__main__':unittest.main()
