"""Exporta a tabela de skills ja decifrada que o cliente mantem na memoria (somente leitura).

SkillData12.bin e cifrado em disco; o cliente o decifra ao carregar. O leitor ja usa a mesma tabela
(effect_table_rva, registros de 0x2d0 bytes) para saber quais skills causam stun, paralisia ou
congelamento. Aqui ela e copiada inteira para analise offline: nomes, recargas, custos e efeitos.

O arquivo exportado e uma copia de dados do jogo: mantenha-o local."""
import json,time,unicodedata
from pathlib import Path

REGISTRO=0x2d0
QUANTIDADE=12000
BLOCO=4096

def exportar(dados,destino,quantidade=QUANTIDADE,relogio=time.time):
    """Le quantidade*0x2d0 bytes a partir de effect_table_rva. Devolve dict de metadados."""
    destino=Path(destino);destino.parent.mkdir(parents=True,exist_ok=True)
    inicio=dados.base+dados.cfg('effect_table_rva');total=quantidade*REGISTRO
    conteudo=bytearray(total);ausentes=[]
    for deslocamento in range(0,total,BLOCO):
        n=min(BLOCO,total-deslocamento)
        try:conteudo[deslocamento:deslocamento+n]=dados.read(inicio+deslocamento,n)
        except RuntimeError:ausentes.append((deslocamento,n))
    destino.write_bytes(bytes(conteudo))
    meta=dict(sha256_cliente=getattr(dados,'sha256',None),endereco=inicio,registro=REGISTRO,quantidade=quantidade,
              tamanho=total,blocos_ilegiveis=ausentes,exportado_em=relogio())
    destino.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta

def registro(conteudo,id_):
    """Bytes do registro da skill id_ em uma exportacao."""
    return conteudo[id_*REGISTRO:(id_+1)*REGISTRO]

# --- Formato do registro (descoberto na tabela decifrada da memoria; ver docs/FORMATO_SKILLS.md) ---
# Os campos de cabecalho da skill de id X ficam no registro X-1; os de efeito, no registro X.
NIVEIS=16
OFF_TIPOS,OFF_MAGNITUDES=0x00,0x10            # 4 x int32 cada (efeitos); efeito
OFF_CONJURACAO_MS=0x3c                        # efeito
OFF_DESCRICAO,TAM_DESCRICAO=0xa8,312          # efeito, cp1252
OFF_NOME_EN,OFF_NOME=0x1e0,0x220              # cabecalho, 64 bytes cada
OFF_CLASSE,OFF_MANA,OFF_RECARGA_MS=0x268,0x278,0x284   # cabecalho
CLASSES={1:'Templario',5:'Clerigo'}           # o digito das dezenas de OFF_CLASSE; so as confirmadas

def _texto(dados,inicio,tamanho):
    return bytes(dados[inicio:inicio+tamanho]).split(b'\0')[0].decode('cp1252',errors='replace')

def _i32(dados,offset):
    return int.from_bytes(dados[offset:offset+4],'little',signed=True)

def _sem_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD',texto.lower()) if not unicodedata.combining(c))

def classificar(descricao,recarga_ms,mana):
    """Tipo provavel da skill, pela descricao: cura, defesa, ameaca, buff, ataque, passiva ou utilidade.

    E uma sugestao para o painel; o usuario pode trocar o tipo de cada tecla."""
    d=_sem_acentos(descricao)
    if recarga_ms==0 and mana==0:return 'passiva'
    if d.startswith(('recupera tu hp','recupera el hp','cura ','restaura tu hp','consume todo el mp para recuperar')):return 'cura'
    # Ameaca age sobre os inimigos; um buff que so cita a propria taxa de amenaza continua buff.
    if 'obliga a fijar' in d or ('amenaza' in d and 'enemigos' in d):return 'ameaca'
    if any(p in d for p in ('reduce todo el','reduce el dano','barrera protectora','anula por completo','repele','absorbe','concentra los ataques','concentrate en la defensa')) or d.startswith('crea un escudo'):return 'defesa'
    if d.startswith(('aumenta','bendice','activa','otorga','mejora')):return 'buff'
    if d.startswith(('inflige','ataca','apunala','explota','salta','explosion')):return 'ataque'
    return 'utilidade'

def interpretar(cabecalho,efeito,id_):
    """Dict legivel da skill id_, a partir dos registros X-1 (cabecalho) e X (efeito)."""
    classe=_i32(cabecalho,OFF_CLASSE);descricao=_texto(efeito,OFF_DESCRICAO,TAM_DESCRICAO)
    recarga=_i32(cabecalho,OFF_RECARGA_MS);mana=_i32(cabecalho,OFF_MANA)
    return dict(id=id_,nivel=(id_-1)%NIVEIS+1,nome=_texto(cabecalho,OFF_NOME,64),nome_en=_texto(cabecalho,OFF_NOME_EN,64),
                classe=classe,classe_nome=CLASSES.get(classe//10,f'classe {classe//10*10+1}') if classe else '-',
                recarga_s=recarga/1000,mana=mana,conjuracao_s=_i32(efeito,OFF_CONJURACAO_MS)/1000,
                descricao=descricao,tipo=classificar(descricao,recarga,mana),
                efeitos=[(_i32(efeito,OFF_TIPOS+4*k),_i32(efeito,OFF_MAGNITUDES+4*k)) for k in range(4) if _i32(efeito,OFF_TIPOS+4*k)])

def interpretar_exportacao(conteudo,id_):
    """interpretar() sobre uma exportacao em bytes."""
    return interpretar(registro(conteudo,id_-1),registro(conteudo,id_),id_)

def ler_skill(dados,id_):
    """Le a skill id_ direto da memoria do cliente (somente leitura)."""
    if not 1<=id_<QUANTIDADE:raise RuntimeError(f'Skill {id_} fora da tabela do cliente.')
    inicio=dados.base+dados.cfg('effect_table_rva')+(id_-1)*REGISTRO
    bruto=dados.read(inicio,2*REGISTRO)
    return interpretar(bruto[:REGISTRO],bruto[REGISTRO:],id_)

# --- Barra de atalhos ---
import struct
SLOTS=40
LINHAS=5   # 40 slots em linhas de 8; o painel confere a ordem com a barra mostrada no jogo

def ler_slots(dados):
    """Os 40 valores brutos da barra do personagem (tipo nos 4 bits baixos, id nos 17 seguintes)."""
    contexto=dados.u32(dados.base+dados.cfg('context_rva'))
    gestor=dados.u32(dados.base+dados.cfg('bar_manager_rva'))
    modo=dados.u32(gestor+0x614)
    endereco=contexto+0x8129c
    if modo==1:
        nome=dados.read(contexto+0x7fea4,128).split(b'\0')[0]
        inicio,fim=struct.unpack('<2I',dados.read(gestor+0x620,8))
        if not nome or fim<inicio or (fim-inicio)%0x120 or (fim-inicio)//0x120>256:raise RuntimeError('Perfil da barra indisponivel')
        endereco=None
        for indice in range((fim-inicio)//0x120):
            registro_perfil=inicio+indice*0x120
            if dados.read(registro_perfil,128).split(b'\0')[0]==nome:endereco=registro_perfil+128;break
        if endereco is None:raise RuntimeError('Barra do personagem nao encontrada')
    return struct.unpack('<40I',dados.read(endereco,SLOTS*4))

def descrever_barra(dados):
    """Cada slot da barra com a skill decodificada: [{slot,linha,coluna,tipo_slot,skill_id,skill|None}]."""
    resultado=[]
    for indice,bruto in enumerate(ler_slots(dados)):
        tipo_slot,skill_id=bruto&15,(bruto>>4)&0x1ffff
        item=dict(slot=indice,linha=indice//8,coluna=indice%8+1,tipo_slot=tipo_slot,skill_id=skill_id,skill=None)
        if tipo_slot==2 and 0<skill_id<QUANTIDADE:
            try:item['skill']=ler_skill(dados,skill_id)
            except RuntimeError:pass
        resultado.append(item)
    return resultado

# --- Adaptador para o painel ---
TIPO_REACAO={'cura':'cura','defesa':'defesa','buff':'buff_combate','ataque':'ataque','ameaca':'ataque'}
TIPO_SLOT_ITEM=6

def tecla_sugerida(linha,coluna):
    """Tecla provavel pela posicao: linha 0 = 1..8, linha 1 = ctrl+1..8. As demais linhas tem atalhos livres."""
    if linha==0:return str(coluna)
    if linha==1:return f'ctrl+{coluna}'
    return ''

def sugerir_reacao(item):
    """Regra inicial para um slot da barra (dict de descrever_barra), ou None se nao cabe numa reacao."""
    tecla=tecla_sugerida(item['linha'],item['coluna'])
    skill=item['skill']
    if skill is None:
        if item['tipo_slot']!=TIPO_SLOT_ITEM or not item['skill_id']:return None
        return dict(nome=f"Item {item['skill_id']}",tecla=tecla,tipo='item_hp',skill_id=0,intervalo_s=5)
    tipo=TIPO_REACAO.get(skill['tipo'])
    if tipo is None or skill['nome_en']=='Attack':return None   # o ataque basico e a tecla de ataque da rotacao
    regra=dict(nome=skill['nome'],tecla=tecla,tipo=tipo,skill_id=skill['id'],mp_min=max(0,skill['mana']),
               intervalo_s=min(3600.,max(1.,skill['recarga_s'],skill['conjuracao_s']+1.)))
    if tipo=='ataque':regra['alcance_m']=5
    if skill['nome_en']=='Remedy':regra['hp_max_pct']=40   # pedido do usuario: Remediar quando a vida chega a 40%
    return regra

def barra_para_painel(slots):
    """Lista enxuta para a tela: so slots com skill ou item, com os dados e a regra sugerida."""
    saida=[]
    for item in slots:
        skill=item['skill']
        if skill is None and not (item['tipo_slot']==TIPO_SLOT_ITEM and item['skill_id']):continue
        base=dict(linha=item['linha'],coluna=item['coluna'],tecla=tecla_sugerida(item['linha'],item['coluna']),
                  skill_id=item['skill_id'],sugestao=sugerir_reacao(item))
        if skill:base.update(tipo_slot='skill',nome=skill['nome'],nome_en=skill['nome_en'],tipo=skill['tipo'],nivel=skill['nivel'],
                             recarga_s=skill['recarga_s'],mana=skill['mana'],conjuracao_s=skill['conjuracao_s'],descricao=skill['descricao'])
        else:base.update(tipo_slot='item',nome=f"Item {item['skill_id']}",tipo='item')
        saida.append(base)
    return saida
