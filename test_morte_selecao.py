import unittest,copy,sys,threading
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from selecao_regional import BuscaRegional
from hunt_core import AgendaBuffs
from cura_prioritaria import CuraPrioritaria


class MorteSelecaoTeste(unittest.TestCase):
    def test_camera_sem_resposta_nao_repete_giro_indefinidamente(self):
        b=BuscaRegional();b.atualizar([dict(id=5458,hp=100,position=(-5,0))])
        acoes=[b.decidir(i*.1,None,dict(yaw=0,position=(0,0)))[0] for i in range(431)]
        self.assertEqual(acoes.count('orientar'),2)
        self.assertGreater(acoes.count('tab'),20)

    def test_muda_candidato_sem_alvo_apos_seis_segundos(self):
        b=BuscaRegional();m=[dict(id=i,hp=100,position=(-5,0)) for i in [5458,5459]];b.atualizar(m)
        b.decidir(0,None,None);acao,id_=b.decidir(6,None,None)
        self.assertEqual((acao,id_),('tab',5459))
        b.atualizar(m);self.assertEqual(b.preferido,5459)

    def test_alvo_confirmado_nao_e_trocado_pelo_timeout(self):
        b=BuscaRegional();m=[dict(id=i,hp=100,position=(-5,0)) for i in [5458,5459]];b.atualizar(m)
        b.decidir(0,None,None)
        self.assertEqual(b.decidir(8,m[0],None),('aceitar',m[0]))

    def test_rebuff_pendente_pausa_ao_tomar_dano_e_retoma_mesmo_indice(self):
        a=AgendaBuffs(0,['ctrl+1','ctrl+2'])
        self.assertEqual(a.proximo(0,True),'ctrl+1');a.confirmar(0)
        self.assertIsNone(a.proximo(4,False))
        self.assertTrue(a.em_andamento)
        self.assertEqual(a.proximo(8,True),'ctrl+2')

    def test_cura_reserva_tempo_para_cliente_reconhecer_cast(self):
        c=CuraPrioritaria('7',.7,154);c.enviada(0,.5)
        self.assertTrue(c.aguardando_inicio(.2));self.assertFalse(c.aguardando_inicio(.41))
        c.observar(.3,.5,dict(ready=False));self.assertFalse(c.aguardando_inicio(.31))

    def test_motor_para_rebuff_e_ataca_quando_toma_dano(self):
        import hunt_native as h
        from perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(minimize_on_start=False,heal_enabled=False,hp_keys=['','',''],buff_gap=3)
        for s in p['skills']:s['enabled']=False
        controle=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];recebeu_buff=[False];selecionado=[False];hp_mob=[100];ctrl=[False];eventos=[];teclas=[]
        def alvo():return dict(ref=1,id=4093,name='Verit Mutante',hp=hp_mob[0],hp_max=100,mp=0,mp_max=0,position=(2,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=(0,0),height=0,hp=90 if recebeu_buff[0] else 100,hp_max=100,mp=100,mp_max=100),target=alvo() if selecionado[0] else None)
            def close(self):pass
        def down(k):
            teclas.append(k)
            if k=='ctrl':ctrl[0]=True
            if k=='1' and ctrl[0]:recebeu_buff[0]=True
            elif k=='1':hp_mob[0]=0
            if k=='tab':selecionado[0]=True
        def up(k):
            if k=='ctrl':ctrl[0]=False
        def dormir(v):
            t[0]+=max(.001,v)
            if t[0]>10:controle.stop.set()
        def emitir(e):
            eventos.append(e)
            if e.get('message')=='Mob abatido; procurando o proximo.':controle.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=up)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,controle)
        self.assertEqual(hp_mob[0],0)
        self.assertEqual([e['atalho'] for e in eventos if e.get('message')=='Atalho de buff enviado.'],['ctrl+1'])
        self.assertIn('tab',teclas);self.assertFalse(ctrl[0])


if __name__=='__main__':unittest.main()
