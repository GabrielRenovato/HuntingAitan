"""Analise estatica reproduzivel das entradas de mouse do cliente; nao executa chamadas."""
from pathlib import Path
import hashlib,json,struct
import pefile,capstone


ROTINAS={
    'wndproc_mouse':(0x40f0c6,0xae),
    'leitura_directinput':(0x46bb00,0x1a0),
    'despacho_mouse':(0x46c8d0,0xda),
    'atualizar_raio':(0x4771e0,0x170),
    'cena_mouse':(0x496130,0x300),
    'duplo_clique_cena':(0x50f640,0xd3),
    'clique_inicial':(0x5754c0,0xa6),
    'consulta_terreno':(0x5a0820,0x1fb),
    'raio_cursor':(0x59f6d0,0x80),
    'preparar_raio_no_frame':(0x40e1bf,0x16),
}


def referencias_binarias(raw,endereco):
    alvo=struct.pack('<I',endereco);inicio=0
    while True:
        pos=raw.find(alvo,inicio)
        if pos<0:return
        yield pos
        inicio=pos+1


def main():
    cliente=Path(r'C:\GoLevel\AikaOnline\AIKACL.exe')
    raw=cliente.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
    destino=Path(__file__).resolve().parents[1]/'build/analise_interacao_jardim'
    destino.mkdir(parents=True,exist_ok=True)
    termos=('CursorPos','Capture','Focus','Foreground','ActiveWindow','KeyState','WindowProc','DispatchMessage','DirectInput','ClientToScreen','ScreenToClient')
    imports={f.address:(d.dll.decode(),f.name.decode()) for d in pe.DIRECTORY_ENTRY_IMPORT for f in d.imports if f.name and any(t in f.name.decode() for t in termos)}
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.skipdata=True
    sec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
    ins=list(md.disasm_lite(sec.get_data(),base+sec.VirtualAddress))
    referencias=[];linhas=[]
    for i,(a,n,m,o) in enumerate(ins):
        for endereco,(dll,nome) in imports.items():
            if hex(endereco) in o:
                referencias.append(dict(va=hex(a),api=nome,iat=hex(endereco)))
                linhas.append('\nREFERENCIA '+nome+' '+hex(a))
                linhas.extend(f'{v:08x} {mn:9s} {op}' for v,_,mn,op in ins[max(0,i-24):i+32])
    (destino/'referencias_mouse.txt').write_text('\n'.join(linhas),encoding='utf-8')
    tabelas={}
    for nome in ('JFieldScene','JFieldSceneB','JFieldSceneABCD','JFieldSceneABC','JFieldSceneAB'):
        nome_off=raw.find(('.?AV'+nome+'@@\0').encode())
        if nome_off<8:continue
        tipo=base+pe.get_rva_from_offset(nome_off-8)
        for ref in referencias_binarias(raw,tipo):
            col=ref-12
            if col<0 or struct.unpack_from('<I',raw,col)[0]!=0:continue
            col_va=base+pe.get_rva_from_offset(col)
            for ponteiro in referencias_binarias(raw,col_va):
                valores=struct.unpack_from('<26I',raw,ponteiro+4)
                if all(base+sec.VirtualAddress<=v<base+sec.VirtualAddress+sec.Misc_VirtualSize for v in valores[:11]):
                    tabelas[nome]=dict(vtable=hex(base+pe.get_rva_from_offset(ponteiro+4)),mouse=hex(valores[10]))
    rotinas={}
    variante=cliente.with_name('AIKACL-multiinstancia-teste.exe')
    outra=pefile.PE(str(variante)) if variante.exists() else None
    for nome,(va,tamanho) in ROTINAS.items():
        codigo=pe.get_data(va-base,tamanho)
        texto='\n'.join(f'{a:08x} {m:9s} {o}' for a,_,m,o in md.disasm_lite(codigo,va))
        (destino/(nome+'.txt')).write_text(texto,encoding='utf-8')
        rotinas[nome]=dict(va=hex(va),rva=hex(va-base),bytes=tamanho,sha256=hashlib.sha256(codigo).hexdigest(),
            identica_na_variante=outra.get_data(va-base,tamanho)==codigo if outra else None)
    resultado=dict(arquivo=str(cliente),sha256=hashlib.sha256(raw).hexdigest(),image_base=hex(base),
        somente_leitura=True,execucao_validada=False,imports=[dict(iat=hex(a),dll=d,api=n) for a,(d,n) in imports.items()],
        referencias=referencias,tabelas=tabelas,rotinas=rotinas)
    (destino/'manifesto.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(resultado,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
