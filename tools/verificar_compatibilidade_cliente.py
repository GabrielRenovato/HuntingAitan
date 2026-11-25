"""Auditoria estatica de compatibilidade: nao abre processo nem executa o cliente."""
import argparse,hashlib,json,sys
from functools import lru_cache
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pefile
from huntingaitan.recursos import DADOS
from huntingaitan.leitura.dados_internos import escolher_layout
from huntingaitan.leitura.janela_cliente import EXECUTAVEIS
from huntingaitan.entrada.ponte_camera import HASHES
from huntingaitan.rotas.jardim_aereo import conferir_nome_jardim


@lru_cache(maxsize=256)
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def auditar(cliente):
    cliente=Path(cliente);pasta=cliente.parent;sha=digest(cliente);pe=pefile.PE(str(cliente))
    resultado=dict(cliente=str(cliente),sha256=sha,somente_leitura=True,executado=False,
        reconhecido_pelo_seletor=cliente.name.lower() in EXECUTAVEIS,ponte_compativel_por_hash=sha in HASHES,
        pe=dict(machine=hex(pe.FILE_HEADER.Machine),base=hex(pe.OPTIONAL_HEADER.ImageBase),
            entrypoint_rva=hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),image_size=pe.OPTIONAL_HEADER.SizeOfImage,
            secoes=[dict(nome=s.Name.rstrip(b'\0').decode(errors='replace'),rva=hex(s.VirtualAddress),tamanho=s.Misc_VirtualSize) for s in pe.sections]),rotas={})
    try:
        escolher_layout((DADOS/'native_layout.json').read_text(encoding='utf-8'),sha)
        resultado['layout_validado']=True
    except RuntimeError as e:resultado.update(layout_validado=False,erro_layout=str(e))
    for f in sorted(DADOS.glob('*.json')):
        plano=json.loads(f.read_text(encoding='utf-8'));arquivos=[]
        if not isinstance(plano,dict) or not isinstance(plano.get('fontes'),dict):continue
        nome=f.name
        for relativo,esperado in plano.get('fontes',{}).items():
            alvo=pasta/relativo;registro=dict(arquivo=relativo,existe=alvo.is_file(),esperado=esperado)
            if alvo.is_file():
                registro.update(atual=digest(alvo),bytes=alvo.stat().st_size)
                registro['identico']=registro['atual']==esperado
                if relativo=='UI/Dungeon.bin':
                    try:registro.update(nome_jardim=conferir_nome_jardim(alvo.read_bytes()),nome_jardim_aceito=True)
                    except RuntimeError as e:registro.update(nome_jardim_aceito=False,erro=str(e))
            arquivos.append(registro)
        resultado['rotas'][nome]=arquivos
    resultado['tabelas']={p.name:p.stat().st_size for p in [pasta/'ItemList6.bin',pasta/'ItemList12.bin',pasta/'SkillData6.bin',pasta/'SkillData12.bin',pasta/'UI/SkillData6.bin',pasta/'UI/SkillData12.bin',pasta/'UI/MN.bin',pasta/'UI/MobPos.bin'] if p.is_file()}
    resultado['compatibilidade_atual']=all(resultado[k] for k in ['reconhecido_pelo_seletor','layout_validado','ponte_compativel_por_hash'])
    return resultado


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--cliente',required=True);a.add_argument('--out',required=True);args=a.parse_args()
    r=auditar(args.cliente);dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='rotas'},ensure_ascii=False,indent=2))
    for nome,arquivos in r['rotas'].items():print(nome,dict(identicos=sum(x.get('identico',False) for x in arquivos),total=len(arquivos),divergentes=[x['arquivo'] for x in arquivos if not x.get('identico')]))
