import math,unittest,threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from tests.test_navegacao_grade import grade
from huntingaitan.rotas.jardim_aereo import JardimAereo
from huntingaitan.rotas.recuperacao_jardim import RecuperacaoJardim
from huntingaitan.rotas.ciclo_jardim import CicloJardim
from huntingaitan.configuracao.perfil_hunt import DEFAULT


def circuito():
    j=JardimAereo.__new__(JardimAereo);pos=(4.5,9.5)
    j.grade_terreno=grade(50,20);j.recuperacao=RecuperacaoJardim(pos)
    j.pontos=[dict(pos=(40.5,9.5),id='antes_shiraz')];j.revisao=0
    j.trechos=[dict(caminho=[])];j.adotar_rota(j.grade_terreno,j.grade_terreno.caminho(pos,(40.5,9.5)),pos)
    return j,pos


class RecuperacaoTeste(unittest.TestCase):
    def test_duas_falhas_sem_deslocamento_geram_passagens_diferentes(self):
        j,pos=circuito();original=j.rota_planejada[:]
        j.observar_navegacao(pos,0,dict(estado='andando',w=True))
        self.assertTrue(j.observar_navegacao(pos,1,dict(estado='bloqueado',ponto=(12.5,9.5))))
        primeira=j.recuperacao.bloqueios.copy();self.assertTrue(primeira)
        self.assertNotEqual(original,j.rota_planejada)
        alvo=j.grade.proximo(pos,j.rota_planejada,4)
        self.assertTrue(j.observar_navegacao(pos,2,dict(estado='bloqueado',ponto=alvo)))
        self.assertGreater(len(j.recuperacao.bloqueios),len(primeira))
        self.assertTrue(all(tuple(map(math.floor,p)) not in j.recuperacao.bloqueios for p in j.rota_planejada))
        self.assertTrue(j.grade.livre(j.grade.celula(pos)))

    def test_quina_sem_w_recupera_sem_ficar_aguardando_para_sempre(self):
        j,pos=circuito();plano=dict(estado='andando',w=False,giro=None,ponto=(12.5,9.5))
        for t in (0,1,2):self.assertFalse(j.observar_navegacao(pos,t,plano))
        self.assertTrue(j.observar_navegacao(pos,3,plano))

    def test_pausa_para_luta_nao_conta_no_prazo_da_recuperacao(self):
        j,pos=circuito()
        for t in range(10):j.observar_navegacao(pos,t,dict(estado='aguardar_grade'))
        j.observar_navegacao(pos,100,dict(estado='aguardar_grade'))
        self.assertFalse(j.recuperacao.reiniciar)
        for t in range(101,126):j.observar_navegacao(pos,t,dict(estado='aguardar_grade'))
        self.assertTrue(j.recuperacao.reiniciar)

    def test_bloqueio_persistente_sai_sem_contar_trecho_e_sem_encerrar_ciclo(self):
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        def motor(p,e,c):e(dict(event='jardim_reset'))
        sair=Mock(return_value=True)
        ciclo=CicloJardim(DEFAULT,c,lambda e:None,lambda:dict(position=(3351,3295),hp=1),motor,sair,Mock())
        ciclo.passo();self.assertEqual(ciclo.etapa,'jardim_corrigir_entrada');self.assertEqual(ciclo.trechos,0)
        ciclo.passo();sair.assert_called_once();self.assertEqual(ciclo.etapa,'jardim_retornar');self.assertFalse(c.stop.is_set())

    def test_duas_posicoes_reais_do_log_tem_rota_e_abandonam_celula_que_falhou(self):
        raiz=Path(r'C:\GoLevel\AikaOnline')
        if not raiz.exists():self.skipTest('Arquivos locais do cliente indisponiveis')
        for pos,alvo in [((3511.3,3268.43),(3511.5,3270.5)),((3689.13,3307.15),(3688.5,3303.5))]:
            with self.subTest(pos=pos):
                j=JardimAereo(pos);j.conferir(raiz)
                j.observar_navegacao(pos,0,dict(estado='andando',w=True))
                self.assertTrue(j.observar_navegacao(pos,1,dict(estado='bloqueado',ponto=alvo)))
                self.assertTrue(j.recuperacao.bloqueios)
                self.assertTrue(all(tuple(map(math.floor,p)) not in j.recuperacao.bloqueios for p in j.rota_planejada))
                self.assertTrue(all(j.grade.passagem(j.grade.celula(a),j.grade.celula(b)) for a,b in zip(j.rota_planejada,j.rota_planejada[1:])))

if __name__=='__main__':unittest.main()
