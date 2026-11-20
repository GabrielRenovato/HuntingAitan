"""Libera entradas mantidas mesmo se o fail-safe impedir novas acoes."""
import inspect

def preparar_pressao_sem_pausa(entrada):
    func=entrada.keyDown
    try:suporta='_pause' in inspect.signature(func).parameters
    except (TypeError,ValueError):suporta=False
    # Mantem o wrapper de fail-safe; desativa somente o sleep(PAUSE), que
    # tambem cedia a thread quando PAUSE era zero.
    return (lambda tecla:func(tecla,_pause=False)) if suporta else func

def liberar_tecla(entrada,tecla):
    # O wrapper do PyDirectInput verifica o canto ate no keyUp. A liberacao
    # deve funcionar mesmo quando o canto ja bloqueou o keyDown.
    func=entrada.keyUp
    return getattr(func,'__wrapped__',func)(tecla)

def liberar_mouse(entrada):
    func=entrada.mouseUp
    return getattr(func,'__wrapped__',func)()
