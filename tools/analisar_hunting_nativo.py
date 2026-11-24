from pathlib import Path
import pefile,capstone,hashlib,json
p=Path(r'C:\GoLevel\AikaOnline\AIKACL.exe');b=p.read_bytes();pe=pefile.PE(data=b);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.skipdata=True
s=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text');ins=list(md.disasm_lite(s.get_data(),base+s.VirtualAddress));hits=[]
for i,x in enumerate(ins):
 if '0xeadf4' in x[3]:hits.append((i,x))
out=Path('build/analise_hunting_nativo');out.mkdir(exist_ok=True)
linhas=[]
for i,x in hits:
 linhas.append('\nREFERENCIA '+hex(x[0]))
 linhas.extend(f'{a:08x} {m:8s} {o}' for a,n,m,o in ins[max(0,i-12):i+25])
(out/'referencias_assistente.txt').write_text('\n'.join(linhas),encoding='utf-8')
imports=[]
for d in pe.DIRECTORY_ENTRY_IMPORT:
 for f in d.imports:
  nome=(f.name or b'').decode(errors='replace')
  if any(t in nome for t in ['Foreground','ActiveWindow','KeyState','DirectInput','SendInput','PostMessage']):imports.append(dict(dll=d.dll.decode(),nome=nome,endereco=hex(f.address)))
(out/'metadados.json').write_text(json.dumps(dict(arquivo=str(p),sha256=hashlib.sha256(b).hexdigest(),instrucoes=len(ins),referencias=len(hits),imports=imports),indent=2),encoding='utf-8');print('Instrucoes',len(ins),'referencias',len(hits));print(json.dumps(imports));print('\n'.join(linhas[:100]))
