import struct,tempfile,unittest
from pathlib import Path
from huntingaitan.leitura import captura as cap

ORIGEM=0x10000;TAM=0x400000
BASE=0x20000;ACTIVE=0x10;CONTEXTO_RVA=0x14
CENA=ORIGEM+0x1000;CONTEXTO=ORIGEM+0x100000;JOGADOR=ORIGEM+0x200000;ALVO=ORIGEM+0x210000;MOB=ORIGEM+0x220000;DIALOGO=ORIGEM+0x300000

class DadosFalsos:
    """Memoria simulada: cena com um ponteiro de dialogo em +0x1a8 e um contador (ruido) em +0x500."""
    sha256='falso';layout=dict(player_offset=0x104,target_offset=0x90)
    base=BASE
    def __init__(self):
        self.mem=bytearray(TAM)
        self.u32w(BASE+ACTIVE,CENA);self.u32w(BASE+CONTEXTO_RVA,CONTEXTO)
        self.u32w(CENA+0x104,JOGADOR);self.u32w(CENA+0x90,0)
        self.ruido=0;self.ilegivel=None
    def cfg(self,nome):return {'context_rva':CONTEXTO_RVA}[nome]
    def u32w(self,endereco,valor):struct.pack_into('<I',self.mem,endereco-ORIGEM,valor)
    def u32(self,endereco):return struct.unpack_from('<I',self.read(endereco,4))[0]
    def read(self,endereco,tamanho):
        if endereco<ORIGEM or endereco+tamanho>ORIGEM+TAM:raise RuntimeError('fora da memoria simulada')
        if self.ilegivel and self.ilegivel[0]<=endereco<self.ilegivel[1]:raise RuntimeError('pagina ilegivel')
        return bytes(self.mem[endereco-ORIGEM:endereco-ORIGEM+tamanho])
    def cena_validada(self):return self.u32(BASE+ACTIVE)
    def snapshot(self):return dict(player=dict(position=(0,0),height=0))
    def listar_mobs(self,centro,raio,player):return [dict(ref=MOB)]
    def abrir_dialogo(self,aberto):self.u32w(CENA+0x1a8,DIALOGO if aberto else 0)
    def passo(self):
        self.ruido+=1;self.u32w(CENA+0x500,self.ruido);self.u32w(JOGADOR+0x1c,self.ruido*7)

def grupo(dados,rotulo,n=3,**kw):
    capturas=[]
    for _ in range(n):
        dados.passo();capturas.append(cap.capturar(dados,rotulo,**kw))
    return capturas

class CapturaTest(unittest.TestCase):
    def test_captura_regioes_conhecidas_e_omite_alvo_nulo(self):
        c=cap.capturar(DadosFalsos(),'x')
        self.assertEqual(sorted(c['regioes']),['cena','contexto','jogador'])
        self.assertEqual(len(c['regioes']['cena']),cap.TAMANHOS['cena'])
        self.assertEqual(c['meta']['regioes']['cena']['endereco'],CENA)

    def test_inclui_alvo_e_mob_quando_existem(self):
        d=DadosFalsos();d.u32w(CENA+0x90,ALVO)
        self.assertIn('alvo',cap.capturar(d,'x')['regioes'])
        self.assertIn('mob',cap.capturar(d,'x',mob=True)['regioes'])
        self.assertNotIn('mob',cap.capturar(d,'x')['regioes'])

    def test_candidatos_acha_o_campo_de_estado_e_descarta_ruido(self):
        d=DadosFalsos();d.abrir_dialogo(False);fechado=grupo(d,'fechado');d.abrir_dialogo(True);aberto=grupo(d,'aberto')
        achados=cap.candidatos(fechado,aberto,'cena')
        self.assertEqual([c['offset'] for c in achados],[0x1a8])
        self.assertEqual((achados[0]['a'],achados[0]['b']),(0,DIALOGO))
        self.assertEqual(cap.candidatos(fechado,aberto,'jogador'),[])

    def test_com_uma_captura_por_grupo_o_ruido_aparece(self):
        d=DadosFalsos();d.abrir_dialogo(False);a=grupo(d,'a',1);d.abrir_dialogo(True);b=grupo(d,'b',1)
        self.assertGreater(len(cap.candidatos(a,b,'cena')),1)

    def test_blocos_ilegiveis_sao_registrados_e_ignorados(self):
        d=DadosFalsos();d.abrir_dialogo(False)
        d.ilegivel=(CENA+0x1000,CENA+0x2000);a=grupo(d,'a')
        self.assertEqual(a[0]['meta']['regioes']['cena']['ausentes'][0],(0x1000,0x1000))
        d.abrir_dialogo(True);b=grupo(d,'b')
        self.assertEqual([c['offset'] for c in cap.candidatos(a,b,'cena')],[0x1a8])
        d.u32w(CENA+0x1100,5);b2=grupo(d,'b')
        self.assertNotIn(0x1100,[c['offset'] for c in cap.candidatos(a,b2,'cena')])

    def test_extra_segue_ponteiro_valido_e_ignora_nulo(self):
        d=DadosFalsos();d.abrir_dialogo(True);struct.pack_into('<I',d.mem,DIALOGO-ORIGEM,0xabcd)
        c=cap.capturar(d,'x',extras=['cena+0x1a8->0x40'])
        self.assertEqual(struct.unpack_from('<I',c['regioes']['cena+0x1a8'])[0],0xabcd)
        self.assertEqual(c['meta']['regioes']['cena+0x1a8']['endereco'],DIALOGO)
        d.abrir_dialogo(False);self.assertNotIn('cena+0x1a8',cap.capturar(d,'x',extras=['cena+0x1a8->0x40'])['regioes'])

    def test_extra_invalido_e_rejeitado(self):
        for ruim in ['cena','cena+0x1a8','cena+0x1a8->0','desconhecida+0x4->0x10','cena+0x3->0x10','cena+0x4->0xffffff']:
            with self.subTest(ruim=ruim),self.assertRaises(ValueError):cap.analisar_extra(ruim)
        self.assertEqual(cap.analisar_extra('cena+0x1a8->0x400'),('cena',0x1a8,0x400))

    def test_salvar_e_carregar_preservam_a_captura(self):
        d=DadosFalsos();c=cap.capturar(d,'rot',extras=[])
        with tempfile.TemporaryDirectory() as pasta:
            destino=Path(pasta)/'sub'/'a.cap.zip';cap.salvar(c,destino);volta=cap.carregar(destino)
        self.assertEqual(volta['regioes'],c['regioes']);self.assertEqual(volta['meta']['rotulo'],'rot')

    def test_classificacao_e_agrupamento(self):
        self.assertEqual(cap.tipo_mudanca(0,1)[1],'flag 0/1')
        self.assertEqual(cap.tipo_mudanca(0,DIALOGO)[1],'nulo <-> ponteiro')
        self.assertEqual(cap.tipo_mudanca(0,0x90000000)[1],'zero <-> valor')
        self.assertEqual(cap.tipo_mudanca(3,9)[1],'contador pequeno')
        lista=cap.classificar([dict(offset=8,a=5,b=900),dict(offset=4,a=0,b=1),dict(offset=0,a=0,b=DIALOGO)])
        self.assertEqual([c['offset'] for c in lista],[4,0,8])
        self.assertEqual([[c['offset'] for c in b] for b in cap.agrupar_adjacentes(lista)],[[0,4,8]])
        self.assertEqual(cap.descrever(0x3f800000)['f32'],1.0);self.assertEqual(cap.descrever(0xffffffff)['i32'],-1)

    def test_regioes_comuns(self):
        d=DadosFalsos();a=[cap.capturar(d,'a')];d.u32w(CENA+0x90,ALVO);b=[cap.capturar(d,'b')]
        self.assertEqual(cap.regioes_comuns(a,b),['cena','contexto','jogador'])

if __name__=='__main__':unittest.main()
