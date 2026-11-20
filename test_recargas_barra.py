import struct
import unittest
from hunt_core import CadenciaCombate
from recargas_barra import decodificar
from dados_internos import DadosInternos


class RecargasBarraTeste(unittest.TestCase):
    def test_skill_liberada_antes_do_timer_configurado(self):
        c=CadenciaCombate({'recargas':{'3':150}});c.registrar('3',0)
        self.assertEqual(c.escolher(2,True,True,1,True,{'3':dict(ready=True)}),'3')

    def test_recarga_real_bloqueia_mesmo_com_timer_expirado(self):
        c=CadenciaCombate({'recargas':{'3':1}})
        self.assertNotEqual(c.escolher(200,True,True,1,True,{'3':dict(ready=False)}),'3')

    def test_falha_de_leitura_usa_timer_e_nao_disponibilidade_antiga(self):
        c=CadenciaCombate({'recargas':{'3':150}});c.registrar('3',0)
        self.assertNotEqual(c.escolher(2,True,True,1,True,{}),'3')

    def test_habilidade_sem_recarga_nao_monopoliza_fila(self):
        c=CadenciaCombate({'recargas':{'3':150,'4':15,'5':17}})
        reais={k:dict(ready=True) for k in c.recargas}
        for i,esperada in enumerate(['3','4','1','5','3']):
            tecla=c.escolher(i,True,True,1,True,reais)
            self.assertEqual(tecla,esperada);c.registrar(tecla,i)

    def test_nao_reenvia_instantaneamente_se_cliente_recusar(self):
        c=CadenciaCombate({'recargas':{'3':150}});c.registrar('3',0)
        self.assertNotEqual(c.escolher(.7,True,True,1,True,{'3':dict(ready=True)}),'3')

    def test_decodifica_skills_sem_confundir_itens_e_buffs(self):
        slots=[(1<<4)|2,(8070<<4)|6,(113<<4)|2]+[0]*37
        slots[8]=(161<<4)|2
        cds=[0.]*43;cds[7]=.4
        r=decodificar(slots,cds)
        self.assertEqual(set(r),{'1','3'})
        self.assertTrue(r['1']['ready']);self.assertFalse(r['3']['ready'])
        cds[7]=0.;self.assertTrue(decodificar(slots,cds)['3']['ready'])

    def test_valor_invalido_nao_significa_pronta(self):
        slots=[(113<<4)|2]+[0]*39;cds=[0.]*43
        for v in [float('nan'),float('inf'),-1]:
            cds[7]=v;self.assertEqual(decodificar(slots,cds),{})

    def test_leitura_de_perfil_do_personagem(self):
        d=object.__new__(DadosInternos);d.base=0x400000
        ctx,gestor,inicio=0x2000000,0x3000000,0x4000000
        d.u32=lambda a:{0x2f9b1e0:ctx,0x322669c:gestor,gestor+0x614:1}[a]
        memoria={ctx+0x7fea4:b'alfeim\0'+bytes(121),gestor+0x620:struct.pack('<2I',inicio,inicio+0x120),inicio:b'alfeim\0'+bytes(121),inicio+128:struct.pack('<40I',(113<<4)|2,*([0]*39)),ctx+0x8bda0:bytes(172)}
        d.read=lambda a,n:memoria[a]
        self.assertEqual(d.recargas_atalhos()['1']['skill'],113)
        memoria[inicio]=b'outro\0'+bytes(122)
        with self.assertRaises(RuntimeError):d.recargas_atalhos()


if __name__=='__main__':unittest.main()
