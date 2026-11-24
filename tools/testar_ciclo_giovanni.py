"""Teste de uma renovacao real na templaria. F12 ou arquivo PARAR encerram.

Usa navegacao interna ja validada e a interface existente para compra e itens;
nao chama a rotina interna candidata de uso de itens. Nao inicia a caca ao terminar.
"""
import ctypes,json,math,os,sys,time
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
import cv2,mss,keyboard,pydirectinput as entrada
from huntingaitan.leitura.escolha_cliente import abrir_leitor
from huntingaitan.leitura.inventario import ler_inventario
from huntingaitan.leitura.skills_cliente import ler_slots
from huntingaitan.leitura.recargas_barra import atalhos_slots
from huntingaitan.entrada.layout_teclado import caractere_do_vk
from huntingaitan.entrada.entrada_motor import EntradaMotor
from huntingaitan.entrada.entrada_segura import mover_cursor_fisico,liberar_tecla,liberar_mouse
from huntingaitan.rotas.navegador_local import NavegadorLocal
from huntingaitan.rotas.navegacao_grade import ler_grade
from huntingaitan.rotas.interface_npc import InterfaceNPC
from huntingaitan.rotas.servico_npc import normalizar
from huntingaitan.rotas.renovacao_giovanni import NPC,CIDADE,TERMES,CompraGiovanni,pode_usar_cidade,zona_cidade,opcao_gratuita
from huntingaitan.visao.captura_janela import CapturaJanela

dest=raiz/'build'/('teste_ciclo_giovanni_'+time.strftime('%Y%m%d_%H%M%S'));dest.mkdir()
(raiz/'build/ultimo_teste_giovanni.txt').write_text(str(dest),encoding='utf-8')
r=dict(ok=False,fase='preflight',compras_enviadas=0,opcao='Bendicion de Giovanni',custo_permitido=0);d=None;motor=None;cap=None;imagem=None
u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
u.SetForegroundWindow.argtypes=[w.HWND];u.ShowWindow.argtypes=[w.HWND,ctypes.c_int]
entrada.PAUSE=0
prazo=time.monotonic()+420

def salvar(): (dest/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
def log(msg,**kw):
    with (dest/'eventos.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(t=time.time(),message=msg,**kw),ensure_ascii=False)+'\n')
    r['ultima_mensagem']=msg;salvar()
def conferir():
    if keyboard.is_pressed('f12') or (dest/'PARAR').exists():raise InterruptedError('Teste interrompido')
    if time.monotonic()>prazo:raise TimeoutError('Prazo do teste encerrado')
    p=d.snapshot()['player']
    if p['hp']<=0 or p['hp']/p['hp_max']<.6:raise RuntimeError('Vida insuficiente; comandos interrompidos')
    return p
def tecla(k):
    conferir();motor.keyDown(k)
    try:time.sleep(.12)
    finally:motor.keyUp(k)
    time.sleep(.25)
def tela():
    global imagem
    conferir();imagem=cap.capturar();return imagem
def clique(p,botao='left',duplo=False):
    conferir()
    if u.GetForegroundWindow()!=d.hwnd:raise RuntimeError('Clique fisico requer Aika em primeiro plano')
    if not mover_cursor_fisico(entrada,cap.area['left']+p[0],cap.area['top']+p[1]):raise RuntimeError('Cursor nao chegou ao controle')
    time.sleep(.1)
    for _ in range(2 if duplo else 1):
        conferir();entrada.mouseDown(button=botao)
        try:time.sleep(.12)
        finally:liberar_mouse_botao(botao)
        time.sleep(.15)
def liberar_mouse_botao(botao):
    func=getattr(entrada.mouseUp,'__wrapped__',entrada.mouseUp);func(button=botao)
def aguardar_pos(alvo,raio,segundos):
    fim=time.monotonic()+segundos;estavel=None
    while time.monotonic()<fim:
        if keyboard.is_pressed('f12') or (dest/'PARAR').exists():raise InterruptedError('Teste interrompido')
        try:
            p=conferir()
            if math.dist(p['position'],alvo)<=raio:
                # Posicao muda antes da origem/tabelas da nova cena. Exigir a
                # grade correspondente e algumas leituras estaveis apos o load.
                ler_grade(d,p['position'])
                if estavel is None:estavel=time.monotonic()
                if time.monotonic()-estavel>=2:return p
            else:estavel=None
        except RuntimeError as e:
            estavel=None
            if not any(x in str(e).lower() for x in ('cena','carregado','grade','tabela','mapa')):raise
        time.sleep(.15)
    raise RuntimeError('Destino do pergaminho nao confirmado; nao repetido')
def caminhar(alvo,alcance=3):
    nav=NavegadorLocal();fim=time.monotonic()+130;ultimo=-100
    while time.monotonic()<fim:
        p=conferir();pos=p['position'];agora=time.monotonic()
        if math.dist(pos,alvo)<=alcance:motor.parar_movimento();return
        cc=d.estados_controle()
        if any(cc.get(k) for k in ('casting','stunned','paralyzed','frozen')):
            motor.parar_movimento();nav.suspender(pos,agora);time.sleep(.1);continue
        op=dict(alcance=alcance,parcial=True,controle_interno=True)
        plano=nav.planejar(d,pos,p.get('heading'),alvo,('giovanni',alvo),agora,**op)
        if plano.get('passagem_bloqueada'):plano=nav.replanejar_agora(d,pos,p.get('heading'),alvo,('giovanni',alvo),agora,plano,**op)
        if plano['estado']=='andando':motor.mover_para(plano['ponto'],agora,forcar=bool(plano.get('replanejado_imediato')))
        else:motor.parar_movimento()
        if agora-ultimo>=2:log('Navegacao do teste',pos=pos,destino=alvo,estado=plano['estado']);ultimo=agora
        time.sleep(.08)
    raise RuntimeError('Caminho nao concluido; teste encerrado sem compra')

try:
    perfil=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    d=abrir_leitor(perfil['client_pid']);p=d.snapshot()['player'];r.update(nome=p['name'],inicio=p['position'])
    os.environ['AIKA_CLIENT_PID']=str(d.pid);os.environ['AIKA_CLIENT_HWND']=str(d.hwnd)
    if p['name']!='Domination':raise RuntimeError('Personagem diferente da templaria esperada')
    if d.caca_original_ativa():raise RuntimeError('Caca original ativa; teste recusado')
    # O mutex da ponte impede disputar com uma sessao Hunting ativa.
    motor=EntradaMotor(d.hwnd,d.pid);motor.conectar(d)
    inv=ler_inventario(d);tx=CompraGiovanni(inv['ouro'],d.estados_controle()['active_skill_ids'],custo=0)
    if inv['itens'][20]['id']!=4521:raise RuntimeError('Pergaminho de retorno nao esta no slot 1 da segunda bolsa')
    u.ShowWindow(d.hwnd,9);u.SetForegroundWindow(d.hwnd);time.sleep(.6);conferir()
    with CapturaJanela(d.hwnd,d.pid) as captura:
        cap=captura;ui=InterfaceNPC()
        if not zona_cidade(p['position']):
            r['fase']='retirada';log('Procurando local livre antes de F5')
            p=conferir();mobs=d.listar_mobs(p['position'],70,p)
            if not pode_usar_cidade(p,mobs,d.estados_controle()):
                g=ler_grade(d,p['position']);candidatos=[]
                for raio in (12,22,32):
                    for ang in range(0,360,30):
                        q=(p['position'][0]+raio*math.cos(math.radians(ang)),p['position'][1]+raio*math.sin(math.radians(ang)))
                        if any(math.dist(q,m['position'])<40 for m in mobs):continue
                        caminho=g.caminho(p['position'],q)
                        if caminho and all(all(math.dist(a,m['position'])>=10 for m in mobs) for a in caminho[1:]):
                            candidatos.append((len(caminho),q))
                if not candidatos:raise RuntimeError('Nenhum ponto seguro alcancavel foi confirmado; F5 nao enviado')
                caminhar(min(candidatos)[1],1.5)
            motor.parar_movimento()
            for _ in range(6):
                p=conferir()
                if not pode_usar_cidade(p,d.listar_mobs(p['position'],70,p),d.estados_controle()):raise RuntimeError('Area nao permaneceu segura; F5 nao enviado')
                time.sleep(.25)
            gestor=d.u32(d.base+d.cfg('bar_manager_rva'))
            mapa=atalhos_slots(d.read(gestor+0x430,468),lambda vk:caractere_do_vk(d.u,d.hwnd,vk))
            slots=ler_slots(d);f5=[slots[i] for i,k in mapa.items() if k=='f5']
            if len(f5)!=1 or f5[0]&15!=6 or (f5[0]>>4)&0x1ffff!=15521:raise RuntimeError('F5 nao corresponde ao pergaminho de cidade')
            r['fase']='pergaminho_cidade';log('F5 enviado uma vez em area livre');tecla('f5');aguardar_pos(CIDADE,20,35)
        else:
            log('Ja em Regenshein: etapa F5 nao foi exercitada neste teste')
            aguardar_pos(CIDADE,260,15)
        r['fase']='caminho_npc';caminhar(NPC,3.5)
        motor.orientar_para(NPC)
        r['fase']='menu_npc';log('No alcance do NPC; procurando Lilola Hawn')
        linhas=ui.ler(tela())
        if not any(opcao_gratuita(x['texto']) for x in linhas):
            nome=next((x for x in linhas if x['nome']=='lilolahawn'),None)
            if not nome:raise RuntimeError('Nome Lilola Hawn nao apareceu na tela; nenhum clique no NPC')
            x0,y0,x1,y1=nome['caixa'];clique((nome['ponto'][0],round(y1+3*max(6,y1-y0))),duplo=True)
            time.sleep(.5);linhas=ui.ler(tela())
        opcao=next((x for x in linhas if opcao_gratuita(x['texto'])),None)
        if not opcao:
            r['textos_menu']=[x['texto'] for x in linhas];raise RuntimeError('Bencao gratuita nao reconhecida; opcao de 50000 proibida neste teste')
        inv=ler_inventario(d);tx=CompraGiovanni(inv['ouro'],d.estados_controle()['active_skill_ids'],custo=0)
        # O menu pode se reposicionar durante o OCR. Reencontrar exatamente o
        # texto gratuito ja conferido, na imagem atual, antes de clicar.
        x0,y0,x1,y1=map(round,opcao['caixa'])
        modelo=cv2.cvtColor(imagem[max(0,y0-2):y1+2,max(0,x0-2):x1+2],cv2.COLOR_BGR2GRAY)
        atual=cv2.cvtColor(tela(),cv2.COLOR_BGR2GRAY)
        if not modelo.size:raise RuntimeError('Texto gratuito sem recorte valido')
        _,score,_,xy=cv2.minMaxLoc(cv2.matchTemplate(atual,modelo,cv2.TM_CCOEFF_NORMED))
        if score<.95:raise RuntimeError('Opcao gratuita mudou antes do clique; nenhuma compra')
        ponto_atual=(xy[0]+modelo.shape[1]//2,xy[1]+modelo.shape[0]//2)
        r['fase']='bencao_gratuita';r['compras_enviadas']=1
        log('Bencao normal gratuita solicitada',ouro_antes=inv['ouro'],ponto_ocr=opcao['ponto'],ponto_atual=ponto_atual,score=score)
        # Prova isolada do clique por mensagens na janela, destinada ao mesmo
        # HWND da leitura. Aceitacao da mensagem nao confirma a bencao.
        if not motor.moveTo(cap.area['left']+ponto_atual[0],cap.area['top']+ponto_atual[1]):raise RuntimeError('Janela nao aceitou posicao do botao')
        motor.mouseDown(button='left')
        try:time.sleep(.15)
        finally:motor.mouseUp(button='left')
        fim=time.monotonic()+12;efeito=None
        while time.monotonic()<fim:
            conferir();inv=ler_inventario(d);ativos=d.estados_controle()['active_skill_ids']
            r.update(ouro_depois=inv['ouro'],efeitos_depois=ativos);salvar()
            efeito=tx.conferir(inv['ouro'],ativos)
            if efeito:break
            time.sleep(.2)
        if not efeito:raise RuntimeError('Saldo e efeito nao confirmaram compra; nao vou comprar novamente nem usar retorno')
        r['efeito_confirmado']=efeito;log('Compra confirmada pelo saldo e efeito',efeito=efeito,ouro=inv['ouro'])
        r['fase']='inventario_retorno';im=tela();inv_ui=ui.achar_npc(im,'npc_inventario',limiar=.91)
        if not inv_ui:
            tecla('b');im=tela();inv_ui=ui.achar_npc(im,'npc_inventario',limiar=.91)
        if not inv_ui:raise RuntimeError('Inventario nao reconhecido; retorno nao usado')
        x,y=inv_ui['ponto'];s=inv_ui['escala'];ponto=(round(x-124*s),round(y+70*s))
        # Identifica o item visivel pela descricao antes de qualquer uso.
        if not motor.moveTo(cap.area['left']+ponto[0],cap.area['top']+ponto[1]):raise RuntimeError('Janela nao aceitou posicao do pergaminho')
        time.sleep(.7);textos=ui.ler(tela());nomes={t['nome'] for t in textos}
        if not any('pergaminoderetorno' in n or n=='returnscroll' for n in nomes):raise RuntimeError('Descricao do retorno nao confirmada; confira a segunda bolsa')
        if ler_inventario(d)['itens'][20]['id']!=4521:raise RuntimeError('Item do retorno mudou antes do uso')
        log('Pergaminho do ponto salvo enviado uma vez')
        motor.mouseDown(button='right')
        try:time.sleep(.15)
        finally:motor.mouseUp(button='right')
        final=aguardar_pos(TERMES,20,35);r.update(ok=True,fase='concluido',final=final['position']);log('Chegada a Termes confirmada; caca permanece parada',pos=final['position'])
except Exception as e:
    r.update(ok=False,erro=str(e));log('Teste interrompido',erro=str(e))
    if cap is not None:
        try:imagem=cap.capturar()
        except Exception:pass
    if imagem is not None:cv2.imwrite(str(dest/'ultima_tela.png'),imagem)
finally:
    if motor:
        try:motor.finalizar();r['ponte_removida']=True
        except Exception as e:r['erro_remocao']=str(e)
    if d:d.close()
    salvar()
