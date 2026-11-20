"""Extrai os pontos cadastrados de Verit Mutante; nao controla o jogo."""
import argparse,csv,hashlib,io,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont


def extrair(pasta):
    raiz=Path(pasta);nomes=['UI/MN.bin','UI/MobPos.bin','Env/AttributeS01.dat']
    fontes={n:(raiz/n).read_bytes() for n in nomes}
    bruto=fontes['UI/MN.bin'];textos=bytes((v-i)%256 for i,v in enumerate(bruto))
    if len(textos)!=4096*128 or len(fontes['UI/MobPos.bin'])!=4096*416:raise ValueError('Formato das tabelas divergente')
    ids=[i for i in range(4096) if textos[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252')=='Verit Mutante']
    if len(ids)!=1:raise ValueError('Identidade de Verit Mutante ambigua ou ausente')
    id_=ids[0];registro=fontes['UI/MobPos.bin'][id_*416:(id_+1)*416]
    if struct.unpack_from('<I',registro)[0]!=id_ or registro[4:16].split(b'\0')[0]!=f'MOB{id_:05d}'.encode():raise ValueError('Codigo de posicoes divergente')
    atributos=fontes['Env/AttributeS01.dat']
    if len(atributos)!=4096*4096*2:raise ValueError('Grade de terreno divergente')
    pontos=[]
    for i in range(50):
        x,y=struct.unpack_from('<2i',registro,16+i*8)
        if (x,y)==(0,0):continue
        if not (2560<=x<3072 and 512<=y<1024):raise ValueError('Ponto fora dos blocos de Termes esperados')
        flags=struct.unpack_from('<H',atributos,(y*4096+x)*2)[0]
        pontos.append(dict(ponto=len(pontos)+1,slot=i+1,x=x,y=y,flags=flags,celula_livre=not bool(flags&1)))
    return dict(schema=1,mob='Verit Mutante',registro=id_,formato=dict(nomes='MN.bin: 4096 nomes de 128 bytes; decodificacao (byte-offset) mod 256',posicoes='MobPos.bin: 4096 registros de 416 bytes; ID uint32, codigo de 12 bytes, 50 pares XY int32'),pontos=pontos,fontes={n:hashlib.sha256(b).hexdigest() for n,b in fontes.items()},nota='Pontos cadastrados no cliente, nao entidades vivas nem garantia de respawn. Numeracao segue os slots do arquivo, nao uma rota. Celula livre valida apenas a flag estatica do terreno, sem objetos ou passagens entre pontos.')


def textura(arquivo):
    b=arquivo.read_bytes();w,h=struct.unpack_from('<2I',b,4)
    if b[:4]!=b'JT31' or len(b)!=12+w*h//2:raise ValueError('Textura JT31 inesperada')
    header=b'DDS '+struct.pack('<7I',124,0x81007,h,w,len(b)-12,0,0)+bytes(44)+struct.pack('<8I',32,4,0x31545844,0,0,0,0,0)+struct.pack('<5I',0x1000,0,0,0,0)
    return Image.open(io.BytesIO(header+b[12:])).convert('RGB')


def salvar(pasta,saida):
    raiz=Path(pasta);out=Path(saida);out.mkdir(parents=True,exist_ok=True);d=extrair(raiz)
    mosaico=Image.new('RGB',(512,512))
    for ty in [2,3]:
        for tx in [10,11]:
            n=f'Env/MMZ01{tx:02d}{ty:02d}.jit';mosaico.paste(textura(raiz/n),((tx-10)*256,(ty-2)*256));d['fontes'][n]=hashlib.sha256((raiz/n).read_bytes()).hexdigest()
    (out/'verit_termes.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'verit_termes.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(d['pontos'][0]));w.writeheader();w.writerows(d['pontos'])
    canvas=Image.new('RGB',(1500,1020),'#111923');draw=ImageDraw.Draw(canvas)
    def fonte(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    draw.text((38,24),'TERMES | VERIT MUTANTE',font=fonte(34),fill='white')
    draw.text((38,70),'20 pontos cadastrados no cliente | registro 1378',font=fonte(21),fill='#9cc4d7')
    x0,y0,x1,y1=2635,675,3000,955;escala=2.7;px,py=58,155
    recorte=mosaico.crop((x0-2560,y0-512,x1-2560,y1-512)).resize((round((x1-x0)*escala),round((y1-y0)*escala)),Image.Resampling.NEAREST)
    canvas.paste(recorte,(px,py));draw=ImageDraw.Draw(canvas)
    for x in range(2650,3000,50):
        xx=px+round((x-x0)*escala);draw.line((xx,py,xx,py+recorte.height),fill='#48504b',width=1);draw.text((xx-20,py-28),str(x),font=fonte(17),fill='#b4c7d4')
    for y in range(700,951,50):
        yy=py+round((y-y0)*escala);draw.line((px,yy,px+recorte.width,yy),fill='#48504b',width=1);draw.text((8,yy-9),str(y),font=fonte(17),fill='#b4c7d4')
    offsets={5:(-29,-18),20:(32,10),8:(-23,-19),10:(18,14),13:(-24,14)}
    for p in d['pontos']:
        x=px+(p['x']-x0)*escala;y=py+(p['y']-y0)*escala;dx,dy=offsets.get(p['ponto'],(0,0));cx,cy=x+dx,y+dy
        draw.line((x,y,cx,cy),fill='#ffe290',width=2);draw.ellipse((x-3,y-3,x+3,y+3),fill='white')
        draw.ellipse((cx-14,cy-14,cx+14,cy+14),fill='#ffc653',outline='#17202a',width=2)
        draw.text((cx,cy),str(p['ponto']),font=fonte(16),fill='#111923',anchor='mm')
    draw.text((1095,126),'PONTO     X       Y',font=fonte(22),fill='#ffc653')
    for i,p in enumerate(d['pontos']):draw.text((1100,170+i*33),f"{p['ponto']:02d}       {p['x']}    {p['y']}",font=fonte(22),fill='white')
    draw.text((38,944),'Numeros = ordem no arquivo, nao percurso. Fundo = texturas de minimapa do jogo.',font=fonte(20),fill='#c8d7e2')
    draw.text((38,975),'Pontos estaticos: nao indicam monstros vivos. Objetos e passagens ainda exigem validacao.',font=fonte(20),fill='#c8d7e2')
    canvas.save(out/'verit_termes.png')
    print(f"{len(d['pontos'])} pontos; registro {d['registro']}; {sum(p['celula_livre'] for p in d['pontos'])} celulas livres; saida {out.resolve()}")


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args();salvar(a.game_dir,a.out)
