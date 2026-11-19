"""Deriva a ocupacao dos objetos MS3 posicionados nos DAT da entrada."""
import argparse,base64,hashlib,json,math,re,struct,time,zlib
from pathlib import Path

LIMITES=(2588,1570,2757,1834)

def ler_ms3(raw):
    import numpy as np
    if len(raw)<116 or struct.unpack_from('<I',raw)[0]!=2222:raise ValueError('MS3 desconhecido')
    materiais=struct.unpack_from('<I',raw,28)[0]
    if not 1<=materiais<=64:raise ValueError('Materiais MS3 invalidos')
    luz=struct.unpack_from('<I',raw,12)[0]
    if luz not in (0,1):raise ValueError('Lightmap MS3 desconhecido')
    cab=32+(materiais+luz)*50+2
    originais,nv,nt=struct.unpack_from('<3I',raw,cab);inicio=cab+32
    fim_vertices=inicio+(originais*12+nv*20 if luz else nv*32)
    esperado=fim_vertices+nt*6+materiais*40+2
    if esperado!=len(raw) or not 0<originais<=65535 or not 0<nv<=65535:raise ValueError('Tamanho MS3 divergente')
    if luz:
        pos=np.frombuffer(raw,dtype='<f4',count=originais*3,offset=inicio).reshape(-1,3)
        mapa=np.ndarray((nv,),dtype='<u4',buffer=raw,offset=inicio+originais*12,strides=(20,))
        if mapa.max(initial=0)>=originais:raise ValueError('Indice de posicao MS3 invalido')
        vertices=pos[mapa]
    else:vertices=np.frombuffer(raw,dtype='<f4',count=nv*6,offset=inicio).reshape(-1,6)[:,:3]
    indices=np.frombuffer(raw,dtype='<u2',count=nt*3,offset=fim_vertices).reshape(-1,3)
    if not np.isfinite(vertices).all() or indices.max(initial=0)>=nv:raise ValueError('Geometria MS3 invalida')
    return vertices.astype(float),indices,struct.unpack_from('<I',raw,4)[0]

def transformar(vertices,pos,rot,escala):
    import numpy as np
    yaw,pitch,roll=rot;cy,sy=math.cos(yaw),math.sin(yaw);cx,sx=math.cos(pitch),math.sin(pitch);cz,sz=math.cos(roll),math.sin(roll)
    # D3DX: roll Z, pitch X, yaw Y; Y vertical no modelo.
    ry=np.array(((cy,0,sy),(0,1,0),(-sy,0,cy)))
    rx=np.array(((1,0,0),(0,cx,-sx),(0,sx,cx)))
    rz=np.array(((cz,-sz,0),(sz,cz,0),(0,0,1)))
    return (vertices*escala)@(ry@rx@rz).T+np.array((pos[0],pos[2],pos[1]))

def recortar_y(poly,altura,acima):
    novo=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=a[1]-altura;db=b[1]-altura;ia=da>=0 if acima else da<=0;ib=db>=0 if acima else db<=0
        if ia:novo.append(a)
        if ia!=ib:
            t=da/(da-db);novo.append(tuple(a[j]+t*(b[j]-a[j]) for j in range(3)))
    return novo

def ocupa(poly,p,raio=.6):
    if not poly:return False
    x,y=p;positivo=negativo=False;menor=float('inf')
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ax,ay=a[0],a[2];bx,by=b[0],b[2];dx,dy=bx-ax,by-ay
        cruz=dx*(y-ay)-dy*(x-ax);positivo|=cruz>1e-8;negativo|=cruz< -1e-8
        t=max(0.,min(1.,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy>1e-12 else 0.
        menor=min(menor,math.hypot(x-ax-t*dx,y-ay-t*dy))
    area=abs(sum(a[0]*b[2]-a[2]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))
    return (area>1e-8 and not(positivo and negativo)) or menor<=raio

def gerar(pasta):
    import numpy as np
    pasta=Path(pasta);x0,y0,x1,y1=LIMITES;largura=x1-x0;altura=y1-y0
    hgt=np.frombuffer((pasta/'Env/z01.hgt').read_bytes(),dtype='<i2',offset=4).reshape(4096,4096)
    fontes={};cache={};mascara=np.zeros((altura,largura),np.uint8);inventario=[];ignorados=[]
    def ler(nome):
        raw=(pasta/nome).read_bytes();fontes[nome]=hashlib.sha256(raw).hexdigest();return raw
    nomes={}
    for l in ler('Objects/MeshList.txt').decode('cp949',errors='replace').splitlines():
        m=re.match(r'(\d+)\s+(\S+)',l)
        if m:nomes[int(m[1])]=m[2].replace('\\','/')
    for tx in range(x0//256,(x1-1)//256+1):
        for ty in range(y0//256,(y1-1)//256+1):
            nome=f'Env/z01{tx:02}{ty:02}.dat';raw=ler(nome)
            if raw[:2]!=bytes((tx,ty)) or (len(raw)-2)%40:raise ValueError('DAT divergente: '+nome)
            for off in range(2,len(raw),40):
                mid,*r=struct.unpack_from('<I6fI2f',raw,off)
                pos=(tx*256+r[0],ty*256+r[1],r[2]);rot=r[3:6];escala=r[7]
                modelo=nomes.get(mid)
                if not modelo or not math.isfinite(escala) or not 0<escala<30:continue
                if modelo not in cache:
                    try:cache[modelo]=ler_ms3(ler(modelo))
                    except (OSError,ValueError,struct.error) as e:cache[modelo]=None;ignorados.append(dict(modelo=modelo,motivo=str(e)))
                obj=cache[modelo]
                if obj is None:continue
                vertices,indices,animado=obj
                if animado:continue
                v=transformar(vertices,pos,rot,escala);lo=v.min(axis=0);hi=v.max(axis=0)
                if hi[0]<x0 or lo[0]>x1 or hi[2]<y0 or lo[2]>y1:continue
                antes=int(mascara.sum());triangulos=0
                for ids in indices:
                    t=v[ids]
                    normal=np.cross(t[1]-t[0],t[2]-t[0]);norma=float(np.linalg.norm(normal))
                    # Pisos e rampas do cenario nao sao paredes. A faixa
                    # vertical so rasteriza superficies inclinadas/verticais.
                    if norma<1e-9 or abs(normal[1])/norma>.65:continue
                    bx0=max(x0,math.floor(t[:,0].min()-.6));bx1=min(x1-1,math.floor(t[:,0].max()+.6));by0=max(y0,math.floor(t[:,2].min()-.6));by1=min(y1-1,math.floor(t[:,2].max()+.6))
                    if bx0>bx1 or by0>by1:continue
                    baixo=float(t[:,1].min());alto=float(t[:,1].max());poly0=[tuple(p) for p in t]
                    for y in range(by0,by1+1):
                        for x in range(bx0,bx1+1):
                            if mascara[y-y0,x-x0]:continue
                            chao=float(hgt[y,x])/10
                            if alto<chao+.35 or baixo>chao+1.8:continue
                            poly=recortar_y(recortar_y(poly0,chao+.35,True),chao+1.8,False)
                            if ocupa(poly,(x+.5,y+.5)):mascara[y-y0,x-x0]=1
                    triangulos+=1
                adicionados=int(mascara.sum())-antes
                if adicionados:inventario.append(dict(id=mid,modelo=modelo,pos=pos,rot=rot,escala=escala,celulas=adicionados))
    ler('Env/AttributeS01.dat');ler('Env/z01.hgt')
    return dict(schema=1,limites=LIMITES,largura=largura,altura=altura,mascara=base64.b64encode(zlib.compress(mascara.tobytes(),9)).decode(),fontes=fontes,objetos=inventario,ignorados=ignorados,criterio='Triangulos estaticos na faixa de .35 a 1.8 acima do terreno, margem horizontal .6; geometrias animadas excluidas.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args();inicio=time.time();d=gerar(a.game_dir);Path(a.out).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print('Objetos',len(d['objetos']),'modelos nao lidos',len(d['ignorados']),'tempo',round(time.time()-inicio,1),'s')
