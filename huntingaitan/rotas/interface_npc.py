"""Reconhecimento dos controles conhecidos do Luis Mandez e do inventario."""
import re,cv2,numpy as np
from huntingaitan.rotas.interface_mina import InterfaceMina
from huntingaitan.rotas.servico_npc import normalizar,inteiro_moeda,nome_corresponde
from huntingaitan.recursos import DADOS

class InterfaceNPC(InterfaceMina):
    def __init__(self,ocr=None):
        super().__init__(ocr)
        self._localizados={};self._npc_roi=None
        for n in ('reparar_todo','pergunta_reparo','pergunta_venda','inventario','comercio','tienda','classe','nome'):
            self.tpl['npc_'+n]=cv2.imread(str(DADOS/f'tpl_npc_{n}.png'),0)
            if self.tpl['npc_'+n] is None:raise RuntimeError('Modelo do NPC ausente: '+n)

    def achar_npc(self,tela,nome,limiar=.90):
        anterior=self._localizados.get(nome)
        if anterior:
            x,y=anterior['xy'];w,h=anterior['tamanho']
            atual=self.achar(tela,nome,(x-12,y-12,x+w+12,y+h+12),limiar)
            if atual:
                self._localizados[nome]=atual;return atual
        atual=self.achar(tela,nome,limiar=limiar)
        if atual:self._localizados[nome]=atual
        return atual

    def ler(self,tela,roi=None):
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,use_cls=False)
        h,w=tela.shape[:2];x0,y0,x1,y1=map(round,roi or (0,0,w,h));x0,y0=max(0,x0),max(0,y0);x1,y1=min(w,x1),min(h,y1)
        if x1<=x0 or y1<=y0:return []
        fator=max(1.,min(2.,1100/max(x1-x0,y1-y0)))
        linhas,_=self.ocr(cv2.resize(tela[y0:y1,x0:x1],None,fx=fator,fy=fator))
        saida=[]
        for caixa,texto,score in linhas or []:
            c=np.asarray(caixa,dtype=float)/fator
            if c.shape==(4,2) and float(score)>=.85:
                saida.append(dict(texto=texto,nome=normalizar(texto),ponto=(round(x0+c[:,0].mean()),round(y0+c[:,1].mean())),caixa=(x0+c[:,0].min(),y0+c[:,1].min(),x0+c[:,0].max(),y0+c[:,1].max())))
        return saida

    def dialogo(self,tela,tipo):
        q=self.achar_npc(tela,'npc_pergunta_'+tipo,limiar=.90)
        if not q:return None
        x,y=q['ponto'];s=q['escala'];roi=(x-180*s,y-12*s,x+180*s,y+115*s)
        confirmar=self.achar(tela,'confirmar',roi,.88)
        textos=self.ler(tela,roi)
        cancelar=next((t for t in textos if t['nome'] in ('cancelar','cancel')),None)
        if not confirmar or not cancelar:return None
        r=dict(tipo=tipo,confirmar=confirmar['ponto'],cancelar=cancelar['ponto'])
        if tipo=='reparo':
            valores=[inteiro_moeda(t['texto']) for t in textos if abs(t['ponto'][0]-x)<100*s and y+20*s<t['ponto'][1]<y+65*s]
            valores=[v for v in valores if v is not None]
            if len(valores)!=1:return None
            return dict(r,custo=valores[0])
        nomes=[t['texto'] for t in textos if abs(t['ponto'][0]-x)<100*s and y+6*s<t['ponto'][1]<y+32*s]
        # O zero no rotulo "Prec0" e uma confusao recorrente do OCR.
        # Os algarismos do valor continuam sujeitos a inteiro_moeda.
        precos=[re.search(r'(?:pre[cçg][o0]|precio|price)\s*:?\s*([\d., ]+)',t['texto'],re.I) for t in textos]
        precos=[inteiro_moeda(m[1].strip()) for m in precos if m]
        if len(nomes)!=1 or len(precos)!=1 or precos[0] is None:return None
        rect=tuple(map(round,(x-105*s,y+5*s,x+105*s,y+65*s)))
        x0,y0,x1,y1=rect
        assinatura=cv2.cvtColor(tela[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)>100
        return dict(r,nome=nomes[0],preco=precos[0],conferencia=(rect,assinatura))

    def confirmacao_estavel(self,tela,venda):
        rect,antes=venda['conferencia'];x0,y0,x1,y1=rect
        depois=cv2.cvtColor(tela[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)>100
        return depois.shape==antes.shape and np.array_equal(antes,depois)

    def loja(self,tela,ler_saldo=True):
        inv=self.achar_npc(tela,'npc_inventario',limiar=.91)
        if not inv:return None
        com=self.achar_npc(tela,'npc_comercio',limiar=.91)
        if not com:return None
        x,y=inv['ponto'];s=inv['escala']
        moedas=[None]
        if ler_saldo:
            valores=self.ler(tela,(x+4*s,y+12*s,x+120*s,y+38*s))
            moedas=[inteiro_moeda(t['texto']) for t in valores];moedas=[m for m in moedas if m is not None]
            if len(moedas)!=1:return None
        paginas=[];px=round(x+118*s);yt=max(0,round(y+42*s));yb=min(tela.shape[0],round(y+225*s));raio=max(5,round(10*s))
        r=tela[yt:yb,max(0,px-raio):px+raio]
        if r.size:
            b,g,v=[r[...,j].astype(float) for j in range(3)]
            ouro=(v>100)&(g>65)&(b<g*.85)&(v>g*.9)
            linhas=(ouro.sum(axis=1)>=max(2,round(3*s))).astype('uint8')[:,None]
            linhas=cv2.morphologyEx(linhas,cv2.MORPH_CLOSE,np.ones((max(1,round(3*s)),1),np.uint8))
            _,_,stats,_=cv2.connectedComponentsWithStats(linhas)
            for _,py,_,altura,_ in stats[1:]:
                if 8*s<=altura<=30*s:paginas.append((px,round(yt+py+altura/2)))
        return dict(ouro=moedas[0],escala=s,origem=(x,y),fechar=(round(x+131*s),round(y-4*s)),
                    slots=[(round(x+(-124+46*c)*s),round(y+(70+47*r)*s)) for r in range(4) for c in range(5)],paginas=paginas)

    def menu(self,tela,opcao,texto=True):
        b=self.achar_npc(tela,'npc_reparar_todo' if opcao=='reparar' else 'npc_tienda',limiar=.91)
        if b:return b['ponto']
        if not texto:return None
        nomes={'tienda','loja','store','shop'} if opcao=='loja' else {'reparartodo','reparartodos','repairall'}
        return next((t['ponto'] for t in self.ler(tela) if t['nome'] in nomes),None)

    def npc(self,tela):
        if hasattr(self,'tpl') and 'npc_nome' in self.tpl:
            b,g,r=cv2.split(tela);mascara=((g>170)&(r<130)&(b<130)).astype('uint8')*255
            achado=self.achar_npc(mascara,'npc_nome',limiar=.88)
            if achado:
                x,y=achado['ponto'];s=achado['escala'];corpo=(x,round(y+43*s))
                if corpo[1]<tela.shape[0]-10:return corpo
        roi=getattr(self,'_npc_roi',None)
        nome=next((t for t in self.ler(tela,roi) if t['nome']=='luismandez'),None) if roi else None
        if not nome:nome=next((t for t in self.ler(tela) if t['nome']=='luismandez'),None)
        if not nome:return None
        x0,y0,x1,y1=nome['caixa'];self._npc_roi=(x0-30,y0-20,x1+30,y1+20)
        # O nome flutua acima do personagem e nao e uma superficie clicavel.
        # Clicar nele pode mandar andar no terreno atras do NPC.
        _,y0,_,y1=nome['caixa'];x=nome['ponto'][0]
        y=round(y1+3*max(6,y1-y0))
        if y>=tela.shape[0]-10:return None
        return x,y

    def descricao(self,tela,nome):
        linhas=self.ler(tela);alvo=normalizar(nome)
        for titulo in linhas:
            bruto=re.sub(r'[+＋]\s*\d+','',titulo['texto'])
            if normalizar(bruto)!=alvo:continue
            x0,y0,x1,y1=titulo['caixa']
            # O painel comparativo equipado e identificado separadamente.
            proximas=[t for t in linhas if x0-5<=t['caixa'][0]<=x0+40 and y0<=t['ponto'][1]<y0+340]
            textos=[titulo['texto']]+[t['texto'] for t in proximas if t is not titulo]
            if not any(t['nome'] in ('equipeditem','equippeditem','itemequipado') and y0<t['ponto'][1]<y0+45 and abs(t['caixa'][0]-x0)<15 for t in linhas):return textos
        return []

    def equipamento_sob_cursor(self,tela,ponto=None,escala=1.,nome_esperado=None,ampliar=False):
        if nome_esperado:
            return self.equipamento_esperado(tela,ponto,escala,nome_esperado,ampliar)
        roi=None
        if ponto:
            x,y=ponto;roi=(x-500*escala,y-400*escala,x+370*escala,y+400*escala)
        linhas=self.ler(tela,roi)
        for classe in linhas:
            if not re.search(r'clas[se]{1,2}\s*:',classe['texto'],re.I):continue
            x,y=classe['caixa'][:2]
            painel=[t for t in linhas if abs(t['caixa'][0]-x)<14 and y-75<=t['caixa'][1]<=y+300]
            if any(t['nome'] in ('equipeditem','equippeditem','itemequipado') for t in painel):continue
            anteriores=[t for t in painel if t['caixa'][1]<y-15 and t['texto'].strip() and not t['texto'].startswith('<')]
            if not anteriores:continue
            titulo=min(anteriores,key=lambda t:t['caixa'][1])
            textos=[titulo['texto']]+[t['texto'] for t in painel if t['caixa'][1]>titulo['caixa'][1]]
            from huntingaitan.rotas.servico_npc import avaliar_equipamento
            if avaliar_equipamento(titulo['texto'],textos)[0]:return titulo['texto'],textos
        return None

    def equipamento_esperado(self,tela,ponto,escala,nome,ampliar=False):
        """Localiza Classe por imagem e le somente o painel do nome esperado."""
        self.motivo_descricao='leitura';g=cv2.cvtColor(tela,cv2.COLOR_BGR2GRAY)
        tpl=cv2.resize(self.tpl['npc_classe'],None,fx=escala,fy=escala)
        if g.shape[0]<tpl.shape[0] or g.shape[1]<tpl.shape[1]:return None
        scores=cv2.matchTemplate(g,tpl,cv2.TM_CCOEFF_NORMED)
        # No maximo dois paineis comparativos; descarta duplicatas proximas.
        encontrados=[]
        for _ in range(4):
            _,score,_,(x,y)=cv2.minMaxLoc(scores)
            if score<.84:break
            scores[max(0,y-12):y+13,max(0,x-20):x+21]=-1
            if ponto and (abs(x-ponto[0])>520*escala or abs(y-ponto[1])>420*escala):continue
            encontrados.append((x,y))
        if ponto:encontrados.sort(key=lambda p:abs(p[0]-ponto[0]))
        regioes=[(x-8*escala,y-80*escala,x+320*escala,y+270*escala) for x,y in encontrados]
        if ampliar:
            x,y=ponto;regioes.append((x-500*escala,y-450*escala,x+450*escala,y+400*escala))
        for regiao in regioes:
            linhas=self.ler(tela,regiao)
            titulo=next((t for t in linhas if nome_corresponde(re.sub(r'[+＋]\s*\d+','',t['texto']),nome,getattr(self,'nomes_inventario',()))),None)
            if not titulo:continue
            x0,y0,_,_=titulo['caixa']
            # Quantidades de itens da mochila acima do titulo nao participam.
            textos=[titulo['texto']]+[t['texto'] for t in linhas if t['caixa'][1]>y0+4*escala and abs(t['caixa'][0]-x0)<18*escala]
            from huntingaitan.rotas.servico_npc import avaliar_equipamento
            ok,motivo=avaliar_equipamento(nome,textos)
            if ok:return nome,textos
            self.motivo_descricao=motivo if motivo in ('Equipamento refinado','Painel de equipamento equipado','Item vinculado ou bloqueado') else 'leitura'
        return None
