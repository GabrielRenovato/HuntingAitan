import unittest,struct,copy,threading,sys
from unittest.mock import patch,MagicMock
from types import SimpleNamespace
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.combate.selecao_regional import BuscaRegional

class ListaTeste(unittest.TestCase):
 def leitor(self):
  d=object.__new__(DadosInternos);d.base=0x400000
  d.layout=dict(active_scene_rva=0x100,scene_vtable_rva=0x200,entity_manager_offset=0x94,entity_array_offset=0x18,entity_count_rva=0x300,entity_stride=0x39bc)
  cena=0x2000000;gerente=0x2100000;pool=0x2200000
  mem={d.base+0x100:cena,cena:d.base+0x200,cena+0x94:gerente,gerente+0x18:pool,d.base+0x300:3}
  d.u32=lambda a:mem.get(a,0)
  mobs=[dict(ref=pool+i*0x39bc,id=9000+i,name='Verit Mutante',position=(i+1,0),height=0,hp=50,hp_max=100,mp=0,mp_max=0,hostile=True) for i in range(3)]
  mobs[1]['hp']=0
  def read(a,n):
   if n==0x40:
    m=next(m for m in mobs if m['ref']==a);buf=bytearray(n);struct.pack_into('<I',buf,4,m['id']);struct.pack_into('<3f',buf,0x1c,*m['position'],m['height']);return bytes(buf)
   return bytes(n)
  d.read=read;d.entidade=lambda a:dict(next(m for m in mobs if m['ref']==a))
  return d,mem,mobs
 def test_lista_descarta_morto_e_aceita_mobs_validos(self):
  d,mem,m=self.leitor();r=d.listar_mobs((0,0),30,dict(height=0,position=(0,0)))
  self.assertEqual([a['id'] for a in r],[9000,9002])
 def test_pet_nao_entra_na_lista_mesmo_com_hp_cheio(self):
  d,mem,m=self.leitor();m[0]['id']=0x2800+19
  self.assertEqual([v['id'] for v in d.listar_mobs((0,0),30,dict(height=0,position=(0,0)))],[9002])
 def test_quantidade_corrompida_nao_varre_memoria(self):
  d,mem,m=self.leitor();mem[d.base+0x300]=50000
  with self.assertRaises(RuntimeError):d.listar_mobs((0,0),30,dict(height=0,position=(0,0)))
 def test_nao_seleciona_fora_da_area_ou_altura(self):
  d,mem,m=self.leitor();m[0]['height']=15;m[2]['position']=(500,500)
  self.assertEqual(d.listar_mobs((0,0),30,dict(height=0,position=(0,0))),[])

class EscolhaTeste(unittest.TestCase):
 def test_mina_nao_espera_oito_segundos_para_reavaliar_busca(self):
  b=BuscaRegional(prazo_aproximar=2.5,prazo_trocar=2.,intervalo_tab=.2,intervalo_giro=.35)
  m=dict(id=3,hp=50,position=(5,0));b.atualizar([m])
  self.assertEqual(b.decidir(0,None,None,pos=(0,0))[0],'tab')
  self.assertEqual(b.decidir(.2,None,None,pos=(0,0))[0],'tab')
  self.assertEqual(b.decidir(2.5,None,None,pos=(0,0))[0],'aproximar')
  self.assertEqual(b.decidir(3,m,None,pos=(0,0))[0],'aceitar')
 def test_busca_padrao_preserva_os_prazos_anteriores(self):
  b=BuscaRegional();b.atualizar([dict(id=3,hp=50,position=(5,0))])
  b.decidir(0,None,None,pos=(0,0))
  self.assertNotEqual(b.decidir(2.5,None,None,pos=(0,0))[0],'aproximar')
  self.assertEqual(b.decidir(8,None,None,pos=(0,0))[0],'aproximar')
 def test_aceita_alvo_valido_sem_tab_adicional(self):
  b=BuscaRegional();m=dict(id=3,hp=50,position=(5,0));b.atualizar([m])
  self.assertEqual(b.decidir(0,m,None)[0],'aceitar')
 def test_giro_so_quando_candidato_esta_fora_do_setor(self):
  b=BuscaRegional();b.atualizar([dict(id=3,hp=50,position=(-5,0))])
  self.assertEqual(b.decidir(0,None,dict(yaw=0,position=(0,0)))[0],'orientar')
  self.assertEqual(b.decidir(.4,None,dict(yaw=150,position=(0,0)))[0],'tab')
 def test_mob_em_movimento_nao_fica_alternando_preferencia(self):
  b=BuscaRegional();a=dict(id=1,hp=50,position=(5,0));c=dict(id=2,hp=50,position=(6,0))
  b.atualizar([a,c]);b.atualizar([c,a])
  self.assertEqual(b.candidatos[0]['id'],1)
  b.atualizar([c]);self.assertEqual(b.candidatos[0]['id'],2)
 def test_sem_candidatos_nao_envia_tab(self):
  self.assertEqual(BuscaRegional().decidir(0,None,None),('aguardar',None))
 def test_camera_com_sentido_inverso_corrige_sinal(self):
  b=BuscaRegional();b.atualizar([dict(id=3,hp=50,position=(0,5))])
  a=b.decidir(0,None,dict(yaw=0,position=(0,0)))
  self.assertEqual(a[1][0],'a')
  a=b.decidir(1.5,None,dict(yaw=330,position=(0,0)))
  self.assertEqual(a[1][0],'d')

class FluxoRegionalTeste(unittest.TestCase):
 def test_mata_dois_verits_sem_retornar_ou_atacar_tet(self):
  import huntingaitan.combate.hunt_native as h
  from huntingaitan.configuracao.perfil_hunt import DEFAULT
  p=copy.deepcopy(DEFAULT);p.update(target='verit',buffs_enabled=False,minimize_on_start=False,hp_keys=['','',''])
  for v in p['skills']:v['enabled']=False
  c=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
  t=[0.];alvo=[99];mobs={i:dict(ref=i,id=i,name='Verit Mutante' if i!=99 else 'Tet das Chamas',position=(0,1),height=0,hp=80,hp_max=80,mp=0,mp_max=0,hostile=True) for i in [42,43,99]}
  ataques=[];eventos=[];passos=[]
  class Dados:
   hwnd=1
   def snapshot(self):return dict(player=dict(position=(0,0),height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=dict(mobs[alvo[0]]))
   def listar_mobs(self,*args):return [dict(m) for m in mobs.values() if m['hp']>0]
   def caca_original_ativa(self):return False
   def camera_regional(self):return dict(yaw=90,position=(0,0))
   def entidade(self,ref):return dict(mobs[ref])
   def close(self):pass
  def evento(e):
   eventos.append(e)
   if sum(v.get('message')=='Mob abatido; procurando o proximo.' for v in eventos)>=2:c.stop.set()
  def dormir(v):
   t[0]+=max(.001,v)
   if t[0]>20:c.stop.set()
  def down(k):
   passos.append(k)
   if k=='tab':alvo[0]=42 if mobs[42]['hp']>0 else 43
   if k=='1':ataques.append(alvo[0]);mobs[alvo[0]]['hp']=max(0,mobs[alvo[0]]['hp']-40)
  u=MagicMock();u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
  entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
  with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:t[0]),patch.object(h.time,'sleep',dormir):h.main(p,evento,c)
  self.assertEqual(ataques,[42,42,43,43])
  self.assertEqual(passos.count('tab'),2)
  self.assertFalse(any(k in ['w','s','a','d'] for k in passos))
  self.assertEqual(sum(v.get('message')=='Mob abatido; procurando o proximo.' for v in eventos),2)

if __name__=='__main__':unittest.main()
