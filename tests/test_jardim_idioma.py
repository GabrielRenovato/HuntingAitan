import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from huntingaitan.rotas.jardim_aereo import conferir_nome_jardim,conferir_fontes_jardim

def tabela(nome):
    b=bytearray(64*6);raw=nome.encode('cp1252')+b'\0'
    b[320:320+len(raw)]=raw
    return bytes(b)

class JardimIdiomaTeste(unittest.TestCase):
    def test_portugues_e_ingles_preservam_a_identidade_do_jardim(self):
        for nome in ('Jardim Aéreo de Mirza','Kynari Aviary'):
            self.assertEqual(conferir_nome_jardim(tabela(nome)),nome)

    def test_outra_dg_nome_vazio_e_tabela_truncada_sao_rejeitados(self):
        for raw in (tabela('Mina LEnfer'),tabela(''),tabela('Kynari Aviary')[:-1]):
            with self.assertRaisesRegex(RuntimeError,'UI/Dungeon.bin'):conferir_nome_jardim(raw)

    def test_traducao_nao_bloqueia_mas_terreno_alterado_continua_bloqueando(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);(p/'UI').mkdir();(p/'Env').mkdir()
            (p/'UI/Dungeon.bin').write_bytes(tabela('Kynari Aviary'))
            (p/'Env/mapa.att').write_bytes(b'terreno validado')
            plano={'fontes':{'UI/Dungeon.bin':hashlib.sha256(tabela('Jardim Aéreo de Mirza')).hexdigest(),
                             'Env/mapa.att':hashlib.sha256(b'terreno validado').hexdigest()}}
            with patch('huntingaitan.rotas.jardim_aereo.plano_jardim',return_value=plano):
                conferir_fontes_jardim(p)
                (p/'Env/mapa.att').write_bytes(b'terreno diferente')
                with self.assertRaisesRegex(RuntimeError,'revalide a rota: Env/mapa.att'):conferir_fontes_jardim(p)

    def test_tabela_ausente_nao_e_ignorada(self):
        with tempfile.TemporaryDirectory() as pasta,patch('huntingaitan.rotas.jardim_aereo.plano_jardim',return_value={'fontes':{'UI/Dungeon.bin':'hash'}}):
            with self.assertRaises(FileNotFoundError):conferir_fontes_jardim(pasta)
