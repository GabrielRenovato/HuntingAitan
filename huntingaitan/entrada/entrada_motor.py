"""Adaptador de entrada ao fundo com acoes na thread do cliente validado."""
import math,time
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.combate.selecao_regional import erro_camera

class EntradaMotor(EntradaJanela):
    def __init__(self,hwnd,pid,u=None):
        super().__init__(hwnd,pid,u);self.ponte=None;self.dados=None;self.nativas=set();self.movendo=False;self.destino=None;self.movimento_em=-100.;self.permitido=lambda:True;self.ultima_resposta=None

    def conectar(self,dados,fabrica=None):
        from huntingaitan.entrada.ponte_camera import PonteCamera
        if dados.pid!=self.pid or dados.hwnd!=self.hwnd:raise RuntimeError('Leitura e ponte apontam para clientes diferentes')
        self.dados=dados;self.ponte=(fabrica or PonteCamera)(dados)

    def validar_regras(self,perfil):
        barra=self.dados.recargas_atalhos();tipos=getattr(self.dados,'tipos_atalhos',{})
        if perfil['attack_key'] not in barra:raise ValueError('Ataque normal nao encontrado na barra: '+perfil['attack_key'])
        for regra in perfil['reacoes']:
            if not regra['ativa']:continue
            atual=barra.get(regra['tecla']);id_=regra['skill_id']
            if id_ and (not atual or (atual['skill']-1)//16!=(id_-1)//16):
                raise ValueError('Regra nao corresponde a habilidade da barra: '+regra['nome']+' em '+regra['tecla'])
            if id_ and atual:regra['skill_id']=atual['skill']
            if not id_ and regra['tecla'] in tipos and tipos[regra['tecla']]==0:
                raise ValueError('Item configurado em slot vazio: '+regra['tecla'])
        avisos=[]
        for i,tecla in enumerate(perfil['buff_keys']):
            if tecla and tipos.get(tecla)==0:
                perfil['buff_keys'][i]='';avisos.append('Buff por tempo ignorado nesta sessao: slot '+tecla+' vazio.')
        return avisos

    def keyDown(self,tecla,_pause=False):
        self.ultima_resposta=None
        self.validar()
        if not self.ponte:raise RuntimeError('Motor interno ainda nao conectado')
        if not self.permitido():return False
        if not self.modificadores_livres():return False
        tecla=tecla.lower()
        if tecla=='tab':self.parar_movimento();self.ponte.selecionar();self.nativas.add(tecla);return True
        barra=self.dados.recargas_atalhos();skill=barra.get(tecla)
        if skill:
            if not skill['ready']:
                self.ultima_resposta=dict(tecla=tecla,skill=skill['skill'],ok=False,motivo='recarga_em_andamento');return False
            self.parar_movimento()
            resposta=self.ponte.usar(skill['skill'])
            self.ultima_resposta=dict(tecla=tecla,skill=skill['skill'],ok=bool(resposta.get('resultado')),motivo='aceito_pelo_cliente' if resposta.get('resultado') else 'recusado_pelo_cliente')
            if not resposta.get('resultado'):return False
            self.nativas.add(tecla);return True
        if getattr(self.dados,'tipos_atalhos',{}).get(tecla)==0:
            self.ultima_resposta=dict(tecla=tecla,ok=False,motivo='slot_vazio');return False
        return super().keyDown(tecla,_pause)

    def keyUp(self,tecla,_pause=False):
        if tecla in self.nativas:self.nativas.discard(tecla);return True
        return super().keyUp(tecla,_pause)

    def orientar_para(self,ponto,ativo=lambda:True):
        if not self.ponte:return False
        for _ in range(24):
            if not ativo() or not self.permitido():return False
            erro=erro_camera(self.dados.camera_regional(),ponto)
            if abs(erro)<=8:return True
            self.ponte.girar(max(-.15,min(.15,math.radians(erro))))
            time.sleep(.005)
        return abs(erro_camera(self.dados.camera_regional(),ponto))<=8

    def recuperar_alvo(self,alvo):
        if not self.ponte or not self.permitido():return False
        # Selecionar uma identidade nao e um ataque. Preserva o destino
        # enquanto o alvo e conferido; a habilidade para o movimento depois.
        return bool(self.ponte.focar(alvo).get('resultado'))

    def mover_para(self,ponto,agora,forcar=False):
        if not self.ponte:raise RuntimeError('Motor nao conectado')
        if not self.permitido():return False
        if not forcar and agora-self.movimento_em<.3 and self.destino is not None and math.dist(ponto,self.destino)<1:return False
        if not forcar and self.movendo and self.destino is not None and agora-self.movimento_em<1.5:
            pos=self.dados.snapshot()['player']['position']
            if math.dist(pos,self.destino)>2 and math.dist(ponto,self.destino)<5:return False
        self.ponte.mover(*ponto);self.destino=tuple(ponto);self.movimento_em=agora;self.movendo=True;return True

    def parar_movimento(self):
        if self.ponte and self.movendo:
            pos=self.dados.snapshot()['player']['position'];self.ponte.mover(*pos)
        self.movendo=False;self.destino=None;self.movimento_em=-100.

    def finalizar(self):
        if self.ponte:
            ponte=self.ponte
            try:self.parar_movimento()
            finally:ponte.close();self.ponte=None
            if ponte.instalada or ponte.incerta:raise RuntimeError('Ponte sem confirmacao de remocao; reinicie esse cliente antes de outra caca')
