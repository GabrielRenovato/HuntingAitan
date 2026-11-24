from pathlib import Path
import pefile,capstone,hashlib,json,struct
from capstone.x86_const import X86_OP_IMM
p=Path(r'C:\GoLevel\AikaOnline\AIKACL.exe');raw=p.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
out=Path('build/analise_hunting_nativo/contratos');out.mkdir(parents=True,exist_ok=True)
funcoes={'camera':0x5b46a0,'acao_skill':0x4ee0d0,'iniciar_acao':0x4f1c90,'selecionar':0x509f60,'validar_alvo_assistente':0x47d3e0,'limpar_ou_definir_alvo':0x507270,'verificar_destino':0x50eb80,'alternativa_destino':0x50eaa0,'retornar_base':0x47d820,'motor':0x47c570}
manifesto=dict(sha256=hashlib.sha256(raw).hexdigest(),image_base=hex(base),arquitetura='x86',execucao_validada=False,funcoes={})
for nome,inicio in funcoes.items():
 fila=[inicio];vistos={};saltos_fora=[]
 while fila:
  a=fila.pop()
  while a not in vistos:
   if not inicio<=a<inicio+0x10000:saltos_fora.append(hex(a));break
   try:i=next(md.disasm(pe.get_data(a-base,16),a,count=1))
   except (StopIteration,pefile.PEFormatError):break
   vistos[a]=(i.size,i.mnemonic,i.op_str)
   if i.mnemonic.startswith('ret') or i.mnemonic in ('int3','ud2'):break
   if i.group(capstone.CS_GRP_JUMP):
    if i.operands and i.operands[0].type==X86_OP_IMM:
     alvo=i.operands[0].imm
     if inicio<=alvo<inicio+0x10000:fila.append(alvo)
     else:saltos_fora.append(hex(alvo))
    if i.mnemonic=='jmp':break
   a+=i.size
   if len(vistos)>18000:break
 linhas=[f'{a:08x} {m:9s} {o}' for a,(n,m,o) in sorted(vistos.items())];(out/(nome+'.txt')).write_text('\n'.join(linhas),encoding='utf-8')
 rets=[dict(va=hex(a),instrucao=m+' '+o) for a,(n,m,o) in sorted(vistos.items()) if m.startswith('ret')]
 chamadas=[dict(va=hex(a),destino=o) for a,(n,m,o) in sorted(vistos.items()) if m=='call']
 manifesto['funcoes'][nome]=dict(va=hex(inicio),rva=hex(inicio-base),instrucoes=len(vistos),retornos=rets,chamadas=chamadas,saltos_fora=sorted(set(saltos_fora)))
 print(nome,hex(inicio),'ins',len(vistos),'ret',rets,'calls',len(chamadas))
(out/'manifesto.json').write_text(json.dumps(manifesto,ensure_ascii=False,indent=2),encoding='utf-8')
