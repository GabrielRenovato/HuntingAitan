import unittest
from huntingaitan.combate.reacoes import validar_reacoes
from huntingaitan.leitura.skills_cliente import barra_para_painel,sugerir_reacao,tecla_sugerida

def skill(id_,nome,tipo,recarga=10.,mana=100,conj=0.,nome_en=None):
    return dict(id=id_,nivel=1,nome=nome,nome_en=nome_en or nome,classe=11,classe_nome='Templario',recarga_s=recarga,mana=mana,
                conjuracao_s=conj,descricao='',tipo=tipo,efeitos=[])

def slot(linha,coluna,sk=None,tipo_slot=2,skill_id=None):
    return dict(slot=linha*8+coluna-1,linha=linha,coluna=coluna,tipo_slot=tipo_slot,skill_id=skill_id if skill_id is not None else (sk['id'] if sk else 0),skill=sk)

class TeclaSugeridaTest(unittest.TestCase):
    def test_linhas_da_barra(self):
        self.assertEqual([tecla_sugerida(0,1),tecla_sugerida(0,8),tecla_sugerida(1,3),tecla_sugerida(2,2)],['1','8','ctrl+3',''])

class SugerirTest(unittest.TestCase):
    def test_cura_vira_reacao_de_cura_com_mana_e_intervalo_da_skill(self):
        g=sugerir_reacao(slot(1,3,skill(1088,'Remediar','cura',recarga=2.,mana=1497,conj=2.)))
        self.assertEqual((g['tipo'],g['tecla'],g['skill_id'],g['mp_min']),('cura','ctrl+3',1088,1497))
        self.assertEqual(g['intervalo_s'],3.)         # conjuracao + 1 s supera a recarga de 2 s

    def test_intervalo_usa_a_recarga_quando_e_maior_e_e_limitado(self):
        self.assertEqual(sugerir_reacao(slot(0,5,skill(1320,'Thymos','buff',recarga=180.,conj=1.5)))['intervalo_s'],180.)
        self.assertEqual(sugerir_reacao(slot(0,5,skill(1,'x','buff',recarga=99999.)))['intervalo_s'],3600.)

    def test_remediar_sugere_40_por_cento_de_vida(self):
        self.assertEqual(sugerir_reacao(slot(1,3,skill(1088,'Remediar','cura',2.,1497,2.,nome_en='Remedy')))['hp_max_pct'],40)
        self.assertNotIn('hp_max_pct',sugerir_reacao(slot(0,3,skill(1146,'Sangre','cura',120.,284,nome_en='Holy Blood'))))

    def test_tipos_mapeados(self):
        casos=[('cura','cura'),('defesa','defesa'),('buff','buff_combate'),('ataque','ataque'),('ameaca','ataque')]
        for tipo,esperado in casos:self.assertEqual(sugerir_reacao(slot(0,2,skill(5,'x',tipo)))['tipo'],esperado)
        for tipo in ('passiva','utilidade'):self.assertIsNone(sugerir_reacao(slot(0,2,skill(5,'x',tipo))))

    def test_ataque_ganha_alcance_e_o_ataque_basico_nao_vira_reacao(self):
        self.assertEqual(sugerir_reacao(slot(0,4,skill(1258,'Emision','ataque')))['alcance_m'],5)
        self.assertIsNone(sugerir_reacao(slot(0,1,skill(961,'ataque','ataque',recarga=.4,mana=0,nome_en='Attack'))))

    def test_item_vira_reacao_de_item_de_vida(self):
        g=sugerir_reacao(slot(1,6,None,tipo_slot=6,skill_id=8086))
        self.assertEqual((g['tipo'],g['tecla'],g['skill_id']),('item_hp','ctrl+6',0))
        self.assertIsNone(sugerir_reacao(slot(1,7,None,tipo_slot=0,skill_id=0)))

    def test_sugestoes_validam_como_reacoes(self):
        # Nenhuma sugestao pode ser rejeitada pelo perfil (teclas, intervalos, limites).
        sugestoes=[sugerir_reacao(s) for s in [slot(0,2,skill(1057,'Pericia','ataque',recarga=12,mana=18)),slot(1,3,skill(1088,'Remediar','cura',2,1497,2)),
                                               slot(1,2,skill(1242,'Proteccion','defesa',300,692,2)),slot(1,6,None,tipo_slot=6,skill_id=8086)]]
        self.assertEqual(len(validar_reacoes([x for x in sugestoes if x])),4)

class BarraParaPainelTest(unittest.TestCase):
    def test_lista_so_skills_e_itens(self):
        itens=barra_para_painel([slot(0,1,skill(1057,'Pericia','ataque')),slot(0,2),slot(1,6,None,tipo_slot=6,skill_id=8086),slot(1,7,None,tipo_slot=6,skill_id=0)])
        self.assertEqual([(i['linha'],i['coluna'],i['tipo_slot']) for i in itens],[(0,1,'skill'),(1,6,'item')])
        self.assertEqual(itens[0]['nome'],'Pericia');self.assertEqual(itens[1]['nome'],'Item 8086');self.assertEqual(itens[0]['tecla'],'1')

if __name__=='__main__':unittest.main()
