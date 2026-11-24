"""Valida a volta 6 -> 3 -> 7 evitando Croshus nao mutantes; ponto 5 excluido."""
import argparse,hashlib,json,math,struct
from pathlib import Path
from validar_circuito_termes import validar

ORDEM=[6,3,7]
RAIO_MENORES=10

def gerar(pasta):
    raiz=Path(pasta);bruto=(raiz/'UI/MN.bin').read_bytes();nomes=bytes((v-i)%256 for i,v in enumerate(bruto))
    posicoes=(raiz/'UI/MobPos.bin').read_bytes()
    if len(nomes)!=4096*128 or len(posicoes)!=4096*416:raise ValueError('Tabelas divergentes')
    def nome(i):return nomes[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252')
    def pontos(i):
        reg=posicoes[i*416:(i+1)*416]
        if struct.unpack_from('<I',reg)[0]!=i:raise ValueError('Registro de posicoes divergente')
        return [(j+1,struct.unpack_from('<2i',reg,16+j*8)) for j in range(50) if struct.unpack_from('<2i',reg,16+j*8)!=(0,0)]
    if nome(1374)!='Cão Mutante Croshu' or nome(1206)!='Croshu Cinzento' or nome(1207)!='Croshu Canino':raise ValueError('Identidades divergentes')
    cadastro=dict(pontos(1374));selecionados=[(i,cadastro[i]) for i in ORDEM]
    if selecionados!=[(6,(1895,1155)),(3,(1901,1166)),(7,(1950,1127))]:raise ValueError('Posicoes selecionadas mudaram')
    menores=[dict(registro=i,nome=nome(i),slot=j,pos=p) for i in [1206,1207] for j,p in pontos(i)]
    centros=[m['pos'] for m in menores]
    d=validar(pasta,selecionados,'Cão Mutante Croshu',True,exclusoes=centros,raio_exclusao=RAIO_MENORES)
    d.update(fechado=True,registro_mob=1374,mapa='Floresta Ungor',ponto_excluido=5,raio_menores=RAIO_MENORES,menores=menores)
    d['fontes'].update({'UI/MN.bin':hashlib.sha256(bruto).hexdigest(),'UI/MobPos.bin':hashlib.sha256(posicoes).hexdigest()})
    d['nota']='Volta 6 -> 3 -> 7 -> 6. Ponto 5 excluido por proximidade de um menor. Terreno e afastamento de 10 unidades dos cadastros nao mutantes validados; mobs vivos e objetos exigem reconfirmacao.'
    return d

def salvar_mapa(pasta,d,arquivo):
    from PIL import Image,ImageDraw,ImageFont
    from mapear_plantas_ungor import textura_ungor
    x0,y0,x1,y1=1855,1090,1995,1220;escala=6;px,py=65,155
    fundo=textura_ungor(Path(pasta)/'Env/MMZ010704.jit').crop((x0-1792,y0-1024,x1-1792,y1-1024)).resize((840,780),Image.Resampling.NEAREST).convert('RGBA')
    sobre=Image.new('RGBA',fundo.size);g=ImageDraw.Draw(sobre)
    for m in d['menores']:
        x=(m['pos'][0]-x0)*escala;y=(m['pos'][1]-y0)*escala;r=d['raio_menores']*escala
        g.ellipse((x-r,y-r,x+r,y+r),fill=(230,65,65,65),outline=(255,105,105,200),width=2)
    fundo=Image.alpha_composite(fundo,sobre).convert('RGB')
    canvas=Image.new('RGB',(1460,1080),'#111923');canvas.paste(fundo,(px,py));g=ImageDraw.Draw(canvas)
    def fonte(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    def xy(p):return (px+(p[0]-x0)*escala,py+(p[1]-y0)*escala)
    g.text((42,22),'CROSHU UNGOR | 6 → 3 → 7 → 6',font=fonte(34),fill='white')
    g.text((42,74),'Ponto 5 retirado | vermelho: zonas dos menores | ciano: percurso validado',font=fonte(21),fill='#9cc4d7')
    for t in d['trechos']:
        pts=[xy(p) for p in t['caminho']];g.line(pts,fill='#69e2ff',width=5)
        i=len(pts)//2;a,b=pts[max(0,i-2)],pts[min(len(pts)-1,i+2)];ang=math.atan2(b[1]-a[1],b[0]-a[0]);cx,cy=pts[i]
        g.polygon([(cx+12*math.cos(ang),cy+12*math.sin(ang)),(cx+10*math.cos(ang+2.5),cy+10*math.sin(ang+2.5)),(cx+10*math.cos(ang-2.5),cy+10*math.sin(ang-2.5))],fill='white')
    for p in d['pontos']:
        x,y=xy(p['pos']);g.ellipse((x-18,y-18,x+18,y+18),fill='#9aefad',outline='#101820',width=2);g.text((x,y),str(p['id']),font=fonte(20),fill='#101820',anchor='mm')
    x,y=xy((1933,1183));g.line((x-10,y-10,x+10,y+10),fill='white',width=4);g.line((x-10,y+10,x+10,y-10),fill='white',width=4);g.text((x+17,y),'5 excluido',font=fonte(18),fill='white')
    linhas=['PONTOS DA VOLTA','6     1895, 1155','3     1901, 1166','7     1950, 1127','','Somente Cão Mutante Croshu.','5 segundos de busca por parada.','Repete a volta.','','MENORES EVITADOS','Croshu Cinzento','Croshu Canino','','31 posições cadastradas.','Margem: 10 unidades.','Reavalia também os mobs vivos.']
    for i,l in enumerate(linhas):g.text((970,170+i*39),l,font=fonte(22 if i in (0,9) else 20),fill='#9aefad' if i in (0,9) else '#c8d6df')
    g.text((42,984),'Caminho estatico validado; movimentos reais dos mobs e objetos ainda exigem teste no jogo.',font=fonte(22),fill='#b6c8d3')
    destino=Path(arquivo);destino.parent.mkdir(parents=True,exist_ok=True);canvas.save(destino)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);p.add_argument('--mapa');a=p.parse_args()
    d=gerar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if a.mapa:salvar_mapa(a.game_dir,d,a.mapa)
    for t in d['trechos']:print(f"{t['de']} -> {t['ate']}: {len(t['caminho'])} celulas; {t['distancia']} unidades; afastamento validado")
