"""Escolha do cliente Aika nas ferramentas de linha de comando quando ha mais de um aberto."""
from pathlib import PureWindowsPath

def descrever(cliente):
    return f"PID {cliente['pid']} ({PureWindowsPath(cliente['caminho']).name})"

def escolher_cliente(clientes,pid=0):
    """Devolve o cliente pedido por PID, o unico aberto, ou explica como escolher."""
    if pid:
        achado=next((c for c in clientes if c['pid']==pid),None)
        if achado:return achado
        abertos=', '.join(descrever(c) for c in clientes) or 'nenhum'
        raise RuntimeError(f'Nenhum cliente com PID {pid}. Abertos: {abertos}.')
    if not clientes:raise RuntimeError('Nenhum cliente Aika compativel aberto. Abra o jogo e entre no mapa.')
    if len(clientes)==1:return clientes[0]
    raise RuntimeError('Mais de um cliente aberto: '+'; '.join(descrever(c) for c in clientes)+'. Rode de novo com --pid <numero>.')

def abrir_leitor(pid=0):
    from huntingaitan.leitura.dados_internos import DadosInternos
    from huntingaitan.leitura.janela_cliente import enumerar_clientes
    return DadosInternos(janela=escolher_cliente(enumerar_clientes(),pid))
