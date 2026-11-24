import struct,unittest
from pathlib import Path
from huntingaitan.leitura import skills_cliente as sk

RAIZ=Path(__file__).resolve().parents[1]
EXPORTACAO=RAIZ/'capturas_leitor'/'skills_memoria.bin'

def montar(nome,nome_en,classe,mana,recarga_ms,descricao,conjuracao_ms=0,efeitos=()):
    """Par (cabecalho, efeito) sintetico no formato descoberto."""
    cab=bytearray(sk.REGISTRO);ef=bytearray(sk.REGISTRO)
    cab[sk.OFF_NOME:sk.OFF_NOME+len(nome)]=nome.encode('cp1252');cab[sk.OFF_NOME_EN:sk.OFF_NOME_EN+len(nome_en)]=nome_en.encode('cp1252')
    struct.pack_into('<i',cab,sk.OFF_CLASSE,classe);struct.pack_into('<i',cab,sk.OFF_MANA,mana);struct.pack_into('<i',cab,sk.OFF_RECARGA_MS,recarga_ms)
    ef[sk.OFF_DESCRICAO:sk.OFF_DESCRICAO+len(descricao)]=descricao.encode('cp1252');struct.pack_into('<i',ef,sk.OFF_CONJURACAO_MS,conjuracao_ms)
    for k,(tipo,mag) in enumerate(list(efeitos)):
        struct.pack_into('<i',ef,sk.OFF_TIPOS+4*k,tipo);struct.pack_into('<i',ef,sk.OFF_MAGNITUDES+4*k,mag)
    return bytes(cab),bytes(ef)

class InterpretarTest(unittest.TestCase):
    def test_campos_de_cabecalho_e_de_efeito(self):
        cab,ef=montar('Remediar','Remedy',11,106,2000,'Recupera tu HP o el de un aliado en 233.',2000,[(110,233)])
        s=sk.interpretar(cab,ef,1073)
        self.assertEqual((s['nome'],s['nome_en'],s['classe'],s['classe_nome']),('Remediar','Remedy',11,'Templario'))
        self.assertEqual((s['recarga_s'],s['mana'],s['conjuracao_s'],s['nivel']),(2.0,106,2.0,1))
        self.assertEqual((s['tipo'],s['efeitos']),('cura',[(110,233)]))

    def test_nivel_vai_de_1_a_16_no_bloco(self):
        cab,ef=montar('x','x',1,1,1,'Inflige 1 de dano.')
        self.assertEqual([sk.interpretar(cab,ef,i)['nivel'] for i in (1073,1074,1088,1089)],[1,2,16,1])

    def test_acentos_e_classes_desconhecidas(self):
        cab,ef=montar('Guardián','Guardian',21,75,6000,'Aumenta la defensa física en 63 puntos')
        s=sk.interpretar(cab,ef,5)
        self.assertEqual(s['nome'],'Guardián');self.assertEqual(s['classe_nome'],'classe 21')
        self.assertEqual(sk.interpretar(*montar('a','a',0,0,1000,'Inflige 1.'),7)['classe_nome'],'-')

class ClassificarTest(unittest.TestCase):
    def test_tipos_do_templario(self):
        casos=[('Recupera tu HP o el de un aliado en 233.',2000,106,'cura'),
               ('Recupera tu HP en el 50% del daño infligido al enemigo durante 20 segundos',120000,56,'cura'),
               ('Consume todo el MP para recuperar el HP del objetivo en 150% del maná',20000,0,'cura'),
               ('Concéntrate en la defensa durante 20 segundos, lo que reduce todo el daño',120000,10,'defesa'),
               ('Crea una barrera protectora que anula por completo la habilidad recibida',300000,175,'defesa'),
               ('Durante 20 segundos, repele el 100% del daño de los enemigos',20000,240,'defesa'),
               ('Concentra los ataques enemigos en el escudo, reduciendo el daño causado',12000,80,'defesa'),
               ('Aumenta 1 nivel la tasa de amenaza de todos los enemigos en un radio de 4 metros.',12000,32,'ameaca'),
               ('Inflige 74 puntos de daño físico al enemigo y lo obliga a fijar la mirada en ti',6000,44,'ameaca'),
               ('Aumenta la resistencia a estados alterados en 37 puntos y la tasa de amenaza en 50%',120000,286,'buff'),
               ('Aumenta la defensa física en 893 puntos',180000,487,'buff'),
               ('Ataca al enemigo con el escudo, infligiendo 26 de daño y paralizando',12000,18,'ataque'),
               ('Inflige 80 de daño físico, además de reducir la velocidad',2000,48,'ataque'),
               ('Aumenta el HP máximo en 65 y el MP máximo en 45.',0,0,'passiva'),
               ('Teletransportarse al círculo mágico',1800000,10,'utilidade')]
        for descricao,recarga,mana,esperado in casos:
            with self.subTest(esperado=esperado,descricao=descricao[:40]):
                self.assertEqual(sk.classificar(descricao,recarga,mana),esperado)

@unittest.skipUnless(EXPORTACAO.exists(),'exporte a tabela com tools/exportar_skills.py para rodar este teste')
class DadosReaisTest(unittest.TestCase):
    """Confere o decodificador com a tabela exportada do cliente real (arquivo local, fora do Git)."""
    @classmethod
    def setUpClass(cls):cls.c=EXPORTACAO.read_bytes()

    def test_remediar_nivel_1(self):
        s=sk.interpretar_exportacao(self.c,1073)
        self.assertEqual((s['nome_en'],s['recarga_s'],s['mana'],s['conjuracao_s'],s['classe_nome'],s['tipo']),('Remedy',2.0,106,2.0,'Templario','cura'))

    def test_recargas_conhecidas(self):
        self.assertEqual(sk.interpretar_exportacao(self.c,977)['recarga_s'],1800.0)     # Return, 30 min
        self.assertEqual(sk.interpretar_exportacao(self.c,993)['recarga_s'],120.0)      # Heavy Guard
        self.assertEqual(sk.interpretar_exportacao(self.c,1233)['recarga_s'],300.0)     # Protect

    def test_nivel_16_usa_o_cabecalho_do_proprio_grupo(self):
        s=sk.interpretar_exportacao(self.c,1088)    # Remedy L16: o registro 1088 ja traz o nome do proximo grupo
        self.assertEqual((s['nome_en'],s['nivel']),('Remedy',16))

class BarraTest(unittest.TestCase):
    BASE=0x400000;ORIGEM=0x10000

    def _dados(self,slots,tabela=None):
        mem=bytearray(0x600000);o=self.ORIGEM;base=self.BASE
        def esc(addr,fmt,*v):struct.pack_into(fmt,mem,addr-o,*v)
        contexto=o+0x100000;gestor=o+0x300000;tab=o+0x400000
        esc(base+0x10,'<I',contexto);esc(base+0x14,'<I',gestor);esc(gestor+0x614,'<I',0)
        for i,v in enumerate(slots):esc(contexto+0x8129c+4*i,'<I',v)
        for id_,(cab,ef) in (tabela or {}).items():
            mem[tab-o+(id_-1)*sk.REGISTRO:tab-o+id_*sk.REGISTRO]=cab
            mem[tab-o+id_*sk.REGISTRO:tab-o+(id_+1)*sk.REGISTRO]=ef
        class D:
            def cfg(self,n):return {'context_rva':0x10,'bar_manager_rva':0x14,'effect_table_rva':tab-base}[n]
            def read(self,a,n):
                if a<o or a+n>o+len(mem):raise RuntimeError('fora')
                return bytes(mem[a-o:a-o+n])
            def u32(self,a):return struct.unpack('<I',self.read(a,4))[0]
        d=D();d.base=base
        return d

    def test_descrever_barra_decodifica_skills_e_marca_o_que_nao_e_skill(self):
        slots=[0]*40;slots[0]=(1073<<4)|2;slots[1]=(500<<4)|6;slots[9]=(993<<4)|2
        tab={1073:montar('Remediar','Remedy',11,106,2000,'Recupera tu HP en 233.',2000),
             993:montar('Guardia pesada','Heavy Guard',11,10,120000,'Concéntrate en la defensa durante 20 segundos')}
        barra=sk.descrever_barra(self._dados(slots,tab))
        self.assertEqual(len(barra),40)
        self.assertEqual((barra[0]['linha'],barra[0]['coluna'],barra[0]['skill']['nome']),(0,1,'Remediar'))
        self.assertEqual((barra[9]['linha'],barra[9]['coluna'],barra[9]['skill']['tipo']),(1,2,'defesa'))
        self.assertEqual((barra[1]['tipo_slot'],barra[1]['skill']),(6,None))
        self.assertEqual(barra[2]['skill_id'],0)

if __name__=='__main__':unittest.main()
