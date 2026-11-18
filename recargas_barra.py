"""Decodifica atalhos e progresso de recarga do layout validado do cliente."""
import math


def decodificar(slots, recargas):
    if len(slots) != 40 or len(recargas) != 43:
        raise ValueError('Tamanho inesperado da barra de atalhos')
    resultado = {}
    # Primeira linha: atalhos 1..8. Tipo 2 usa a tabela de skills (0x659d45).
    # Itens (tipo 6), slots vazios e teclas 9/0 nao usam esta tabela.
    for indice, raw in enumerate(slots[:8]):
        tipo, skill = raw & 15, (raw >> 4) & 0x1ffff
        grupo = ((skill - 1) % 960) // 16 if skill else None
        if tipo != 2 or not 0 < skill < 12000 or grupo > 42:
            continue
        valor = recargas[grupo]
        if not math.isfinite(valor) or valor < 0:
            continue
        resultado[str(indice + 1)] = dict(skill=skill, cooldown=valor, ready=valor == 0)
    return resultado
