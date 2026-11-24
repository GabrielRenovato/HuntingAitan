"""Observacoes de paradas e transicao continua em revisitas vazias."""
import math

class VisitasCircuito:
    def iniciar_visitas(self,pontos):
        self.pontos_observados=pontos
        self.inteligente=False;self.observacao_em=-100.;self.mobs=[];self.limpos={};self.reaparecimentos={};self.ultimo_abate={};self.vistos=set()

    def observar(self,mobs,pos,agora):
        self.observacao_em=agora;self.observacao_pos=tuple(pos);self.mobs=list(mobs)
        ids={m['id'] for m in mobs};retornos=[]
        for m in mobs:
            ponto=min(self.pontos_observados,key=lambda p:math.dist(p['pos'],m['position']))
            i=ponto['id']
            if math.dist(ponto['pos'],m['position'])>20:continue
            if m['id'] not in self.vistos and i in self.ultimo_abate:
                intervalo=agora-self.ultimo_abate[i]
                if intervalo>=5:
                    self.reaparecimentos.setdefault(i,[]).append(intervalo)
                    retornos.append(dict(ponto=i,intervalo_observado=round(intervalo,1),amostras=len(self.reaparecimentos[i])))
                self.ultimo_abate.pop(i,None)
            self.limpos.pop(i,None)
        self.vistos=ids
        return retornos

    def abate(self,alvo,pos,agora):
        ponto=min(self.pontos_observados,key=lambda p:math.dist(p['pos'],alvo['position']))
        if math.dist(ponto['pos'],alvo['position'])<=20:
            self.ultimo_abate[ponto['id']]=agora
        # Reancora o indice no trecho atual. Apos perseguir um mob nao tenta
        # voltar a uma celula antiga anterior a posicao real.
        self.indice=min(range(len(self.trechos[self.trecho]['caminho'])),key=lambda i:math.dist(pos,self.trechos[self.trecho]['caminho'][i]))

    def destino(self,pos,agora):
        if not self.inteligente:return super().destino(pos,agora)
        t=self.trechos[self.trecho];i=t['ate']
        if math.dist(pos,t['caminho'][-1])<=3.5 and agora-self.observacao_em<.8 and math.dist(pos,self.observacao_pos)<=2:
            perto=any(math.dist(m['position'],pos)<=20 for m in self.mobs)
            if not perto:
                if i in self.limpos or i in self.ultimo_abate:
                    # Faz a transicao antes de chegar ao ponto final para nao
                    # mandar parar e arrancar de novo numa revisita vazia.
                    self.limpos[i]=agora;self.trecho=(self.trecho+1)%len(self.trechos)
                    if self.trecho==0:self.voltas+=1
                    self.indice=0;self.espera_ate=None
                    return super().destino(pos,agora)
        antes=self.trecho;resultado=super().destino(pos,agora)
        if self.trecho!=antes:self.limpos[i]=agora
        return resultado
