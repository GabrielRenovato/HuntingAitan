"""Interacao visual com reparo confirmado pelo saldo e vendas verificadas."""
import math,time,re
from pathlib import Path
from huntingaitan.leitura.inventario import ler_inventario,equipamento_candidato,nome_item,precisa_reparar
from huntingaitan.rotas.servico_npc import NPC,TransacaoNPC,normalizar,durabilidade,nome_corresponde

def reparar_e_vender(dados,control,emitir,limite=360):
    import keyboard,mss,pydirectinput as entrada
    from huntingaitan.visao.captura_aika import CapturaAika
    from huntingaitan.rotas.interface_npc import InterfaceNPC
    from huntingaitan.entrada.entrada_segura import mover_cursor_fisico,liberar_tecla
    from huntingaitan.visao.avisos_hunt import DetectorAvisos,reconfirmar
    fase='inicio';ultima_imagem=None;ultima_verificacao=-10
    ui=InterfaceNPC();avisos=DetectorAvisos();tx=TransacaoNPC();prazo=time.monotonic()+limite;entrada.PAUSE=0
    def ativo():return not control.stop.is_set() and not keyboard.is_pressed('f12') and not control.pause.is_set() and dados.u.GetForegroundWindow()==dados.hwnd
    def log(m,**kw):emitir(dict(event='log',message=m,**kw))
    with mss.MSS() as sct:
        cap=CapturaAika(sct)
        def tela(forcar_avisos=False):
            nonlocal prazo,ultima_imagem,ultima_verificacao
            while True:
                while not ativo():
                    if control.stop.is_set() or keyboard.is_pressed('f12'):raise InterruptedError('Operacao interrompida')
                    time.sleep(.1);prazo+=.1
                if time.monotonic()>prazo:raise TimeoutError('Servico do NPC excedeu o prazo sem confirmacao')
                p=dados.snapshot()['player']
                if p['hp']<=0:raise RuntimeError('Personagem sem vida durante servico do NPC')
                if math.dist(p['position'],NPC)>10:raise RuntimeError('Personagem saiu do alcance do Luis Mandez')
                im=cap.capturar();ultima_imagem=im
                agora=time.monotonic();aviso=None
                if forcar_avisos or agora-ultima_verificacao>=2.5:
                    aviso=avisos.localizar(im);ultima_verificacao=time.monotonic()
                if aviso and aviso['tipo'] in ('cte_elter','arena_elter','conversa_amigo'):
                    ponto=reconfirmar(aviso)
                    if ponto and ativo() and mover_cursor_fisico(entrada,*ponto):
                        entrada.mouseDown()
                        try:time.sleep(.06)
                        finally:entrada.mouseUp()
                        log('Janela que interrompia o servico fechada.',tipo=aviso['tipo'])
                    time.sleep(.15);continue
                return im
        def mover(p):
            if not ativo():raise RuntimeError('Aika perdeu o foco antes do movimento do cursor')
            if not mover_cursor_fisico(entrada,cap.area['left']+p[0],cap.area['top']+p[1]):
                raise RuntimeError('Windows nao confirmou a posicao fisica do cursor')
            return True
        def clicar(p,botao='left',duplo=False):
            if not mover(p):return False
            time.sleep(.04)
            for _ in range(2 if duplo else 1):
                if not ativo():raise RuntimeError('Aika perdeu o foco antes do clique')
                entrada.mouseDown(button=botao)
                try:time.sleep(.06)
                finally:entrada.mouseUp(button=botao)
                time.sleep(.07)
            return True
        def buscar(fn,segundos=12):
            fim=time.monotonic()+segundos
            while time.monotonic()<fim:
                im=tela();r=fn(im)
                if r:return r
                time.sleep(.1)
            return None
        def abrir_menu(opcao):
            im=tela();p=ui.menu(im,opcao,False)
            if not p:
                p=ui.npc(im)
                if not p:raise RuntimeError('Luis Mandez nao reconhecido na tela')
                if not clicar(p,duplo=True):return False
                p=buscar(lambda t:ui.menu(t,opcao))
            if not p:raise RuntimeError('Opcao do NPC nao reconhecida: '+opcao)
            # Nova imagem confirma que a opcao ainda existe antes de clicar.
            atual=ui.menu(tela(),opcao)
            if not atual or math.dist(atual,p)>5:raise RuntimeError('Menu do NPC mudou antes do clique')
            return clicar(atual)
        def loja():
            atual=ui.loja(tela(),False)
            if atual:return atual
            if not abrir_menu('loja'):raise RuntimeError('Nao foi possivel abrir a Tienda')
            atual=buscar(lambda t:ui.loja(t,False))
            if not atual:raise RuntimeError('Tienda e saldo do inventario nao confirmados')
            return atual
        try:
            emitir(dict(event='cycle',state='jardim_npc_reparar',message='Conferindo saldo e reparando tudo no Luis Mandez.'))
            pendente=ui.dialogo(tela(),'venda')
            if pendente:
                clicar(pendente['cancelar'])
                log('Pergunta de venda anterior cancelada; conferindo novamente a mochila.')
            fase='abrir_reparo';estado_inicial=ler_inventario(dados);saldo=estado_inicial['ouro']
            if not precisa_reparar(dados,estado_inicial):
                tx.preparar_reparo(saldo,0);tx.confirmar_reparo(saldo,True)
                log('Equipamentos ja reparados; seguindo direto para a Tienda.')
            else:
                # Se a loja ja estava aberta, fecha uma vez para acessar Reparar Todo.
                aberta=ui.loja(tela(),False)
                if aberta:
                    clicar(aberta['fechar']);time.sleep(.2)
                if not abrir_menu('reparar'):return False
                reparo=buscar(lambda t:ui.dialogo(t,'reparo'))
                if not reparo:raise RuntimeError('Pergunta e custo do reparo nao reconhecidos')
                if not tx.preparar_reparo(saldo,reparo['custo']):
                    clicar(reparo['cancelar']);raise RuntimeError('Saldo insuficiente ou custo de reparo invalido')
                atual=ui.dialogo(tela(),'reparo')
                if not atual or atual['custo']!=reparo['custo']:raise RuntimeError('Custo do reparo mudou antes da confirmacao')
                if not clicar(atual['confirmar']):return False
                fase='confirmar_reparo';time.sleep(.3)
                def reparo_concluido(im):
                    l=ler_inventario(dados)
                    return l if tx.confirmar_reparo(l['ouro'],ui.dialogo(im,'reparo') is None) else None
                apos=buscar(reparo_concluido,6)
                if not apos:raise RuntimeError('Reparo nao confirmado pelo custo e pela alteracao do saldo; venda bloqueada')
                log('Reparar Todo confirmado pelo saldo.',custo=tx.custo,saldo=apos['ouro'])
            emitir(dict(event='cycle',state='jardim_npc_vender',message='Vendendo equipamentos identificados da mochila.'))
            fase='abrir_loja';atual=loja();inventario=ler_inventario(dados)
            bolsas=inventario['bolsas']
            ui.nomes_inventario=tuple({nome_item(dados,i) for i in inventario['itens'] if equipamento_candidato(dados,i)})
            nao_confirmados=[]
            if len(atual['paginas'])!=len(bolsas):raise RuntimeError('Icones de bolsas nao correspondem as bolsas internas')
            for pagina,bolsa in enumerate(bolsas):
                fase='bolsa_'+str(bolsa)
                clicar(atual['paginas'][pagina]);time.sleep(.2)
                log('Bolsa selecionada.',bolsa=bolsa)
                for indice,p in enumerate(atual['slots']):
                    estado=ler_inventario(dados);slot=bolsa*20+indice
                    item_nativo=estado['itens'][slot]
                    if not equipamento_candidato(dados,item_nativo):continue
                    fase='equipamento_'+str(slot);inicio_item=time.monotonic()
                    tela()
                    if not mover(p):return False
                    time.sleep(.3)
                    esperado=nome_item(dados,item_nativo)
                    imagem_item=tela()
                    # Abrir a pergunta e reversivel. A leitura da captura pode
                    # acontecer com a pergunta aberta; Enter continua bloqueado.
                    antes=ler_inventario(dados)
                    if antes['itens'][slot]!=item_nativo:raise RuntimeError('Item mudou antes de abrir a venda')
                    if not clicar(p,'right'):return False
                    ate_clique=time.monotonic()-inicio_item
                    log('Janela de venda solicitada.',item=esperado,slot=slot,ate_clique_segundos=round(ate_clique,3))
                    venda=buscar(lambda t:ui.dialogo(t,'venda'),4)
                    if not venda:raise RuntimeError('Confirmacao de venda nao reconhecida; nenhum item foi confirmado')
                    inicio_leitura=time.monotonic()
                    item=ui.equipamento_sob_cursor(imagem_item,p,atual['escala'],esperado)
                    if not item and getattr(ui,'motivo_descricao','leitura')=='leitura':
                        if ler_inventario(dados)['itens'][slot]!=item_nativo:raise RuntimeError('Item mudou durante a releitura')
                        item=ui.equipamento_sob_cursor(imagem_item,p,atual['escala'],esperado,True)
                    if not item:
                        clicar(venda['cancelar'])
                        motivo=getattr(ui,'motivo_descricao','leitura')
                        if motivo=='leitura':
                            nao_confirmados.append(esperado)
                            try:
                                import cv2,os
                                destino=Path(os.environ.get('APPDATA',str(Path.home())))/'aika-caca-automatica'/'app_sessions'
                                destino.mkdir(parents=True,exist_ok=True)
                                cv2.imwrite(str(destino/('item_npc_'+time.strftime('%Y%m%d_%H%M%S')+'_'+str(slot)+'.png')),imagem_item)
                            except OSError:pass
                        log('Item mantido: descricao nao confirmada.',item=esperado,slot=slot,motivo=motivo)
                        continue
                    leitura_segundos=time.monotonic()-inicio_leitura
                    nome,descricao=item
                    dur=durabilidade(descricao)
                    if normalizar(nome)!=normalizar(esperado) or dur!=(item_nativo['atual'],item_nativo['maxima']):
                        raise RuntimeError(f'Bolsa/slot visual divergiu do inventario interno: nome={nome!r}, esperado={esperado!r}, durabilidade={dur}, interna={(item_nativo["atual"],item_nativo["maxima"])}')
                    if ler_inventario(dados)['itens'][slot]!=item_nativo:raise RuntimeError('Item mudou durante a leitura da descricao')
                    if not nome_corresponde(venda['nome'],esperado,ui.nomes_inventario):
                        clicar(venda['cancelar']);nao_confirmados.append(esperado);log('Item mantido: nome da venda divergiu da descricao.',item=venda['nome'],esperado=esperado);continue
                    ok,motivo=tx.preparar_venda(esperado,venda['preco'],descricao,antes['ouro'])
                    if not ok:
                        clicar(venda['cancelar']);log('Item mantido.',item=venda['nome'],motivo=motivo);continue
                    # Confere a mesma janela por pixels, sem repetir OCR por item.
                    conferencia=tela(True)
                    if not ui.confirmacao_estavel(conferencia,venda):
                        confirmar=ui.dialogo(conferencia,'venda')
                        if not confirmar or confirmar['preco']!=venda['preco'] or not nome_corresponde(confirmar['nome'],esperado,ui.nomes_inventario):
                            raise RuntimeError('Venda mudou antes de confirmar')
                    estado=ler_inventario(dados)
                    if estado['itens'][slot]!=item_nativo or estado['ouro']!=antes['ouro']:raise RuntimeError('Item ou saldo mudou antes de confirmar')
                    if not ativo():raise RuntimeError('Aika perdeu foco antes de confirmar')
                    entrada.keyDown('enter')
                    try:time.sleep(.035)
                    finally:liberar_tecla(entrada,'enter')
                    depois=None;fim=time.monotonic()+6;ultima_tela=time.monotonic()
                    while time.monotonic()<fim:
                        if control.stop.is_set() or keyboard.is_pressed('f12'):raise InterruptedError('Operacao interrompida')
                        if not ativo():tela()
                        estado=ler_inventario(dados)
                        removido=not any(i['id']==item_nativo['id'] and i['serial']==item_nativo['serial'] for i in estado['itens'])
                        if removido and estado['ouro']==tx.ouro_antes+tx.preco:
                            depois=estado;break
                        if time.monotonic()-ultima_tela>=.5:tela();ultima_tela=time.monotonic()
                        time.sleep(.04)
                    if not depois or not tx.confirmar_venda(depois['ouro'],True):raise RuntimeError('Venda nao confirmada pelo saldo e pela remocao do item')
                    log('Equipamento vendido e transacao conferida.',item=venda['nome'],preco=venda['preco'],vendidos=tx.vendidos,pagina=pagina+1,slot=indice,segundos=round(time.monotonic()-inicio_item,3),ate_clique_segundos=round(ate_clique,3),leitura_segundos=round(leitura_segundos,3))
            if nao_confirmados:
                raise RuntimeError('Equipamentos ainda sem identificacao confirmada: '+', '.join(nao_confirmados))
            if not clicar(atual['fechar']):return False
            emitir(dict(event='cycle',state='jardim_npc_concluido',message='Servico do Luis Mandez concluido.',vendidos=tx.vendidos))
            return True
        except (RuntimeError,ValueError,OSError,TimeoutError,InterruptedError) as e:
            log('Servico do NPC nao confirmado; aguardando intervencao sem novas vendas.',detail=str(e),fase=fase,vendidos=tx.vendidos)
            try:
                import cv2,os
                destino=Path(os.environ.get('APPDATA',str(Path.home())))/'aika-caca-automatica'/'app_sessions'
                destino.mkdir(parents=True,exist_ok=True)
                if ultima_imagem is not None:cv2.imwrite(str(destino/('falha_npc_'+time.strftime('%Y%m%d_%H%M%S')+'.png')),ultima_imagem)
            except OSError:pass
            if not control.stop.is_set():control.reason='servico_npc_nao_confirmado'
            return False
