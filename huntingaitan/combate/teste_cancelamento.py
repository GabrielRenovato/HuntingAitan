"""Sequencia experimental isolada; nao habilita cancelamento na caca."""
import math

def condicao_teste(snapshot,controle,id_esperado):
    p=snapshot['player'];t=snapshot.get('target')
    if p['hp']<=0 or p['hp']/p['hp_max']<.65:return False
    if any(controle.get(k) for k in ('casting','stunned','paralyzed','frozen')):return False
    return bool(t and t['id']==id_esperado and t['hostile'] and t['hp']>0 and math.dist(p['position'],t['position'])<=2.4)

def sequencia(entrada,permitido,combo=False):
    enviados=[]
    # Sem esperas programadas entre as teclas. O tempo real das chamadas e
    # medido pelo teste; nao e anunciado como zero milissegundo.
    for i,tecla in enumerate(('1','r','r','1','w','w') if combo else ('1',)):
        if not permitido():break
        try:
            ok=entrada.keyDown(tecla)
            enviados.append((tecla,ok))
            if ok is False and (i==0 or tecla!='1'):break
        finally:entrada.keyUp(tecla)
    return enviados

def avaliar(rodadas):
    grupos={modo:[r for r in rodadas if r['modo']==modo and r.get('valida')] for modo in ('normal','sequencia')}
    taxas={modo:sum(r['dano'] for r in rs)/sum(r['duracao'] for r in rs) if rs else None for modo,rs in grupos.items()}
    suficiente=all(len(rs)>=4 for rs in grupos.values())
    ganho=(taxas['sequencia']/taxas['normal']-1) if taxas['normal'] and taxas['sequencia'] is not None else None
    return dict(amostras={m:len(rs) for m,rs in grupos.items()},taxas_observadas=taxas,ganho=ganho,evidencia_suficiente=suficiente,
                candidato_a_validacao=suficiente and ganho is not None and ganho>.15,
                ativar_automaticamente=False)
