"""Percorre o Jardim ate os Lazapas finais e sai, sem repetir a entrada."""
import time
from huntingaitan.rotas.jardim_aereo import dentro_jardim


def executar_trecho(perfil,emitir,control,motor,sair,parar=None):
    parar=parar or control.stop.is_set;limite=False
    def evento(e):
        nonlocal limite
        if e.get('event')=='jardim_limit':limite=True
        if e.get('event')!='finished':emitir(e)
    try:
        motor(perfil,evento,control)
        if parar() or not limite:return
        emitir(dict(event='cycle',state='jardim_sair',message='Trecho final alcancado; saindo antes dos Lazapas.'))
        while not parar():
            if sair():
                control.reason='jardim_trecho_encerrado'
                emitir(dict(event='cycle',state='jardim_saida_confirmada',message='Saida do Jardim confirmada; trecho encerrado sem enfrentar os Lazapas finais.'))
                return
            if not parar():
                emitir(dict(event='log',message='Saida do Jardim ainda nao confirmada; retomando a etapa de sair.'))
                time.sleep(.3)
    finally:
        emitir(dict(event='finished',reason=getattr(control,'reason','controle_de_parada'),message='Trecho do Jardim encerrado; teclas liberadas.'))


def main(perfil,emitir,control):
    import keyboard
    from huntingaitan.combate.hunt_native import main as motor
    from huntingaitan.leitura.dados_internos import DadosInternos
    from huntingaitan.rotas.operacoes_mina import sair_grupo
    def parar():
        if keyboard.is_pressed('f12'):control.reason='F12';control.stop.set()
        return control.stop.is_set()
    def sair():
        dados=DadosInternos()
        try:
            if dados.snapshot()['player']['hp']<=0:
                control.reason='personagem_sem_vida';control.stop.set();return False
            return sair_grupo(dados,control,emitir,dentro=dentro_jardim,nome='Jardim')
        finally:dados.close()
    executar_trecho(perfil,emitir,control,motor,sair,parar)
