"""Le somente as tabelas virtuais do cliente selecionado, sem instalar ponte."""
from pathlib import Path
import os,sys,json

raiz=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(raiz))
from huntingaitan.leitura.escolha_cliente import abrir_leitor


def main():
    perfil=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    destino=raiz/'build/analise_interacao_jardim/contexto.json'
    resultado=dict(somente_leitura=True)
    d=None
    try:
        d=abrir_leitor(perfil['client_pid'])
        if d.hwnd!=perfil['client_hwnd']:raise RuntimeError('Janela selecionada mudou')
        s=d.snapshot()['player']
        if s['name']!='Domination':raise RuntimeError('Cliente diferente da templaria')
        cena=d.cena_validada();vtable=d.u32(cena)
        if not d.base<=vtable<d.base+0x400000:raise RuntimeError('Tabela fora do modulo validado')
        resultado.update(pid=d.pid,hwnd=d.hwnd,nome=s['name'],posicao=s['position'],sha256=d.sha256,
            arquivo=str(d.caminho),base=hex(d.base),cena=hex(cena),vtable=hex(vtable),
            metodos=[dict(offset=hex(i*4),va=hex(d.u32(vtable+i*4)),rva=hex(d.u32(vtable+i*4)-d.base)) for i in range(26)])
    except Exception as e:resultado['erro']=str(e)
    finally:
        if d:d.close()
        destino.parent.mkdir(parents=True,exist_ok=True)
        destino.write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
