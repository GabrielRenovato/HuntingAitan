import sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from huntingaitan.rotas.operacoes_npc import reparar_e_vender
from tests.test_servico_npc import DESC

class OperacaoTeste(unittest.TestCase):
    def executar(self,reparo_funciona=True,janela_alterada=False,descricao_indisponivel=False,leitura_lenta=False,venda_pendente=False):
        fase=['venda' if venda_pendente else 'loja'];ouro=[1000];pos=[(0,0)];vendido=[False];tempo=[0.];cliques=[];eventos=[]
        self.teclas=[];leituras_venda=[0];ordem=[];self.ordem=ordem
        cfg=dict(ouro=1000,escala=1.,origem=(0,0),fechar=(10,10),paginas=[(50,50)],slots=[(70,70)])
        class UI:
            def loja(self,t,*a):return dict(cfg,ouro=ouro[0]) if fase[0]=='loja' else None
            def menu(self,t,op,*a):return (30,30) if op=='reparar' else (20,20)
            def confirmacao_estavel(self,t,v):return not janela_alterada
            def npc(self,t):return (5,5)
            def dialogo(self,t,tipo):
                if tipo=='reparo' and fase[0]=='reparo':return dict(custo=20,confirmar=(40,40),cancelar=(45,45))
                if tipo=='venda' and fase[0]=='venda':
                    leituras_venda[0]+=1
                    return dict(nome='Espada de Termes',preco=99 if janela_alterada and leituras_venda[0]>1 else 50,confirmar=(40,40),cancelar=(45,45))
                return None
            def equipamento_sob_cursor(self,*a):
                ordem.append(('ler',tempo[0],fase[0]))
                if leitura_lenta:tempo[0]+=5
                return None if descricao_indisponivel else ('Espada de Termes',DESC)
        def mover(ent,x,y):pos[0]=(x,y);return True
        def down(button='left'):
            p=pos[0];cliques.append((fase[0],button,p,ouro[0]))
            if button=='right':ordem.append(('right',tempo[0],fase[0]));fase[0]='venda';return
            if p==(10,10):fase[0]='menu'
            elif p==(30,30):fase[0]='reparo'
            elif p==(20,20):fase[0]='loja'
            elif p==(45,45):fase[0]='loja'
            elif p==(40,40) and fase[0]=='reparo':fase[0]='menu';ouro[0]-=20 if reparo_funciona else 0
            elif p==(40,40) and fase[0]=='venda':fase[0]='loja';ouro[0]+=50;vendido[0]=True
        class MSS:
            def __enter__(self):return self
            def __exit__(self,*a):pass
        def capturar():
            im=np.zeros((500,600,3),np.uint8)
            if vendido[0]:im[54:86,54:86]=255
            return im
        cap=SimpleNamespace(area=dict(left=0,top=0),capturar=capturar)
        d=SimpleNamespace(hwnd=1,u=SimpleNamespace(GetForegroundWindow=lambda:1),snapshot=lambda:dict(player=dict(hp=100,position=(1892,1067))))
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        def key_down(k):
            ordem.append(('enter',tempo[0],fase[0]))
            self.assertEqual(k,'enter');self.assertEqual(fase[0],'venda');self.teclas.append(k)
            fase[0]='loja';ouro[0]+=50;vendido[0]=True
        entrada=SimpleNamespace(PAUSE=0,mouseDown=down,mouseUp=lambda **k:None,keyDown=key_down,keyUp=lambda k:None)
        def inventario(d):
            return dict(ouro=ouro[0],bolsas=[0],itens=[dict(slot=0,id=0 if vendido[0] else 1042,serial=123,atual=8,maxima=151,refino=0)])
        def sleep(v):tempo[0]+=max(.01,v)
        with patch('cv2.imwrite',return_value=True),patch('huntingaitan.rotas.operacoes_npc.precisa_reparar',return_value=True),patch('huntingaitan.rotas.operacoes_npc.ler_inventario',inventario),patch('huntingaitan.rotas.operacoes_npc.equipamento_candidato',lambda d,i:bool(i['id'])),patch('huntingaitan.rotas.operacoes_npc.nome_item',return_value='Espada de Termes'),patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),mss=SimpleNamespace(MSS=MSS),pydirectinput=entrada),patch('huntingaitan.rotas.interface_npc.InterfaceNPC',UI),patch('huntingaitan.visao.captura_aika.CapturaAika',return_value=cap),patch('huntingaitan.entrada.entrada_segura.mover_cursor_fisico',mover),patch('huntingaitan.visao.avisos_hunt.DetectorAvisos') as av,patch('huntingaitan.rotas.operacoes_npc.time.monotonic',lambda:tempo[0]),patch('huntingaitan.rotas.operacoes_npc.time.sleep',sleep):
            av.return_value.localizar.return_value=None
            ok=reparar_e_vender(d,c,eventos.append)
        return ok,cliques,eventos,c

    def test_repara_antes_de_vender_e_verifica_remocao_e_saldo(self):
        ok,cliques,eventos,c=self.executar()
        self.assertTrue(ok)
        self.assertEqual(self.teclas,['enter'])
        self.assertFalse(any(fase=='venda' and botao=='left' for fase,botao,_,_ in cliques))
        direitos=[e for e in cliques if e[1]=='right'];self.assertEqual(len(direitos),1);self.assertEqual(direitos[0][3],980)
        self.assertTrue(any(e.get('state')=='jardim_npc_concluido' and e.get('vendidos')==1 for e in eventos))

    def test_reparo_sem_resposta_nao_clica_para_vender(self):
        ok,cliques,eventos,c=self.executar(False)
        self.assertFalse(ok);self.assertFalse(any(e[1]=='right' for e in cliques))
        self.assertEqual(c.reason,'servico_npc_nao_confirmado')

    def test_janela_alterada_nao_recebe_enter(self):
        ok,cliques,eventos,c=self.executar(janela_alterada=True)
        self.assertFalse(ok);self.assertEqual(self.teclas,[])
        self.assertTrue(any('Venda mudou' in e.get('detail','') for e in eventos))

    def test_item_sem_leitura_nao_e_contado_como_servico_completo(self):
        ok,cliques,eventos,c=self.executar(descricao_indisponivel=True)
        self.assertFalse(ok);self.assertEqual(self.teclas,[])
        self.assertFalse(any(e.get('state')=='jardim_npc_concluido' for e in eventos))
        self.assertTrue(any('ainda sem identificacao' in e.get('detail','') for e in eventos))

    def test_leitura_lenta_nao_atrasa_clique_mas_bloqueia_enter(self):
        ok,cliques,eventos,c=self.executar(leitura_lenta=True)
        self.assertTrue(ok)
        self.assertEqual([e[0] for e in self.ordem],['right','ler','enter'])
        self.assertEqual(self.ordem[1][2],'venda')
        self.assertGreaterEqual(self.ordem[2][1]-self.ordem[1][1],5)

    def test_reinicio_cancela_pergunta_antiga_antes_de_reparar(self):
        ok,cliques,eventos,c=self.executar(venda_pendente=True)
        self.assertTrue(ok)
        self.assertEqual(cliques[0],('venda','left',(45,45),1000))
        self.assertEqual(self.teclas,['enter'])

if __name__=='__main__':unittest.main()
