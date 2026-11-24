"""Mapeia Cao Mutante Croshu em Ungor; a cor do modelo nao e inferida da tabela de nomes."""
import argparse,csv,hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from mapear_plantas_ungor import textura_ungor


def salvar(pasta,saida):
    raiz=Path(pasta);out=Path(saida);out.mkdir(parents=True,exist_ok=True);fontes={}
    def ler(nome):
        b=(raiz/nome).read_bytes();fontes[nome]=hashlib.sha256(b).hexdigest();return b
    bruto=ler('UI/MN.bin');nomes=bytes((v-i)%256 for i,v in enumerate(bruto))
    posicoes=ler('UI/MobPos.bin');mapas=ler('UI/Map.bin');atributos=ler('Env/AttributeS01.dat')
    if len(nomes)!=4096*128 or len(posicoes)!=4096*416 or len(atributos)!=4096*4096*2:raise ValueError('Formato das tabelas divergente')
    mob='Cão Mutante Croshu'
    ids=[i for i in range(4096) if nomes[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252')==mob]
    setores=[i for i in range(64) if mapas[0x400+i*64:0x400+(i+1)*64].split(b'\0')[0].decode('cp1252')=='Bosque de Ungor']
    if len(ids)!=1 or len(setores)!=1:raise ValueError('Identidade ou setor ambiguo/ausente')
    id_=ids[0];setor=setores[0];limites=struct.unpack_from('<4i',mapas,setor*16)
    if limites!=(1792,1024,2556,1534):raise ValueError('Limites de Ungor divergentes')
    registro=posicoes[id_*416:(id_+1)*416]
    if struct.unpack_from('<I',registro)[0]!=id_ or registro[4:16].split(b'\0')[0]!=f'MOB{id_:05d}'.encode():raise ValueError('Cabecalho divergente')
    pontos=[]
    for i in range(50):
        x,y=struct.unpack_from('<2i',registro,16+i*8)
        if (x,y)==(0,0):continue
        if not (limites[0]<=x<=limites[2] and limites[1]<=y<=limites[3]):raise ValueError('Ponto fora de Ungor')
        flags=struct.unpack_from('<H',atributos,(y*4096+x)*2)[0]
        pontos.append(dict(ponto=len(pontos)+1,slot=i+1,x=x,y=y,flags=flags,celula_livre=not bool(flags&1)))
    if not pontos:raise ValueError('Sem posicoes cadastradas')
    mosaico=Image.new('RGB',(768,512))
    for tx in [7,8,9]:
        for ty in [4,5]:
            att=ler(f'Env/z01{tx:02d}{ty:02d}.att')
            if len(att)!=256*256*2:raise ValueError('Tamanho do tile divergente')
            for y in range(256):
                off=((ty*256+y)*4096+tx*256)*2
                if att[y*512:(y+1)*512]!=atributos[off:off+512]:raise ValueError('Orientacao XY divergente')
            nome=f'Env/MMZ01{tx:02d}{ty:02d}.jit';ler(nome)
            mosaico.paste(textura_ungor(raiz/nome),((tx-7)*256,(ty-4)*256))
    d=dict(schema=1,mapa='Floresta Ungor',nome_setor_cliente='Bosque de Ungor',setor=setor,limites=list(limites),mob=mob,registro=id_,pontos=pontos,fontes=fontes,
           identificacao='Pedido: Croshu azul mutante. O nome exato desta especie no cliente e Cao Mutante Croshu; a cor do modelo nao foi confirmada visualmente.',
           nota='Todas as posicoes nao vazias desta especie no cadastro do cliente. Nao representam monstros vivos, quantidade simultanea, respawn nem eventuais spawns exclusivos do servidor. Numeracao segue os slots, nao uma rota. Celula livre nao garante passagem entre pontos.')
    (out/'croshu_ungor.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'croshu_ungor.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(pontos[0]));w.writeheader();w.writerows(pontos)
    canvas=Image.new('RGB',(1460,1090),'#111923');draw=ImageDraw.Draw(canvas)
    def fonte(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    draw.text((42,22),'FLORESTA UNGOR | CÃO MUTANTE CROSHU',font=fonte(34),fill='white')
    draw.text((42,72),f'{len(pontos)} pontos cadastrados | registro {id_} | detalhe do noroeste de Ungor',font=fonte(22),fill='#9cc4d7')
    x0,y0,x1,y1=1855,1090,1995,1220;px,py,escala=65,155,6
    if not all(x0<p['x']<x1 and y0<p['y']<y1 for p in pontos):raise ValueError('Ajuste o enquadramento para incluir os novos pontos')
    fundo=mosaico.crop((x0-1792,y0-1024,x1-1792,y1-1024)).resize(((x1-x0)*escala,(y1-y0)*escala),Image.Resampling.NEAREST)
    canvas.paste(fundo,(px,py));draw=ImageDraw.Draw(canvas)
    for x in range(1860,1991,20):
        xx=px+(x-x0)*escala;draw.line((xx,py,xx,py+fundo.height),fill='#454d47');draw.text((xx,py-22),str(x),font=fonte(17),fill='#d6e0e7',anchor='mm')
    for y in range(1100,1220,20):
        yy=py+(y-y0)*escala;draw.line((px,yy,px+fundo.width,yy),fill='#454d47');draw.text((px-8,yy),str(y),font=fonte(17),fill='#d6e0e7',anchor='rm')
    for p in pontos:
        x=px+(p['x']-x0)*escala;y=py+(p['y']-y0)*escala
        draw.ellipse((x-17,y-17,x+17,y+17),fill='#73d9f0',outline='#101820',width=2)
        draw.text((x,y),str(p['ponto']),font=fonte(19),fill='#101820',anchor='mm')
    draw.text((975,158),'PONTO       X          Y',font=fonte(23),fill='#73d9f0')
    for i,p in enumerate(pontos):draw.text((975,208+i*48),f"{p['ponto']:02d}          {p['x']}      {p['y']}",font=fonte(24),fill='white')
    draw.text((975,592),'LOCALIZAÇÃO EM UNGOR',font=fonte(22),fill='#73d9f0')
    ox,oy=975,640;canvas.paste(mosaico.resize((384,256),Image.Resampling.NEAREST),(ox,oy));draw=ImageDraw.Draw(canvas)
    draw.rectangle((ox+(x0-1792)/2,oy+(y0-1024)/2,ox+(x1-1792)/2,oy+(y1-1024)/2),outline='#73d9f0',width=3)
    draw.text((975,919),f"{sum(p['celula_livre'] for p in pontos)}/{len(pontos)} celulas sem bloqueio estatico.",font=fonte(20),fill='#b6c8d3')
    draw.text((42,988),'Nome do cadastro: Cão Mutante Croshu. A cor do modelo ainda não foi confirmada.',font=fonte(22),fill='#b6c8d3')
    draw.text((42,1030),'Posições do cliente; não indicam mobs vivos agora nem uma rota livre de objetos.',font=fonte(22),fill='#b6c8d3')
    canvas.save(out/'croshu_ungor.png')
    print(json.dumps(dict(registro=id_,total=len(pontos),pontos=pontos,saida=str(out.resolve())),ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args();salvar(a.game_dir,a.out)
