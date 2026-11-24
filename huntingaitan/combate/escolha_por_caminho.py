"""Selecao por caminho acessivel compartilhada pelos circuitos internos."""
import math

class EscolhaPorCaminho:
    def __init__(self,prioridade=None):
        self.prioridade=prioridade or (lambda m:False)
        self.ate=0.;self.cache={};self.assinatura=None;self.selecionar_em=0.;self.selecao_id=None;self.selecao_desde=0.

    def tentar_selecao(self,id_,agora):
        if self.selecao_id!=id_:self.selecao_id=id_;self.selecao_desde=agora
        return agora-self.selecao_desde<2.

    def ordenar(self,dados,navegador,pos,mobs,agora,limite):
        if not mobs:
            self.cache={};self.assinatura=();self.ate=agora+1.;self.origem=tuple(pos)
            return []
        assinatura=tuple(sorted((m['id'],round(m['position'][0]/2),round(m['position'][1]/2)) for m in mobs))
        if agora>=self.ate or assinatura!=self.assinatura or math.dist(pos,self.origem)>2:
            grade=navegador.grade
            if grade is None or agora-navegador.grade_em>2 or grade.indice(grade.celula(pos)) is None:
                grade=navegador.leitor(dados,pos)
            custos={}
            # Limita trabalho por leitura; os demais entram na rodada seguinte
            # se os mais proximos nao tiverem passagem.
            for m in sorted(mobs,key=lambda m:(not self.prioridade(m),math.dist(pos,m['position'])))[:8]:
                # Um alvo a 49 unidades pode cair fora da janela de raio 48.
                # Nessa borda segue um trecho confirmado e reconfirma adiante,
                # em vez de declarar que o candidato nao tem passagem.
                parcial=grade.indice(grade.celula(m['position'])) is None
                rota=grade.caminho(pos,m['position'],alcance=2.,max_nos=4500,limite=limite,parcial=parcial)
                if rota:
                    custo=sum(math.dist(a,b) for a,b in zip(rota,rota[1:]))
                    custo+=sum(grade.penalidade_parede(grade.celula(p)) for p in rota)*.25
                    if parcial:custo+=math.dist(rota[-1],m['position'])+3
                    custos[m['id']]=custo
            self.cache=custos;self.ate=agora+1.;self.assinatura=assinatura;self.origem=tuple(pos)
        return sorted((m for m in mobs if m['id'] in self.cache),key=lambda m:(not self.prioridade(m),self.cache[m['id']],m['id']))
