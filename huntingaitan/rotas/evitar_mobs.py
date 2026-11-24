"""Acrescenta zonas de afastamento a uma copia da grade, preservando a colisao original."""
import math
from huntingaitan.rotas.navegacao_grade import Grade


def fora_das_zonas(pos,centros,raio):
    return all(math.dist(pos,c)>raio for c in centros)


def aplicar_zonas(grade,centros,raio,saida=None):
    flags=bytearray(grade.flags)
    # Inclui a diagonal de meia celula: toda a celula bloqueada respeita a margem.
    margem=raio+math.sqrt(.5)
    for centro in centros:
        cx,cy=grade.celula(centro);r=math.ceil(margem)+1
        for y in range(max(grade.canto[1],cy-r),min(grade.canto[1]+grade.altura,cy+r+1)):
            for x in range(max(grade.canto[0],cx-r),min(grade.canto[0]+grade.largura,cx+r+1)):
                c=(x,y)
                if math.dist(grade.mundo(c),centro)<=margem:flags[grade.indice(c)]|=1
    if saida is not None:
        c=grade.celula(saida);i=grade.indice(c)
        if i is not None and grade.livre(c):flags[i]=grade.flags[i]
    return Grade(grade.origem,grade.canto,grade.largura,grade.altura,bytes(flags),grade.alturas,grade.mapa)
