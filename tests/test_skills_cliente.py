import json,tempfile,unittest
from pathlib import Path
from huntingaitan.leitura.skills_cliente import REGISTRO,exportar,registro

BASE=0x400000;RVA=0x1000

class DadosFalsos:
    sha256='falso';base=BASE
    def __init__(self,quantidade=40,ilegivel=None):
        self.mem=bytearray(quantidade*REGISTRO);self.ilegivel=ilegivel
        for i in range(quantidade):self.mem[i*REGISTRO:i*REGISTRO+4]=i.to_bytes(4,'little')
    def cfg(self,nome):return {'effect_table_rva':RVA}[nome]
    def read(self,endereco,tamanho):
        inicio=endereco-(BASE+RVA)
        if inicio<0 or inicio+tamanho>len(self.mem):raise RuntimeError('fora da tabela')
        if self.ilegivel and self.ilegivel[0]<=inicio<self.ilegivel[1]:raise RuntimeError('ilegivel')
        return bytes(self.mem[inicio:inicio+tamanho])

class ExportarSkillsTest(unittest.TestCase):
    def test_exporta_todos_os_registros_na_ordem(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino=Path(pasta)/'sub'/'s.bin';meta=exportar(DadosFalsos(),destino,quantidade=40)
            conteudo=destino.read_bytes()
            self.assertEqual(len(conteudo),40*REGISTRO);self.assertEqual(meta['blocos_ilegiveis'],[])
            self.assertEqual(int.from_bytes(registro(conteudo,17)[:4],'little'),17)
            self.assertEqual(json.loads(destino.with_suffix('.json').read_text())['quantidade'],40)

    def test_bloco_ilegivel_e_informado_e_zerado(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino=Path(pasta)/'s.bin';meta=exportar(DadosFalsos(ilegivel=(4096,8192)),destino,quantidade=40)
            self.assertEqual(meta['blocos_ilegiveis'],[(4096,4096)])
            self.assertEqual(destino.read_bytes()[4096:8192],bytes(4096))

if __name__=='__main__':unittest.main()
