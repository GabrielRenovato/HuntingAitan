"""Libera entradas mantidas mesmo se o fail-safe impedir novas acoes."""
def liberar_tecla(entrada,tecla):
    # O wrapper do PyDirectInput verifica o canto ate no keyUp. A liberacao
    # deve funcionar mesmo quando o canto ja bloqueou o keyDown.
    func=entrada.keyUp
    return getattr(func,'__wrapped__',func)(tecla)

def liberar_mouse(entrada):
    func=entrada.mouseUp
    return getattr(func,'__wrapped__',func)()
