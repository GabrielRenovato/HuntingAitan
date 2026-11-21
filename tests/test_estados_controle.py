import unittest,struct
from huntingaitan.leitura.dados_internos import DadosInternos

class EstadosTeste(unittest.TestCase):
 def leitor(self,efeitos):
  d=object.__new__(DadosInternos);d.base=0x400000;ctx=0x2000000;raiz=ctx+0x7fea0
  d.u32=lambda a:ctx if a==0x2f9b1e0 else (0x3000000 if a==0x2100000+0x104 else 0)
  d.cena_validada=lambda:0x2100000
  d.ids=[100];d.chamadas=[]
  def read(a,n):
   d.chamadas.append((a,n))
   if a==raiz+0xd4:return struct.pack('<20h',*(d.ids+[0]*(20-len(d.ids))))
   if a in [raiz+0x11b8,raiz+0x1230]:return bytes(40)
   if a==0xf9c1f4+100*0x2d0:
    tipos=[v[0] for v in efeitos]+[0]*(4-len(efeitos));valores=[v[1] for v in efeitos]+[0]*(4-len(efeitos))
    return struct.pack('<8i',*(tipos+valores))
   return bytes(n)
  d.read=read;return d
 def test_recarga_real_do_ataque_normal(self):
  d=self.leitor([]);u=d.u32;r=d.read
  d.u32=lambda a:0x3100000 if a==0x2100000+0x4170 else (0x3200000 if a==0x3100000+0x1f4 else u(a))
  valor=[.5]
  d.read=lambda a,n:struct.pack('<h',1) if a==0x3200000+0x538 else (struct.pack('<f',valor[0]) if a==0x2000000+0x8bda0 else r(a,n))
  self.assertFalse(d.estados_controle()['normal_ready'])
  valor[0]=0.;self.assertTrue(d.estados_controle()['normal_ready'])
 def test_efeito_real_atordoado_paralisado_congelado(self):
  d=self.leitor([(73,1),(219,1),(235,1)]);r=d.estados_controle()
  self.assertTrue(r['stunned']);self.assertTrue(r['paralyzed']);self.assertTrue(r['frozen'])
  self.assertEqual(r['skill_ids'],[100])
 def test_fim_do_debuff_nao_fica_preso_no_cache(self):
  d=self.leitor([(73,1)]);self.assertTrue(d.estados_controle()['stunned'])
  d.ids=[];self.assertFalse(d.estados_controle()['stunned'])
 def test_efeito_zero_nao_significa_stun(self):
  self.assertFalse(self.leitor([(73,0)]).estados_controle()['stunned'])
 def test_animation_sozinha_nao_e_tratada_como_stun(self):
  self.assertFalse(self.leitor([]).estados_controle()['stunned'])

if __name__=='__main__':unittest.main()
