"""Inventario somente leitura do cliente cujo hash DadosInternos ja validou.

0x429df0: registros de 20 bytes; 0x429ec0: sete bolsas de vinte slots.
0x54a9f0: seis equipados e 140 slots participam de Reparar Todo.
"""
import struct


def registro(raw, slot):
    item, base, serial = struct.unpack_from('<HHI', raw)
    if item != base and item:
        raise RuntimeError('Registro de inventario inconsistente')
    return dict(slot=slot, id=item, serial=serial, atual=raw[14],
                maxima=raw[15], refino=raw[16] >> 4)


def ler_inventario(dados):
    contexto = dados.u32(dados.base + dados.cfg('context_rva'))
    raw = dados.read(contexto + 0x80130, 140 * 20)
    equipados = dados.read(contexto + 0x80014, 6 * 20)
    bolsas = dados.read(contexto + 0x80c20, 7 * 20)
    ouro = struct.unpack('<Q', dados.read(contexto + 0x80cb0, 8))[0]
    if ouro > 10**15 or dados.u32(dados.base + dados.cfg('context_rva')) != contexto:
        raise RuntimeError('Inventario mudou durante a leitura')
    itens = [registro(raw[i*20:(i+1)*20], i) for i in range(140)]
    ativas = [i for i in range(7) if struct.unpack_from('<H', bolsas, i*20)[0]]
    if not ativas or any(it['id'] and it['slot']//20 not in ativas for it in itens):
        raise RuntimeError('Bolsas nao correspondem aos itens carregados')
    return dict(ouro=ouro, bolsas=ativas, itens=itens,
                equipados=[registro(equipados[i*20:(i+1)*20],i) for i in range(6)])


def equipamento_candidato(dados, item):
    if not item['id'] or item['refino'] or not item['maxima']:
        return False
    return equipamento_reparavel(dados,item)


def equipamento_reparavel(dados,item):
    if not 0<item['id']<31000:return False
    # ItemList: tipo, subtipo e durabilidade configurada. Outros tipos nao sao vendidos.
    raw = dados.read(dados.base + 0x199a290 - 0x400000 + item['id']*0x1d0, 0x198)
    tipo, subtipo = struct.unpack_from('<HH', raw, 0x100)
    return tipo == 0 and (subtipo <= 7 or 1001 <= subtipo <= 1008)


def precisa_reparar(dados,estado):
    return any(i['id'] and (i['atual']<i['maxima'] or not i['maxima']) and equipamento_reparavel(dados,i)
               for i in estado['itens']+estado['equipados'])


def nome_item(dados, item):
    return dados.read(dados.base + 0x199a290 - 0x400000 + item['id']*0x1d0, 64).split(b'\0')[0].decode('cp1252')
