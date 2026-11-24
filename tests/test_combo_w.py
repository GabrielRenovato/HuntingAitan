import copy,sys,threading,unittest
from types import SimpleNamespace
from unittest.mock import patch,MagicMock,Mock
from huntingaitan.combate.cancelamento_normal import CancelamentoNormal,executar_combo,perfil_combo


class ComboWTeste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
    def executar(self,normal):
        eventos=[];t=[0.]
        def down(k):eventos.append(('down',k,t[0]));return True
        def up(k):eventos.append(('up',k,t[0]))
        def esperar(s):t[0]+=s
        r=executar_combo(down,up,esperar,lambda:True,'1' if normal else '4',normal,skill_id=1 if normal else 177,relogio=lambda:t[0])
        self.assertEqual(r,(True,True))
        self.assertAlmostEqual(eventos[1][2]-eventos[0][2],0 if normal else .0035)
        self.assertAlmostEqual(t[0],0 if normal else .0765)
        return eventos

    def test_padrao_1rr1ww_sem_esperas_e_com_liberacao_de_cada_tecla(self):
        e=self.executar(True)
        self.assertEqual([v[:2] for v in e],[(acao,k) for k in '1rr1ww' for acao in ['down','up']])
        self.assertTrue(all(v[2]==0 for v in e))

    def test_padrao_nao_chama_esperar_nem_mesmo_com_zero(self):
        esperar=Mock()
        self.assertEqual(executar_combo(lambda k:True,lambda k:None,esperar,lambda:True,'1',True),(True,True))
        esperar.assert_not_called()

    def test_falha_no_r_libera_tecla_e_nao_continua_sequencia(self):
        e=[]
        def down(k):
            e.append(('down',k))
            if k=='r':raise RuntimeError('entrada interrompida')
            return True
        with self.assertRaisesRegex(RuntimeError,'entrada interrompida'):
            executar_combo(down,lambda k:e.append(('up',k)),lambda s:None,lambda:True,'1',True)
        self.assertEqual(e,[('down','1'),('up','1'),('down','r'),('up','r')])

    def test_skill_4_com_w_antes_e_liberacoes_independentes(self):
        e=self.executar(False);self.assertEqual([v[:2] for v in e],[('down','w'),('down','4'),('up','w'),('up','4')])

    def test_perda_de_foco_solta_1_e_nao_aperta_w(self):
        e=[];foco=[True]
        def down(k):e.append(('down',k));foco[0]=False;return True
        r=executar_combo(down,lambda k:e.append(('up',k)),lambda s:None,lambda:foco[0],'1',True)
        self.assertEqual(r,(True,False));self.assertNotIn(('down','w'),e);self.assertIn(('up','1'),e)

    def test_w_recusado_nao_envia_skill_4(self):
        e=[]
        def down(k):e.append(('down',k));return k!='w'
        self.assertEqual(executar_combo(down,lambda k:e.append(('up',k)),lambda s:None,lambda:True,'4',False,skill_id=177),(False,False))
        self.assertNotIn(('down','4'),e)

    def test_excecao_na_espera_libera_as_duas_teclas(self):
        e=[]
        def esperar(s):raise RuntimeError('entrada interrompida')
        t=[0.]
        def falhar_no_hold(s):
            if t[0]>.003:raise RuntimeError('entrada interrompida')
            t[0]+=s
        with self.assertRaises(RuntimeError):executar_combo(lambda k:True,lambda k:e.append(k),falhar_no_hold,lambda:True,'4',False,skill_id=177,relogio=lambda:t[0])
        self.assertEqual(e,['4','w'])

    def test_sem_alcance_ou_sem_primeiro_dano_nao_cancela_aproximacao(self):
        c=CancelamentoNormal(True);a=dict(id=42,hp=100,position=(0,1))
        self.assertFalse(c.permitir_combo(a,(0,0),42,False))
        self.assertTrue(c.permitir_combo(a,(0,0),42,True))
        a['position']=(0,3);self.assertFalse(c.permitir_combo(a,(0,0),42,True))
        a['position']=(0,1);c.suspender_alvo(42)
        self.assertFalse(c.permitir_combo(a,(0,0),42,True))

    def motor(self,skill,pronto_depois=0,repeticoes=1,bloquear_apos_dano=False):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.configuracao.perfil_hunt import DEFAULT
        p=copy.deepcopy(DEFAULT);p.update(cancel_normal=True,combo_repeat_ms=40,buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for v in p['skills']:v['enabled']=False
        if skill:p['skills'][2].update(key='4',seconds=1,enabled=True)
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event());t=[0.];hp=[100];teclas=[];eventos=[]
        def alvo():return dict(ref=1,id=4093,name='Verit Mutante',hp=hp[0],hp_max=100,mp=0,mp_max=0,position=(2,0),height=0,hostile=True)
        class Dados:
            hwnd=1
            def snapshot(self):return dict(player=dict(position=(0,0),height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo())
            def estados_controle(self):return dict(normal_skill=1,normal_ready=t[0]>=pronto_depois and (not bloquear_apos_dano or hp[0]==100))
            def recargas_atalhos(self):return {'4':dict(skill=177,ready=True,cooldown=0.)}
            def close(self):pass
        def down(k):
            teclas.append((k,t[0]))
            if k in ['1','4']:hp[0]-=1
        def dormir(s):
            t[0]+=max(.001,s)
            if t[0]>5:c.stop.set()
        def emitir(e):
            eventos.append(dict(e,teste_t=t[0]))
            if sum(v.get('combo_w')==('w+skill' if skill else '1rr1ww') for v in eventos)>=repeticoes:c.stop.set()
        u=MagicMock();u.GetForegroundWindow.return_value=1;u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(p,emitir,c)
        acoes=[e for e in eventos if e.get('event')=='action']
        self.assertIsNone(acoes[0]['combo_w']);self.assertEqual(acoes[-1]['combo_w'],'w+skill' if skill else '1rr1ww')
        self.assertEqual([k for k,t in teclas[-2:]],['w','4'] if skill else ['w','w'])
        self.assertAlmostEqual(teclas[-1][1]-teclas[-2][1],.0035 if skill else 0.)
        if not skill:self.assertEqual([k for k,t in teclas[-6:]],list('1rr1ww'))
        self.assertTrue(all(instante>=pronto_depois for k,instante in teclas if k=='1'))
        return acoes

    def test_modo_repetido_continua_entradas_sem_depender_da_recarga_visual_do_normal(self):
        acoes=self.motor(False,repeticoes=2,bloquear_apos_dano=True)
        combos=[e for e in acoes if e.get('combo_w')=='1rr1ww']
        self.assertEqual(len(combos),2)
        self.assertAlmostEqual(combos[1]['teste_t']-combos[0]['teste_t'],.04,delta=.001)
        self.assertEqual(combos[0]['combo_repeticao_ms'],40)

    def test_skill_5_usa_25ms_e_79ms_de_w(self):
        e=[];t=[0.]
        def esperar(s):t[0]+=s
        self.assertEqual(executar_combo(lambda k:e.append(('down',k,t[0])),lambda k:e.append(('up',k,t[0])),esperar,lambda:True,'5',False,skill_id=273,relogio=lambda:t[0]),(True,True))
        self.assertEqual(e[:2],[('down','w',0.),('down','5',.025)])
        self.assertAlmostEqual(e[2][2],.079);self.assertAlmostEqual(e[3][2],.086)

    def test_skill_diferente_no_mesmo_atalho_nao_herda_w(self):
        self.assertIsNone(perfil_combo('4',False,999))
        self.assertIsNone(perfil_combo('4',False,None))

    def test_3_6_e_cura_7_sem_w(self):
        for key,skill in [('3',113),('6',289),('7',49)]:
            e=[]
            self.assertEqual(executar_combo(lambda k:e.append(k),lambda k:None,lambda s:None,lambda:True,key,False,skill_id=skill),(True,False))
            self.assertEqual(e,[key])

    def test_motor_aguarda_recarga_real_antes_do_padrao_calibrado(self):
        self.motor(False,pronto_depois=2)

    def test_falha_da_skill_apos_w_libera_o_movimento(self):
        e=[];t=[0.]
        def down(k):e.append(('down',k));return k!='4'
        def esperar(s):t[0]+=s
        self.assertEqual(executar_combo(down,lambda k:e.append(('up',k)),esperar,lambda:True,'4',False,skill_id=177,relogio=lambda:t[0]),(False,False))
        self.assertEqual(e[-1],('up','w'))

    def test_motor_normal_so_combina_apos_dano_confirmado(self):self.motor(False)
    def test_motor_skill_usa_ordem_skill_w(self):self.motor(True)


if __name__=='__main__':unittest.main()
