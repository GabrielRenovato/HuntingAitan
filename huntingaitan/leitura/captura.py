"""Captura somente leitura de objetos conhecidos do cliente, para descobrir campos de estado.

Uso tipico: capture varias vezes um estado (ex.: dialogo fechado) e varias vezes outro (dialogo
aberto); candidatos() devolve as palavras de 4 bytes que sao estaveis dentro de cada grupo e
diferentes entre os grupos. O ruido (posicao, timers) varia dentro do grupo e some.

Le apenas pelo metodo read() do leitor, em objetos ja usados pelo projeto: cena, contexto,
jogador, alvo e um mob. Nao escreve na memoria do jogo. As capturas contem dados do processo
(nomes, textos): mantenha-as locais e nao as compartilhe."""
import json,math,struct,time,zipfile
from pathlib import Path
import numpy as np

# Extensao dos objetos lidos. Sao tamanhos de leitura, nao a definicao exata de cada estrutura.
TAMANHOS={'cena':0xEC000,'contexto':0x8E000,'jogador':0x39bc,'alvo':0x39bc,'mob':0x39bc}
BLOCO=4096
PONTEIRO_MIN,PONTEIRO_MAX=0x10000,0x7ffeffff
TAMANHO_EXTRA_MAX=0x2000

def _ler_regiao(dados,endereco,tamanho):
    """Le em blocos; os ilegiveis ficam zerados e sao listados como ausentes."""
    conteudo=bytearray(tamanho);ausentes=[]
    for inicio in range(0,tamanho,BLOCO):
        n=min(BLOCO,tamanho-inicio)
        try:conteudo[inicio:inicio+n]=dados.read(endereco+inicio,n)
        except RuntimeError:ausentes.append((inicio,n))
    return bytes(conteudo),ausentes

def _enderecos(dados,incluir_mob):
    cena=dados.cena_validada()
    contexto=dados.u32(dados.base+dados.cfg('context_rva'))
    regioes={'cena':cena,'contexto':contexto}
    jogador=dados.u32(cena+dados.layout['player_offset'])
    if jogador:regioes['jogador']=jogador
    alvo=dados.u32(cena+dados.layout['target_offset'])
    if alvo:regioes['alvo']=alvo
    if incluir_mob:
        instantaneo=dados.snapshot();player=instantaneo['player']
        mobs=dados.listar_mobs(player['position'],60,player)
        if mobs:regioes['mob']=mobs[0]['ref']
    return {n:(a,TAMANHOS[n]) for n,a in regioes.items() if a}

def analisar_extra(especificacao):
    """'cena+0x1a8->0x400' -> ('cena',0x1a8,0x400): le o ponteiro em cena+0x1a8 e captura 0x400 bytes dele."""
    try:
        origem,tamanho=especificacao.split('->');regiao,offset=origem.split('+')
        offset,tamanho=int(offset,0),int(tamanho,0)
    except ValueError:raise ValueError(f'Extra invalido: {especificacao!r}. Use regiao+offset->tamanho, ex.: cena+0x1a8->0x400')
    if regiao not in TAMANHOS:raise ValueError(f'Regiao desconhecida: {regiao}. Opcoes: {", ".join(TAMANHOS)}')
    if not 0<tamanho<=TAMANHO_EXTRA_MAX:raise ValueError(f'Tamanho do extra deve estar entre 1 e {TAMANHO_EXTRA_MAX:#x}')
    if offset<0 or offset%4:raise ValueError('O offset do extra deve ser positivo e multiplo de 4')
    return regiao,offset,tamanho

def capturar(dados,rotulo,mob=False,extras=(),relogio=time.time):
    """Le as regioes conhecidas e devolve dict(meta,regioes)."""
    enderecos=_enderecos(dados,mob)
    regioes={};meta=dict(rotulo=rotulo,sha256=getattr(dados,'sha256',None),t=relogio(),regioes={})
    for nome,(endereco,tamanho) in enderecos.items():
        conteudo,ausentes=_ler_regiao(dados,endereco,tamanho)
        regioes[nome]=conteudo;meta['regioes'][nome]=dict(endereco=endereco,tamanho=tamanho,ausentes=ausentes)
    for especificacao in extras:
        regiao,offset,tamanho=analisar_extra(especificacao)
        if regiao not in regioes:continue
        palavras=struct.unpack_from('<I',regioes[regiao],offset)[0]
        if not PONTEIRO_MIN<=palavras<=PONTEIRO_MAX:continue
        nome=f'{regiao}+{offset:#x}'
        conteudo,ausentes=_ler_regiao(dados,palavras,tamanho)
        regioes[nome]=conteudo;meta['regioes'][nome]=dict(endereco=palavras,tamanho=tamanho,ausentes=ausentes,origem=especificacao)
    return dict(meta=meta,regioes=regioes)

def salvar(captura,caminho):
    caminho=Path(caminho);caminho.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(caminho,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('meta.json',json.dumps(captura['meta'],ensure_ascii=False))
        for nome,conteudo in captura['regioes'].items():z.writestr(f'regioes/{nome}.bin',conteudo)

def carregar(caminho):
    with zipfile.ZipFile(caminho) as z:
        meta=json.loads(z.read('meta.json'))
        regioes={n:z.read(f'regioes/{n}.bin') for n in meta['regioes']}
    for r in meta['regioes'].values():r['ausentes']=[tuple(x) for x in r['ausentes']]
    return dict(meta=meta,regioes=regioes)

def _palavras(captura,regiao):
    conteudo=captura['regioes'][regiao]
    return np.frombuffer(conteudo[:len(conteudo)//4*4],dtype='<u4')

def regioes_comuns(*grupos):
    comuns=None
    for grupo in grupos:
        for captura in grupo:
            nomes=set(captura['regioes']);comuns=nomes if comuns is None else comuns&nomes
    return sorted(comuns or [])

def candidatos(grupo_a,grupo_b,regiao):
    """Palavras estaveis em cada grupo e diferentes entre os grupos: [{offset,a,b}]."""
    if not grupo_a or not grupo_b:raise ValueError('Cada grupo precisa de ao menos uma captura')
    A=np.stack([_palavras(c,regiao) for c in grupo_a]);B=np.stack([_palavras(c,regiao) for c in grupo_b])
    valido=np.ones(A.shape[1],dtype=bool)
    for c in (*grupo_a,*grupo_b):
        for inicio,n in c['meta']['regioes'][regiao]['ausentes']:valido[inicio//4:(inicio+n)//4]=False
    selecao=valido&(A==A[0]).all(axis=0)&(B==B[0]).all(axis=0)&(A[0]!=B[0])
    return [dict(offset=int(i)*4,a=int(A[0,i]),b=int(B[0,i])) for i in np.nonzero(selecao)[0]]

def _flutuante(valor):
    f=struct.unpack('<f',struct.pack('<I',valor))[0]
    return f if math.isfinite(f) and 1e-6<abs(f)<1e7 else None

def tipo_mudanca(a,b):
    """Classifica a mudanca e devolve (prioridade,rotulo); menor prioridade = mais provavel de ser estado."""
    if {a,b}<={0,1}:return 0,'flag 0/1'
    if a==0 or b==0:
        outro=b if a==0 else a
        if PONTEIRO_MIN<=outro<=PONTEIRO_MAX:return 1,'nulo <-> ponteiro'
        return 2,'zero <-> valor'
    if max(a,b)<=0xff:return 3,'contador pequeno'
    return 4,'valor'

def descrever(valor):
    assinado=valor-(1<<32) if valor>=1<<31 else valor
    return dict(u32=f'{valor:#010x}',i32=assinado,f32=_flutuante(valor))

def classificar(lista):
    """Ordena candidatos por probabilidade e anexa tipo e interpretacoes."""
    saida=[]
    for c in lista:
        prioridade,rotulo=tipo_mudanca(c['a'],c['b'])
        saida.append(dict(c,prioridade=prioridade,tipo=rotulo,a_desc=descrever(c['a']),b_desc=descrever(c['b'])))
    return sorted(saida,key=lambda c:(c['prioridade'],c['offset']))

def agrupar_adjacentes(lista):
    """Junta offsets consecutivos (de 4 em 4): blocos grandes costumam ser texto/array, nao um campo de estado."""
    blocos=[]
    for c in sorted(lista,key=lambda c:c['offset']):
        if blocos and c['offset']==blocos[-1][-1]['offset']+4:blocos[-1].append(c)
        else:blocos.append([c])
    return blocos
