import copy,unittest
from types import SimpleNamespace
from huntingaitan.entrada.entrada_janela import EntradaJanela,codigo_tecla
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.leitura.recargas_barra import atalhos_slots,decodificar


class User32:
    def __init__(self):self.pid=20;self.envios=[];self.modificador=False
    def IsWindow(self,h):return h==10
    def IsIconic(self,h):return False
    def GetWindowThreadProcessId(self,h,p):p._obj.value=self.pid
    def GetAsyncKeyState(self,k):return 0x8000 if self.modificador else 0
    def MapVirtualKeyW(self,k,m):return 30
    def PostMessageW(self,*args):self.envios.append(args);return 1
    def ScreenToClient(self,h,p):p._obj.x-=100;p._obj.y-=200;return 1
    def GetClientRect(self,h,r):r._obj.right=800;r._obj.bottom=600;return 1


class EntradaTeste(unittest.TestCase):
    def test_destino_exato_repeticao_e_liberacao(self):
        u=User32();e=EntradaJanela(10,20,u)
        e.keyDown('1');e.keyDown('1');e.keyUp('1')
        self.assertEqual([x[:3] for x in u.envios],[(10,0x100,49),(10,0x100,49),(10,0x101,49)])
        self.assertFalse(u.envios[0][3]&(1<<30));self.assertTrue(u.envios[1][3]&(1<<30))
        self.assertEqual(u.envios[2][3]&0xc0000000,0xc0000000);self.assertFalse(e.pressionadas)

    def test_hwnd_reciclado_nao_recebe_tecla(self):
        u=User32();e=EntradaJanela(10,20,u);u.pid=30
        with self.assertRaises(RuntimeError):e.keyDown('7')
        self.assertFalse(u.envios)

    def test_ctrl_fisico_bloqueia_down_mas_permite_liberar(self):
        u=User32();e=EntradaJanela(10,20,u);e.keyDown('w');u.modificador=True
        self.assertFalse(e.keyDown('7'));self.assertTrue(e.keyUp('w'))
        self.assertEqual(len(u.envios),2)

    def test_diagnostico_distingue_minimizado_e_modificador(self):
        u=User32();e=EntradaJanela(10,20,u)
        self.assertIsNone(e.motivo_indisponivel())
        u.modificador=True;self.assertIn('Ctrl',e.motivo_indisponivel())
        u.IsIconic=lambda h:True;self.assertIn('minimizou',e.motivo_indisponivel())

    def test_clique_por_mensagem_sem_api_de_cursor_global(self):
        u=User32();e=EntradaJanela(10,20,u)
        self.assertTrue(e.moveTo(120,230));e.mouseDown();e.mouseUp()
        self.assertEqual(u.envios,[(10,0x200,0,(30<<16)|20),(10,0x201,1,(30<<16)|20),(10,0x202,0,(30<<16)|20)])
        self.assertFalse(e.moveTo(-500,0))
        with self.assertRaises(RuntimeError):e.mouseDown()

    def test_duplo_clique_envia_mensagem_propria_e_libera_botao(self):
        u=User32();e=EntradaJanela(10,20,u)
        e.moveTo(120,230);e.mouseDown();e.mouseUp();e.mouseDown(duplo=True);e.mouseUp()
        self.assertEqual([m[1] for m in u.envios],[0x200,0x201,0x202,0x203,0x202])
        self.assertFalse(e.botoes)

    def test_ctrl_nao_e_substituido_por_entrada_global(self):
        with self.assertRaises(ValueError):codigo_tecla('ctrl+1')
        self.assertEqual(codigo_tecla('f8'),119)

    def test_arrasto_preserva_botao_direito_na_mensagem_de_movimento(self):
        u=User32();e=EntradaJanela(10,20,u)
        e.moveTo(120,230);e.mouseDown('right');e.moveTo(140,230);e.mouseUp('right')
        self.assertEqual(u.envios[-2],(10,0x200,2,(30<<16)|40))
        self.assertEqual(u.envios[-1],(10,0x205,0,(30<<16)|40))


class ConfigTeste(unittest.TestCase):
    def perfil(self):
        p=copy.deepcopy(DEFAULT);p.update(client_pid=20,client_hwnd=10,background_keys=True,
            buff_keys=['f3','','','',''],extra_buff_keys=['f8','f10'],periodic_item_key='f7',hp_keys=['f9','',''])
        return p

    def test_atalhos_novos_validam_e_reservam(self):
        p=self.perfil();self.assertTrue(validar(p)['background_keys'])
        p['reacoes']=[dict(nome='duplicado',tipo='buff',tecla='f8')]
        with self.assertRaisesRegex(ValueError,'repetido'):validar(p)

    def test_combo_e_mina_sao_rejeitados_e_jardim_e_aceito(self):
        p=self.perfil();p['buff_keys'][0]='ctrl+1'
        with self.assertRaisesRegex(ValueError,'teclas simples'):validar(p)
        p=self.perfil();p['patrol_mode']='mina_lenfer'
        with self.assertRaisesRegex(ValueError,'Mina'):validar(p)
        p['patrol_mode']='jardim_aereo'
        self.assertTrue(validar(p)['background_keys'])


class RecargasTeste(unittest.TestCase):
    def test_f4_cura_f8_item_e_recarga_lida_da_skill(self):
        hot=bytearray(468);hot[45*4:45*4+2]=bytes([115,1]);hot[48*4:48*4+2]=bytes([119,1])
        mapa=atalhos_slots(hot);self.assertEqual(mapa,{18:'f4',21:'f8'})
        slots=[0]*40;slots[18]=(1088<<4)|2;slots[21]=(8086<<4)|6
        cds=[0.]*43;cds[((1088-1)%960)//16]=.5
        self.assertEqual(decodificar(slots,cds,mapa),{'f4':dict(skill=1088,cooldown=.5,ready=False)})
