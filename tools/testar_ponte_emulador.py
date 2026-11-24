"""Exercita o codigo x86 da ponte sem abrir nem modificar um processo real."""
import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
from keystone import Ks,KS_ARCH_X86,KS_MODE_32
from huntingaitan.entrada.ponte_camera import montar,validar_angulos
ks=Ks(KS_ARCH_X86,KS_MODE_32);u=Uc(UC_ARCH_X86,UC_MODE_32);D=0x10000000;C=0x10010000;CTX=0x20000000;CAM=0x200a0000;SCENE=0x200b0000;ST=0x300f0000;END=0x71f000;OLD=0x710500
for a,n in [(D,0x20000),(CTX,0x300000),(0x2f90000,0x10000),(0x70b000,0x1000),(0x710000,0x10000),(0x5b4000,0x1000),(0x509000,0x1000),(0x507000,0x1000),(0x4ee000,0x1000),(0x47d000,0x1000),(0x30000000,0x100000)]:u.mem_map(a,n)
def put(a,*x):u.mem_write(a,struct.pack('<'+'I'*len(x),*x))
def get(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def asm(a,s):u.mem_write(a,bytes(ks.asm(s,a)[0]))
u.mem_write(C,montar(D,C,0x400000));put(D+4,OLD);put(D+8,0xc100);put(D+12,123);put(D+48,42);put(D+56,99);put(D+0x80,OLD)
u.mem_write(D+0x100,b'user32.dll\0');u.mem_write(D+0x120,b'CallWindowProcA\0')
for addr,stub,s in [(0x70b2c8,0x710000,'mov eax,1;ret 4'),(0x70b2a4,0x710100,'mov eax,0x710600;ret 8'),(0x70b550,0x710200,f'mov eax,dword ptr [{D+0x80}];ret 8'),(0x70b554,0x710300,f'mov eax,dword ptr [{D+0x80}];mov edx,dword ptr [esp+12];mov dword ptr [{D+0x80}],edx;ret 12'),(0x70b3c0,0x710400,'mov eax,42;ret')]:put(addr,stub);asm(stub,s)
asm(0x710600,'mov eax,0x12345678;ret 20');asm(0x5b46a0,'movss xmm0,dword ptr [ecx+8];addss xmm0,xmm1;movss dword ptr [ecx+8],xmm0;ret')
asm(0x509f60,'mov dword ptr [ecx+0x90],0x123456;ret 4')
asm(0x4ee0d0,f'mov eax,dword ptr [esp+4];mov dword ptr [{D+0x90}],eax;mov eax,1;ret 4')
asm(0x47d820,f'mov eax,dword ptr [ecx+0x274];mov dword ptr [{D+0x94}],eax;mov eax,dword ptr [ecx+0x278];mov dword ptr [{D+0x98}],eax;ret 4')
put(0x70b298,0x710700);asm(0x710700,'mov eax,1000;ret')
ASSIST=CTX+0x200000;put(SCENE+0xeadf4,ASSIST);put(ASSIST,0x72bb34);put(ASSIST+0x274,11,12)
put(0x2f9b148,SCENE);put(0x2f9b1e0,CTX);put(CTX+0x8d2a8,CAM)
def executar(a,args):
 esp=ST;u.mem_write(esp,struct.pack('<'+'I'*(1+len(args)),END,*args));u.reg_write(UC_X86_REG_ESP,esp)
 for reg in (UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP):u.reg_write(reg,0x13579)
 u.reg_write(UC_X86_REG_XMM1,0x1234)
 u.emu_start(a,END,count=10000)
 assert u.reg_read(UC_X86_REG_ESP)==esp+4*(1+len(args)),'Pilha incorreta'
 for reg in (UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP):assert u.reg_read(reg)==0x13579,'Registrador nao preservado'
 return u.reg_read(UC_X86_REG_EAX)
assert executar(C+0x400,[0])==1;assert get(D+64)==1 and get(D+0x80)==C
assert executar(C,[99,15,0,0])==0x12345678
seq=0
def pedido(op,scene=SCENE):
 global seq
 seq+=1;u.mem_write(D+16,struct.pack('<6I2f',seq,0,op,0,scene,CAM,.03,0.))
 assert executar(C,[99,0xc100,123,seq])==1
 assert u.reg_read(UC_X86_REG_XMM1)==0x1234,'SSE nao preservado'
 assert get(D+20)==seq
 return get(D+28)
assert pedido(1)==1
assert pedido(2)==1
assert abs(struct.unpack('<f',u.mem_read(CAM+8,4))[0]-.03)<1e-6
assert pedido(2,SCENE+4)==0xffffffff
assert pedido(4)==1 and get(SCENE+0x90)==0x123456
asm(0x507270,'mov eax,dword ptr [esp+4];mov dword ptr [ecx+0x90],eax;ret 4')
ALVO=CTX+0x210000;put(ALVO+4,2049);put(ALVO+0x498,100);put(D+72,ALVO);put(D+80,2049)
assert pedido(7)==1 and get(SCENE+0x90)==ALVO and get(D+76)==1
put(D+80,2050);assert pedido(7)==0xffffffff
put(D+72,1088);assert pedido(5)==1 and get(D+0x90)==1088 and get(D+76)==1
assert pedido(6)==1 and get(ASSIST+0x274)==11 and get(ASSIST+0x278)==12
assert get(D+0x94)==struct.unpack('<I',struct.pack('<f',.03))[0]
assert pedido(3)==1 and get(D+0x80)==OLD and get(D+64)==0
for v in (float('nan'),float('inf'),.16):
 try:validar_angulos(v,0)
 except ValueError:pass
 else:raise AssertionError('Angulo perigoso aceito')
print('OK: instalacao/remocao, encaminhamento, thread, nonce/sequencia, cena, camera, pilha, GPR e SSE em emulador x86.')
