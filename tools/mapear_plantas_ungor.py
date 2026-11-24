"""Extrai todas as posicoes cadastradas de Planta Carnivora Mutante em Ungor."""
import argparse,csv,hashlib,io,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from mapear_verit_termes import textura


def textura_ungor(arquivo):
    b=arquivo.read_bytes()
    if b[:4]==b'JT31':return textura(arquivo)
    w,h=struct.unpack_from('<2I',b,4)
    if b[:4]!=b'JT33' or len(b)!=12+w*h:raise ValueError('Formato de textura inesperado')
    header=b'DDS '+struct.pack('<7I',124,0x81007,h,w,len(b)-12,0,0)+bytes(44)+struct.pack('<8I',32,4,0x33545844,0,0,0,0,0)+struct.pack('<5I',0x1000,0,0,0,0)
    return Image.open(io.BytesIO(header+b[12:])).convert('RGB')


def salvar(pasta,saida):
    raiz=Path(pasta);out=Path(saida);out.mkdir(parents=True,exist_ok=True);fontes={}
    def ler(nome):
        b=(raiz/nome).read_bytes();fontes[nome]=hashlib.sha256(b).hexdigest();return b
    bruto=ler('UI/MN.bin');nomes=bytes((v-i)%256 for i,v in enumerate(bruto))
    posicoes=ler('UI/MobPos.bin');mapas=ler('UI/Map.bin');atributos=ler('Env/AttributeS01.dat')
    if len(nomes)!=4096*128 or len(posicoes)!=4096*416 or len(atributos)!=4096*4096*2:
        raise ValueError('Formato das tabelas divergente')
    mob='Planta Carnívora Mutante'
    ids=[i for i in range(4096) if nomes[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252')==mob]
    setores=[i for i in range(64) if mapas[0x400+i*64:0x400+(i+1)*64].split(b'\0')[0].decode('cp1252')=='Bosque de Ungor']
    if len(ids)!=1 or len(setores)!=1:raise ValueError('Nome do mob ou setor ausente/ambiguo')
    id_=ids[0];setor=setores[0];limites=struct.unpack_from('<4i',mapas,setor*16)
    if limites!=(1792,1024,2556,1534):raise ValueError('Limites de Ungor divergentes')
    registro=posicoes[id_*416:(id_+1)*416]
    if struct.unpack_from('<I',registro)[0]!=id_ or registro[4:16].split(b'\0')[0]!=f'MOB{id_:05d}'.encode():
        raise ValueError('Cabecalho das posicoes divergente')
    pontos=[]
    for i in range(50):
        x,y=struct.unpack_from('<2i',registro,16+i*8)
        if (x,y)==(0,0):continue
        if not (limites[0]<=x<=limites[2] and limites[1]<=y<=limites[3]):
            raise ValueError('Posicao da especie fora de Ungor: reavalie o escopo antes de exportar')
        flags=struct.unpack_from('<H',atributos,(y*4096+x)*2)[0]
        pontos.append(dict(ponto=len(pontos)+1,slot=i+1,x=x,y=y,flags=flags,celula_livre=not bool(flags&1)))
    if not pontos:raise ValueError('Nenhuma posicao cadastrada')
    tx0,ty0=limites[0]//256,limites[1]//256
    tx1,ty1=limites[2]//256,limites[3]//256
    mosaico=Image.new('RGB',((tx1-tx0+1)*256,(ty1-ty0+1)*256))
    for tx in range(tx0,tx1+1):
        for ty in range(ty0,ty1+1):
            att=ler(f'Env/z01{tx:02d}{ty:02d}.att')
            if len(att)!=256*256*2:raise ValueError('Tile de colisao com tamanho divergente')
            for y in range(256):
                off=((ty*256+y)*4096+tx*256)*2
                if att[y*512:(y+1)*512]!=atributos[off:off+512]:raise ValueError('Orientacao XY divergente')
            nome=f'Env/MMZ01{tx:02d}{ty:02d}.jit';ler(nome)
            mosaico.paste(textura_ungor(raiz/nome),((tx-tx0)*256,(ty-ty0)*256))
    d=dict(schema=1,mapa='Floresta Ungor',nome_setor_cliente='Bosque de Ungor',setor=setor,limites=list(limites),mob=mob,registro=id_,pontos=pontos,fontes=fontes,
           nota='Todas as posicoes nao vazias da especie no cadastro do cliente. Nao representam monstros vivos, quantidade simultanea, tempo de respawn nem eventuais spawns exclusivos do servidor. Numeracao segue os slots, nao uma rota. Celula livre nao garante ausencia de objetos ou passagem entre pontos.')
    (out/'plantas_ungor.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'plantas_ungor.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(pontos[0]));w.writeheader();w.writerows(pontos)
    canvas=Image.new('RGB',(1770,1080),'#111923');draw=ImageDraw.Draw(canvas)
    def fonte(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    draw.text((42,22),'FLORESTA UNGOR | PLANTA CARNÍVORA MUTANTE',font=fonte(34),fill='white')
    draw.text((42,72),f'{len(pontos)} pontos cadastrados no cliente | registro {id_} | setor {setor}: Bosque de Ungor',font=fonte(22),fill='#9cc4d7')
    px,py,escala=65,150,1.6
    fundo=mosaico.resize((round(mosaico.width*escala),round(mosaico.height*escala)),Image.Resampling.NEAREST)
    canvas.paste(fundo,(px,py));draw=ImageDraw.Draw(canvas)
    for x in range(1800,2551,50):
        xx=px+round((x-tx0*256)*escala);draw.line((xx,py,xx,py+fundo.height),fill='#454d47');draw.text((xx,py-22),str(x),font=fonte(16),fill='#d6e0e7',anchor='mm')
    for y in range(1050,1501,50):
        yy=py+round((y-ty0*256)*escala);draw.line((px,yy,px+fundo.width,yy),fill='#454d47');draw.text((px-8,yy),str(y),font=fonte(16),fill='#d6e0e7',anchor='rm')
    for p in pontos:
        x=px+(p['x']-tx0*256)*escala;y=py+(p['y']-ty0*256)*escala
        draw.ellipse((x-15,y-15,x+15,y+15),fill='#85e29c',outline='#101820',width=2)
        draw.text((x,y),str(p['ponto']),font=fonte(17),fill='#101820',anchor='mm')
    draw.text((1340,155),'PONTO       X          Y',font=fonte(23),fill='#85e29c')
    for i,p in enumerate(pontos):draw.text((1340,205+i*48),f"{p['ponto']:02d}          {p['x']}      {p['y']}",font=fonte(24),fill='white')
    linhas=['50 slots lidos: 10 preenchidos.', 'Fundo: minimapa original do jogo.', '',
            f"{sum(p['celula_livre'] for p in pontos)}/{len(pontos)} celulas sem bloqueio",'na flag estatica do terreno.', '',
            'Nao indica plantas vivas agora.', 'Numeros nao definem uma rota.']
    for i,l in enumerate(linhas):draw.text((1340,755+i*30),l,font=fonte(20),fill='#b6c8d3')
    draw.text((42,1010),'Orientacao conferida em seis tiles de terreno. Arvores, objetos e passagens ainda exigem validacao.',font=fonte(22),fill='#b6c8d3')
    canvas.save(out/'plantas_ungor.png')
    print(json.dumps(dict(registro=id_,setor=setor,total=len(pontos),celulas_livres=sum(p['celula_livre'] for p in pontos),pontos=pontos,saida=str(out.resolve())),ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();salvar(a.game_dir,a.out)
