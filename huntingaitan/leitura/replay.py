"""Executa o motor sobre uma sessao gravada, com relogio, teclado e janela simulados.

Serve para comparar o comportamento do motor entre duas versoes do codigo: rode a mesma
gravacao nas duas e compare os tracos com comparar(). A navegacao por grade depende dos
arquivos do jogo e nao e reproduzida; o foco esta nas decisoes de combate, cura e buffs."""
import copy,sys,threading
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from huntingaitan.leitura.sessao import DadosReplay,ler_registros

def reproduzir(registros,perfil=None,limite_segundos=120.):
    """Devolve dict(eventos,teclas,duracao,erro,restantes). Aceita lista de registros ou caminho do JSONL."""
    import huntingaitan.combate.hunt_native as h
    from huntingaitan.configuracao.perfil_hunt import DEFAULT
    if not isinstance(registros,list):registros=ler_registros(registros)
    # patch.dict(sys.modules) descarta o que for importado dentro dele e as extensoes nativas
    # nao recarregam; importa antes, como o proprio motor faz ao iniciar.
    from huntingaitan.visao.controle_avisos import preparar_runtime_visual
    preparar_runtime_visual()
    p=copy.deepcopy(perfil or DEFAULT);p.update(minimize_on_start=False)
    controle=SimpleNamespace(stop=threading.Event(),pause=threading.Event())
    tempo=[0.];eventos=[];teclas=[]
    dados=DadosReplay(registros,ao_acabar=controle.stop.set)
    def dormir(segundos):
        tempo[0]+=max(.001,segundos)
        if tempo[0]>limite_segundos:controle.stop.set()
    def registrar(tipo):return lambda k:teclas.append((round(tempo[0],3),tipo,k))
    nada=lambda *a,**k:None
    entrada=SimpleNamespace(PAUSE=0,keyDown=registrar('down'),keyUp=registrar('up'),press=registrar('press'),
                            moveTo=nada,mouseDown=nada,mouseUp=nada,click=nada,doubleClick=nada)
    janela=MagicMock();janela.GetForegroundWindow.return_value=1;janela.GetWindowTextW.side_effect=lambda hwnd,buf,n:setattr(buf,'value','AikaClient')
    erro=None
    with patch.dict(sys.modules,keyboard=SimpleNamespace(is_pressed=lambda k:False),pydirectinput=entrada),\
         patch.object(h,'DadosInternos',lambda:dados),patch.object(h.ctypes.windll,'user32',janela),\
         patch.object(h.threading,'Thread'),patch.object(h.time,'monotonic',lambda:tempo[0]),patch.object(h.time,'sleep',dormir):
        try:h.main(p,eventos.append,controle)
        except Exception as e:erro=f'{type(e).__name__}: {e}'
    return dict(eventos=eventos,teclas=teclas,duracao=round(tempo[0],3),erro=erro,restantes=dados.restantes())

def comparar(a,b):
    """Descreve a primeira divergencia entre dois tracos de reproduzir(), ou None se iguais."""
    for campo in ('teclas','eventos'):
        x,y=a[campo],b[campo]
        for i,(u,v) in enumerate(zip(x,y)):
            if u!=v:return f'{campo}[{i}] difere: {u!r} != {v!r}'
        if len(x)!=len(y):return f'{campo} tem {len(x)} itens contra {len(y)}'
    if a.get('erro')!=b.get('erro'):return f"erro difere: {a.get('erro')!r} != {b.get('erro')!r}"
    return None
