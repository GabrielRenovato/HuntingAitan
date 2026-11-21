import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.combate.cura_prioritaria import CuraPrioritaria


class CuraTeste(unittest.TestCase):
    def test_reproduz_cura_presa_no_timer_154s(self):
        c=CuraPrioritaria('7',.7,154);c.enviada(0,.5)
        c.observar(1,.5,dict(ready=False))
        self.assertTrue(c.necessaria(20,.3,dict(ready=True)))
        self.assertFalse(c.necessaria(20,.3,dict(ready=False)))

    def test_nao_gasta_cura_com_hp_cheio_ou_morto(self):
        c=CuraPrioritaria('7',.7,154)
        for hp in [1,.71,0]:self.assertFalse(c.necessaria(0,hp,dict(ready=True)))
        self.assertTrue(c.necessaria(0,.7,dict(ready=True)))

    def test_input_recusado_nao_inicia_recarga_de_154_segundos(self):
        c=CuraPrioritaria('7',.7,154);c.enviada(0,.5)
        self.assertFalse(c.necessaria(1,.4,dict(ready=True)))
        self.assertEqual(c.observar(2,.4,dict(ready=True)),'sem_confirmacao')
        self.assertTrue(c.necessaria(2,.4,dict(ready=True)))

    def test_confirmacao_exige_recarga_ou_aumento_de_hp(self):
        c=CuraPrioritaria('7',.7,154);c.enviada(0,.5)
        self.assertIsNone(c.observar(.2,.5,dict(ready=True)))
        self.assertEqual(c.observar(.3,.5,dict(ready=False)),'recarga_confirmada')
        self.assertFalse(c.necessaria(2,.4,None))

    def test_fallback_respeita_recarga_apos_hp_recuperado(self):
        c=CuraPrioritaria('7',.7,154);c.enviada(0,.4)
        self.assertEqual(c.observar(1,.8,None),'hp_recuperado')
        self.assertFalse(c.necessaria(2,.3,None))
        self.assertTrue(c.necessaria(154,.3,None))

    def test_duas_falhas_pedem_recuperacao_com_pausa_sem_inventar_recarga(self):
        c=CuraPrioritaria('7',.7,154)
        c.enviada(0,.5);c.observar(2,.4,dict(ready=True))
        c.enviada(2,.4);self.assertEqual(c.observar(4,.3,dict(ready=True)),'sem_confirmacao')
        self.assertTrue(c.recuperar);self.assertFalse(c.necessaria(6,.3,dict(ready=True)))
        self.assertTrue(c.necessaria(7,.3,dict(ready=True)))
        c.enviada(7,.3);c.observar(8,.3,dict(ready=False));self.assertEqual(c.falhas,0)

    def motor(self,efeito=None):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.configuracao.perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''],hp_percent=70)
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());tempo=[0.];entradas=[];eventos=[]
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=(0,0),heading=90,height=0,hp=50,hp_max=100,mp=100,mp_max=100),target=None)
            def estados_controle(self):return dict(stunned=efeito=='stun' and tempo[0]<1,casting=efeito=='casting' and tempo[0]<1)
            def recargas_atalhos(self):return {'7':dict(skill=49,ready=True,cooldown=0.)}
            def close(self):pass
        def dormir(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>3:c.stop.set()
        def emitir(e):
            eventos.append(e)
            if e.get('kind')=='heal':c.stop.set()
        u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=lambda k:entradas.append((tempo[0],k)),keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,c)
        self.assertEqual([k for t,k in entradas],['7'])
        self.assertEqual(len([e for e in eventos if e.get('kind')=='heal']),1)
        self.assertNotIn('7',next(e['atalhos'] for e in eventos if e.get('message')=='Habilidades ativas nesta sessao.'))
        return entradas

    def test_cura_sem_alvo_antes_de_tab_ou_movimento(self):self.motor()
    def test_stun_impede_envio_e_cura_sai_imediatamente_apos(self):self.assertGreaterEqual(self.motor('stun')[0][0],1)
    def test_cura_nao_interrompe_casting(self):self.assertGreaterEqual(self.motor('casting')[0][0],1)


if __name__=='__main__':unittest.main()
