import copy,unittest
from unittest.mock import patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT
from huntingaitan.leitura.replay import reproduzir
from huntingaitan.leitura.sessao import DadosReplay,para_json

JOGADOR=dict(ref=1,id=1,name='Heroi',position=(10.,20.),height=0.,heading=90.,hp=100,hp_max=100,mp=100,mp_max=100,hostile=False)

def mob(id_=2049):
    return dict(ref=1000+id_,id=id_,name='Verit Mutante',position=(12.,20.),height=0.,heading=0.,hp=100,hp_max=100,mp=0,mp_max=0,hostile=True,slot=1)

def sessao(lista,n=800,inicio=(10.,20.)):
    """Sem alvo selecionado; listar_mobs devolve `lista` (ou um erro, se for str).

    O motor captura a base nas 3 primeiras leituras (ou usa a base fixa do modo); depois o jogador
    esta a 10 de distancia dela, como logo apos abater um mob longe da base, que e quando o TAB
    as cegas acontecia."""
    comeco=dict(JOGADOR,position=inicio);longe=dict(JOGADOR,position=(inicio[0]+10,inicio[1]))
    leituras=[comeco]*3+[longe]*(n-3)
    reg=[dict(m='snapshot',r=para_json(dict(source='native',player=j,target=None))) for j in leituras]
    if isinstance(lista,str):reg+=[dict(m='listar_mobs',erro=lista) for _ in range(n)]
    else:reg+=[dict(m='listar_mobs',r=para_json(lista)) for _ in range(n)]
    reg+=[dict(m='estados_controle',r=para_json(dict(stunned=False,paralyzed=False,frozen=False,casting=False,effects={73:0,219:0,235:0}))) for _ in range(n)]
    reg+=[dict(m='recargas_atalhos',r=para_json({})) for _ in range(n)]
    reg+=[dict(m='caca_original_ativa',r=False) for _ in range(n)]
    return reg

def perfil():
    p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,hp_keys=['','',''])
    return p

def tabs(traco):
    return [t for t,tipo,k in traco['teclas'] if k=='tab' and tipo=='down']

class SemLista(DadosReplay):
    """Cliente sem a leitura de mobs: o TAB e a unica forma de encontrar alvo."""
    def __getattr__(self,nome):
        if nome=='listar_mobs':raise AttributeError(nome)
        return super().__getattr__(nome)

class BuscaSemTabTest(unittest.TestCase):
    def test_alvo_selecionado_valido_nao_depende_da_lista_regional(self):
        registros=sessao([])
        for r in registros:
            if r['m']=='snapshot':
                r['r']=para_json(dict(source='native',player=JOGADOR,target=mob()))
        t=reproduzir(registros,perfil=perfil(),limite_segundos=2)
        self.assertIsNone(t['erro']);self.assertEqual(tabs(t),[])
        self.assertTrue(any(tipo=='down' and k=='1' for _,tipo,k in t['teclas']))

    def test_lista_sem_mobs_vivos_nao_aperta_tab(self):
        # Limite de 4 s: depois de no_damage_seconds o motor volta a base pela grade do jogo,
        # que o replay nao reproduz. A janela de 4 s e onde o TAB as cegas acontecia.
        t=reproduzir(sessao([]),perfil=perfil(),limite_segundos=4)
        self.assertIsNone(t['erro']);self.assertGreater(t['duracao'],3)
        self.assertEqual(tabs(t),[])

    def test_todos_os_modos_de_base_fixa_nao_apertam_tab_sem_mob_vivo(self):
        # Os modos de base fixa passam pelo estado de selecao e precisam da regra; os circuitos
        # sao cobertos por test_circuito_com_lista_vazia_percorre_a_rota_sem_tab.
        from huntingaitan.configuracao.perfil_hunt import validar
        modos=['base','buto_trio']
        testados=0
        for modo in modos:
            with self.subTest(modo=modo):
                try:p=validar(dict(patrol_mode=modo,buffs_enabled=False,hp_keys=['','','']))
                except ValueError:self.skipTest(f'modo {modo} nao existe nesta versao');continue
                inicio=tuple(float(v) for v in p['base']) if not p['auto_base'] else (10.,20.)
                t=reproduzir(sessao([],inicio=inicio),perfil=p,limite_segundos=4)
                self.assertIsNone(t['erro']);self.assertEqual(tabs(t),[]);testados+=1
        self.assertGreaterEqual(testados,1)

    def test_circuito_com_lista_vazia_percorre_a_rota_sem_tab(self):
        import sys,threading
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        import huntingaitan.combate.hunt_native as h
        if not hasattr(h,'conferir_plantas'):self.skipTest('circuito de plantas nao existe nesta versao')
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='ungor_plantas',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for s in p['skills']:s['enabled']=False
        control=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];pos=[(2430.,1367.)];teclas=[];navegacao=[]
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=None)
            def listar_mobs(self,*args):return []
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kw):
                pos[0]=tuple(args[3]);navegacao.append(pos[0]);return dict(estado='chegou',w=False)
        def dormir(s):
            tempo[0]+=max(.001,s)
            if tempo[0]>30:control.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1
        entrada=SimpleNamespace(PAUSE=0,keyDown=teclas.append,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h,'conferir_plantas'),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):
            h.main(p,lambda e:None,control)
        self.assertTrue(navegacao,'o motor deveria seguir a rota');self.assertEqual(teclas.count('tab'),0)

    def test_lista_indisponivel_nao_aperta_tab_as_cegas(self):
        t=reproduzir(sessao('Mapa mudou durante a leitura das entidades'),perfil=perfil(),limite_segundos=15)
        self.assertIsNone(t['erro']);self.assertEqual(tabs(t),[])

    def test_mob_vivo_na_lista_continua_selecionando_com_tab(self):
        t=reproduzir(sessao([mob()]),perfil=perfil(),limite_segundos=6)
        self.assertGreater(len(tabs(t)),0)

    def test_sem_leitura_de_mobs_o_tab_continua_como_reserva(self):
        with patch('huntingaitan.leitura.replay.DadosReplay',SemLista):
            t=reproduzir(sessao([]),perfil=perfil(),limite_segundos=6)
        self.assertGreater(len(tabs(t)),0)

if __name__=='__main__':unittest.main()
