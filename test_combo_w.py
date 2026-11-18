import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from cancelamento_normal import CancelamentoNormal,executar_combo


class ComboWTeste(unittest.TestCase):
    def executar(self,normal):
        eventos=[];t=[0.]
        def down(k):eventos.append(('down',k,t[0]));return True
        def up(k):eventos.append(('up',k,t[0]))
        def esperar(s):t[0]+=s
        r=executar_combo(down,up,esperar,lambda:True,'1' if normal else '4',normal)
        self.assertEqual(r,(True,True));self.assertEqual(eventos[0][2],eventos[1][2])
        self.assertAlmostEqual(t[0],.035)
        return eventos

    def test_w_e_1_sobrepostos_sem_espera_entre_eles(self):
        e=self.executar(True);self.assertEqual([v[:2] for v in e],[('down','w'),('down','1'),('up','1'),('up','w')])

    def test_skill_primeiro_e_w_imediatamente_depois(self):
        e=self.executar(False);self.assertEqual([v[:2] for v in e],[('down','4'),('down','w'),('up','w'),('up','4')])

    def test_perda_de_foco_solta_w_e_nao_aperta_1(self):
        e=[];foco=[True]
        def down(k):e.append(('down',k));foco[0]=False;return True
        r=executar_combo(down,lambda k:e.append(('up',k)),lambda s:None,lambda:foco[0],'1',True)
        self.assertEqual(r,(False,False));self.assertNotIn(('down','1'),e);self.assertIn(('up','w'),e)

    def test_skill_enviada_e_contabilizada_se_w_falhar(self):
        e=[]
        def down(k):e.append(('down',k));return k!='w'
        self.assertEqual(executar_combo(down,lambda k:e.append(('up',k)),lambda s:None,lambda:True,'4',False),(True,False))
        self.assertIn(('up','4'),e)

    def test_excecao_na_espera_libera_as_duas_teclas(self):
        e=[]
        def esperar(s):raise RuntimeError('entrada interrompida')
        with self.assertRaises(RuntimeError):executar_combo(lambda k:True,lambda k:e.append(k),esperar,lambda:True,'4',False)
        self.assertEqual(e,['w','4'])

    def test_sem_alcance_ou_sem_primeiro_dano_nao_cancela_aproximacao(self):
        c=CancelamentoNormal(True);a=dict(id=42,hp=100,position=(0,1))
        self.assertFalse(c.permitir_combo(a,(0,0),42,False))
        self.assertTrue(c.permitir_combo(a,(0,0),42,True))
        a['position']=(0,3);self.assertFalse(c.permitir_combo(a,(0,0),42,True))
        a['position']=(0,1);c.suspender_alvo(42)
        self.assertFalse(c.permitir_combo(a,(0,0),42,True))

    def motor(self,skill):
        import hunt_native as h
        from perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(cancel_normal=True,buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for v in p['skills']:v['enabled']=False
        if skill:p['skills'][2].update(key='4',seconds=1,enabled=True)
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];hp=[100];teclas=[];eventos=[]
        def alvo():return dict(ref=1,id=4093,name='Verit Mutante',hp=hp[0],hp_max=100,mp=0,mp_max=0,position=(2,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=(0,0),height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo())
            def close(self):pass
        def down(k):
            teclas.append((k,t[0]))
            if k in ['1','4']:hp[0]-=1
        def dormir(s):
            t[0]+=max(.001,s)
            if t[0]>5:c.stop.set()
        def emitir(e):
            eventos.append(e)
            if e.get('combo_w')==('skill+w' if skill else 'w+ataque'):c.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,c)
        acoes=[e for e in eventos if e.get('event')=='action']
        self.assertIsNone(acoes[0]['combo_w']);self.assertEqual(acoes[-1]['combo_w'],'skill+w' if skill else 'w+ataque')
        self.assertEqual([k for k,t in teclas[-2:]],['4','w'] if skill else ['w','1'])
        self.assertEqual(teclas[-2][1],teclas[-1][1])

    def test_motor_normal_so_combina_apos_dano_confirmado(self):self.motor(False)
    def test_motor_skill_usa_ordem_skill_w(self):self.motor(True)


if __name__=='__main__':unittest.main()
