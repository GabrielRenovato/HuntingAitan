import struct

def decodificar_config(d):
    if len(d)!=180:raise ValueError('Configuracao precisa de 180 bytes')
    return dict(hp_percentual=d[0],mp_percentual=d[1],modo_alvo=d[2],alcance=d[3],
        exclusoes_texto=list(struct.unpack_from('<50h',d,16)),
        skills=list(struct.unpack_from('<10h',d,116)),
        intervalos_skills=list(struct.unpack_from('<10h',d,136)),
        itens_adicionais=list(struct.unpack_from('<5h',d,156)),
        intervalos_itens=list(struct.unpack_from('<5h',d,166)),
        item_retorno=struct.unpack_from('<h',d,176)[0],flags=struct.unpack_from('<H',d,178)[0])
