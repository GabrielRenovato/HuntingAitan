import copy,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from huntingaitan.configuracao.perfil_hunt import DEFAULT,validar
from huntingaitan.combate.hunt_native import alvo_permitido


class GrupoButoTest(unittest.TestCase):
    def test_modo_fixa_grupo_sem_mudar_skills_cura_e_buffs(self):
        original=copy.deepcopy(DEFAULT)
        p=validar(dict(original,patrol_mode='buto_trio',base=[1,2],auto_base=True,radius=50,target='qualquer',data_source='visual',mina_repeat=True))
        self.assertEqual((p['base'],p['radius'],p['target'],p['auto_base'],p['data_source'],p['mina_repeat']),([2711,1292],30,'buto',False,'native',False))
        for k in ['skills','heal_key','hp_percent','buff_keys','buff_minutes']:
            self.assertEqual(p[k],original[k])
        self.assertEqual(original,DEFAULT)

    def test_so_os_tres_spawns_estao_no_raio_e_npc_e_outras_especies_sao_excluidos(self):
        p=validar(dict(patrol_mode='buto_trio'));player=dict(position=(2711,1292),height=0)
        pontos=[(2715,1287),(2731,1338),(2718,1425),(2742,1427),(2767,1432),(2731,1297),(2709,1300),(2612,1248),(2684,1172),(2611,1220)]
        def alvo(pos,nome='Buto Mutante',hostile=True):return dict(position=pos,height=0,hp=100,hostile=hostile,name=nome)
        aceitos=[i+1 for i,pos in enumerate(pontos) if alvo_permitido(alvo(pos),player,p['base'],p)]
        self.assertEqual(aceitos,[1,6,7])
        self.assertFalse(alvo_permitido(alvo((2715,1287),'Buto Cinzento'),player,p['base'],p))
        self.assertFalse(alvo_permitido(alvo((2715,1287),hostile=False),player,p['base'],p))
        self.assertFalse(alvo_permitido(alvo((2731,1338)),dict(player,position=(2731,1338)),p['base'],p))

    def test_motor_mata_tres_espera_respawn_e_repete_sem_tab_no_meio_da_luta(self):
        import huntingaitan.combate.hunt_native as h
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
        p=copy.deepcopy(DEFAULT);p.update(patrol_mode='buto_trio',buffs_enabled=False,heal_enabled=False,minimize_on_start=False,hp_keys=['','',''])
        for skill in p['skills']:skill['enabled']=False
        controle=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
        tempo=[0.];pos=[(2711.,1292.)];vida=[100,100,100];selecionado=[None];onda=[0];respawn_em=[None]
        eventos=[];trocas_vivo=[];retornos=[]
        locais=[(2715,1287),(2731,1297),(2709,1300)]
        def mob(i):return dict(ref=0x100000+i,id=9000+onda[0]*3+i,name='Buto Mutante',position=locais[i],height=0,hp=vida[i],hp_max=100,hostile=True)
        class Dados:
            hwnd=1;caminho=Path('AIKACL.exe')
            def snapshot(self):return dict(player=dict(position=pos[0],heading=90,height=0,hp=100,hp_max=100,mp=100,mp_max=100),target=mob(selecionado[0]) if selecionado[0] is not None else None)
            def listar_mobs(self,*args):return [mob(i) for i in range(3) if vida[i]>0]
            def entidade(self,ref):return mob(ref-0x100000)
            def cena_validada(self):return 1
            def close(self):pass
        class Nav:
            def invalidar(self):pass
            def suspender(self,*args):pass
            def planejar(self,*args,**kwargs):
                destino=args[3];pos[0]=tuple(destino)
                if tuple(destino)==(2711,1292):retornos.append((onda[0],sum(vida)))
                return dict(estado='chegou',w=False)
        def down(k):
            i=selecionado[0]
            if k=='tab':
                if i is not None and vida[i]>0:trocas_vivo.append(i)
                selecionado[0]=next((j for j in range(3) if vida[j]>0),None)
            elif k=='1' and i is not None:vida[i]=max(0,vida[i]-50)
        def dormir(s):
            tempo[0]+=max(.001,s)
            abates=sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos)
            if abates==3 and pos[0]==(2711,1292) and respawn_em[0] is None:respawn_em[0]=tempo[0]+1
            if respawn_em[0] is not None and tempo[0]>=respawn_em[0] and onda[0]==0:
                onda[0]=1;vida[:]=[100,100,100];selecionado[0]=None
            if abates==6 and pos[0]==(2711,1292) or tempo[0]>55:controle.stop.set()
        janela=MagicMock();janela.GetForegroundWindow.return_value=1;janela.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
        entrada=SimpleNamespace(PAUSE=0,keyDown=down,keyUp=lambda k:None)
        with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),patch.object(h,'DadosInternos',Dados),patch.object(h,'NavegadorLocal',Nav),patch.object(h.ctypes.windll,'user32',janela),patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):
            h.main(p,eventos.append,controle)
        self.assertEqual(sum(e.get('message')=='Mob abatido; procurando o proximo.' for e in eventos),6)
        self.assertFalse(trocas_vivo)
        self.assertTrue(retornos);self.assertTrue(all(hp==0 for _,hp in retornos))
        self.assertEqual(next(e['base'] for e in eventos if e.get('event')=='base'),(2711,1292))


if __name__=='__main__':unittest.main()
