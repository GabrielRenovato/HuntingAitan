import unittest
from huntingaitan.leitura.dados_internos import DadosInternos,PADROES,escolher_layout
from huntingaitan.leitura.verificacao import verificar,aprovado

A='a'*64;B='b'*64;C='c'*64

class EscolherLayoutTest(unittest.TestCase):
    def test_layout_unico_antigo_continua_valido(self):
        self.assertEqual(escolher_layout({'sha256':A,'x':1},A)['x'],1)

    def test_lista_de_layouts_escolhe_pelo_hash(self):
        dados={'layouts':[{'sha256':A,'x':1},{'sha256':B,'x':2}]}
        self.assertEqual(escolher_layout(dados,B)['x'],2)
        self.assertEqual(escolher_layout(dados,A)['x'],1)

    def test_aceita_texto_json(self):
        self.assertEqual(escolher_layout('{"layouts":[{"sha256":"%s","x":3}]}'%A,A)['x'],3)

    def test_versao_desconhecida_informa_hash_do_cliente_e_conhecidos(self):
        with self.assertRaises(RuntimeError) as e:escolher_layout({'layouts':[{'sha256':A},{'sha256':B}]},C)
        msg=str(e.exception)
        self.assertIn(C,msg);self.assertIn(A[:12],msg);self.assertIn('mudou de versao',msg)

class OffsetsConfiguraveisTest(unittest.TestCase):
    def test_sem_layout_usa_padrao(self):
        d=object.__new__(DadosInternos)
        self.assertEqual(d.cfg('ent_hpmp'),PADROES['ent_hpmp'])

    def test_layout_sobrescreve_padrao(self):
        d=object.__new__(DadosInternos);d.layout={'ent_hpmp':0x500}
        self.assertEqual(d.cfg('ent_hpmp'),0x500)
        self.assertEqual(d.cfg('ent_nome'),PADROES['ent_nome'])

class VerificacaoTest(unittest.TestCase):
    class Dados:
        def __init__(self,falhas=()):self.falhas=set(falhas)
        def _l(self,nome,valor):
            if nome in self.falhas:raise RuntimeError('quebrou '+nome)
            return valor
        def snapshot(self):return self._l('snapshot',dict(player=dict(position=(1,2),height=0),target=None))
        def cena_validada(self):return self._l('cena',123)
        def estados_controle(self):return self._l('estados',{})
        def recargas_atalhos(self):return self._l('recargas',{})
        def camera_regional(self):return self._l('camera',{})
        def listar_mobs(self,c,r,p):return self._l('mobs',[])
        def caca_original_ativa(self):return self._l('original',False)

    def test_tudo_ok_aprova(self):
        r=verificar(self.Dados());self.assertTrue(aprovado(r));self.assertTrue(all(x['ok'] for x in r))

    def test_falha_nao_critica_aprova_e_avisa(self):
        r=verificar(self.Dados(['camera']));self.assertTrue(aprovado(r))
        self.assertFalse(next(x for x in r if x['nome']=='camera')['ok'])

    def test_falha_critica_reprova(self):
        self.assertFalse(aprovado(verificar(self.Dados(['cena']))))

    def test_sem_snapshot_nao_lista_mobs(self):
        r=verificar(self.Dados(['snapshot']))
        self.assertNotIn('lista de mobs',[x['nome'] for x in r]);self.assertFalse(aprovado(r))

if __name__=='__main__':unittest.main()
