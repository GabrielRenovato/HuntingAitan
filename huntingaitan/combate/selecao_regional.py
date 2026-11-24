"""Decisoes de selecao a partir dos candidatos lidos, sem entrada no jogo."""
import math

def erro_camera(camera,ponto):
    dx=ponto[0]-camera['position'][0];dy=ponto[1]-camera['position'][1]
    desejado=math.degrees(math.atan2(dy,dx))%360
    return (desejado-camera['yaw']+540)%360-180

class BuscaRegional:
    def __init__(self,prazo_aproximar=8.,prazo_trocar=6.,intervalo_tab=.3,intervalo_giro=1.):
        self.prazo_aproximar=prazo_aproximar;self.prazo_trocar=prazo_trocar;self.intervalo_tab=intervalo_tab;self.intervalo_giro=intervalo_giro
        self.candidatos=[];self.preferido=None;self.proximo_tab=0.;self.orientar_em=0.
        self.inverter=False;self.verificar_giro=None;self.n_tabs=0
        self.buscando_id=None;self.busca_desde=0.;self.giros=0
        self.sem_alvo_desde=None;self.falharam={};self.aproximacoes=0
    def reiniciar_busca(self,agora):
        self.sem_alvo_desde=agora;self.buscando_id=None
    def confirmar_alvo(self):
        self.n_tabs=0;self.buscando_id=None;self.sem_alvo_desde=None
        self.falharam.clear();self.aproximacoes=0
    def atualizar(self,candidatos):
        lista=list(candidatos)
        ids={m['id'] for m in lista}
        if self.preferido not in ids:self.preferido=lista[0]['id'] if lista else None
        self.candidatos=sorted(lista,key=lambda m:m['id']!=self.preferido)
    def decidir(self,agora,atual,camera,pos=None):
        ids={m['id'] for m in self.candidatos}
        if atual and atual['id'] in ids and atual['hp']>0:
            self.confirmar_alvo();return ('aceitar',atual)
        if not self.candidatos:return ('aguardar',None)
        if self.sem_alvo_desde is None:self.sem_alvo_desde=agora
        if pos is not None and agora-self.sem_alvo_desde>=self.prazo_aproximar:
            if self.aproximacoes>=3:
                self.aproximacoes=0;self.reiniciar_busca(agora)
                return ('retornar',None)
            # O prazo global nao reinicia ao alternar o candidato preferido.
            vivos=[m for m in self.candidatos if self.falharam.get(m['id'],0)<=agora]
            if not vivos:vivos=self.candidatos
            destino=min(vivos,key=lambda m:math.dist(pos,m['position']))
            self.falharam[destino['id']]=agora+20
            self.aproximacoes+=1
            self.reiniciar_busca(agora)
            return ('aproximar',destino)
        destino=self.candidatos[0]
        if self.buscando_id!=destino['id']:
            self.buscando_id=destino['id'];self.busca_desde=agora;self.giros=0
        if agora-self.busca_desde>=self.prazo_trocar and len(self.candidatos)>1:
            self.falharam[destino['id']]=agora+20
            self.candidatos=self.candidatos[1:]+self.candidatos[:1]
            elegiveis=[m for m in self.candidatos if self.falharam.get(m['id'],0)<=agora]
            if elegiveis:
                melhor=elegiveis[0]['id'];self.candidatos.sort(key=lambda m:m['id']!=melhor)
            destino=self.candidatos[0];self.preferido=destino['id']
            self.buscando_id=destino['id'];self.busca_desde=agora;self.giros=0
            self.verificar_giro=None;self.n_tabs=0
            self.proximo_tab=agora+self.intervalo_tab
            return ('tab',destino['id'])
        if camera is not None:
            if self.verificar_giro:
                antes,sinal=self.verificar_giro
                delta=(camera['yaw']-antes+540)%360-180
                if abs(delta)>2 and delta*sinal<0:self.inverter=not self.inverter
                self.verificar_giro=None
            erro=erro_camera(camera,destino['position'])
            # O TAB original usa um setor da camera, nao a regiao inteira.
            # Orienta uma vez para o candidato fora do setor; reconfirma pela leitura.
            if self.giros<2 and agora>=self.orientar_em and (abs(erro)>70 or (self.n_tabs>=2 and abs(erro)>15)):
                self.giros+=1
                self.orientar_em=agora+self.intervalo_giro;self.n_tabs=0
                sinal=1 if erro>0 else -1
                self.verificar_giro=(camera['yaw'],sinal)
                tecla='a' if sinal>0 else 'd'
                if self.inverter:tecla='d' if tecla=='a' else 'a'
                return ('orientar',(tecla,min(.35,max(.04,abs(erro)/150.))))
        if agora>=self.proximo_tab:
            self.proximo_tab=agora+self.intervalo_tab;self.n_tabs+=1
            return ('tab',destino['id'])
        return ('aguardar',None)
