import unittest,copy,struct,json,math
from pathlib import Path
from perfil_hunt import DEFAULT,validar
from hunt_native import alvo_permitido,ProgressoNativo
from dados_internos import DadosInternos

class TestePerfil(unittest.TestCase):
 def test_perfil_antigo_da_janela_nao_desativa_atalhos_preenchidos(self):
  p=copy.deepcopy(DEFAULT);p['version']=1
  for s in p['skills']:s['enabled']=False
  r=validar(p)
  self.assertEqual(r['version'],3)
  self.assertEqual([s['key'] for s in r['skills'] if s['enabled']],['2','3','4','5','6','7'])
 def test_v2_preserva_desativacao_explicita(self):
  p=copy.deepcopy(DEFAULT);p['skills'][0]['enabled']=False
  self.assertFalse(validar(p)['skills'][0]['enabled'])
 def test_migracao_nao_ativa_duplicatas_e_ataque_normal(self):
  p=copy.deepcopy(DEFAULT);p['version']=1
  p['skills'][0].update(key='1',enabled=False)
  p['skills'][1].update(key='2',enabled=False)
  p['skills'][2].update(key='2',enabled=False)
  r=validar(p)
  self.assertFalse(r['skills'][0]['enabled']);self.assertTrue(r['skills'][1]['enabled']);self.assertFalse(r['skills'][2]['enabled'])
 def test_padrao_tem_base_automatica_e_dados_internos(self):
  p=validar(DEFAULT);self.assertTrue(p['auto_base']);self.assertEqual(p['data_source'],'native')
  self.assertEqual(len(p['skills']),10);self.assertEqual(len(p['items']),5)
 def test_rejeita_atalhos_reservados(self):
  p=copy.deepcopy(DEFAULT);p['skills'][0]['key']='f12'
  with self.assertRaises(ValueError):validar(p)
 def test_rejeita_atalho_de_pocao_em_skill(self):
  p=copy.deepcopy(DEFAULT);p['skills'][0]['key']='8'
  with self.assertRaises(ValueError):validar(p)
 def test_nao_muda_configuracao_original(self):
  antes=copy.deepcopy(DEFAULT);p=validar(DEFAULT);p['base'][0]=1
  self.assertEqual(DEFAULT,antes)
 def test_limites_da_area(self):
  p=copy.deepcopy(DEFAULT);p['radius']=1000
  with self.assertRaises(ValueError):validar(p)

class TesteAlvoInterno(unittest.TestCase):
 def setUp(self):
  self.player={'position':(100,100),'height':0}
  self.target={'position':(105,100),'height':0,'hp':100,'hostile':True,'name':'Verit Mutante','ref':123,'id':9000}
 def test_so_aceita_hostil_perto(self):
  self.assertTrue(alvo_permitido(self.target,self.player,(100,100),DEFAULT))
  self.target['position']=(150,100);self.assertFalse(alvo_permitido(self.target,self.player,(100,100),DEFAULT))
 def test_rejeita_outro_andar_e_npc(self):
  self.target['height']=10;self.assertFalse(alvo_permitido(self.target,self.player,(100,100),DEFAULT))
  self.target['height']=0;self.target['hostile']=False;self.assertFalse(alvo_permitido(self.target,self.player,(100,100),DEFAULT))
 def test_filtro_de_especie(self):
  p=dict(DEFAULT,target='penza');self.assertFalse(alvo_permitido(self.target,self.player,(100,100),p))
 def test_nao_abandona_mob_ferido_durante_stun(self):
  t=self.target;p=ProgressoNativo(t,0);p.observar(dict(t,hp=50),1)
  self.assertFalse(p.aproximacao_falhou(20,25,DEFAULT))
  self.assertEqual(p.observar(dict(t,hp=40),21),'mesmo')
 def test_cinco_segundos_valem_so_antes_de_comecar_dano(self):
  p=ProgressoNativo(self.target,0)
  self.assertTrue(p.aproximacao_falhou(5,5,DEFAULT))
 def test_zero_isolado_nao_libera_outro_alvo(self):
  p=ProgressoNativo(self.target,0)
  self.assertEqual(p.observar(dict(self.target,hp=0),1),'confirmando_morte')
  self.assertEqual(p.observar(dict(self.target,hp=50),1.1),'mesmo')
  self.assertEqual(p.observar(dict(self.target,hp=0),2),'confirmando_morte')
 def test_referencia_e_id_impedem_confundir_dois_mobs_iguais(self):
  t=self.target;p=ProgressoNativo(t,0)
  self.assertEqual(p.observar(dict(t,ref=124),1),'mesmo');self.assertEqual(p.ref,124)
  self.assertEqual(p.observar(dict(t,id=9001),1),'outro')
  self.assertEqual(p.observar(dict(t,hp=80),2),'mesmo');self.assertEqual(p.ultimo_dano,2)
  self.assertEqual(p.observar(dict(t,hp=0),3),'confirmando_morte')
  self.assertEqual(p.observar(dict(t,hp=0),3.3),'morto')

class TesteLayout(unittest.TestCase):
 def setUp(self):
  self.d=DadosInternos.__new__(DadosInternos);self.ptr=0x100000;self.mem=bytearray(8192)
  struct.pack_into('<I',self.mem,4,9000);struct.pack_into('<3f',self.mem,0x1c,2767,846,0)
  struct.pack_into('<4i',self.mem,0x498,80,100,40,50)
  nome=b'Verit Mutante';self.mem[0x19ac:0x19ac+len(nome)]=nome
  self.d.read=lambda a,n:bytes(self.mem[a-self.ptr:a-self.ptr+n]);self.d.u32=lambda a:struct.unpack('<I',self.d.read(a,4))[0]
 def test_snapshot_usa_global_ativo_sem_cache_temporario(self):
  d=self.d;d.base=0x400000;scene=0x200000
  d.layout={'active_scene_rva':0x2f9b148-0x400000,'scene_vtable_rva':0x72bfdc-0x400000,'player_offset':0x104,'target_offset':0x90}
  leituras=[]
  valores={d.base+d.layout['active_scene_rva']:scene,scene:0x72bfdc,scene+0x104:self.ptr,scene+0x90:0}
  original=d.u32
  def u32(a):
   leituras.append(a)
   return valores[a] if a in valores else original(a)
  d.u32=u32
  snap=d.snapshot();self.assertEqual(snap['player']['position'],(2767,846));self.assertIsNone(snap['target'])
  self.assertEqual(leituras[0],0x2f9b148)
 def test_cena_nula_informa_carregamento(self):
  d=self.d;d.base=0x400000;d.layout={'active_scene_rva':1};d.u32=lambda a:0
  with self.assertRaisesRegex(RuntimeError,'ainda nao carregada'):d.snapshot()
 def test_decodifica_posicao_vida_e_nome(self):
  e=self.d.entidade(self.ptr)
  self.assertEqual(e['position'],(2767,846));self.assertEqual(e['hp'],80);self.assertEqual(e['name'],'Verit Mutante')
 def test_pran_com_id_do_dono_nao_e_hostil(self):
  struct.pack_into('<I',self.mem,4,0x2800+19)
  self.assertFalse(self.d.entidade(self.ptr)['hostile'])
 def test_rejeita_hp_invalido(self):
  struct.pack_into('<i',self.mem,0x498,1000)
  with self.assertRaises(RuntimeError):self.d.entidade(self.ptr)
 def test_rejeita_coordenada_nan(self):
  struct.pack_into('<f',self.mem,0x1c,float('nan'))
  with self.assertRaises(RuntimeError):self.d.entidade(self.ptr)

if __name__=='__main__':unittest.main()
