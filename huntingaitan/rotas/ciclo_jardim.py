"""Percorre ate os Shiraz Infernais e repete a entrada no Jardim Dificil."""
import time,threading,math
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
        emitir(dict(event='cycle',state='jardim_sair',message='Trecho final alcancado; saindo antes dos Shiraz Infernais.'))
        while not parar():
            if sair():
                control.reason='jardim_trecho_encerrado'
                emitir(dict(event='cycle',state='jardim_saida_confirmada',message='Saida do Jardim confirmada; trecho encerrado sem enfrentar os Shiraz Infernais.'))
                return
            if not parar():
                emitir(dict(event='log',message='Saida do Jardim ainda nao confirmada; retomando a etapa de sair.'))
                time.sleep(.3)
    finally:
        emitir(dict(event='finished',reason=getattr(control,'reason','controle_de_parada'),message='Trecho do Jardim encerrado; teclas liberadas.'))


class CicloJardim:
    def __init__(self,perfil,control,emitir,ler,motor,sair,entrar,criar_rota=None,*,servico=None,criar_rota_npc=None):
        from huntingaitan.rotas.entrada_jardim import EntradaJardim
        self.perfil=perfil;self.control=control;self.emitir=emitir;self.ler=ler
        self.motor=motor;self.sair=sair;self.entrar=entrar;self.criar_rota=criar_rota or EntradaJardim
        self.servico=servico;self.criar_rota_npc=criar_rota_npc;self.encerrar_apos_servico=False
        self.etapa='iniciar';self.trechos=0;self.limite=False;self.reiniciar=False

    def evento(self,e):
        if e.get('event')=='jardim_limit':self.limite=True
        if e.get('event')=='jardim_reset':self.reiniciar=True
        if e.get('event') not in ('finished','dungeon_complete'):self.emitir(e)

    def passo(self):
        from huntingaitan.rotas.entrada_jardim import PORTAL,ALCANCE_ENTRADA
        contexto=self.ler();pos=contexto['position']
        if contexto['hp']<=0:
            self.control.reason='personagem_sem_vida';self.control.stop.set();return
        if self.etapa=='iniciar':self.etapa='jardim_percurso' if dentro_jardim(pos) else 'jardim_npc_retornar' if self.servico and self.perfil.get('jardim_servico_npc',True) else 'jardim_retornar'
        self.emitir(dict(event='cycle',state=self.etapa,segments_completed=self.trechos))
        if self.etapa=='jardim_percurso':
            if not dentro_jardim(pos):self.etapa='jardim_retornar';return
            self.limite=False;self.reiniciar=False;self.control.reason='etapa_em_andamento'
            self.motor(dict(self.perfil,duration_minutes=0),self.evento,self.control)
            if self.control.stop.is_set():return
            if self.limite:self.trechos+=1;self.etapa='jardim_sair'
            elif self.reiniciar:self.etapa='jardim_corrigir_entrada'
            else:self.control.stop.set()
        elif self.etapa in ('jardim_sair','jardim_corrigir_entrada'):
            corrigir=self.etapa=='jardim_corrigir_entrada'
            if not dentro_jardim(pos) or self.sair():
                self.emitir(dict(event='cycle',state='jardim_saida_confirmada',segments_completed=self.trechos))
                limite=self.perfil.get('jardim_cycles',0)
                encerrar=not corrigir and (not self.perfil.get('jardim_repeat',True) or limite and self.trechos>=limite)
                if self.servico and self.perfil.get('jardim_servico_npc',True):
                    self.encerrar_apos_servico=bool(encerrar);self.etapa='jardim_npc_retornar'
                elif encerrar:
                    self.control.reason='jardim_trecho_encerrado';self.control.stop.set()
                else:self.etapa='jardim_retornar'
        elif self.etapa=='jardim_npc_retornar':
            from huntingaitan.rotas.servico_npc import NPC,RotaLuis,ALCANCE_NPC
            if dentro_jardim(pos):self.etapa='jardim_corrigir_entrada';return
            if math.dist(pos,NPC)<=ALCANCE_NPC:self.etapa='jardim_npc_servico';return
            rota=(self.criar_rota_npc or RotaLuis)(contexto['pasta'],pos)
            self.control.reason='etapa_em_andamento'
            self.motor(dict(self.perfil,duration_minutes=0),self.evento,self.control,percurso=rota)
            if self.control.reason=='entrada_alcancada':self.etapa='jardim_npc_servico'
            elif not self.control.stop.is_set():self.control.stop.set()
        elif self.etapa=='jardim_npc_servico':
            if self.servico():
                if self.encerrar_apos_servico:
                    self.control.reason='jardim_trecho_encerrado';self.control.stop.set()
                else:self.etapa='jardim_retornar'
            elif not self.control.stop.is_set():
                self.control.reason='servico_npc_nao_confirmado';self.control.stop.set()
        elif self.etapa in ('jardim_retornar','jardim_liberar_entrada'):
            if dentro_jardim(pos):self.etapa='jardim_corrigir_entrada';return
            liberar=self.etapa=='jardim_liberar_entrada'
            if not liberar and math.dist(pos,PORTAL)<=ALCANCE_ENTRADA:self.etapa='jardim_entrar';return
            rota=self.criar_rota(contexto['pasta'],pos,bloqueadores=getattr(self.control,'bloqueadores_portal',()) if liberar else ())
            self.control.reason='etapa_em_andamento'
            self.motor(dict(self.perfil,duration_minutes=0),self.evento,self.control,percurso=rota)
            if self.control.reason=='entrada_alcancada':self.etapa='jardim_entrar'
            elif not self.control.stop.is_set():self.control.stop.set()
        elif self.etapa=='jardim_entrar':
            if self.entrar():self.etapa='jardim_percurso'
            elif dentro_jardim(self.ler()['position']):self.etapa='jardim_corrigir_entrada'
            elif getattr(self.control,'bloqueadores_portal',None):self.etapa='jardim_liberar_entrada'
            else:self.etapa='jardim_retornar'


def main(perfil,emitir,control):
    import keyboard
    from huntingaitan.combate.hunt_native import main as motor
    from huntingaitan.leitura.dados_internos import DadosInternos
    from huntingaitan.rotas.operacoes_mina import sair_grupo,entrar_jardim
    from huntingaitan.visao.controle_avisos import preparar_runtime_visual
    inicio=time.monotonic();fim=threading.Event();control.cycle_context=True
    control.auto_ui_scale=perfil.get('auto_ui_scale',True)
    def evento(e):
        if e.get('event')=='telemetry':e=dict(e,elapsed=time.monotonic()-inicio)
        emitir(e)
    def ler():
        dados=DadosInternos()
        try:
            p=dados.snapshot()['player']
            return dict(position=p['position'],hp=p['hp']/p['hp_max'],pasta=dados.caminho.parent)
        finally:dados.close()
    def operacao(entrada=False):
        dados=DadosInternos()
        try:
            if dados.snapshot()['player']['hp']<=0:
                control.reason='personagem_sem_vida';control.stop.set();return False
            if entrada:return entrar_jardim(dados,control,evento)
            return sair_grupo(dados,control,evento,dentro=dentro_jardim,nome='Jardim')
        finally:dados.close()
    def vigiar():
        while not fim.wait(.05):
            if keyboard.is_pressed('f12'):control.reason='F12';control.stop.set();return
            if perfil.get('duration_minutes',0) and time.monotonic()-inicio>=perfil['duration_minutes']*60:
                control.reason='tempo_encerrado';control.stop.set();return
    def servico():
        from huntingaitan.rotas.operacoes_npc import reparar_e_vender
        d=DadosInternos()
        try:return reparar_e_vender(d,control,evento)
        finally:d.close()
    ciclo=CicloJardim(perfil,control,evento,ler,motor,operacao,lambda:operacao(True),servico=servico)
    preparar_runtime_visual();threading.Thread(target=vigiar,daemon=True).start()
    try:
        while not control.stop.is_set():
            if control.pause.is_set():control.stop.wait(.1);continue
            ciclo.passo()
            if not control.stop.is_set():control.stop.wait(.3)
    finally:
        fim.set()
        emitir(dict(event='finished',reason=getattr(control,'reason','controle_de_parada'),segments_completed=ciclo.trechos,message='Ciclo do Jardim encerrado; teclas liberadas.'))
