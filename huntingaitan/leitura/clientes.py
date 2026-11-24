"""Lista personagens por processo, sem selecionar alvos nem enviar comandos ao jogo."""
from pathlib import PureWindowsPath
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos


def listar_clientes():
    resultado=[]
    for janela in enumerar_clientes():
        item=dict(pid=janela['pid'],hwnd=janela['hwnd'],exe=PureWindowsPath(janela['caminho']).name,name=None,ready=False,error=None)
        leitor=None
        try:
            leitor=DadosInternos(janela=janela)
            player=leitor.snapshot()['player']
            item.update(name=player['name'],position=player['position'],ready=True)
        except (RuntimeError,OSError,ValueError) as erro:item['error']=str(erro)
        finally:
            if leitor:leitor.close()
        resultado.append(item)
    return resultado
