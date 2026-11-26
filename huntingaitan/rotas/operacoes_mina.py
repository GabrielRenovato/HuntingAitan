"""Operacoes de interface da Mina com reconhecimento e confirmacao de transicoes."""
import ctypes,math,time
from ctypes import wintypes as w
from huntingaitan.rotas.interface_mina import InterfaceMina
from huntingaitan.rotas.mina_lenfer import dentro_mina
from huntingaitan.entrada.entrada_segura import mover_cursor_fisico

def sair_grupo(dados,control,emitir,limite=120,dentro=dentro_mina,nome='Mina'):
    import keyboard,pydirectinput as entrada,mss
    from huntingaitan.visao.captura_aika import CapturaAika
    from huntingaitan.visao.avisos_hunt import DetectorAvisos,reconfirmar,reconfirmar_imagem
    segundo_plano=getattr(control,'background_keys',False)
    if segundo_plano:
        from huntingaitan.entrada.entrada_janela import EntradaJanela
        entrada=EntradaJanela(dados.hwnd,dados.pid)
    from huntingaitan.visao.captura_interface import captura_interface
    entrada.PAUSE=0;dados.u.GetForegroundWindow.restype=w.HWND
    detector=InterfaceMina();avisos=DetectorAvisos();inicio=time.monotonic();acao_em=0.;ultimo=None;fora=0;erro_em=-100.
    def ativo():return not control.stop.is_set() and not keyboard.is_pressed('f12') and (entrada.disponivel() if segundo_plano else dados.u.GetForegroundWindow()==dados.hwnd) and not control.pause.is_set()
    def clicar(p,botao='left'):
        if not ativo():return False
        if not (entrada.mover_sem_cursor(*p) if segundo_plano else mover_cursor_fisico(entrada,*p)):return False
        time.sleep(.045)
        if not ativo():return False
        entrada.mouseDown(button=botao)
        try:time.sleep(.065)
        finally:entrada.mouseUp(button=botao)
        return True
    with captura_interface(dados,segundo_plano,mss,CapturaAika) as cap:
        while not control.stop.is_set() and not keyboard.is_pressed('f12'):
            if time.monotonic()-inicio>limite:
                emitir(dict(event='log',message='Saida do grupo ainda nao confirmada; mantendo a etapa para nova tentativa.'));return False
            if not ativo():time.sleep(.1);continue
            try:
                s=dados.snapshot()
                detector.nome_personagem=s['player'].get('name','')
            except RuntimeError:time.sleep(.2);continue
            if s['player']['hp']<=0:
                control.reason='personagem_sem_vida';control.stop.set();return False
            if not dentro(s['player']['position']):
                fora+=1
                if fora>=3:
                    emitir(dict(event='cycle',state='save_confirmado',position=s['player']['position'],hp=s['player']['hp']/s['player']['hp_max']));return True
                time.sleep(.15);continue
            fora=0
            if time.monotonic()<acao_em:time.sleep(.1);continue
            try:
                tela=cap.capturar();aviso=avisos.localizar(tela)
                if aviso and aviso['tipo'] in ['cte_elter','arena_elter','conversa_amigo','season_pass']:
                    ponto=reconfirmar_imagem(aviso,cap.capturar(),cap.area) if segundo_plano else reconfirmar(aviso)
                    if ponto and aviso['tipo']=='season_pass':
                        from huntingaitan.visao.season_pass import fechar_com_escape
                        fechar_com_escape(entrada,ativo,time.sleep)
                    elif ponto:clicar(ponto)
                    time.sleep(.2);continue
                acao=detector.saida(tela)
                if acao['acao']!=ultimo:
                    emitir(dict(event='cycle',state=acao['acao'],message='Saida do '+nome+': '+acao['acao']));ultimo=acao['acao']
                if 'ponto' in acao:
                    # Confirma o mesmo controle numa captura atual antes do clique.
                    atual=detector.saida(cap.capturar())
                    if atual['acao']!=acao['acao'] or 'ponto' not in atual or math.dist(atual['ponto'],acao['ponto'])>6:continue
                    p=atual['ponto'];absoluto=(cap.area['left']+p[0],cap.area['top']+p[1])
                    if clicar(absoluto,acao.get('botao','left')):
                        emitir(dict(event='cycle',state='clique_enviado',control=acao['acao'],point=absoluto))
                        acao_em=time.monotonic()+.7
                else:time.sleep(.2)
            except (RuntimeError,OSError,ValueError) as e:
                if time.monotonic()-erro_em>=3:emitir(dict(event='log',message='Reconhecimento da saida indisponivel; aguardando sem clicar.',detail=str(e)));erro_em=time.monotonic()
                time.sleep(.2)
    return False

def entrar_elite(dados,control,emitir,limite=120):
    return entrar_dungeon(dados,control,emitir,limite)


def entrar_jardim(dados,control,emitir,limite=120):
    from huntingaitan.rotas.entrada_jardim import PORTAL
    from huntingaitan.rotas.interface_jardim import InterfaceJardim
    from huntingaitan.rotas.jardim_aereo import dentro_jardim
    return entrar_dungeon(dados,control,emitir,limite,portal=PORTAL,dentro=dentro_jardim,
                          spawn=(3351,3295),dificuldade='dificil',nome='Jardim',interface=InterfaceJardim)


def entrar_dungeon(dados,control,emitir,limite=120,*,portal=None,dentro=dentro_mina,
                   spawn=(2850,3344),dificuldade='elite',nome='Mina',interface=None):
    import keyboard,pydirectinput as entrada,mss
    from huntingaitan.visao.captura_aika import CapturaAika
    from huntingaitan.visao.avisos_hunt import DetectorAvisos,reconfirmar,reconfirmar_imagem
    from huntingaitan.rotas.interface_mina import VerificadorElite
    from huntingaitan.rotas.entrada_mina import PORTAL as portal_mina
    PORTAL=portal or portal_mina
    def bloqueadores_da_porta(mobs,pos):
        if math.dist(pos,PORTAL)>8:return set()
        return {m['id'] for m in mobs if m.get('hostile') and m.get('hp',0)>0 and math.dist(m['position'],PORTAL)<=6 and math.dist(m['position'],pos)<=3}
    segundo_plano=getattr(control,'background_keys',False)
    if segundo_plano:
        from huntingaitan.entrada.entrada_janela import EntradaJanela
        entrada=EntradaJanela(dados.hwnd,dados.pid)
    from huntingaitan.visao.captura_interface import captura_interface
    entrada.PAUSE=0;dados.u.GetForegroundWindow.restype=w.HWND
    detector=(interface or InterfaceMina)();verificador=VerificadorElite(dificuldade=dificuldade,auto_escala=getattr(control,'auto_ui_scale',True));avisos=DetectorAvisos();inicio=time.monotonic();acao_em=0.;ultimo=None;elite=False;confirmacoes=0;erro_em=-100.
    progresso_em=inicio;ferido_em=-float('inf');hp_anterior=None;control.bloqueadores_portal=set();verificar_mob_em=0.
    def ativo():return not control.stop.is_set() and not keyboard.is_pressed('f12') and (entrada.disponivel() if segundo_plano else dados.u.GetForegroundWindow()==dados.hwnd) and not control.pause.is_set()
    def clicar(p,duplo=False,confirmar=None):
        if not ativo():return False
        if not (entrada.mover_sem_cursor(*p) if segundo_plano else mover_cursor_fisico(entrada,*p)):return False
        time.sleep(.045)
        for i in range(2 if duplo else 1):
            if not ativo() or confirmar is not None and not confirmar():return False
            # PostMessage nao sintetiza WM_LBUTTONDBLCLK a partir de dois downs.
            if segundo_plano and duplo and i==1:entrada.mouseDown(duplo=True)
            else:entrada.mouseDown()
            try:time.sleep(.065)
            finally:entrada.mouseUp()
            if duplo:time.sleep(.10)
        return True
    with captura_interface(dados,segundo_plano,mss,CapturaAika) as cap:
        while not control.stop.is_set() and not keyboard.is_pressed('f12'):
            if time.monotonic()-inicio>limite:
                emitir(dict(event='log',message='Entrada '+nome+' '+dificuldade+' ainda nao confirmada; tentando novamente sem registrar conclusao.'));return False
            if not ativo():time.sleep(.1);continue
            try:s=dados.snapshot()
            except RuntimeError:time.sleep(.2);continue
            if s['player']['hp']<=0:
                control.reason='personagem_sem_vida';control.stop.set();return False
            try:
                tela=cap.capturar()
                if dentro(s['player']['position']):
                    correto=math.dist(s['player']['position'],spawn)<=15 and verificador.confirmar(tela)
                    confirmacoes=confirmacoes+1 if correto else 0
                    if confirmacoes>=2:
                        emitir(dict(event='log',message='Indicador '+dificuldade+' reconhecido; leitura da escala ajustada.',leitura_interface=verificador.diagnostico))
                        emitir(dict(event='cycle',state='elite_confirmado' if dificuldade=='elite' else 'dificil_confirmado',position=s['player']['position'],message='Nova entrada '+nome+' '+dificuldade+' confirmada por posicao e indicador do jogo.'));return True
                    time.sleep(.4);continue
                if math.dist(s['player']['position'],PORTAL)>(3.5 if nome=='Jardim' else 8):
                    emitir(dict(event='log',message='Personagem fora do alcance do portal; retomando aproximacao por coordenadas.'));return False
                hp=s['player']['hp'];agora=time.monotonic()
                if agora>=verificar_mob_em:
                    verificar_mob_em=agora+.4
                    perto=dados.listar_mobs(s['player']['position'],3,s['player'])
                    bloqueadores=bloqueadores_da_porta(perto,s['player']['position'])
                    if bloqueadores:
                        control.bloqueadores_portal=bloqueadores
                        emitir(dict(event='cycle',state='liberar_entrada',message='Mob colado a porta; liberando o acesso antes de entrar na DG.',target_ids=sorted(bloqueadores)));return False
                if hp_anterior is not None and hp<hp_anterior:ferido_em=agora
                hp_anterior=hp
                if agora-progresso_em>=5 and agora-ferido_em<=3:
                    mobs=dados.listar_mobs(s['player']['position'],4,s['player'])
                    control.bloqueadores_portal={m['id'] for m in mobs if m['hostile'] and m['hp']>0 and math.dist(m['position'],PORTAL)<=8}
                    if control.bloqueadores_portal:
                        emitir(dict(event='cycle',state='liberar_entrada',message='Acesso ao portal sem progresso e recebendo dano; combatendo somente os hostis junto da entrada.'));return False
                if time.monotonic()<acao_em:time.sleep(.1);continue
                aviso=avisos.localizar(tela)
                if aviso and aviso['tipo'] in ['cte_elter','arena_elter','conversa_amigo','season_pass']:
                    ponto=reconfirmar_imagem(aviso,cap.capturar(),cap.area) if segundo_plano else reconfirmar(aviso)
                    if ponto and aviso['tipo']=='season_pass':
                        from huntingaitan.visao.season_pass import fechar_com_escape
                        fechar_com_escape(entrada,ativo,time.sleep)
                    elif ponto:clicar(ponto)
                    time.sleep(.2);continue
                acao=detector.entrada(tela,elite)
                if acao['acao']!=ultimo:
                    emitir(dict(event='cycle',state=acao['acao'],message='Entrada '+nome+': '+acao['acao']));ultimo=acao['acao'];progresso_em=time.monotonic()
                if 'ponto' not in acao:
                    time.sleep(.2);continue
                nova_tela=cap.capturar()
                atual=detector.reconfirmar(nova_tela,acao,elite) if hasattr(detector,'reconfirmar') else detector.entrada(nova_tela,elite)
                if atual['acao']!=acao['acao'] or 'ponto' not in atual or math.dist(atual['ponto'],acao['ponto'])>6:continue
                p=atual['ponto'];absoluto=(cap.area['left']+p[0],cap.area['top']+p[1])
                conferir_clique=None
                if segundo_plano and nome=='Jardim' and acao['acao']=='abrir_portal':
                    from huntingaitan.rotas.interacao_altar import localizar_altar_clicavel,altar_sob_cursor
                    achado=localizar_altar_clicavel(dados,entrada,cap,p,ativo)
                    if not achado:
                        emitir(dict(event='log',message='Altar ainda nao confirmado sob o cursor; nenhum clique enviado.'))
                        acao_em=time.monotonic()+.5;continue
                    absoluto=achado['ponto']
                    confirmado=altar_sob_cursor(dados)
                    if not confirmado or confirmado['ref']!=achado['altar']['ref']:continue
                    emitir(dict(event='cycle',state='altar_clicavel_confirmado',point=absoluto,npc_id=confirmado['id']))
                    def conferir_clique():
                        alvo=altar_sob_cursor(dados)
                        return bool(alvo and alvo['ref']==confirmado['ref'] and alvo['id']==confirmado['id'])
                if clicar(absoluto,acao.get('duplo',False),conferir_clique):
                    if acao['acao'] in ['selecionar_elite','selecionar_dificil']:elite=True
                    elif acao['acao'] in ['abrir_portal','entrar_mina_1','entrar_jardim']:elite=False
                    emitir(dict(event='cycle',state='clique_enviado',control=acao['acao'],point=absoluto))
                    acao_em=time.monotonic()+(.2 if interface is not None else 1.)
            except (RuntimeError,OSError,ValueError) as e:
                if time.monotonic()-erro_em>=3:emitir(dict(event='log',message='Reconhecimento da entrada indisponivel; aguardando sem clicar.',detail=str(e)));erro_em=time.monotonic()
                time.sleep(.2)
    return False
