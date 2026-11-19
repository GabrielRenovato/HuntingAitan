import copy,math,unittest
from unittest.mock import patch
from jardim_aereo import JardimAereo,dentro_jardim,plano_jardim
from mina_lenfer import MinaLenfer,plano_mina
from perfil_hunt import validar
from interface_mina import VerificadorElite
from test_navegacao_grade import grade

class JardimTeste(unittest.TestCase):
    def test_perfil_fixa_hostis_e_fonte_nativa_sem_ativar_ciclo_da_mina(self):
        p=validar(dict(patrol_mode='jardim_aereo',data_source='visual',target='verit',mina_repeat=True))
        self.assertEqual((p['target'],p['data_source'],p['mina_repeat']),('qualquer','native',False))

    def test_jardim_abrange_dois_blocos_mas_exclui_mina_e_mundo_externo(self):
        for p in [(3351,3295),(3633.5,3212.5)]:self.assertTrue(dentro_jardim(p))
        for p in [(2850,3344),(2716,1611),(0,0)]:
            self.assertFalse(dentro_jardim(p))
            with self.assertRaises(RuntimeError):JardimAereo(p)

    def test_rota_percorre_passos_adjuntos_ate_altar_em_outro_bloco(self):
        d=plano_jardim();r=d['trechos'][0]['caminho']
        self.assertEqual(d['registro_dificil'],21);self.assertEqual(d['entrada'],[3351,3295])
        self.assertGreater(len(r),2000)
        self.assertTrue(all(dentro_jardim(p) for p in r))
        self.assertTrue(all(math.dist(a,b)<=math.sqrt(2)+1e-5 for a,b in zip(r,r[1:])))
        self.assertLess(r[0][0],3584);self.assertGreater(r[-1][0],3584)

    def test_somente_seridunn_do_jardim_confirma_conclusao(self):
        j=JardimAereo((3351,3295));pos=(3633.5,3212.5)
        for nome in ['Malik','Guarda de Seridunn','Seridunn Corrompido','Portao do Jardim','Administrador do Jardim Celeste']:
            self.assertIsNone(j.registrar_abate(1,nome,pos,0))
        self.assertEqual(j.registrar_abate(2,'Seridunn',pos,0),'seridunn')
        self.assertEqual(j.destino(pos,0)['estado'],'aguardar')
        self.assertEqual(j.destino(pos,15)['estado'],'concluido')

    def test_chegar_no_altar_nao_finge_abate(self):
        j=JardimAereo((3351,3295));pos=j.pontos[-1]['pos']
        self.assertEqual(j.destino(pos,1000)['estado'],'aguardar_chefe')
        self.assertFalse(j.abates)

    def test_mina_continua_exigindo_malik(self):
        m=MinaLenfer((2850,3344));j=JardimAereo((3351,3295))
        self.assertTrue(m.eh_chefe('Malik'));self.assertFalse(m.eh_chefe('Seridunn'))
        self.assertTrue(j.eh_chefe('Seridunn'));self.assertFalse(j.eh_chefe('Malik'))

    def test_filtro_prioriza_seridunn_sem_selecionar_por_parede(self):
        j=JardimAereo((3351,3295));j.grade=grade(16,8);j.rota_planejada=[(1.5,1.5),(14.5,1.5)]
        mobs=[dict(id=1,name='Guarda',position=(3.5,1.5)),dict(id=2,name='Seridunn',position=(10.5,1.5))]
        self.assertEqual([m['id'] for m in j.filtrar_mobs(mobs,(1.5,1.5),20)],[2])

    def test_rota_de_uma_sessao_nao_altera_o_plano_da_outra_dg(self):
        antes=copy.deepcopy(plano_jardim());m=copy.deepcopy(plano_mina())
        j=JardimAereo((3351,3295));j.grade=grade(20,8);j.pontos=[dict(id=0,pos=(18.5,1.5),chefe='seridunn',espera=15)]
        j.replanejar_passagem((1.5,1.5))
        self.assertEqual(plano_jardim(),antes);self.assertEqual(plano_mina(),m)

    def test_indicador_dificil_nao_aceita_elite_ou_normal(self):
        import numpy as np
        for texto,esperado in [('Difícil',True),('Dificil',True),('Elite',False),('Normal',False)]:
            v=VerificadorElite(ocr=lambda im:([[None,texto,.99]],None),dificuldade='dificil')
            self.assertEqual(v.confirmar(np.zeros((500,700,3),np.uint8)),esperado)

if __name__=='__main__':unittest.main()
