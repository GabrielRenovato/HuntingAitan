import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from selecao_regional import BuscaRegional
from hunt_core import AgendaBuffs,executar_buff


class BuscaBuffsTeste(unittest.TestCase):
    def test_lista_atualizada_nao_retorna_sempre_aos_dois_primeiros_ids(self):
        b=BuscaRegional();m=[dict(id=i,hp=100,position=(i,0)) for i in [10,11,12,13]]
        b.atualizar(m);b.decidir(0,None,None)
        for t,id_ in [(6,11),(12,12),(18,13)]:
            b.atualizar(m);self.assertEqual(b.decidir(t,None,None),('tab',id_))

    def test_prazo_global_nao_reinicia_ao_trocar_preferencia(self):
        b=BuscaRegional();b.atualizar([dict(id=i,hp=100,position=(i,0)) for i in [10,11,12]])
        b.decidir(0,None,None,pos=(0,0));b.decidir(6,None,None,pos=(0,0))
        acao,m=b.decidir(8,None,None,pos=(0,0))
        self.assertEqual(acao,'aproximar');self.assertEqual(m['id'],11)

    def test_tres_aproximacoes_sem_selecao_forcam_volta_a_base(self):
        b=BuscaRegional();b.atualizar([dict(id=10,hp=100,position=(10,0))])
        b.decidir(0,None,None,pos=(0,0))
        for t in [8,16,24]:self.assertEqual(b.decidir(t,None,None,pos=(0,0))[0],'aproximar')
        self.assertEqual(b.decidir(32,None,None,pos=(0,0))[0],'retornar')

    def test_buff_atrasado_229s_nao_adia_os_anteriores(self):
        a=AgendaBuffs(0,['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5'])
        for t,k in [(0,'ctrl+1'),(16,'ctrl+2'),(30,'ctrl+3'),(45,'ctrl+4'),(229,'ctrl+5')]:
            self.assertEqual(a.proximo(t,True),k);a.confirmar(t)
        self.assertEqual(a.vencimentos['ctrl+1'],540)
        self.assertEqual(a.vencimentos['ctrl+5'],769)
        self.assertEqual(a.proximo(540,True),'ctrl+1')

    def test_falha_de_entrada_nao_confirma_envio_de_buff(self):
        eventos=[]
        def down(k):eventos.append(('down',k));return k!='2'
        self.assertFalse(executar_buff('ctrl+2',down,lambda k:eventos.append(('up',k)),lambda t:None,lambda:True))
        self.assertEqual(eventos[-1],('up','ctrl'))

    def motor(self,buff,renovacao=False):
        import hunt_native as h
        from perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=buff,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''],buff_gap=3)
        for v in p['skills']:v['enabled']=False
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];pos=[(0,0)];alvo_selecionado=[False];aproximou=[False];ctrl=[False];buff1=[False];buff2=[False];hp=[100];eventos=[];teclas=[];navs=[]
        def alvo():return dict(ref=1,id=4093,name='Verit Mutante',hp=hp[0],hp_max=100,mp=0,mp_max=0,position=(2 if buff else 8,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=90 if buff1[0] else 100,hp_max=100,mp=100,mp_max=100),target=alvo() if alvo_selecionado[0] else None)
            def listar_mobs(self,*args):return [alvo()] if hp[0]>0 else []
            def caca_original_ativa(self):return False
            def camera_regional(self):return dict(yaw=180,position=(0,0))
            def cena_validada(self):return 1
            def entidade(self,r):return alvo()
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kw):
                navs.append(t[0]);aproximou[0]=True;pos[0]=(6,0)
                return dict(estado='chegou',w=False)
        def down(k):
            teclas.append((t[0],k))
            if k=='ctrl':ctrl[0]=True
            if ctrl[0] and k=='1':buff1[0]=True
            if ctrl[0] and k=='2':buff2[0]=True
            if k=='tab' and (buff or aproximou[0]):alvo_selecionado[0]=True
            if k=='1' and not ctrl[0] and alvo_selecionado[0] and (buff2[0] if buff else aproximou[0]):hp[0]=0
        def up(k):
            if k=='ctrl':ctrl[0]=False
        def dormir(v):
            t[0]+=max(.001,v)
            if t[0]>30:c.stop.set()
        def emitir(e):
            eventos.append(e)
            if e.get('message')=='Mob abatido; procurando o proximo.':c.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=up)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'AgendaBuffs',lambda inicio,*args:AgendaBuffs(inicio+2 if renovacao else inicio,*args)),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,c)
        self.assertEqual(hp[0],0);self.assertFalse(ctrl[0]);return eventos,teclas,navs

    def test_renovacao_durante_luta_pausa_ataques_ate_ultimo_buff(self):
        eventos,teclas,navs=self.motor(True,renovacao=True)
        inicio=next(i for i,e in enumerate(eventos) if e.get('message')=='Ciclo de buffs iniciado; ataque, TAB e movimento suspensos.')
        fim=next(i for i,e in enumerate(eventos) if e.get('message')=='Ciclo de buffs concluido; combate liberado com a selecao preservada.')
        self.assertTrue(any(e.get('kind')=='normal' for e in eventos[:inicio]))
        self.assertFalse(any(e.get('event')=='action' for e in eventos[inicio:fim]))
        self.assertEqual(len([e for e in eventos[inicio:fim] if e.get('message')=='Atalho de buff enviado.']),5)
        self.assertTrue(any(e.get('kind')=='normal' for e in eventos[fim:]))
        self.assertEqual(sum(k=='tab' for _,k in teclas),1)

    def test_motor_aproxima_apos_oito_segundos_sem_alvo_e_retoma_combate(self):
        eventos,teclas,navs=self.motor(False)
        self.assertTrue(navs);self.assertGreaterEqual(navs[0],8)
        self.assertTrue(any(e.get('message') in ['Alvo confirmado apos aproximacao de busca.','Alvo confirmado por dados internos.'] for e in eventos))

    def test_ciclo_buffs_nao_envia_tab_ou_ataques_entre_slots_mesmo_com_dano(self):
        eventos,teclas,navs=self.motor(True)
        self.assertIn('ctrl+2',[e.get('atalho') for e in eventos])
        instante_buff2=next(t for t,k in teclas if k=='2')
        self.assertGreaterEqual(instante_buff2,3)
        self.assertEqual([e['atalho'] for e in eventos if e.get('message')=='Atalho de buff enviado.'],['ctrl+1','ctrl+2','ctrl+3','ctrl+4','ctrl+5'])
        fim=next(i for i,e in enumerate(eventos) if e.get('message')=='Ciclo de buffs concluido; combate liberado com a selecao preservada.')
        self.assertFalse(any(e.get('event')=='action' for e in eventos[:fim]))
        self.assertGreater(next(t for t,k in teclas if k=='tab'),max(t for t,k in teclas if k=='ctrl'))
        self.assertTrue(any(e.get('kind')=='normal' for e in eventos))


if __name__=='__main__':unittest.main()
