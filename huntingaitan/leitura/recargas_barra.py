"""Decodifica atalhos e progresso de recarga do layout validado do cliente."""
import math


def atalhos_slots(hotkeys,caractere=None):
    """Tecla de cada slot. `caractere(vk)` informa o caractere do VK no layout do cliente; sem ele vale o layout
    americano (apostrofo = 222). No ABNT2 o apostrofo e o VK 192 e o 222 e o til."""
    if len(hotkeys)!=468:raise ValueError('Tabela de atalhos inesperada')
    apostrofo=(lambda vk:vk==222) if caractere is None else (lambda vk:caractere(vk)=="'")
    resultado={};bases=(27,35,43,19,51)
    for slot in range(40):
        off=(bases[slot//8]+slot%8)*4;vk,mod=hotkeys[off:off+2]
        if mod not in (1,2,3,4):continue
        if 48<=vk<=90:tecla=chr(vk).lower()
        elif 112<=vk<=122:tecla='f'+str(vk-111)
        elif apostrofo(vk):tecla="'"
        else:continue
        resultado[slot]={1:'',2:'alt+',3:'ctrl+',4:'shift+'}[mod]+tecla
    return resultado


def decodificar(slots, recargas, atalhos=None):
    if len(slots) != 40 or len(recargas) != 43:
        raise ValueError('Tamanho inesperado da barra de atalhos')
    resultado = {}
    # Primeira linha: atalhos 1..8. Tipo 2 usa a tabela de skills (0x659d45).
    # Itens (tipo 6), slots vazios e teclas 9/0 nao usam esta tabela.
    mapa=atalhos if atalhos is not None else {i:str(i+1) for i in range(8)}
    repetidos={k for k in mapa.values() if list(mapa.values()).count(k)>1}
    for indice, raw in enumerate(slots):
        if indice not in mapa or mapa[indice] in repetidos:continue
        tipo, skill = raw & 15, (raw >> 4) & 0x1ffff
        grupo = ((skill - 1) % 960) // 16 if skill else None
        if tipo != 2 or not 0 < skill < 12000 or grupo > 42:
            continue
        valor = recargas[grupo]
        if not math.isfinite(valor) or valor < 0:
            continue
        resultado[mapa[indice]] = dict(skill=skill, cooldown=valor, ready=valor == 0)
    return resultado
