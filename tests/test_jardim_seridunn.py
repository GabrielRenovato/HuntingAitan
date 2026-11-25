import copy,math,threading,unittest,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,MagicMock,patch
from huntingaitan.rotas.jardim_seridunn import JardimSeridunn,plano_seridunn
from huntingaitan.rotas.jardim_aereo import plano_jardim
from huntingaitan.rotas.ciclo_jardim import CicloJardim
from huntingaitan.configuracao.perfil_hunt import validar,DEFAULT
from huntingaitan.combate.hunt_native import alvo_permitido
from tests.test_navegacao_grade import grade


class SeridunnTeste(unittest.TestCase):
    def circuito(self):
        j=JardimSeridunn((3351,3295));j.grade=grade(24,16)
        j.rota_planejada=[(x+.5,1.5) for x in range(1,22)]
        return j

    def mob(self,id_,nome,pos):return dict(id=id_,name=nome,position=pos)

    def test_preserva_rota_curta_e_estende_ate_area_final(self):
        curto=copy.deepcopy(plano_jardim());p=plano_seridunn();r=p['trechos'][0]['caminho']
        self.assertEqual(p['objetivo'],'seridunn');self.assertEqual(p['pontos'][0]['chefe'],'seridunn')
        self.assertLessEqual(math.dist(r[-1],p['referencia_area_final']),9)
        self.assertGreater(len(r),len(curto['trechos'][0]['caminho']))
        self.assertTrue(all(math.dist(a,b)<=math.sqrt(2)+1e-6 for a,b in zip(r,r[1:])))
        self.assertFalse(p['posicao_chefe_confirmada'])
        self.assertTrue(all(not c['pontos'] for c in p['catalogo_seridunn']))
        self.assertEqual(plano_jardim(),curto)

    def test_chegada_aguarda_chefe_e_so_abate_exato_conclui(self):
        j=JardimSeridunn((3351,3295));pos=j.pontos[-1]['pos']
        self.assertEqual(j.destino(pos,0)['estado'],'aguardar_chefe')
        self.assertFalse(j.atingiu_limite(pos));self.assertFalse(j.abates)
        for nome in ['Guarda de Seridunn','Seridunn Corrompido','Malik']:
            self.assertIsNone(j.registrar_abate(1,nome,pos,1))
        self.assertIsNone(j.registrar_abate(1,'Seridunn',(1856,1082),1))
        self.assertEqual(j.registrar_abate(2,'Seridunn',pos,2),'seridunn')
        self.assertEqual(j.destino(pos,3)['estado'],'concluido')

    def test_nao_para_por_shiraz_nem_pelo_limite_antigo(self):
        j=JardimSeridunn((3351,3295));pos=plano_jardim()['pontos'][0]['pos']
        self.assertFalse(j.atingiu_limite(pos));self.assertIsNone(j.limite_proximo([self.mob(1,'Shiraz Infernal',pos)],pos))
        self.assertEqual(j.destino(pos,1)['estado'],'andar')

    def test_ignora_laterais_e_distantes_e_prioriza_chefe(self):
        j=self.circuito();pos=(1.5,1.5)
        bloqueador=self.mob(1,'Shiraz Infernal',(3.5,1.5))
        lateral=self.mob(2,'Lazapa',(2.5,4.5));distante=self.mob(3,'Soldado',(9.5,1.5))
        self.assertEqual(j.filtrar_mobs([bloqueador,lateral,distante],pos,50),[bloqueador])
        chefe=self.mob(4,'Seridunn',(12.5,1.5))
        self.assertEqual(j.filtrar_mobs([bloqueador,lateral,chefe],pos,50),[chefe])

    def test_defesa_restringe_ao_entorno_e_nao_atravessa_parede(self):
        j=self.circuito();pos=(1.5,1.5)
        perto=self.mob(1,'Lazapa',(2.5,4.5));longe=self.mob(2,'Lazapa',(12.5,1.5))
        self.assertEqual(j.filtrar_mobs([perto,longe],pos,50,True),[perto])
        j.grade=grade(24,16,[(5,y) for y in range(16)]);j.custo_origem=None
        self.assertEqual(j.filtrar_mobs([self.mob(3,'Seridunn',(12.5,1.5))],pos,50),[])

    def test_mob_que_saiu_da_passagem_nao_e_perseguido(self):
        j=self.circuito();pos=(1.5,1.5)
        self.assertFalse(j.permite_perseguir(self.mob(1,'Soldado',(15.5,1.5)),pos))
        self.assertFalse(j.permite_perseguir(self.mob(1,'Soldado',(2.5,5.5)),pos))
        self.assertTrue(j.permite_perseguir(self.mob(2,'Seridunn',(15.5,1.5)),pos))

    def test_perfil_e_filtro_preservam_curto_e_liberam_chefe_no_novo(self):
        p=validar(dict(patrol_mode='jardim_aereo'));self.assertEqual(p['jardim_goal'],'seridunn')
        with self.assertRaises(ValueError):validar(dict(jardim_goal='qualquer'))
        player=dict(position=(3757,3146),height=0)
        mob=dict(name='Seridunn',position=(3758,3146),height=0,hp=100,hostile=True)
        self.assertTrue(alvo_permitido(mob,player,player['position'],p))
        self.assertFalse(alvo_permitido(mob,player,player['position'],dict(p,jardim_goal='antes_shiraz')))

    def test_rota_real_respeita_todas_as_passagens(self):
        raiz=Path(r'C:\GoLevel\AikaOnline')
        if not raiz.exists():self.skipTest('Cliente local indisponivel')
        j=JardimSeridunn((3351,3295));j.conferir(raiz)
        self.assertTrue(all(j.grade.passagem(j.grade.celula(a),j.grade.celula(b)) for a,b in zip(j.rota_planejada,j.rota_planejada[1:])))
        self.assertLessEqual(math.dist(j.rota_planejada[-1],plano_seridunn()['referencia_area_final']),9)

    def test_motor_confirma_vida_zero_do_chefe_antes_de_concluir(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        pos=(3640.5,3209.5);vida=[100];selecionado=[False];tempo=[0.];eventos=[];teclas=[]
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        def alvo():return dict(ref=123,id=3000,name='Seridunn',position=(3641.5,3209.5),height=0,hp=vida[0],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos,heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=alvo() if selecionado[0] else None)
            def cena_validada(self):return 1
            def u32(self,*a):return 30005
            def listar_mobs(self,*a):return [alvo()] if vida[0]>0 else []
            def close(self):pass
        def down(k):
            teclas.append(k)
            if k=='tab':selecionado[0]=True
            if k=='1' and selecionado[0]:vida[0]=0
        def dormir(v):
            tempo[0]+=max(.001,v)
            if tempo[0]>20:c.stop.set()
        def conferir(j,pasta):
            j.grade=grade(50,50);j.grade.origem=(3616,3180)
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='jardim_aereo',jardim_goal='seridunn',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for skill in p['skills']:skill['enabled']=False
        u=MagicMock();u.GetForegroundWindow.return_value=1;u.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        e=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=e),patch('huntingaitan.rotas.jardim_aereo.conferir_dificil',return_value=True),patch.object(JardimSeridunn,'conferir',conferir),patch.object(h,'DadosInternos',Dados),patch.object(h.ctypes.windll,'user32',u),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):
            h.main(p,eventos.append,c)
        self.assertEqual(vida[0],0);self.assertEqual(c.reason,'jardim_finalizado')
        conclusao=[e for e in eventos if e.get('event')=='dungeon_complete']
        self.assertEqual(len(conclusao),1);self.assertEqual(conclusao[0]['abates']['seridunn']['id'],3000)
        self.assertEqual(teclas.count('tab'),1)


class CicloSeridunnTeste(unittest.TestCase):
    def preparar(self,eventos_motor):
        c=SimpleNamespace(stop=threading.Event(),pause=threading.Event(),reason='')
        pos=[3351,3295];eventos=[]
        def motor(p,e,control,**kw):
            for evento in eventos_motor:e(evento)
        def sair():pos[:]=[1856.4,1082.4];return True
        saida=Mock(side_effect=sair)
        ciclo=CicloJardim(dict(DEFAULT,jardim_goal='seridunn',jardim_repeat=False,jardim_servico_npc=False),c,eventos.append,
            lambda:dict(position=pos[:],hp=1,pasta='jogo'),motor,saida,Mock())
        return ciclo,c,saida,eventos

    def test_abate_confirmado_conta_e_sai(self):
        ciclo,c,sair,eventos=self.preparar([dict(event='dungeon_complete',abates=dict(seridunn=dict(id=99,nome='Seridunn')))])
        ciclo.passo();self.assertEqual(ciclo.etapa,'jardim_sair');self.assertEqual(ciclo.trechos,1)
        ciclo.passo();sair.assert_called_once();self.assertEqual(c.reason,'jardim_concluido')
        self.assertEqual(len([e for e in eventos if e['event']=='dungeon_complete']),1)

    def test_limite_antigo_e_conclusao_sem_abate_nao_contam(self):
        for evento in [dict(event='jardim_limit'),dict(event='dungeon_complete',abates={})]:
            ciclo,c,sair,eventos=self.preparar([evento]);ciclo.passo()
            self.assertEqual(ciclo.trechos,0);sair.assert_not_called()
            self.assertFalse(any(e['event']=='dungeon_complete' for e in eventos))


if __name__=='__main__':unittest.main()
