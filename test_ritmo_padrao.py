import ctypes,unittest
from types import SimpleNamespace
from ctypes import wintypes as w
from unittest.mock import Mock,patch
from ritmo_padrao import configurar_ritmo,intervalo_por_velocidade,ler_velocidade_windows
from hunt_core import CadenciaCombate
from perfil_hunt import validar
from cancelamento_normal import executar_combo
from entrada_segura import preparar_pressao_sem_pausa


class RitmoTeste(unittest.TestCase):
    def test_pressao_desativa_sleep_da_biblioteca_sem_pular_wrapper_de_failsafe(self):
        e=[]
        def key_down(tecla,_pause=True):
            e.append(('failsafe',tecla));e.append(('pausa',_pause))
        preparar_pressao_sem_pausa(SimpleNamespace(keyDown=key_down))('1')
        self.assertEqual(e,[('failsafe','1'),('pausa',False)])

    def test_pressao_nao_contorna_recusa_do_failsafe(self):
        def key_down(tecla,_pause=True):raise RuntimeError('fail-safe')
        with self.assertRaisesRegex(RuntimeError,'fail-safe'):
            preparar_pressao_sem_pausa(SimpleNamespace(keyDown=key_down))('1')

    def test_zero_usa_ritmo_estimado_do_windows_sem_pausa_entre_teclas(self):
        r=configurar_ritmo({},consulta=lambda:31)
        self.assertEqual(r['pausa_teclas'],0)
        self.assertAlmostEqual(r['intervalo_repeticao'],1/30)
        self.assertEqual(r['origem'],'windows_estimado')
        self.assertAlmostEqual(intervalo_por_velocidade(0),.4)

    def test_intervalo_configurado_nao_depende_do_windows(self):
        consulta=Mock(side_effect=AssertionError('nao consultar'))
        r=configurar_ritmo(dict(combo_key_delay_ms=5,combo_repeat_ms=60),consulta)
        self.assertEqual(r['pausa_teclas'],.005);self.assertEqual(r['intervalo_repeticao'],.06)
        consulta.assert_not_called()

    def test_consulta_apenas_le_a_velocidade_do_teclado(self):
        with patch('ritmo_padrao.ctypes.windll.user32.SystemParametersInfoW') as spi:
            def ler(acao,ui,ptr,flags):
                self.assertEqual(acao,0x000A)
                ctypes.cast(ptr,ctypes.POINTER(w.DWORD)).contents.value=31;return 1
            spi.side_effect=ler
            self.assertEqual(ler_velocidade_windows(),31)

    def test_falha_na_consulta_tem_ritmo_limitado_e_explicito(self):
        r=configurar_ritmo({},consulta=lambda:None)
        self.assertEqual(r['origem'],'padrao_30hz');self.assertAlmostEqual(r['intervalo_repeticao'],1/30)

    def test_cadencia_repetida_nao_fica_limitada_a_170_ou_120ms(self):
        c=CadenciaCombate({'recargas':{}});c.registrar('1',0,intervalo_normal=.04,normal_repetido=True)
        self.assertIsNone(c.escolher(.039,True,True,1,True))
        self.assertEqual(c.escolher(.04,True,True,1,True),'1')

    def test_skill_mantem_a_pausa_exclusiva_na_agenda(self):
        c=CadenciaCombate({'intervalo_skills':.7,'recargas':{'4':1}})
        c.registrar('4',0)
        self.assertIsNone(c.escolher(.6,True,True,1,True))

    def test_pausa_configuravel_fica_entre_as_teclas_sem_sobreposicao(self):
        t=[0.];e=[]
        def esperar(s):t[0]+=s
        executar_combo(lambda k:e.append(('down',k,t[0])),lambda k:e.append(('up',k,t[0])),esperar,lambda:True,'1',True,intervalo_teclas=.005)
        self.assertEqual([k for a,k,t in e if a=='down'],list('1rr1ww'))
        self.assertAlmostEqual(t[0],.025)
        for down,up in zip(e[::2],e[1::2]):self.assertEqual(down[1:],up[1:])

    def test_perfil_preserva_os_dois_intervalos_e_rejeita_valores_invalidos(self):
        p=validar(dict(combo_key_delay_ms=5,combo_repeat_ms=50))
        self.assertEqual((p['combo_key_delay_ms'],p['combo_repeat_ms']),(5,50))
        for dados in [dict(combo_key_delay_ms=-1),dict(combo_repeat_ms=3000),dict(combo_key_delay_ms=True)]:
            with self.assertRaises(ValueError):validar(dados)


if __name__=='__main__':unittest.main()
