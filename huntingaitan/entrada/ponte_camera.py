"""Prova local de ponte x86: camera na thread da janela, com destino e versao fixados.
Nao habilitada pelo painel. Nao modifica o executavel em disco.
"""
import ctypes,struct,secrets,math,threading
from ctypes import wintypes as w

HASHES={'a378297211a51bd0032975b2263c78b962a3a734caf5705a80319d129d246a3b','e286c435100b7e03ec326fba6ae4ec94ea4f9ed17c3e473a2c37a2f3651834b3'}

def validar_angulos(yaw,pitch):
    if not all(math.isfinite(x) and abs(x)<=.15 for x in (yaw,pitch)):raise ValueError('Incremento de camera deve ser finito e de ate 0.15 radianos')


def montar(d,c,b):
    from keystone import Ks,KS_ARCH_X86,KS_MODE_32
    ks=Ks(KS_ARCH_X86,KS_MODE_32)
    getlong=b+0x30b550;setlong=b+0x30b554;getmod=b+0x30b2c8;getproc=b+0x30b2a4;thread=b+0x30b3c0
    callback=f'''
    push ebp
    mov ebp,esp
    mov eax, dword ptr [{d+8}]
    cmp dword ptr [ebp+12],eax
    jne encaminhar
    mov eax,dword ptr [{d+12}]
    cmp dword ptr [ebp+16],eax
    jne encaminhar
    pushfd
    pushad
    sub esp,544
    lea edi,[esp+15]
    and edi,0xfffffff0
    fxsave [edi]
    mov esi,{d}
    mov eax,dword ptr [ebp+20]
    cmp eax,dword ptr [esi+16]
    jne rejeitar
    mov dword ptr [esi+28],100
    call dword ptr [{thread}]
    mov dword ptr [esi+52],eax
    cmp eax,dword ptr [esi+48]
    jne rejeitar
    push -4
    push dword ptr [esi+56]
    call dword ptr [{getlong}]
    cmp eax,{c}
    jne rejeitar
    mov eax,dword ptr [esi+24]
    cmp eax,1
    je sucesso
    cmp eax,3
    je remover
    mov eax,dword ptr [{b+0x2b9b148}]
    cmp eax,dword ptr [esi+32]
    jne rejeitar
    mov ecx,eax
    mov eax,dword ptr [esi+24]
    cmp eax,4
    je selecionar
    cmp eax,5
    je habilidade
    cmp eax,6
    je movimento
    cmp eax,7
    je focar
    cmp eax,2
    jne rejeitar
    mov ecx,dword ptr [{b+0x2b9b1e0}]
    test ecx,ecx
    jz rejeitar
    mov ecx,dword ptr [ecx+0x8d2a8]
    cmp ecx,dword ptr [esi+36]
    jne rejeitar
    test ecx,ecx
    jz rejeitar
    movss xmm1,dword ptr [esi+40]
    movss xmm2,dword ptr [esi+44]
    mov eax,{b+0x1b46a0}
    call eax
    jmp sucesso
    selecionar:
    push 0
    mov eax,{b+0x109f60}
    call eax
    mov dword ptr [esi+76],eax
    jmp sucesso
    habilidade:
    mov eax,dword ptr [esi+72]
    cmp eax,1
    jb rejeitar
    cmp eax,11999
    ja rejeitar
    push eax
    mov eax,{b+0xee0d0}
    call eax
    mov dword ptr [esi+76],eax
    jmp sucesso
    focar:
    mov edx,dword ptr [esi+72]
    cmp edx,0x10000
    jb rejeitar
    mov eax,dword ptr [edx+4]
    cmp eax,dword ptr [esi+80]
    jne rejeitar
    cmp eax,0x800
    jb rejeitar
    cmp eax,0x2800
    jae rejeitar
    cmp dword ptr [edx+0x498],0
    jle rejeitar
    cmp word ptr [edx+0x134],0
    jne rejeitar
    push edx
    mov eax,{b+0x107270}
    call eax
    mov ecx,dword ptr [esi+32]
    mov edx,dword ptr [esi+72]
    xor eax,eax
    cmp dword ptr [ecx+0x90],edx
    sete al
    mov dword ptr [esi+76],eax
    jmp sucesso
    movimento:
    mov ebx,dword ptr [ecx+0xeadf4]
    test ebx,ebx
    jz rejeitar
    cmp dword ptr [ebx],{b+0x32bb34}
    jne rejeitar
    cmp dword ptr [ebx+0x1f4],0
    jne rejeitar
    push dword ptr [ebx+0x274]
    push dword ptr [ebx+0x278]
    mov eax,dword ptr [esi+40]
    mov dword ptr [ebx+0x274],eax
    mov eax,dword ptr [esi+44]
    mov dword ptr [ebx+0x278],eax
    call dword ptr [{b+0x30b298}]
    push eax
    mov ecx,ebx
    mov eax,{b+0x7d820}
    call eax
    pop dword ptr [ebx+0x278]
    pop dword ptr [ebx+0x274]
    jmp sucesso
    remover:
    push dword ptr [esi]
    push -4
    push dword ptr [esi+56]
    call dword ptr [{setlong}]
    test eax,eax
    jz rejeitar
    mov dword ptr [esi+64],0
    sucesso:
    mov dword ptr [esi+28],1
    inc dword ptr [esi+68]
    jmp concluir
    rejeitar:
    mov dword ptr [esi+28],-1
    concluir:
    mov eax,dword ptr [esi+16]
    mov dword ptr [esi+20],eax
    fxrstor [edi]
    add esp,544
    popad
    popfd
    mov esp,ebp
    pop ebp
    mov eax,1
    ret 16
    encaminhar:
    push dword ptr [ebp+20]
    push dword ptr [ebp+16]
    push dword ptr [ebp+12]
    push dword ptr [ebp+8]
    push dword ptr [{d}]
    call dword ptr [{d+60}]
    mov esp,ebp
    pop ebp
    ret 16
    '''
    cb=bytes(ks.asm(callback,c)[0]);inicio=c+0x400
    bootstrap=f'''
    push ebp
    mov ebp,esp
    push esi
    mov esi,{d}
    push {d+0x100}
    call dword ptr [{getmod}]
    test eax,eax
    jz falha
    push {d+0x120}
    push eax
    call dword ptr [{getproc}]
    test eax,eax
    jz falha
    mov dword ptr [esi+60],eax
    push -4
    push dword ptr [esi+56]
    call dword ptr [{getlong}]
    test eax,eax
    jz falha
    mov dword ptr [esi],eax
    push {c}
    push -4
    push dword ptr [esi+56]
    call dword ptr [{setlong}]
    test eax,eax
    jz falha
    mov dword ptr [esi+64],1
    mov eax,1
    jmp fim
    falha:
    xor eax,eax
    fim:
    pop esi
    mov esp,ebp
    pop ebp
    ret 4
    '''
    boot=bytes(ks.asm(bootstrap,inicio)[0])
    if len(cb)>0x400 or len(boot)>0x400:raise RuntimeError('Ponte excedeu limite')
    return cb+b'\xcc'*(0x400-len(cb))+boot


class PonteCamera:
    def __init__(self,dados):
        self.dados=dados;self.hwnd=dados.hwnd;self.pid=dados.pid;self.h=None;self.codigo=0;self.d=0;self.instalada=False;self.incerta=False;self.seq=0;self.lock=threading.Lock();self.mutex=None
        if dados.sha256 not in HASHES:raise RuntimeError('Cliente sem contrato validado')
        if not 0x10000<=dados.base<0xf0000000:raise RuntimeError('Base do modulo fora do intervalo x86 validado')
        # RVAs estaveis no hash validado; a assinatura inicial nao contem relocacoes.
        if dados.read(dados.base+0x1b46a0,6)!=bytes.fromhex('558bec83ec1c'):raise RuntimeError('Rotina de camera diferente')
        self.k=ctypes.WinDLL('kernel32',use_last_error=True);self.u=ctypes.WinDLL('user32',use_last_error=True)
        k=self.k;u=self.u
        k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
        k.VirtualAllocEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_size_t,w.DWORD,w.DWORD];k.VirtualAllocEx.restype=ctypes.c_void_p
        k.WriteProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=w.BOOL
        k.VirtualProtectEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_size_t,w.DWORD,ctypes.POINTER(w.DWORD)]
        k.VirtualFreeEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_size_t,w.DWORD]
        k.FlushInstructionCache.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_size_t]
        k.CreateRemoteThread.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD)];k.CreateRemoteThread.restype=w.HANDLE
        k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.GetExitCodeThread.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];k.CloseHandle.argtypes=[w.HANDLE]
        k.CreateMutexW.argtypes=[ctypes.c_void_p,w.BOOL,w.LPCWSTR];k.CreateMutexW.restype=w.HANDLE;k.ReleaseMutex.argtypes=[w.HANDLE]
        u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.GetWindowThreadProcessId.restype=w.DWORD
        u.GetWindowLongA.argtypes=[w.HWND,ctypes.c_int];u.GetWindowLongA.restype=w.LONG
        u.RegisterWindowMessageW.argtypes=[w.LPCWSTR];u.RegisterWindowMessageW.restype=w.UINT
        u.SendMessageTimeoutW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM,w.UINT,w.UINT,ctypes.POINTER(ctypes.c_size_t)];u.SendMessageTimeoutW.restype=w.LPARAM
        self.mutex=k.CreateMutexW(None,False,'Local\\HuntingAitan.PonteCamera.'+str(self.pid))
        if not self.mutex or k.WaitForSingleObject(self.mutex,0) not in (0,0x80):
            if self.mutex:k.CloseHandle(self.mutex);self.mutex=None
            raise RuntimeError('Ja existe uma ponte para esse cliente')
        try:
            pid=w.DWORD();self.thread=u.GetWindowThreadProcessId(self.hwnd,ctypes.byref(pid))
            if pid.value!=self.pid:raise RuntimeError('Janela mudou')
            self.original=0  # GWL_WNDPROC e consultado dentro do processo alvo pelo bootstrap.
            self.msg=u.RegisterWindowMessageW('HuntingAitan.PonteCamera.'+secrets.token_hex(16));self.token=secrets.randbits(30)|1
            self.h=k.OpenProcess(0x43a,False,self.pid)
            if not self.h:raise RuntimeError('Acesso da ponte negado')
            self.d=k.VirtualAllocEx(self.h,None,4096,0x3000,4);self.codigo=k.VirtualAllocEx(self.h,None,4096,0x3000,4)
            if not self.d or not self.codigo:raise RuntimeError('Alocacao da ponte falhou')
            raw=bytearray(4096)
            for off,val in ((4,self.original),(8,self.msg),(12,self.token),(48,self.thread),(56,self.hwnd)):struct.pack_into('<I',raw,off,val)
            for off,valor in ((0x100,b'user32.dll\0'),(0x120,b'CallWindowProcA\0')):raw[off:off+len(valor)]=valor
            self.escrever(self.d,raw);code=montar(self.d,self.codigo,dados.base);self.escrever(self.codigo,code);old=w.DWORD()
            if not k.VirtualProtectEx(self.h,self.codigo,4096,0x20,ctypes.byref(old)):raise RuntimeError('Protecao de codigo falhou')
            k.FlushInstructionCache(self.h,self.codigo,len(code));tid=w.DWORD();t=k.CreateRemoteThread(self.h,None,0,self.codigo+0x400,None,0,ctypes.byref(tid))
            if not t:raise RuntimeError('Instalacao da ponte nao iniciou')
            try:
                if k.WaitForSingleObject(t,3000)!=0:self.incerta=True;raise RuntimeError('Instalacao sem confirmacao; nao reutilizar ponte')
                status=w.DWORD();k.GetExitCodeThread(t,ctypes.byref(status))
                if status.value!=1:raise RuntimeError('Instalacao recusada')
            finally:k.CloseHandle(t)
            self.instalada=True;self.original=dados.u32(self.d);self.pedir(1)
        except Exception:
            self.close();raise

    def escrever(self,a,raw):
        n=ctypes.c_size_t();buf=ctypes.create_string_buffer(bytes(raw))
        if not self.k.WriteProcessMemory(self.h,a,buf,len(raw),ctypes.byref(n)) or n.value!=len(raw):raise RuntimeError('Escrita da ponte falhou')

    def pedir(self,op,yaw=0.,pitch=0.,parametro=0,alvo_id=0):
        if op not in (1,2,3,4,5,6,7):raise ValueError('Operacao nao permitida')
        if op==6:
            if not all(math.isfinite(x) and 0<=x<=9999 for x in (yaw,pitch)):raise ValueError('Destino fora do mapa')
            if math.dist(self.dados.snapshot()['player']['position'],(yaw,pitch))>12:raise ValueError('Movimento interno limitado a trechos de 12 unidades')
        else:validar_angulos(yaw,pitch)
        if op==5 and (not isinstance(parametro,int) or not 1<=parametro<=11999):raise ValueError('Skill invalida')
        if op==7:
            alvo=self.dados.entidade(parametro);player=self.dados.snapshot()['player']
            if not alvo or alvo['id']!=alvo_id or not alvo['hostile'] or alvo['hp']<=0:raise ValueError('Alvo deixou de ser o hostil esperado')
            if math.dist(alvo['position'],player['position'])>50 or abs(alvo['height']-player['height'])>5:raise ValueError('Alvo fora do alcance validado')
        with self.lock:
            if self.incerta or not self.instalada:raise RuntimeError('Ponte indisponivel')
            pid=w.DWORD();thread=self.u.GetWindowThreadProcessId(self.hwnd,ctypes.byref(pid))
            if pid.value!=self.pid or thread!=self.thread:raise RuntimeError('Janela do cliente foi substituida')
            self.seq+=1;scene=camera=0
            # Probe/remocao sao tratados antes de acessar a cena no callback.
            # Um teleporte pode destruir a cena; isso nao pode impedir restaurar
            # a WndProc e liberar a ponte que continua instalada na janela.
            if op not in (1,3):
                scene=self.dados.cena_validada();contexto=self.dados.u32(self.dados.base+self.dados.cfg('context_rva'));camera=self.dados.u32(contexto+0x8d2a8)
                if not camera:raise RuntimeError('Camera indisponivel')
            self.escrever(self.d+16,struct.pack('<6I2f',self.seq,0,op,0,scene,camera,yaw,pitch));resultado=ctypes.c_size_t()
            self.escrever(self.d+72,struct.pack('<II',parametro,0))
            self.escrever(self.d+80,struct.pack('<I',alvo_id))
            ok=self.u.SendMessageTimeoutW(self.hwnd,self.msg,self.token,self.seq,3,1500,ctypes.byref(resultado))
            if not ok:self.incerta=True;raise RuntimeError('Thread do jogo nao confirmou; ponte suspensa')
            seq,concluido,op_,status=struct.unpack('<4I',self.dados.read(self.d+16,16))
            if concluido!=self.seq or status!=1:raise RuntimeError('Operacao rejeitada pela ponte: '+str(status))
            if op==3:self.instalada=False
            return dict(seq=seq,thread=self.dados.u32(self.d+52),status=status,resultado=self.dados.u32(self.d+76))

    def girar(self,yaw,pitch=0.):return self.pedir(2,yaw,pitch)
    def selecionar(self):return self.pedir(4)
    def usar(self,skill_id):return self.pedir(5,parametro=skill_id)
    def mover(self,x,y):return self.pedir(6,x,y)
    def focar(self,alvo):return self.pedir(7,parametro=alvo['ref'],alvo_id=alvo['id'])

    def close(self):
        if self.instalada and not self.incerta:
            try:self.pedir(3)
            except Exception:self.incerta=True
        if self.h:
            if not self.instalada and not self.incerta:
                for ptr in (self.codigo,self.d):
                    if ptr:self.k.VirtualFreeEx(self.h,ptr,0,0x8000)
            self.k.CloseHandle(self.h);self.h=None
        if self.mutex:self.k.ReleaseMutex(self.mutex);self.k.CloseHandle(self.mutex);self.mutex=None
