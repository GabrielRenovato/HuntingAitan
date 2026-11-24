import struct,unittest
from huntingaitan.leitura.inventario import ler_inventario,equipamento_candidato,precisa_reparar


class LeitorTeste(unittest.TestCase):
    def criar(self):
        class Dados:
            base=0x400000
            def cfg(self,n):return 100
            def u32(self,a):return 0x100000
            def read(self,a,n):return self.mem[a][:n]
        d=Dados();raw=bytearray(2800);bolsas=bytearray(140)
        for i in (0,1,4):struct.pack_into('<H',bolsas,i*20,5300)
        for slot in (20,80):
            struct.pack_into('<HHI',raw,slot*20,1042,1042,slot+100)
            raw[slot*20+14:slot*20+17]=bytes((8,151,0))
        d.mem={0x180014:bytes(120),0x180130:raw,0x180c20:bolsas,0x180cb0:struct.pack('<Q',2**32+123)}
        tabela=bytearray(0x198);struct.pack_into('<HH',tabela,0x100,0,1001)
        d.mem[0x199a290+1042*0x1d0]=tabela
        return d

    def test_sete_bolsas_esparsas_e_saldo_64_bits(self):
        d=self.criar();r=ler_inventario(d)
        self.assertEqual(r['bolsas'],[0,1,4]);self.assertEqual(len(r['itens']),140)
        self.assertEqual(r['ouro'],2**32+123)
        self.assertTrue(equipamento_candidato(d,r['itens'][80]))

    def test_refinado_nao_e_candidato(self):
        d=self.criar();d.mem[0x180130][20*20+16]=0x70
        i=ler_inventario(d)['itens'][20]
        self.assertEqual(i['refino'],7);self.assertFalse(equipamento_candidato(d,i))

    def test_bolsa_ausente_e_registro_inconsistente_bloqueiam(self):
        d=self.criar();d.mem[0x180c20][80:82]=b'\0\0'
        with self.assertRaises(RuntimeError):ler_inventario(d)
        d=self.criar();d.mem[0x180130][402:404]=b'\0\0'
        with self.assertRaises(RuntimeError):ler_inventario(d)

    def test_consumivel_nao_e_equipamento(self):
        d=self.criar();d.mem[0x199a290+1042*0x1d0][0x100]=1
        self.assertFalse(equipamento_candidato(d,ler_inventario(d)['itens'][20]))

    def test_reparo_inclui_equipado_refinado_e_pula_tudo_cheio(self):
        d=self.criar();r=ler_inventario(d)
        self.assertTrue(precisa_reparar(d,r))
        for i in r['itens']:i['atual']=i['maxima']
        self.assertFalse(precisa_reparar(d,r))
        r['equipados'][0]=dict(id=1042,serial=999,atual=7,maxima=151,refino=7)
        self.assertTrue(precisa_reparar(d,r))
