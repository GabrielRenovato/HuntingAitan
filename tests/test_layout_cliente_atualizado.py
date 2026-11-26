"""Regressoes da selecao por hash e do diagnostico de cena, sem abrir o jogo."""
import json
import unittest
from huntingaitan.recursos import DADOS
from huntingaitan.leitura.dados_internos import DadosInternos, escolher_layout


class TesteClienteAtualizado(unittest.TestCase):
    def test_hash_novo_nao_reutiliza_globais_do_cliente_antigo(self):
        layouts=json.loads((DADOS/'native_layout.json').read_text(encoding='utf-8'))
        novo=escolher_layout(layouts,'28e70ccec05bbb1c9399d5af354ce0d7b19e186b33ed4ae232d28fcdebc4b703')
        antigo=escolher_layout(layouts,'e286c435100b7e03ec326fba6ae4ec94ea4f9ed17c3e473a2c37a2f3651834b3')
        for chave in ('active_scene_rva','context_rva','entity_count_rva','bar_manager_rva','effect_table_rva','mob_flag_rva','scene_vtable_rva'):
            self.assertNotEqual(novo[chave],antigo[chave],chave)
        self.assertEqual(novo['active_scene_rva'],0x2f9fdd4-0x400000)
        self.assertEqual(antigo['active_scene_rva'],0x2f9b148-0x400000)

    def leitor(self):
        d=DadosInternos.__new__(DadosInternos)
        d.pid=42;d.sha256='hash-diagnostico';d.base=0x900000
        d.layout=dict(active_scene_rva=0x100,scene_vtable_rva=0x200,login_scene_vtable_rva=0x300)
        return d

    def test_login_tem_mensagem_propria(self):
        d=self.leitor();d.u32=lambda a:0x100000 if a==d.base+0x100 else d.base+0x300
        with self.assertRaisesRegex(RuntimeError,'tela de login.*PID 42'):
            d.snapshot()

    def test_cena_nula_registra_cliente_e_global(self):
        d=self.leitor();d.u32=lambda a:0
        with self.assertRaisesRegex(RuntimeError,'PID 42; SHA-256 hash-diagnostico; global 0x900100'):
            d.snapshot()

    def test_cena_desconhecida_continua_recusada(self):
        d=self.leitor();d.u32=lambda a:0x100000
        with self.assertRaisesRegex(RuntimeError,'nao corresponde.*vtable 0x100000'):
            d.snapshot()
