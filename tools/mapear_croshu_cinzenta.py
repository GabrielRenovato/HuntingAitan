"""Mapeia os Croshus Mutantes das Cinzas cadastrados no cliente, sem controlar o jogo."""
import argparse,csv,hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from mapear_verit_termes import textura


def salvar(pasta,saida):
    raiz=Path(pasta);out=Path(saida);out.mkdir(parents=True,exist_ok=True)
    fontes={}
    def ler(nome):
        b=(raiz/nome).read_bytes();fontes[nome]=hashlib.sha256(b).hexdigest();return b
    nomes=ler('UI/MN.bin');nomes=bytes((v-i)%256 for i,v in enumerate(nomes))
    posicoes=ler('UI/MobPos.bin');mapas=ler('UI/Map.bin');atributos=ler('Env/AttributeS01.dat')
    if len(nomes)!=4096*128 or len(posicoes)!=4096*416 or len(atributos)!=4096*4096*2:
        raise ValueError('Formato das tabelas diferente do validado')
    ids=[i for i in range(4096) if nomes[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252')=='Croshu Mutante das Cinzas']
    if len(ids)!=1:raise ValueError('Identidade de Croshu Mutante das Cinzas ausente ou ambigua')
    id_=ids[0];registro=posicoes[id_*416:(id_+1)*416]
    if struct.unpack_from('<I',registro)[0]!=id_ or registro[4:16].split(b'\0')[0]!=f'MOB{id_:05d}'.encode():
        raise ValueError('Cabecalho das posicoes divergente')
    setor=13;limites=struct.unpack_from('<4i',mapas,setor*16)
    if limites!=(2560,1024,3070,1534):raise ValueError('Limites do setor da floresta divergentes')
    nome_cliente=mapas[0x400+setor*64:0x400+(setor+1)*64].split(b'\0')[0].decode('cp1252')
    pontos=[]
    for i in range(50):
        x,y=struct.unpack_from('<2i',registro,16+i*8)
        if (x,y)==(0,0):continue
        if not (limites[0]<=x<=limites[2] and limites[1]<=y<=limites[3]):
            raise ValueError('Posicao fora do setor da Floresta Cinzenta')
        flags=struct.unpack_from('<H',atributos,(y*4096+x)*2)[0]
        pontos.append(dict(ponto=len(pontos)+1,slot=i+1,x=x,y=y,flags=flags,celula_livre=not bool(flags&1)))
    if not pontos:raise ValueError('Nenhuma posicao cadastrada')
    mosaico=Image.new('RGB',(512,512))
    for ty in [4,5]:
        for tx in [10,11]:
            att=ler(f'Env/z01{tx:02d}{ty:02d}.att')
            if len(att)!=256*256*2:raise ValueError('Tile de colisao com tamanho divergente')
            for y in range(256):
                off=((ty*256+y)*4096+tx*256)*2
                if att[y*512:(y+1)*512]!=atributos[off:off+512]:raise ValueError('Orientacao XY do terreno divergente')
            nome=f'Env/MMZ01{tx:02d}{ty:02d}.jit';ler(nome)
            mosaico.paste(textura(raiz/nome),((tx-10)*256,(ty-4)*256))
    d=dict(schema=1,mapa='Floresta Cinzenta',nome_setor_cliente=nome_cliente,setor=setor,
           limites=list(limites),mob='Croshu Mutante das Cinzas',registro=id_,pontos=pontos,fontes=fontes,
           identificacao='Pedido: Croshu roxo mutante da Floresta Cinzenta. Nome do cadastro: Croshu Mutante das Cinzas. Cor do modelo nao confirmada pela tabela.',
           nota='Todas as posicoes nao vazias do registro do cliente; nao representam monstros vivos, quantidade simultanea ou garantia de respawn. Numeros seguem os slots, nao uma rota. Celula livre valida apenas a flag estatica do terreno, sem objetos ou passagens entre pontos.')
    (out/'croshu_cinzenta.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'croshu_cinzenta.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(pontos[0]));w.writeheader();w.writerows(pontos)
    canvas=Image.new('RGB',(1580,1220),'#111923');draw=ImageDraw.Draw(canvas)
    def fonte(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    draw.text((42,22),'FLORESTA CINZENTA | CROSHU MUTANTE DAS CINZAS',font=fonte(34),fill='white')
    draw.text((42,70),f'{len(pontos)} pontos cadastrados no cliente | registro {id_}',font=fonte(22),fill='#9cc4d7')
    px,py,escala=65,145,2
    canvas.paste(mosaico.resize((1024,1024),Image.Resampling.NEAREST),(px,py));draw=ImageDraw.Draw(canvas)
    for x in range(2600,3051,50):
        xx=px+(x-2560)*escala;draw.line((xx,py,xx,py+1024),fill='#454d47');draw.text((xx,py-22),str(x),font=fonte(16),fill='#d6e0e7',anchor='mm')
    for y in range(1050,1501,50):
        yy=py+(y-1024)*escala;draw.line((px,yy,px+1024,yy),fill='#454d47');draw.text((px-8,yy),str(y),font=fonte(16),fill='#d6e0e7',anchor='rm')
    for p in pontos:
        x=px+(p['x']-2560)*escala;y=py+(p['y']-1024)*escala
        dx,dy={}.get(p['ponto'],(0,0));cx,cy=x+dx,y+dy
        if dx or dy:
            draw.line((x,y,cx,cy),fill='white',width=2);draw.ellipse((x-2,y-2,x+2,y+2),fill='white')
        draw.ellipse((cx-16,cy-16,cx+16,cy+16),fill='#bd94ff',outline='#101820',width=2)
        draw.text((cx,cy),str(p['ponto']),font=fonte(18),fill='#101820',anchor='mm')
    draw.text((1130,150),'PONTO       X          Y',font=fonte(23),fill='#bd94ff')
    for i,p in enumerate(pontos):
        draw.text((1130,200+i*48),f"{p['ponto']:02d}          {p['x']}      {p['y']}",font=fonte(24),fill='white')
    linhas=['Pontos do arquivo MobPos.bin.', 'Fundo: minimapa original do jogo.', '',
            'Todos os 50 slots foram lidos.',f'{len(pontos)} preenchidos; {50-len(pontos)} vazios.', '',
            f"{sum(p['celula_livre'] for p in pontos)}/{len(pontos)} celulas sem bloqueio",'na flag estatica do terreno.', '',
            'Nao e uma rota de navegacao.', 'Nao indica mobs vivos agora.', 'Objetos exigem validacao.']
    for i,l in enumerate(linhas):draw.text((1130,735+i*30),l,font=fonte(20),fill='#b6c8d3')
    canvas.save(out/'croshu_cinzenta.png')
    print(json.dumps(dict(registro=id_,total=len(pontos),celulas_livres=sum(p['celula_livre'] for p in pontos),pontos=pontos,saida=str(out.resolve())),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();salvar(a.game_dir,a.out)
