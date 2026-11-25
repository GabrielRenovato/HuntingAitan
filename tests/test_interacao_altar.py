import struct,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from huntingaitan.rotas.interacao_altar import altar_sob_cursor,localizar_altar_clicavel,pontos_busca
from huntingaitan.rotas.entrada_jardim import PORTAL


class InteracaoAltarTeste(unittest.TestCase):
    def leitor(self,nome='Altar da Ascensão',pos=PORTAL,player=PORTAL):
        memoria={2000+0x19ac:nome.encode('cp1252')+b'\0',2000+0x1c:struct.pack('<3f',*pos,30)}
        d=SimpleNamespace(base=0,cena_validada=lambda:1000,
            u32=lambda a:{1000+0x108:2000,2004:2258,0x2f4cd90:3000}[a],
            read=lambda a,n:memoria.get(a,b'\0'*n),snapshot=lambda:dict(player=dict(hp=100,position=player)))
        return d

    def test_aceita_objeto_correto_por_nome_e_posicao(self):
        self.assertEqual(altar_sob_cursor(self.leitor())['id'],2258)
        self.assertIsNone(altar_sob_cursor(self.leitor(nome='Guarda da Floresta das Cinzas')))
        self.assertIsNone(altar_sob_cursor(self.leitor(pos=(1900,1100))))
        self.assertIsNone(altar_sob_cursor(self.leitor(player=(1850,1092))))

    def test_busca_nao_clica_em_candidato_sem_objeto_confirmado(self):
        d=self.leitor();e=Mock();cap=SimpleNamespace(capturar=lambda:None,area=dict(left=-1400,top=30,width=1280,height=960))
        with patch('huntingaitan.rotas.interacao_altar.altar_sob_cursor',return_value=None):
            self.assertIsNone(localizar_altar_clicavel(d,e,cap,(790,248),lambda:True,dormir=lambda t:None))
        e.mouseDown.assert_not_called();self.assertGreater(e.mover_sem_cursor.call_count,1)

    def test_exige_mesma_identidade_em_duas_leituras_e_respeita_monitor(self):
        d=self.leitor();e=Mock();cap=SimpleNamespace(capturar=lambda:None,area=dict(left=-1400,top=30,width=1280,height=960))
        ident=dict(ref=2000,id=2258)
        with patch('huntingaitan.rotas.interacao_altar.altar_sob_cursor',side_effect=[ident,dict(ref=3000,id=99),ident,ident]):
            r=localizar_altar_clicavel(d,e,cap,(790,248),lambda:True,dormir=lambda t:None)
        self.assertEqual(r['altar'],ident);self.assertEqual(r['ponto'],e.mover_sem_cursor.call_args.args)
        self.assertGreater(e.mover_sem_cursor.call_count,1);e.mouseDown.assert_not_called()

    def test_parada_impede_busca_e_candidatos_excluem_hud(self):
        d=self.leitor();e=Mock();cap=SimpleNamespace(capturar=lambda:None,area=dict(left=0,top=0,width=1280,height=960))
        self.assertIsNone(localizar_altar_clicavel(d,e,cap,(790,248),lambda:False))
        e.mover_sem_cursor.assert_not_called()
        ps=list(pontos_busca((1250,800),1280,960))
        self.assertEqual(len(ps),len(set(ps)))
        self.assertTrue(all(102.4<=x<1216 and 96<=y<768 for x,y in ps))


if __name__=='__main__':unittest.main()
