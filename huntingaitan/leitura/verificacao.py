"""Verifica quais leituras do cliente continuam validas, para revalidar o layout apos uma atualizacao do jogo."""

def _resumo(valor,limite=120):
    texto=repr(valor)
    return texto if len(texto)<=limite else texto[:limite-3]+'...'

def verificar(dados):
    """Roda cada leitura do leitor e devolve [{nome,ok,critica,detalhe}].

    As leituras criticas (jogador/alvo e cena) bloqueiam a caca; as demais degradam
    recursos especificos, como cura por recarga real ou selecao regional."""
    resultados=[]
    def sonda(nome,critica,leitura):
        try:valor=leitura()
        except Exception as erro:
            resultados.append(dict(nome=nome,ok=False,critica=critica,detalhe=f'{type(erro).__name__}: {erro}'))
            return None
        resultados.append(dict(nome=nome,ok=True,critica=critica,detalhe=_resumo(valor)))
        return valor
    instantaneo=sonda('jogador e alvo',True,dados.snapshot)
    sonda('cena ativa',True,dados.cena_validada)
    sonda('estados de controle',False,dados.estados_controle)
    sonda('recargas dos atalhos',False,dados.recargas_atalhos)
    sonda('camera',False,dados.camera_regional)
    if instantaneo:
        jogador=instantaneo['player']
        sonda('lista de mobs',False,lambda:dados.listar_mobs(jogador['position'],60,jogador))
    sonda('caca original',False,dados.caca_original_ativa)
    return resultados

def aprovado(resultados):
    return all(r['ok'] for r in resultados if r['critica'])
