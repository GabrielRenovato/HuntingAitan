"""Alterna combate, saida, retorno ao portal e entrada Elite confirmada."""
import copy,math,threading,time
from huntingaitan.rotas.entrada_mina import EntradaMina,PORTAL
from huntingaitan.rotas.mina_lenfer import dentro_mina


class CicloMina:
    def __init__(self,perfil,control,emitir,ler,executar,sair,entrar,criar_rota=EntradaMina):
        self.perfil=copy.deepcopy(perfil);self.control=control;self.emitir=emitir
        self.ler=ler;self.executar=executar;self.sair=sair;self.entrar=entrar;self.criar_rota=criar_rota
        self.concluidas=0;self.etapa='iniciar';self.abate_confirmado=False

    def evento(self,e):
        # Cada motor libera suas teclas ao terminar uma etapa; o painel so
        # recebe finished quando todo o ciclo realmente termina.
        if e.get('event')=='finished':return
        if e.get('event')=='dungeon_complete':self.abate_confirmado=True
        self.emitir(dict(e,cycles_completed=self.concluidas))

    def passo(self):
        contexto=self.ler();pos=contexto['position']
        if contexto['hp']<=0:
            self.control.reason='personagem_sem_vida';self.control.stop.set();return
        if self.etapa=='iniciar':self.etapa='dg' if dentro_mina(pos) else 'retornar'
        self.emitir(dict(event='cycle',state=self.etapa,cycles_completed=self.concluidas))
        if self.etapa=='dg':
            if not dentro_mina(pos):self.etapa='retornar';return
            self.abate_confirmado=False;self.control.reason='etapa_em_andamento'
            p=dict(self.perfil,duration_minutes=0,mina_repeat=False)
            self.executar(p,self.evento,self.control)
            if self.abate_confirmado:
                self.concluidas+=1;self.etapa='sair'
                self.emitir(dict(event='cycle',state='dg_concluida',cycles_completed=self.concluidas,message='Malik confirmado; saindo do grupo para repetir no Elite.'))
            elif not self.control.stop.is_set():
                # Um motor que encerrou por morte/cena invalida nao e uma DG
                # concluida e nao deve ser reiniciado silenciosamente.
                self.control.stop.set()
        elif self.etapa=='sair':
            if not dentro_mina(pos) or self.sair():
                limite=self.perfil.get('mina_cycles',0)
                if limite and self.concluidas>=limite:
                    self.control.reason='ciclos_concluidos';self.control.stop.set()
                else:self.etapa='retornar'
        elif self.etapa in ('retornar','liberar_entrada'):
            if dentro_mina(pos):self.etapa='corrigir_entrada';return
            liberar=self.etapa=='liberar_entrada'
            if not liberar and math.dist(pos,PORTAL)<=4:self.etapa='entrar';return
            if liberar:rota=self.criar_rota(contexto['pasta'],pos,bloqueadores=getattr(self.control,'bloqueadores_portal',()))
            else:rota=self.criar_rota(contexto['pasta'],pos)
            self.control.reason='etapa_em_andamento'
            self.executar(dict(self.perfil,duration_minutes=0,mina_repeat=False),self.evento,self.control,percurso=rota)
            if getattr(self.control,'reason',None)=='entrada_alcancada':self.etapa='entrar'
            elif not self.control.stop.is_set():self.control.stop.set()
        elif self.etapa=='entrar':
            if self.entrar():self.etapa='dg'
            elif dentro_mina(self.ler()['position']):self.etapa='corrigir_entrada'
            elif getattr(self.control,'bloqueadores_portal',None):self.etapa='liberar_entrada'
            else:self.etapa='retornar'
        elif self.etapa=='corrigir_entrada':
            # Posicao interna sem comprovacao de Elite: sai sem contar abate.
            if self.sair():self.etapa='retornar'


def main(perfil,emitir,control):
    control.auto_ui_scale=perfil.get('auto_ui_scale',True)
    import keyboard
    from huntingaitan.leitura.dados_internos import DadosInternos
    from huntingaitan.combate.hunt_native import main as executar
    inicio=time.monotonic();fim=threading.Event();control.cycle_context=True
    def evento(e):
        if e.get('event')=='telemetry':e=dict(e,elapsed=time.monotonic()-inicio)
        emitir(e)
    def contexto():
        d=DadosInternos()
        try:
            p=d.snapshot()['player']
            return dict(position=p['position'],hp=p['hp']/p['hp_max'],pasta=d.caminho.parent)
        finally:d.close()
    def operacao(nome):
        evento(dict(event='status',state='initializing',message='Preparando saida do grupo.' if nome=='sair_grupo' else 'Preparando entrada da Mina no Elite.'))
        # Carrega reconhecimento visual somente ao chegar a uma interface.
        # Importar OpenCV aqui no inicio atrasava a primeira navegacao.
        import huntingaitan.rotas.operacoes_mina
        fn=getattr(operacoes_mina,nome)
        d=DadosInternos()
        try:return fn(d,control,evento)
        finally:d.close()
    def vigiar():
        while not fim.wait(.05):
            if keyboard.is_pressed('f12'):control.reason='F12';control.stop.set();return
            if perfil['duration_minutes'] and time.monotonic()-inicio>=perfil['duration_minutes']*60:
                control.reason='tempo_encerrado';control.stop.set();return
    ciclo=CicloMina(perfil,control,evento,contexto,executar,lambda:operacao('sair_grupo'),lambda:operacao('entrar_elite'))
    if not control.stop.is_set():
        from huntingaitan.visao.controle_avisos import preparar_runtime_visual
        preparar_runtime_visual()
    threading.Thread(target=vigiar,daemon=True).start()
    try:
        emitir(dict(event='status',state='initializing',message='Conferindo posicao para iniciar o ciclo da Mina.'))
        if perfil['minimize_on_start'] and not control.stop.is_set() and not control.pause.is_set():
            d=DadosInternos()
            try:
                import ctypes
                from ctypes import wintypes as w
                d.u.ShowWindow.argtypes=[w.HWND,ctypes.c_int];d.u.SetForegroundWindow.argtypes=[w.HWND]
                d.u.ShowWindow(d.hwnd,9);d.u.SetForegroundWindow(d.hwnd)
            finally:d.close()
        while not control.stop.is_set():
            if control.pause.is_set():control.stop.wait(.1);continue
            ciclo.passo()
            if not control.stop.is_set():control.stop.wait(.5)
    finally:
        fim.set()
        emitir(dict(event='finished',message='Ciclo da Mina encerrado; teclas liberadas.',cycles_completed=ciclo.concluidas,reason=getattr(control,'reason','controle_de_parada')))
