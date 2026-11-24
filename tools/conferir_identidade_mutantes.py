"""Leitura da identidade de mobs; nao instala ponte nem envia comandos."""
import json,os,struct,sys,time,hashlib
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.janela_cliente import enumerar_clientes
r=dict(em=time.time());d=None
try:
    p=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    j=next(j for j in enumerar_clientes() if j['pid']==p['client_pid'] and j['hwnd']==p['client_hwnd'])
    d=DadosInternos(janela=j);s=d.snapshot();r.update(pid=d.pid,cliente_sha256=d.sha256,player=s['player'],mobs=[])
    bruto=(d.caminho.parent/'UI/MN.bin').read_bytes();nomes=bytes((v-i)%256 for i,v in enumerate(bruto))
    if len(nomes)!=4096*128:raise RuntimeError('Tabela de nomes divergente')
    r['mn_sha256']=hashlib.sha256(bruto).hexdigest()
    for m in d.listar_mobs(s['player']['position'],50,s['player']):
        id_=struct.unpack('<h',d.read(m['ref']+0x474,2))[0]
        nome=nomes[id_*128:(id_+1)*128].split(b'\0')[0].decode('cp1252') if 0<=id_<4096 else None
        r['mobs'].append(dict(id=m['id'],name=m['name'],template_id=id_,nome_cadastro=nome,confere=nome==m['name'],position=m['position']))
    r['ok']=True
except Exception as e:r.update(ok=False,erro=str(e))
finally:
    if d:d.close()
(raiz/'build/identidade_mutantes.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
