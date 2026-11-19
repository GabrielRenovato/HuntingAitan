"""Motor por dados internos validados; nao usa minimapa para posicao, vida ou alvo."""
import ctypes,time,math,threading,re,unicodedata
from ctypes import wintypes as w
from dados_internos import DadosInternos
from perfil_hunt import validar
from recuperacao_alvo import RecuperacaoAlvo
from selecao_regional import BuscaRegional
from entrada_segura import liberar_tecla,liberar_mouse
from navegador_local import NavegadorLocal
from cancelamento_normal import CancelamentoNormal,executar_combo,perfil_combo,duracao_tecla
from cura_prioritaria import CuraPrioritaria
from vigia_ataque import VigiaAtaque
from controle_avisos import ObservadorAvisos
from circuito_termes import CircuitoTermes,dentro_regiao,conferir_arquivos,distancia_segmento
from mina_lenfer import MinaLenfer,dentro_mina
from hunt_core import CadenciaCombate,erro_angular,VerificadorMovimento,AgendaBuffs,executar_buff

NOMES={'verit':'Verit Mutante','penza':'Penza Poderosa Mutante','croshu':'Croshu Mutante das Cinzas','tet':'Tet das Chamas'}
def nome_normal(s):return re.sub('[^a-z]','',unicodedata.normalize('NFKD',s.lower()))
def alvo_permitido(target,player,base,profile):
    if not target or not target['hostile'] or target['hp']<=0:return False
    if abs(target['height']-player['height'])>5:return False
    if profile.get('patrol_mode')=='termes_penza':
        if not dentro_regiao(target['position']):return False
    elif profile.get('patrol_mode')=='mina_lenfer':
        if not dentro_mina(target['position']):return False
    elif math.dist(target['position'],base)>profile['radius']:return False
    if math.dist(target['position'],player['position'])>profile['radius']:return False
    return profile['target']=='qualquer' or nome_normal(target['name'])==nome_normal(NOMES[profile['target']])

class ProgressoNativo:
    def __init__(self,alvo,agora):
        self.ref=alvo['ref'];self.id=alvo['id'];self.nome=nome_normal(alvo['name']);self.hp=alvo['hp'];self.posicao=alvo.get('position');self.nome_original=alvo['name']
        self.ultimo_dano=agora;self.dano=False;self.zero_desde=None;self.leituras_zero=0
    def observar(self,alvo,agora):
        if alvo is None:return 'ausente'
        if alvo['id']!=self.id or nome_normal(alvo['name'])!=self.nome:return 'outro'
        # O endereco pode mudar na atualizacao do cliente; o ID continua sendo
        # a identidade do mob. Aceita a nova referencia sem buscar com TAB.
        self.ref=alvo['ref'];self.posicao=alvo.get('position',self.posicao)
        if alvo['hp']<=0:
            if self.zero_desde is None:self.zero_desde=agora
            self.leituras_zero+=1
            return 'morto' if self.leituras_zero>=2 and agora-self.zero_desde>=.25 else 'confirmando_morte'
        self.zero_desde=None;self.leituras_zero=0
        if alvo['hp']<self.hp:self.hp=alvo['hp'];self.ultimo_dano=agora;self.dano=True
        return 'mesmo'
    def precisa_aproximar(self,agora,distancia):
        # Tambem vale depois de acertar: stun, deslocamento do mob ou um toque
        # de cancelamento podem tirar o personagem do alcance novamente.
        return distancia>3. or (distancia>2.4 and (not self.dano or agora-self.ultimo_dano>=1.5))
    def aproximacao_falhou(self,agora,distancia,perfil):
        # Depois do primeiro dano, stun ou recarga nao autorizam abandonar o mob.
        return not self.dano and (agora-self.ultimo_dano>=perfil['no_damage_seconds'] or distancia>perfil['radius'])


def main(profile,event_sink,control,percurso=None):
    import keyboard,pydirectinput as entrada
    p=validar(profile);entrada.PAUSE=0
    if percurso is not None:p.update(patrol_mode='base',target='qualquer',radius=min(12,p['radius']))
    u=ctypes.windll.user32;u.GetForegroundWindow.restype=w.HWND
    u.ShowWindow.argtypes=[w.HWND,ctypes.c_int];u.SetForegroundWindow.argtypes=[w.HWND]
    def foco():
        t=ctypes.create_unicode_buffer(256);u.GetWindowTextW(u.GetForegroundWindow(),t,256);return t.value=='AikaClient'
    def parar():return control.stop.is_set() or keyboard.is_pressed('f12')
    def ativo():return foco() and not parar() and not control.pause.is_set()
    seg=set();lock=threading.RLock();fim=threading.Event();ultima=[time.monotonic()];modal_bloqueia=threading.Event()
    def soltar():
        with lock:
            for k in list(seg):
                if liberar_tecla(entrada,k) is not False:seg.discard(k)
    def liberar(k):
        with lock:
            if k in seg and liberar_tecla(entrada,k) is not False:seg.discard(k)
    def segurar(k):
        with lock:
            if not ativo() or modal_bloqueia.is_set():return False
            if k not in seg:
                if entrada.keyDown(k) is False:return False
                seg.add(k)
            return True
    def esperar(s):
        ate=time.monotonic()+s
        while ativo():
            restante=ate-time.monotonic()
            if restante<=0:break
            time.sleep(min(.005,restante))
    def pulso(k,s=.045):
        if not k or not ativo():return False
        if not segurar(k):return False
        try:esperar(s)
        finally:liberar(k)
        return True
    def log(msg,**d):event_sink(dict(event='log',message=msg,**d))
    def vigia():
        while not fim.wait(.03):
            if not ativo() or modal_bloqueia.is_set() or time.monotonic()-ultima[0]>.5:soltar()
    dados=None
    try:
        dados=DadosInternos();s=dados.snapshot();s2=dados.snapshot()
        if math.dist(s['player']['position'],s2['player']['position'])>5:raise RuntimeError('Posicao interna instavel; tente novamente com o personagem parado.')
        event_sink(dict(event='status',state='waiting',message='Dados internos validados. Volte ao Aika para capturar a base e comecar.'))
        threading.Thread(target=vigia,daemon=True).start()
        # Pedido normal de foco apos o usuario clicar em Comecar.
        if p['minimize_on_start'] and not control.pause.is_set() and not parar():
            u.ShowWindow(dados.hwnd,9)
            u.SetForegroundWindow(dados.hwnd)
        while not ativo():
            if parar():return
            time.sleep(.04)
        s=dados.snapshot();base=tuple(s['player']['position']) if p['auto_base'] else tuple(p['base'])
        event_sink(dict(event='base',base=base));log('Base capturada por dados internos.',posicao=base)
        circuito=None;circuito_log=None;circuito_replanejar_em=0.;regiao=dentro_regiao;mina=p['patrol_mode']=='mina_lenfer';mapa_mina=None
        if percurso is not None:
            circuito=percurso;regiao=percurso.contem
            log('Retorno ao portal da Mina iniciado por coordenadas e colisao.')
        elif p['patrol_mode']=='termes_penza':
            circuito=CircuitoTermes(s['player']['position'])
            conferir_arquivos(dados.caminho.parent)
            log('Circuito Termes ativado: 6, 5, 4, 7, 8, 9 e volta pelo mesmo corredor. Apenas Penza Poderosa Mutante.')
        elif mina:
            circuito=MinaLenfer(s['player']['position']);circuito.conferir(dados.caminho.parent);regiao=dentro_mina
            mapa_mina=dados.u32(dados.cena_validada()+0x38)
            log('Mina LEnfer: caminho direto para Malik iniciado.',entrada=s['player']['position'],mapa=mapa_mina)
        trilha=[base];volta=[];estado='buscar';progresso=None;ultima_tab=0.;fim_busca=0.;ultima_telemetria=0.;inicio=time.monotonic();heading=None;origem_mov=None;falhas_desde=None;espera_na_base=False
        tecla_cura=p['heal_key'] if p['heal_enabled'] else ''
        cadencia=CadenciaCombate({'intervalo_skills':p['action_gap'],'recargas':{v['key']:v['seconds'] for v in p['skills'] if v['enabled'] and v['key']!=tecla_cura}})
        cura=CuraPrioritaria(tecla_cura,p['hp_percent']/100,next((v['seconds'] for v in p['skills'] if v['key']==tecla_cura),15.))
        vigia_ataque=VigiaAtaque()
        ultimo_hp=s['player']['hp'];ultimo_ferimento=-float('inf')
        navegador=NavegadorLocal();cc={};cc_em=0.;cc_desde=None;cc_log=False;cc_motivo=None;nav_log_em=-100.;aprox_pos=None;reaprox_id=None
        regional=BuscaRegional();indisponiveis={};mobs_regiao=None;pool_em=0.;nativo_em=0.;nativo_pausou=False;pool_erro_em=-100.
        busca_destino=None;busca_ate=0.;reconhecer_buff_ate=0.;retorno_busca=False;buff_pausa_desde=None
        recuperacao=RecuperacaoAlvo()
        cancelamento=CancelamentoNormal(p['cancel_normal'])
        log('Cancelamento de ataque normal experimental.',ativo=p['cancel_normal'])
        buffs=getattr(control,'buff_agenda',None) if getattr(control,'cycle_context',False) else None
        if buffs is None:buffs=AgendaBuffs(inicio,p['buff_keys'],p['buff_minutes']*60,p['buff_gap'],p['buffs_enabled'])
        if getattr(control,'cycle_context',False):control.buff_agenda=buffs
        log('Rebuff programado.',ativo=p['buffs_enabled'],minutos=p['buff_minutes'],atalhos=p['buff_keys'])
        log('Habilidades ativas nesta sessao.',atalhos=list(cadencia.recargas))
        log('Motor com recargas reais e cura prioritaria.',versao='mina-lenfer-9',cura=tecla_cura,hp_percent=p['hp_percent'])
        verificador=VerificadorMovimento(p['stationary_seconds']);suprimento_em={};item_em={};janela_pausa=None
        monitor=ObservadorAvisos(fim,ativo,log,bloqueio=modal_bloqueia)
        monitor.iniciar()
        log('Monitor CTE e Arena Elter: prioridade de fechamento ativa.')
        modal_desde=None;clique_modal_em=0.;cliques_modal=0;modal_log_em=-100.
        while not parar():
            if not ativo():
                soltar();antes=time.monotonic();event_sink(dict(event='status',state='paused',message='Pausado pelo painel.' if control.pause.is_set() else 'Aika sem foco; volte ao jogo para retomar.'))
                while not ativo() and not parar():time.sleep(.04)
                decorrido=time.monotonic()-antes
                if modal_desde is not None:modal_desde+=decorrido
                if buff_pausa_desde is not None:buff_pausa_desde+=decorrido
                if circuito:circuito.pausar(decorrido)
                vigia_ataque.suspender(time.monotonic())
                if progresso:progresso.ultimo_dano+=decorrido
                cancelamento=CancelamentoNormal(p['cancel_normal'])
                recuperacao.pausar(decorrido);fim_busca+=decorrido;busca_ate+=decorrido;verificador.observar(None,0,False);continue
            # Fecha o aviso antes de teclado, movimento, cura ou ataque. Um
            # clique sozinho nao e prova de fechamento: aguarda duas capturas.
            aviso=monitor.atual();agora_modal=time.monotonic()
            if modal_bloqueia.is_set():
                soltar();navegador.suspender(s['player']['position'],agora_modal)
                verificador.observar(None,agora_modal,False)
                if modal_desde is None:
                    modal_desde=agora_modal;cliques_modal=0
                    log('Janela bloqueando o jogo; combate suspenso para fechar o aviso.',tipo=(aviso or {}).get('tipo'),ponto=(aviso or {}).get('ponto'))
                if agora_modal-ultima_telemetria>=.2:
                    try:leitura_modal=dados.snapshot()
                    except RuntimeError:leitura_modal=None
                    if leitura_modal:
                        s=leitura_modal;pm=s['player'];tm=s['target'];ultima[0]=time.monotonic()
                        event_sink(dict(event='telemetry',source='native',state='aviso',aviso_tipo=(aviso or {}).get('tipo'),position=pm['position'],base=base,hp=pm['hp']/pm['hp_max'],mp=pm['mp']/pm['mp_max'] if pm['mp_max'] else None,elapsed=agora_modal-inicio,target=tm['name'] if tm else None,target_id=tm['id'] if tm else None,target_hp=tm['hp'] if tm else None,target_hp_max=tm['hp_max'] if tm else None))
                        ultima_telemetria=agora_modal
                        if pm['hp']<=0:
                            control.reason='personagem_sem_vida';log('Personagem sem vida com janela bloqueante aberta; caca encerrada.');break
                conhecido=aviso and aviso['tipo'] in ('cte_elter','arena_elter','conversa_amigo')
                if conhecido and agora_modal-aviso['capturado']<=1. and agora_modal>=clique_modal_em:
                    from avisos_hunt import reconfirmar
                    try:ponto=reconfirmar(aviso)
                    except Exception as e:
                        log('Nao consegui reconfirmar o aviso.',detail=str(e));ponto=None
                    clique_modal_em=agora_modal+.6
                    if ponto and ativo():
                        entrada.moveTo(*ponto)
                        if ativo():
                            entrada.mouseDown()
                            try:esperar(.045)
                            finally:liberar_mouse(entrada)
                            cliques_modal+=1
                            log('Aviso: clique de fechamento enviado; aguardando desaparecer.',tipo=aviso['tipo'],tentativa=cliques_modal)
                elif aviso and aviso['tipo']=='janela_desconhecida' and agora_modal-modal_log_em>=5:
                    log('Janela com Confirmar/Cancelar nao reconhecida; entradas pausadas para evitar clique incorreto.');modal_log_em=agora_modal
                esperar(.025);continue
            if modal_desde is not None:
                duracao=agora_modal-modal_desde
                if buff_pausa_desde is not None:buff_pausa_desde+=duracao
                if circuito:circuito.pausar(duracao)
                if progresso:progresso.ultimo_dano+=duracao
                recuperacao.pausar(duracao);fim_busca+=duracao;busca_ate+=duracao
                vigia_ataque.suspender(agora_modal)
                cancelamento=CancelamentoNormal(p['cancel_normal'])
                log('Fechamento confirmado em duas capturas; retomando combate.',cliques=cliques_modal,segundos=round(duracao,2))
                modal_desde=None
            agora=time.monotonic()
            try:s=dados.snapshot();ultima[0]=time.monotonic();falhas_desde=None
            except RuntimeError:
                soltar()
                if falhas_desde is None:falhas_desde=agora
                if agora-falhas_desde>5:raise
                esperar(.1);continue
            player=s['player'];pos=tuple(player['position']);target=s['target']
            if percurso is not None:base=pos
            if mina and dados.u32(dados.cena_validada()+0x38)!=mapa_mina:
                soltar();raise RuntimeError('A cena da Mina mudou; percurso interrompido sem registrar conclusao.')
            if player['hp']<ultimo_hp:ultimo_ferimento=agora
            ultimo_hp=player['hp']
            if hasattr(dados,'caca_original_ativa') and agora>=nativo_em:
                nativo_em=agora+.5
                if dados.caca_original_ativa():
                    soltar()
                    if not nativo_pausou:log('O F12 original esta ativo; aguardando ele ser finalizado para evitar dois controles.')
                    nativo_pausou=True;esperar(.1);continue
                if nativo_pausou:
                    nativo_pausou=False;estado='buscar';progresso=None;heading=None;origem_mov=None
                    if p['auto_base']:base=pos;event_sink(dict(event='base',base=base))
                    trilha=[base];pool_em=0.;log('Controle independente retomado; F12 original finalizado.')
            elif nativo_pausou:
                soltar();esperar(.04);continue
            if hasattr(dados,'estados_controle') and agora>=cc_em:
                try:
                    cc=dados.estados_controle();cc_em=agora+.1
                    if hasattr(dados,'recargas_atalhos'):
                        try:
                            cc['recargas_atalhos']=dados.recargas_atalhos()
                            cc['tipos_atalhos']=getattr(dados,'tipos_atalhos',{})
                        except RuntimeError as e:
                            cc['recargas_atalhos']={}
                            if agora-pool_erro_em>=3:log('Recarga da barra indisponivel; usando intervalos configurados.',detail=str(e));pool_erro_em=agora
                except RuntimeError as e:
                    soltar()
                    if agora-pool_erro_em>=3:log('Aguardando estados do personagem.',detail=str(e));pool_erro_em=agora
                    esperar(.1);continue
            if estado!='combater' and hasattr(dados,'listar_mobs') and agora>=pool_em:
                try:
                    lista=dados.listar_mobs(pos if circuito else base,p['radius'],player)
                    indisponiveis={id_:ate for id_,ate in indisponiveis.items() if ate>agora}
                    mobs_regiao=[m for m in lista if m['id'] not in indisponiveis and alvo_permitido(m,player,base,p)]
                    if mina:mobs_regiao=circuito.filtrar_mobs(mobs_regiao,pos,p['radius'])
                    if percurso is not None:mobs_regiao=[m for m in mobs_regiao if regiao(m['position'])]
                    regional.atualizar(mobs_regiao);pool_em=agora+.4
                except RuntimeError as e:
                    soltar();mobs_regiao=None
                    if agora-pool_erro_em>=5:log('Aguardando lista de mobs valida.',detail=str(e));pool_erro_em=agora
                    esperar(.1);continue
            if mina and (estado=='combater' or mobs_regiao):circuito.combate_ativo()
            if not circuito and estado=='retornar' and not retorno_busca and mobs_regiao and math.dist(pos,base)<=p['radius']+2:
                soltar();heading=None;origem_mov=None;estado='selecionar';fim_busca=agora+p['no_damage_seconds']
                log('Mobs validos na regiao; priorizando combate antes de retornar.',quantidade=len(mobs_regiao))
            if agora-ultima_telemetria>.15:
                event_sink(dict(event='telemetry',controle=cc,heading=player.get('heading'),mobs_regiao=len(mobs_regiao) if mobs_regiao is not None else None,source='native',dungeon=mina,patrol_point=circuito.trechos[circuito.trecho]['ate'] if circuito else None,patrol_laps=circuito.voltas if circuito else None,state='rebufar' if buffs.em_andamento or buff_pausa_desde is not None else estado,position=pos,base=base,hp=player['hp']/player['hp_max'],mp=player['mp']/player['mp_max'] if player['mp_max'] else None,elapsed=agora-inicio,next_buff_seconds=max(0,buffs.vencimento-agora) if p['buffs_enabled'] else None,next_buffs_seconds={k:round(max(0,v-agora),2) for k,v in buffs.vencimentos.items()} if p['buffs_enabled'] else {},target=target['name'] if target else None,target_id=target['id'] if target else None,target_hostile=target['hostile'] if target else None,target_distance=round(math.dist(target['position'],player['position']),2) if target else None,target_hp=target['hp'] if target else None,target_hp_max=target['hp_max'] if target else None));ultima_telemetria=agora
            if p['duration_minutes'] and agora-inicio>=p['duration_minutes']*60:
                soltar();pulso(p['return_key']);control.reason='tempo_encerrado';log('Tempo de caca encerrado.');break
            if player['hp']<=0:soltar();control.reason='personagem_sem_vida';log('Personagem sem vida; caca encerrada.');break
            usou=False
            for tipo in ['hp','mp']:
                maxi=player[tipo+'_max'];fracao=player[tipo]/maxi if maxi else 1
                keys=[k for k in p[tipo+'_keys'] if k]
                if fracao<p[tipo+'_percent']/100 and keys and agora>=suprimento_em.get(tipo,0):
                    if pulso(keys[0]):suprimento_em[tipo]=agora+3;cadencia.registrar('8',agora);usou=True;break
            if usou:
                cancelamento.acao(False,agora,agora+1.4);continue
            bloqueado_cc=any(cc.get(k,False) for k in ('stunned','paralyzed','frozen'))
            motivo_cc='controle' if bloqueado_cc else ('execucao' if cc.get('casting',False) else None)
            if motivo_cc:
                vigia_ataque.suspender(agora)
                soltar();navegador.suspender(pos,agora);verificador.observar(None,agora,False)
                if cc_desde is None:cc_desde=agora
                if cc_motivo!=motivo_cc:
                    log('Controle temporario detectado; aguardando sem trocar alvo.' if motivo_cc=='controle' else 'Cliente executando habilidade; aguardando finalizar.',efeitos=cc)
                    cc_log=True;cc_motivo=motivo_cc
                esperar(.03);continue
            if cc_desde is not None:
                if buff_pausa_desde is not None:buff_pausa_desde+=agora-cc_desde
                if circuito:circuito.pausar(agora-cc_desde)
                if progresso:progresso.ultimo_dano+=agora-cc_desde
                recuperacao.pausar(agora-cc_desde);cc_desde=None;cc_log=False
                cancelamento=CancelamentoNormal(p['cancel_normal']);navegador.suspender(pos,agora)
                log('Controle temporario terminou; retomando o mesmo alvo.' if cc_motivo=='controle' else 'Execucao do cliente finalizada; retomando o mesmo alvo.');cc_motivo=None
            hp_atual=player['hp']/player['hp_max']
            recarga_cura=cc.get('recargas_atalhos',{}).get(tecla_cura)
            confirmacao=cura.observar(agora,hp_atual,recarga_cura)
            if confirmacao:
                log('Verificacao da cura.',resultado=confirmacao,tecla=tecla_cura,hp=hp_atual,recarga=recarga_cura)
            if cura.necessaria(agora,hp_atual,recarga_cura):
                vigia_ataque.suspender(agora)
                # Independente de mob, dano recente, alcance e fila ofensiva.
                # Os bloqueios reais de stun e casting ja foram respeitados acima.
                soltar();navegador.suspender(pos,agora)
                if pulso(tecla_cura,duracao_tecla((recarga_cura or {}).get('skill'))):
                    cura.enviada(time.monotonic(),hp_atual)
                    cadencia.livre_em=max(cadencia.livre_em,time.monotonic()+p['action_gap'])
                    cancelamento.acao(False,agora,cadencia.livre_em)
                    event_sink(dict(event='action',key=tecla_cura,kind='heal',hp=hp_atual,skill_state=recarga_cura,target_id=target['id'] if target else None))
                    log('Cura prioritaria enviada; aguardando confirmacao.',tecla=tecla_cura,hp=hp_atual)
                esperar(.015);continue
            if cura.aguardando_inicio(agora):
                soltar();esperar(.015);continue
            if agora<reconhecer_buff_ate:
                soltar();esperar(.015);continue
            tranquilo=estado in ['buscar','percorrer'] and agora-ultimo_ferimento>=3
            # Um buff vencido nao pode depender de toda a regiao ficar sem dano.
            # Inicia a sequencia entre acoes, com HP suficiente e fora de stun/cast.
            janela_curta=(estado=='combater' and target is not None and progresso is not None
                          and target['id']==progresso.id and hp_atual>=.5
                          and agora-ultimo_ferimento>=.5 and agora>=cadencia.livre_em
                          and agora>=buffs.vencimento+5)
            seguro_buff=buffs.em_andamento or tranquilo or janela_curta
            buff=buffs.proximo(agora,seguro_buff)
            if (buffs.em_andamento or agora<reconhecer_buff_ate) and buff_pausa_desde is None:
                buff_pausa_desde=agora
                log('Ciclo de buffs iniciado; ataque, TAB e movimento suspensos.')
            if buff_pausa_desde is not None:
                vigia_ataque.suspender(agora);navegador.suspender(pos,agora)
                verificador.observar(None,agora,False)
            if buff is not None:
                soltar()
                if executar_buff(buff,segurar,liberar,esperar,ativo):
                    log('Atalho de buff enviado.',atalho=buff)
                    buffs.confirmar(time.monotonic());reconhecer_buff_ate=time.monotonic()+.4
                    cadencia.livre_em=max(cadencia.livre_em,reconhecer_buff_ate)
                    log('Agenda individual de buffs atualizada.',vencimentos=buffs.vencimentos)
                    if not buffs.em_andamento:log('Buffs vencidos enviados; cada atalho tem sua propria renovacao de '+str(p['buff_minutes'])+' minutos.')
                continue
            if buffs.em_andamento:
                soltar();esperar(.02);continue
            if buff_pausa_desde is not None:
                decorrido=agora-buff_pausa_desde
                if circuito:circuito.pausar(decorrido)
                if progresso:progresso.ultimo_dano+=decorrido
                recuperacao.pausar(decorrido);fim_busca+=decorrido;busca_ate+=decorrido
                cancelamento=CancelamentoNormal(p['cancel_normal']);buff_pausa_desde=None
                log('Ciclo de buffs concluido; combate liberado com a selecao preservada.')
            if math.dist(pos,trilha[-1])>=1.5 and estado!='retornar':trilha.append(pos)
            def seguir_grade(destino,chave,alcance):
                nonlocal nav_log_em
                retorno=chave[0]=='base'
                # O limite de caca nao pode impedir a propria reentrada.
                raio=max(p['radius']+2,math.dist(pos,base)+2) if retorno else p['radius']+2
                limite=(base,raio)
                if circuito:
                    # Ao ser empurrado para fora da faixa, permite somente
                    # uma passagem estreita de reentrada, com colisao validada.
                    reentrada=chave[0]=='circuito' and not regiao(pos)
                    limite=lambda q:regiao(q) or (reentrada and distancia_segmento(q,pos,destino)<=2)
                try:plano=navegador.planejar(dados,pos,player.get('heading'),destino,chave,agora,alcance=alcance,limite=limite,parcial=retorno or bool(circuito))
                except RuntimeError as e:
                    soltar()
                    if agora-nav_log_em>=3:log('Aguardando grade valida antes de mover.',detail=str(e));nav_log_em=agora
                    return 'aguardar_grade'
                if plano['estado']!='andando':
                    soltar()
                    if plano['estado'] in ['sem_caminho','bloqueado','replanejar'] and agora-nav_log_em>=1:
                        log('Navegacao: '+plano['estado']+'.',destino=destino);nav_log_em=agora
                    return plano['estado']
                if agora-nav_log_em>=2:
                    log('Seguindo rota com colisao validada.',pontos=plano['pontos'],destino=destino,erro=round(plano['erro'],1),andando=plano['w'],giro=plano.get('giro'),pulso_giro=plano.get('tempo'));nav_log_em=agora
                if plano['w']:segurar('w')
                else:liberar('w')
                if plano.get('giro'):pulso(plano['giro'],plano['tempo'])
                return 'andando'
            if circuito:
                if not regiao(pos,margem=50):
                    soltar();raise RuntimeError('Personagem saiu da regiao do percurso; reposicione antes de retomar.')
                if estado=='retornar':estado='percorrer'
                reentrar=not regiao(pos)
                if reentrar or (estado!='combater' and not mobs_regiao):
                    if mobs_regiao is None and not reentrar:
                        soltar();esperar(.03);continue
                    if estado!='combater':estado='percorrer'
                    vigia_ataque.suspender(agora);verificador.observar(None,agora,False)
                    if agora<circuito_replanejar_em:soltar();esperar(.03);continue
                    passo=circuito.destino(pos,agora)
                    marca=(circuito.trecho,passo['estado'])
                    if passo['estado']=='concluido':
                        if percurso is not None:
                            soltar();control.reason='entrada_alcancada';event_sink(dict(event='cycle',state='entrada_confirmada',position=pos));break
                        soltar();control.reason='mina_finalizada'
                        event_sink(dict(event='dungeon_complete',abates=passo['abates'],message='Malik abatido com vida zero confirmada e area final limpa.'))
                        log('Mina finalizada: Malik confirmado e area final limpa.');break
                    if marca!=circuito_log:
                        if mina:
                            msg='Aguardando confirmacao do chefe da sala.' if passo['estado']=='aguardar_chefe' else 'Verificando sala limpa.' if passo['estado'].startswith('aguardar') else 'Percorrendo Mina LEnfer por caminho validado.'
                        elif percurso is not None:msg='Seguindo caminho ate a entrada da Mina.'
                        else:msg='Procurando Penzas por 5s no ponto.' if passo['estado']=='aguardar' else 'Percorrendo circuito de Termes por caminho validado.'
                        log(msg,ponto=passo['ponto'],voltas=passo['voltas'],chefe=passo.get('chefe'));circuito_log=marca
                    if passo['estado'].startswith('aguardar'):soltar();esperar(.03);continue
                    nav=seguir_grade(passo['destino'],passo['chave'],.9)
                    if nav in ['sem_caminho','bloqueado','aguardar_grade']:
                        circuito_replanejar_em=agora+2
                        log('Passagem do circuito indisponivel na grade atual; aguardando nova leitura sem avancar o ponto.',ponto=passo['ponto'])
                    esperar(.015);continue
                if estado=='percorrer':
                    soltar();estado='buscar';regional.confirmar_alvo();retorno_busca=False
                    log('Hostil proximo; percurso pausado para combate.' if mina or percurso is not None else 'Penza encontrado no corredor; percurso pausado para combate.')
            if not circuito and math.dist(pos,base)>p['radius']+2 and estado!='retornar':
                soltar();pulso('s',.06)
                navegador.invalidar();estado='retornar';progresso=None;pool_em=0.
                log('Fora da area de caca; interrompendo perseguicao e retornando por trechos.',distancia=math.dist(pos,base),raio=p['radius'])
            if estado=='buscar':
                soltar()
                if mobs_regiao is None:pulso('tab');ultima_tab=agora
                fim_busca=agora+p['no_damage_seconds'];estado='selecionar';continue
            if estado=='selecionar':
                if mobs_regiao is not None:
                    try:camera=dados.camera_regional() if hasattr(dados,'camera_regional') else None
                    except RuntimeError:camera=None
                    acao,valor=regional.decidir(agora,target,camera,pos=pos)
                    if acao=='retornar':
                        if circuito:
                            soltar();navegador.invalidar()
                            for m in mobs_regiao:indisponiveis[m['id']]=agora+15
                            mobs_regiao=[];pool_em=0.;estado='percorrer';regional.confirmar_alvo()
                            log('Alvos sem selecao confirmada; seguindo o percurso sem registrar abate.');continue
                        soltar();pulso('s',.06);navegador.invalidar()
                        retorno_busca=True;estado='retornar'
                        log('Tres aproximacoes sem alvo; voltando a base para recomecar a busca.')
                        continue
                    if acao=='aproximar':
                        soltar();busca_destino=valor;busca_ate=agora+3
                        navegador.invalidar();estado='aproximar_busca'
                        log('Busca sem alvo por 8s; aproximando de candidato por caminho validado.',alvo_id=valor['id'])
                        continue
                    if acao=='orientar':
                        soltar();tecla,tempo=valor
                        if pulso(tecla,tempo):log('Orientando para mob identificado na regiao.',alvo_id=regional.preferido)
                        continue
                    if acao=='tab':
                        if pulso('tab'):event_sink(dict(event='selection',key='tab',candidate_id=valor))
                        ultima_tab=agora;esperar(.015);continue
                    if acao!='aceitar':
                        # Nenhum candidato: aguarda ou volta apenas se estiver distante.
                        if mobs_regiao or math.dist(pos,base)<=3:
                            soltar();esperar(.03);continue
                    target=valor if acao=='aceitar' else None
                if alvo_permitido(target,player,base,p):
                    progresso=ProgressoNativo(target,agora);recuperacao.reiniciar();espera_na_base=False;estado='combater';log('Alvo confirmado por dados internos.',alvo=target['name']);continue
                if agora>=fim_busca:
                    if math.dist(pos,base)<=3:
                        soltar();trilha=[base];heading=None;origem_mov=None
                        if not espera_na_base:log('Na base sem alvo valido; aguardando novos mobs.')
                        espera_na_base=True;fim_busca=agora+p['no_damage_seconds'];ultima_tab=agora
                        esperar(.1);continue
                    estado='retornar';volta=list(reversed(trilha));heading=None;origem_mov=None
                    pulso('s',.06);log('Sem alvo proximo; retornando a base.');continue
                if agora-ultima_tab>=.25:pulso('tab');ultima_tab=agora
                esperar(.015);continue
            if estado=='aproximar_busca':
                if alvo_permitido(target,player,base,p):
                    soltar();progresso=ProgressoNativo(target,agora);recuperacao.reiniciar()
                    estado='combater';regional.confirmar_alvo()
                    log('Alvo confirmado apos aproximacao de busca.',alvo=target['name'],alvo_id=target['id']);continue
                candidato=next((m for m in mobs_regiao or [] if m['id']==busca_destino['id']),None)
                if candidato is None:
                    soltar();estado='selecionar';regional.reiniciar_busca(agora);continue
                nav=seguir_grade(candidato['position'],('busca',candidato['id']),2.)
                if nav=='andando' and agora<busca_ate:esperar(.015);continue
                soltar();estado='selecionar';regional.reiniciar_busca(agora)
                if nav in ['bloqueado','sem_caminho']:
                    indisponiveis[candidato['id']]=agora+20;pool_em=0.
                    log('Candidato sem passagem; buscando outro ID.',alvo_id=candidato['id'])
                else:
                    if pulso('tab'):event_sink(dict(event='selection',key='tab',candidate_id=candidato['id'],apos_aproximacao=True))
                    log('Aproximacao de busca concluida; reconfirmando alvo.',alvo_id=candidato['id'])
                continue
            if estado=='combater':
                if target is None or math.dist(pos,target['position'])<=2.4:soltar()
                resultado=progresso.observar(target,agora)
                if resultado in ['ausente','outro']:
                    soltar();navegador.suspender(pos,agora)
                    anterior=None
                    try:anterior=dados.entidade(progresso.ref)
                    except RuntimeError:pass
                    r=progresso.observar(anterior,agora)
                    if r=='morto':resultado='morto'
                    elif r=='confirmando_morte':
                        esperar(.03);continue
                    else:
                        acao=recuperacao.decidir(agora)
                        if acao=='indisponivel':
                            log('Alvo nao recuperado; encerrando busca desse ID sem registrar abate.',id_esperado=progresso.id,tentativas=recuperacao.tentativas)
                            indisponiveis[progresso.id]=agora+15
                            recuperacao.reiniciar();pool_em=0.;cancelamento=CancelamentoNormal(p['cancel_normal'])
                            verificador.observar(None,agora,False)
                            if alvo_permitido(target,player,base,p):
                                progresso=ProgressoNativo(target,agora)
                                log('Atacando o alvo proximo ja selecionado.',alvo=target['name'],alvo_id=target['id'])
                            else:
                                progresso=None;estado='selecionar';fim_busca=agora+p['no_damage_seconds'];ultima_tab=agora
                            continue
                        if acao=='tab':
                            log('Recuperando somente o alvo travado.',id_esperado=progresso.id,id_atual=target['id'] if target else None,tentativa=recuperacao.tentativas)
                            pulso('tab');ultima_tab=agora
                        esperar(.03);continue
                if resultado=='mesmo':
                    recuperacao.reiniciar()
                    if not progresso.precisa_aproximar(agora,math.dist(pos,target['position'])):soltar()
                if resultado=='confirmando_morte':soltar();esperar(.03);continue
                if resultado=='morto':
                    if mina:
                        chefe=circuito.registrar_abate(progresso.id,progresso.nome_original,progresso.posicao or pos,agora)
                        if chefe:log('Chefe da Mina abatido com vida zero confirmada.',chefe=chefe,alvo_id=progresso.id)
                    soltar();reaprox_id=None;estado='buscar';pool_em=0.;log('Mob abatido; procurando o proximo.');continue
                if progresso.precisa_aproximar(agora,math.dist(pos,target['position'])) and player.get('heading') is not None and hasattr(dados,'cena_validada'):
                    if progresso.dano and reaprox_id!=progresso.id:
                        reaprox_id=progresso.id;cancelamento.suspender_alvo(progresso.id);navegador.invalidar()
                        log('Alvo saiu do alcance; reaproximando e suspendendo cancelamento nesta luta.',alvo_id=progresso.id,distancia=round(math.dist(pos,target['position']),2))
                    if aprox_pos is None or math.dist(pos,aprox_pos)>=.6:
                        aprox_pos=pos
                        if not progresso.dano:progresso.ultimo_dano=agora
                    nav=seguir_grade(target['position'],('mob',progresso.id),2.)
                    if nav in ['sem_caminho','bloqueado']:
                        indisponiveis[progresso.id]=agora+15;pool_em=0.;estado='buscar';progresso=None;aprox_pos=None
                        log('Alvo sem passagem; procurando outro na regiao.');continue
                    if nav!='chegou':esperar(.015);continue
                else:aprox_pos=None;reaprox_id=None
                if progresso.aproximacao_falhou(agora,math.dist(pos,target['position']) if circuito else math.dist(pos,base),p):
                    indisponiveis[progresso.id]=agora+15;pool_em=0.
                    soltar();estado='buscar';progresso=None;aprox_pos=None
                    log('Alvo sem dano; procurando outro mob antes de retornar.');continue
                if resultado!='mesmo':esperar(.01);continue
                vigia_ataque.observar(target,agora)
                if not vigia_ataque.recuperar_ate and vigia_ataque.iniciar(agora,math.dist(pos,target['position'])):
                    soltar();navegador.invalidar();cancelamento.suspender_alvo(progresso.id)
                    log('Ataques sem dano por 3s; corrigindo aproximacao e orientacao sem trocar alvo.',alvo_id=progresso.id,hp_alvo=target['hp'],distancia=math.dist(pos,target['position']),envios=vigia_ataque.envios)
                if vigia_ataque.recuperar_ate:
                    if agora>=vigia_ataque.recuperar_ate:
                        soltar();vigia_ataque.suspender(agora)
                        log('Reposicionamento curto encerrado; verificando dano no mesmo alvo.',alvo_id=progresso.id)
                    else:
                        if math.dist(pos,target['position'])>1.3 and player.get('heading') is not None and hasattr(dados,'cena_validada'):
                            nav=seguir_grade(target['position'],('recuperar_ataque',progresso.id),1.3)
                            if nav=='andando':esperar(.015);continue
                        soltar()
                        if player.get('heading') is not None:
                            dx,dy=target['position'][0]-pos[0],target['position'][1]-pos[1]
                            erro=erro_angular(math.degrees(math.atan2(dx,dy)),player['heading'])
                            if math.hypot(dx,dy)>.1 and abs(erro)>15:
                                pulso('d' if erro>0 else 'a',min(.08,max(.015,abs(erro)/150)))
                                continue
                        vigia_ataque.suspender(agora)
                    cadencia.normal_em=min(cadencia.normal_em,agora)
                if verificador.observar(pos,agora,not progresso.dano and math.dist(pos,target['position'])>3):pulso(p['unstuck_key']);log('Sem deslocamento; tecla de recuperacao enviada.')
                tecla=cadencia.escolher(agora,True,progresso.dano and agora-progresso.ultimo_dano<2.5,target['hp']/target['hp_max'],em_alcance=math.dist(pos,target['position'])<=2.4,recargas_reais=cc.get('recargas_atalhos'))
                if tecla=='1' and cc.get('normal_ready') is False:tecla=None
                item=False
                if agora>=cadencia.livre_em:
                    for v in p['items']:
                        if v['enabled'] and agora>=item_em.get(v['key'],0):
                            if pulso(v['key']):item_em[v['key']]=agora+v['seconds'];cadencia.registrar('8',agora);cancelamento.acao(False,agora,agora+1.4);item=True
                            break
                real=cc.get('recargas_atalhos',{}).get(tecla)
                skill_id=cc.get('normal_skill') if tecla=='1' else (real or {}).get('skill')
                timing=perfil_combo(tecla,tecla=='1',skill_id)
                combo=bool(tecla and not item and timing and cancelamento.permitir_combo(target,pos,progresso.id,progresso.dano))
                if cc.get('tipos_atalhos',{}).get(tecla,2)!=2:combo=False
                enviada=False
                inicio_envio=time.monotonic()
                if tecla and not item:
                    atalho=p['attack_key'] if tecla=='1' else tecla
                    if combo:enviada,combo=executar_combo(segurar,liberar,esperar,ativo,atalho,tecla=='1',skill_id=skill_id)
                    else:enviada=pulso(atalho,duracao_tecla(skill_id))
                if enviada:
                    real=cc.get('recargas_atalhos',{}).get(tecla)
                    event_sink(dict(event='action',key=p['attack_key'] if tecla=='1' else tecla,kind='normal' if tecla=='1' else 'skill',target_id=target['id'],normal_cooldown=cc.get('normal_cooldown'),skill_state=real,combo_w=timing['ordem'] if combo else None,combo_timing=timing if combo else None))
                    cadencia.registrar(tecla,inicio_envio if combo and tecla=='1' else time.monotonic(),intervalo_normal=.17 if combo and tecla=='1' else None)
                    if tecla=='1':vigia_ataque.enviado()
                    cancelamento.acao(tecla=='1',time.monotonic(),cadencia.livre_em)
                    if tecla!='1':log('Tecla de habilidade enviada.',tecla=tecla,intervalo=cadencia.recargas[tecla],recarga_real=real)
                esperar(.015);continue
            # Retorno sem cone de camera: deriva orientacao do deslocamento real.
            if math.dist(pos,base)<=3:
                soltar();log('Retornou a base.');trilha=[base];estado='buscar';progresso=None;heading=None;origem_mov=None;retorno_busca=False;regional.reiniciar_busca(agora);verificador.observar(None,agora,False);continue
            if player.get('heading') is not None and hasattr(dados,'cena_validada'):
                seguir_grade(base,('base',base),2.)
                esperar(.015);continue
            while len(volta)>1 and math.dist(pos,volta[0])<2:volta.pop(0)
            destino=volta[0] if volta else base
            if origem_mov is not None:
                dx,dy=pos[0]-origem_mov[0],pos[1]-origem_mov[1]
                if math.hypot(dx,dy)>=1.5:heading=math.degrees(math.atan2(dx,dy))%360;origem_mov=pos
            if heading is None:
                antes=pos;pulso('w',.16);depois=dados.snapshot()['player']['position'];dx,dy=depois[0]-antes[0],depois[1]-antes[1]
                if math.hypot(dx,dy)>.5:heading=math.degrees(math.atan2(dx,dy))%360
                else:pulso('d',.2)
                continue
            dx,dy=destino[0]-pos[0],destino[1]-pos[1];erro=erro_angular(math.degrees(math.atan2(dx,dy))%360,heading)
            if abs(erro)<=28:
                segurar('w')
                if origem_mov is None:origem_mov=pos
            else:liberar('w');origem_mov=None
            if abs(erro)>12:
                tempo=min(.45,max(.025,abs(erro)/107.85*.7))
                if pulso('d' if erro>0 else 'a',tempo):heading=(heading+(1 if erro>0 else -1)*tempo*107.85)%360
                origem_mov=None
            if verificador.observar(pos,agora,'w' in seg):soltar();pulso(p['unstuck_key']);pulso('d',.25);heading=(heading+27)%360
            esperar(.015)
    finally:
        fim.set();soltar()
        if dados:dados.close()
        event_sink(dict(event='finished',message='Caca encerrada; teclas liberadas.',reason='F12' if keyboard.is_pressed('f12') else getattr(control,'reason','controle_de_parada')))
