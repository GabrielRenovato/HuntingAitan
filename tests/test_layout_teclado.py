import unittest
from types import SimpleNamespace
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.entrada.layout_teclado import caractere_do_vk,vk_da_tecla
from huntingaitan.leitura.recargas_barra import atalhos_slots

def user32(abnt2=True,envios=None):
    """Fake com so as chamadas do layout. ABNT2: ' = VK 192 e ~ = VK 222 (tecla morta). Americano: ' = VK 222."""
    envios=[] if envios is None else envios
    def vk_scan(c,layout):
        if c=="'":return 192 if abnt2 else 222
        return -1
    def mapa(vk,modo,layout):
        if abnt2:return {192:39,222:0x80000000|126}.get(vk,0)
        return {222:39,192:96}.get(vk,0)
    return SimpleNamespace(GetWindowThreadProcessId=lambda h,p:77,GetKeyboardLayout=lambda t:0x4160416,VkKeyScanExW=vk_scan,
        MapVirtualKeyExW=mapa,IsWindow=lambda h:True,MapVirtualKeyW=lambda k,m:30,GetAsyncKeyState=lambda k:0,
        PostMessageW=lambda *a:envios.append(a) or 1,envios=envios)

class LayoutTest(unittest.TestCase):
    def test_apostrofo_segue_o_layout(self):
        self.assertEqual(vk_da_tecla(user32(True),10,"'"),192)
        self.assertEqual(vk_da_tecla(user32(False),10,"'"),222)

    def test_sem_como_resolver_usa_o_layout_americano(self):
        self.assertEqual(vk_da_tecla(SimpleNamespace(),10,"'"),222)
        sem_vk=SimpleNamespace(VkKeyScanExW=lambda c,l:-1,GetWindowThreadProcessId=lambda h,p:1,GetKeyboardLayout=lambda t:1)
        self.assertEqual(vk_da_tecla(sem_vk,10,"'"),222)

    def test_caractere_do_vk_ignora_tecla_morta(self):
        u=user32(True)
        self.assertEqual(caractere_do_vk(u,10,192),"'");self.assertEqual(caractere_do_vk(u,10,222),'')
        self.assertEqual(caractere_do_vk(user32(False),10,222),"'")

    def test_entrada_envia_o_vk_do_layout_e_nao_o_fixo(self):
        u=user32(True)
        e=EntradaJanela(10,20,u);e.validar=lambda:None
        e.keyDown("'");e.keyUp("'")
        self.assertEqual([x[2] for x in u.envios],[192,192])
        self.assertFalse(e.pressionadas)

    def test_entrada_mantem_222_quando_o_layout_nao_resolve(self):
        u=SimpleNamespace(IsWindow=lambda h:True,MapVirtualKeyW=lambda k,m:30,GetAsyncKeyState=lambda k:0,envios=[])
        u.PostMessageW=lambda *a:u.envios.append(a) or 1
        e=EntradaJanela(10,20,u);e.validar=lambda:None;e.keyDown("'")
        self.assertEqual(u.envios[0][2],222)

    def test_barra_abnt2_mostra_o_apostrofo_no_slot_certo(self):
        # Slot 14 (linha 2, coluna 7) fica na entrada 41 da tabela; no ABNT2 o apostrofo e o VK 192.
        hot=bytearray(468);hot[(35+6)*4:(35+6)*4+2]=bytes([192,1])
        self.assertEqual(atalhos_slots(hot,lambda vk:{192:"'"}.get(vk,'')),{14:"'"})
        self.assertEqual(atalhos_slots(hot),{})
        hot=bytearray(468);hot[(35+6)*4:(35+6)*4+2]=bytes([222,1])
        self.assertEqual(atalhos_slots(hot),{14:"'"})
        self.assertEqual(atalhos_slots(hot,lambda vk:{192:"'"}.get(vk,'')),{})

if __name__=='__main__':unittest.main()
