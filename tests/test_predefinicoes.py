import json,tempfile,unittest
from pathlib import Path
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.configuracao.predefinicoes import TEMPLARIO,aplicar,aplicar_em_arquivo

class PredefinicoesTest(unittest.TestCase):
    def test_remediar_a_40_por_cento(self):
        r=aplicar(validar({}))['reacoes']
        self.assertEqual(len(r),1)
        self.assertEqual((r[0]['nome'],r[0]['tecla'],r[0]['tipo'],r[0]['skill_id'],r[0]['hp_max_pct'],r[0]['mp_min']),('Remediar','f2','cura',1088,40.0,1497))

    def test_nao_altera_o_perfil_original_e_substitui_reacoes_anteriores(self):
        base=validar(dict(reacoes=[dict(nome='velha',tecla='f4',tipo='defesa')]))
        novo=aplicar(base)
        self.assertEqual([x['nome'] for x in base['reacoes']],['velha']);self.assertEqual([x['nome'] for x in novo['reacoes']],['Remediar'])

    def test_conflito_com_tecla_da_rotacao_e_rejeitado(self):
        base=validar({});base['skills'][1].update(key='f2',enabled=True,seconds=10)
        with self.assertRaises(ValueError):aplicar(base)

    def test_aplicar_em_arquivo_guarda_copia_e_preserva_o_resto(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'profile.json';original=validar(dict(radius=33,target='penza'))
            caminho.write_text(json.dumps(original),encoding='utf-8')
            gravado=aplicar_em_arquivo(caminho,agora=lambda f:'TESTE')
            lido=json.loads(caminho.read_text(encoding='utf-8'))
            self.assertEqual(lido['reacoes'][0]['nome'],'Remediar');self.assertEqual(lido['radius'],33);self.assertEqual(lido['target'],'penza')
            self.assertEqual(lido,json.loads(json.dumps(gravado)))
            copia=json.loads((Path(pasta)/'profile.antes_reacoes_TESTE.json').read_text(encoding='utf-8'))
            self.assertEqual(copia['reacoes'],[])
            self.assertFalse(list(Path(pasta).glob('*.tmp')))

    def test_templario_usa_o_remediar_de_f2(self):
        self.assertEqual(TEMPLARIO[0]['tecla'],'f2')

if __name__=='__main__':unittest.main()
