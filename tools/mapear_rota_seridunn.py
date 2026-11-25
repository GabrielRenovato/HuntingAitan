"""Deriva o acesso a area final usando terreno e geometria do cliente, sem inventar spawns."""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.validar_jardim_aereo import carregar_grade
from huntingaitan.rotas.geometria_dg_jardim import GeometriaDGJardim
from huntingaitan.rotas.jardim_aereo import conferir_fontes_jardim,plano_jardim


def mapear(pasta):
    p=Path(pasta);conferir_fontes_jardim(p)
    objetos=(p/'Env/z011412.dat').read_bytes()
    altares=[struct.unpack_from('<3f',objetos,o+4) for o in range(2,len(objetos),40) if struct.unpack_from('<I',objetos,o)[0]==3721]
    if len(altares)!=1:raise ValueError('Referencia da area final divergente')
    altar=(3584+altares[0][0],3072+altares[0][1]);terreno=carregar_grade(p)
    grade=GeometriaDGJardim(p).aplicar(terreno)
    rota=grade.caminho((3351,3295),altar,alcance=8,max_nos=131072)
    if not rota or not all(grade.passagem(grade.celula(a),grade.celula(b)) for a,b in zip(rota,rota[1:])):
        raise ValueError('Sem caminho estatico conferido ate a area final')
    bruto=(p/'UI/MN.bin').read_bytes();nomes=bytes((v-i)%256 for i,v in enumerate(bruto));pos=(p/'UI/MobPos.bin').read_bytes();chefes=[]
    for i in range(4096):
        nome=nomes[i*128:(i+1)*128].split(b'\0')[0].decode('cp1252',errors='replace')
        if nome.lower()=='seridunn':
            r=pos[i*416:(i+1)*416]
            pontos=[struct.unpack_from('<ii',r,16+n*8) for n in range(50)]
            chefes.append(dict(template_id=i,pontos=[q for q in pontos if q!=(0,0)]))
    return dict(schema=1,nome='Jardim Aereo de Mirza - acesso a Seridunn',chefe='seridunn',objetivo='seridunn',
        dificuldade='dificil',registro_dificil=21,origem=[3328,3072],entrada=[3351,3295],limites=[3328,3072,3840,3328],
        fontes=plano_jardim()['fontes'],referencia_area_final=altar,posicao_chefe_confirmada=False,catalogo_seridunn=chefes,
        fontes_catalogo={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['UI/MN.bin','UI/MobPos.bin']},
        pontos=[dict(id='seridunn',pos=rota[-1],chefe='seridunn',espera=0)],
        trechos=[dict(ate='seridunn',caminho=rota,distancia=round(sum(math.dist(a,b) for a,b in zip(rota,rota[1:])),2))],
        criterio='Navegar ate a area final; reconhecer Seridunn ao vivo e confirmar vida zero. Ignorar hostis laterais; combater bloqueadores proximos ou por defesa. O altar e referencia de area, nao spawn confirmado do chefe.')


def desenhar(plano,pasta,arquivo):
    from PIL import Image,ImageDraw
    grade=carregar_grade(pasta);im=Image.new('RGB',(512,256));px=im.load()
    for y in range(256):
        for x in range(512):px[x,y]=(65,83,72) if grade.livre((x,y)) else (18,23,26)
    d=ImageDraw.Draw(im);pontos=[(x-3328,y-3072) for x,y in plano['trechos'][0]['caminho']]
    d.line(pontos,fill=(255,200,65),width=2)
    for ponto,cor in [(plano['entrada'],(70,240,120)),(plano['referencia_area_final'],(255,80,90))]:
        x,y=ponto[0]-3328,ponto[1]-3072;d.ellipse((x-3,y-3,x+3,y+3),fill=cor)
    im=im.resize((1536,768),Image.Resampling.NEAREST);d=ImageDraw.Draw(im)
    d.text((15,15),'Verde: entrada | Vermelho: altar da area final | Amarelo: caminho no terreno',fill='white')
    im.save(arquivo)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--game-dir',required=True);a.add_argument('--out',required=True);a.add_argument('--imagem');args=a.parse_args()
    plano=mapear(args.game_dir);Path(args.out).write_text(json.dumps(plano,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.imagem:desenhar(plano,args.game_dir,args.imagem)
    print(json.dumps(dict(destino=plano['pontos'][0]['pos'],altar=plano['referencia_area_final'],distancia=plano['trechos'][0]['distancia'],celulas=len(plano['trechos'][0]['caminho']),spawns_seridunn=plano['catalogo_seridunn']),ensure_ascii=False))
