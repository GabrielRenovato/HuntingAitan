"""Leitor somente leitura, limitado ao layout de AIKACL.exe verificado por hash."""
from huntingaitan.recursos import DADOS
import ctypes,struct,math,hashlib,json
from ctypes import wintypes as w
from pathlib import Path
P=DADOS

class MODULEENTRY32W(ctypes.Structure):
    _fields_=[('dwSize',w.DWORD),('th32ModuleID',w.DWORD),('th32ProcessID',w.DWORD),('GlblcntUsage',w.DWORD),('ProccntUsage',w.DWORD),('modBaseAddr',ctypes.POINTER(ctypes.c_ubyte)),('modBaseSize',w.DWORD),('hModule',w.HMODULE),('szModule',w.WCHAR*256),('szExePath',w.WCHAR*260)]

class DadosInternos:
    def __init__(self):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True);self.u=ctypes.WinDLL('user32',use_last_error=True);self.handle=None
        self.u.FindWindowW.argtypes=[w.LPCWSTR,w.LPCWSTR];self.u.FindWindowW.restype=w.HWND
        self.u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        self.k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];self.k.OpenProcess.restype=w.HANDLE
        self.k.ReadProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];self.k.ReadProcessMemory.restype=w.BOOL
        self.k.CloseHandle.argtypes=[w.HANDLE];self.k.CloseHandle.restype=w.BOOL
        self.k.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];self.k.CreateToolhelp32Snapshot.restype=w.HANDLE
        self.k.Module32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(MODULEENTRY32W)];self.k.Module32NextW.argtypes=self.k.Module32FirstW.argtypes
        h=self.u.FindWindowW(None,'AikaClient');pid=w.DWORD()
        if not h:raise RuntimeError('Abra o Aika antes de ler os dados internos.')
        self.hwnd=h
        self.u.GetWindowThreadProcessId(h,ctypes.byref(pid))
        self.handle=self.k.OpenProcess(0x410,False,pid.value)
        if not self.handle:raise RuntimeError('Leitura interna: acesso negado. Abra este aplicativo como administrador.')
        try:
            snap=self.k.CreateToolhelp32Snapshot(0x18,pid.value)
            if snap==ctypes.c_void_p(-1).value:raise RuntimeError('Nao foi possivel identificar o modulo do Aika.')
            try:
                e=MODULEENTRY32W();e.dwSize=ctypes.sizeof(e);ok=self.k.Module32FirstW(snap,ctypes.byref(e));self.base=None
                while ok:
                    if e.szModule.lower()=='aikacl.exe':
                        self.base=ctypes.cast(e.modBaseAddr,ctypes.c_void_p).value;self.caminho=Path(e.szExePath);break
                    ok=self.k.Module32NextW(snap,ctypes.byref(e))
            finally:self.k.CloseHandle(snap)
            if self.base is None:raise RuntimeError('Modulo AIKACL.exe nao encontrado.')
            self.layout=json.loads((P/'native_layout.json').read_text())
            if hashlib.sha256(self.caminho.read_bytes()).hexdigest()!=self.layout['sha256']:raise RuntimeError('O cliente Aika mudou de versao. O layout interno precisa ser validado novamente.')
        except Exception:self.close();raise
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None
    def read(self,address,size):
        if not 0x10000<=address<=0xffff0000 or not 1<=size<=8192:raise RuntimeError('Endereco interno fora dos limites esperados.')
        buf=ctypes.create_string_buffer(size);n=ctypes.c_size_t()
        if not self.k.ReadProcessMemory(self.handle,address,buf,size,ctypes.byref(n)) or n.value!=size:raise RuntimeError('Dado interno indisponivel. O personagem pode estar carregando o mapa.')
        return buf.raw
    def u32(self,a):return struct.unpack('<I',self.read(a,4))[0]
    def entidade(self,ptr):
        if not ptr:return None
        # Campos usados pela validacao de alvo e pelo calculo de HP/MP do assistente.
        id_=self.u32(ptr+4);pos=struct.unpack('<3f',self.read(ptr+0x1c,12));hp,hpmax,mp,mpmax=struct.unpack('<4i',self.read(ptr+0x498,16))
        if not all(math.isfinite(v) and abs(v)<100000 for v in pos):raise RuntimeError('Coordenadas internas nao passaram na validacao.')
        if not 0<=hp<=hpmax<=100000000 or hpmax==0 or not 0<=mp<=mpmax<=100000000:raise RuntimeError('HP/MP internos nao passaram na validacao.')
        nome=self.read(ptr+0x19ac,128).split(b'\0')[0].decode('cp1252',errors='replace')
        status=struct.unpack('<H',self.read(ptr+0x134,2))[0]
        hostil=0x800<=id_<0x2800 and status==0
        rotacao=struct.unpack('<f',self.read(ptr+0x28,4))[0]
        heading=math.degrees(rotacao)%360 if math.isfinite(rotacao) and abs(rotacao)<100000 else None
        return dict(ref=ptr,id=id_,name=nome,position=pos[:2],height=pos[2],heading=heading,hp=hp,hp_max=hpmax,mp=mp,mp_max=mpmax,hostile=hostil)
    def cena_validada(self):
        cena=self.u32(self.base+self.layout['active_scene_rva'])
        if not cena or self.u32(cena)!=self.base+self.layout['scene_vtable_rva']:
            raise RuntimeError('Cena indisponivel para leitura')
        return cena
    def estados_controle(self):
        # 0x4f2125..4f21e3: consulta efeitos 73/219/235 antes da skill.
        contexto=self.u32(self.base+0x2f9b1e0-0x400000);raiz=contexto+0x7fea0
        ids=set()
        for offset in (0xd4,0x11b8,0x1230):
            ids.update(v for v in struct.unpack('<20h',self.read(raiz+offset,40)) if 0<v<12000)
        cache=getattr(self,'_efeitos_cache',{})
        ativos={73:0,219:0,235:0};causas=[]
        for skill in ids:
            if skill not in cache:
                # 0x428830: quatro tipos e quatro magnitudes, stride 0x2d0.
                raw=self.read(self.base+0xf9c1f4-0x400000+skill*0x2d0,32)
                cache[skill]=struct.unpack('<8i',raw)
            valores=cache[skill];relevante=False
            for tipo,valor in zip(valores[:4],valores[4:]):
                if tipo in ativos and valor>0:ativos[tipo]=max(ativos[tipo],valor);relevante=True
            if relevante:causas.append(skill)
        self._efeitos_cache=cache
        cena=self.cena_validada();player=self.u32(cena+0x104)
        skill,tick=self.u32(cena+0xdb1a8),self.u32(cena+0xdb1bc)
        barra=self.u32(cena+0x4170);item=self.u32(barra+0x1f4) if barra else 0
        normal=struct.unpack('<h',self.read(item+0x538,2))[0] if item else None
        cd=None
        if normal and 0<normal<12000:
            grupo=((normal-1)%960)//16
            if grupo<=42:
                valor=struct.unpack('<f',self.read(contexto+0x8bda0+grupo*4,4))[0]
                if math.isfinite(valor):cd=valor
        return dict(stunned=bool(ativos[73]),paralyzed=bool(ativos[219]),frozen=bool(ativos[235]),effects=ativos,skill_ids=sorted(causas),animation=self.read(player+0x1e0,1)[0],casting=bool(tick and 0<skill<12000),casting_skill=skill if 0<skill<12000 else None,casting_token=tick,normal_skill=normal,normal_cooldown=cd,normal_ready=(cd==0) if cd is not None else None)

    def caca_original_ativa(self):
        cena=self.cena_validada();assistente=self.u32(cena+0xeadf4)
        return bool(assistente and self.u32(assistente+0x1f4))
    def recargas_atalhos(self):
        from huntingaitan.leitura.recargas_barra import decodificar
        contexto=self.u32(self.base+0x2f9b1e0-0x400000)
        gestor=self.u32(self.base+0x322669c-0x400000)
        modo=self.u32(gestor+0x614)
        endereco=contexto+0x8129c
        if modo==1:
            nome=self.read(contexto+0x7fea4,128).split(b'\0')[0]
            inicio,fim=struct.unpack('<2I',self.read(gestor+0x620,8))
            if not nome or fim<inicio or (fim-inicio)%0x120 or (fim-inicio)//0x120>256:
                raise RuntimeError('Perfil da barra indisponivel')
            endereco=None
            for indice in range((fim-inicio)//0x120):
                registro=inicio+indice*0x120
                if self.read(registro,128).split(b'\0')[0]==nome:
                    endereco=registro+128;break
            if endereco is None:raise RuntimeError('Barra do personagem nao encontrada')
        slots=struct.unpack('<40I',self.read(endereco,160))
        self.tipos_atalhos={str(i+1):raw&15 for i,raw in enumerate(slots[:8])}
        recargas=struct.unpack('<43f',self.read(contexto+0x8bda0,172))
        return decodificar(slots,recargas)
    def camera_regional(self):
        # Camera usada no setor de selecao em 0x50a021 e 0x50a0ef.
        contexto=self.u32(self.base+0x2f9b1e0-0x400000)
        cam=self.u32(contexto+0x8d2a8)
        yaw=struct.unpack('<f',self.read(cam+8,4))[0]
        pos=struct.unpack('<3f',self.read(cam+0x28,12))
        if not all(math.isfinite(v) and abs(v)<100000 for v in (*pos,yaw)):
            raise RuntimeError('Camera fora dos limites validados')
        return dict(yaw=math.degrees(yaw)%360,position=(pos[0],pos[2]))

    def listar_mobs(self,centro,raio,player):
        # 0x50a1e4: scene+94 -> manager+18; slots contiguos de 0x39bc.
        cena=self.u32(self.base+self.layout['active_scene_rva'])
        if not cena or self.u32(cena)!=self.base+self.layout['scene_vtable_rva']:
            raise RuntimeError('Cena indisponivel para listar entidades')
        gerente=self.u32(cena+self.layout['entity_manager_offset'])
        pool=self.u32(gerente+self.layout['entity_array_offset'])
        quantidade=self.u32(self.base+self.layout['entity_count_rva'])
        passo=self.layout['entity_stride']
        if not 1<=quantidade<=1024 or passo!=0x39bc or not 0x10000<=pool<=0xffff0000-quantidade*passo:
            raise RuntimeError('Lista de entidades fora dos limites validados')
        encontrados=[];vistos=set()
        for i in range(quantidade):
            ptr=pool+i*passo
            try:
                cab=self.read(ptr,0x40);id_=struct.unpack_from('<I',cab,4)[0]
                if not 0x800<=id_<0x2800 or id_ in vistos:continue
                pos=struct.unpack_from('<3f',cab,0x1c)
                if not all(math.isfinite(v) for v in pos) or math.dist(pos[:2],centro)>raio or abs(pos[2]-player['height'])>5:continue
                mob=self.entidade(ptr)
                if not mob or mob['id']!=id_ or not mob['hostile'] or mob['hp']<=0:continue
                # Duas exclusoes diretas da validacao original 0x5e2480.
                if struct.unpack('<h',self.read(ptr+0x1dc,2))[0]<0:continue
                if self.read(ptr+0x450,1)[0] and not self.u32(self.base+0x2f9e08c-0x400000):continue
                mob['slot']=i;encontrados.append(mob);vistos.add(id_)
            except RuntimeError:continue
        if self.u32(self.base+self.layout['active_scene_rva'])!=cena or self.u32(gerente+self.layout['entity_array_offset'])!=pool:
            raise RuntimeError('Mapa mudou durante a leitura das entidades')
        return sorted(encontrados,key=lambda m:math.dist(m['position'],player['position']))

    def snapshot(self):
        # 0x44c774 ativa a cena neste global. O cache context+0x8d2b0
        # e zerado em 0x44c791 e nao deve ser usado como cena ativa.
        scene=self.u32(self.base+self.layout['active_scene_rva'])
        if not scene:raise RuntimeError('Cena do jogo ainda nao carregada. Entre no mapa e tente Ler dados novamente.')
        if self.u32(scene)!=self.base+self.layout['scene_vtable_rva']:raise RuntimeError('Cena ativa nao corresponde ao layout validado. Entre no mapa com o personagem.')
        player=self.entidade(self.u32(scene+self.layout['player_offset']))
        if not player:raise RuntimeError('Personagem ainda nao carregado.')
        try:target=self.entidade(self.u32(scene+self.layout['target_offset']))
        except RuntimeError:target=None
        return dict(source='native',player=player,target=target)

if __name__=='__main__':
    d=DadosInternos()
    try:print(json.dumps(d.snapshot(),ensure_ascii=False))
    finally:d.close()
