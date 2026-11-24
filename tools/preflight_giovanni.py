"""Confere clientes, pergaminhos e mobs para preparar o teste, sem enviar comandos."""
import json,sys,math,time
from pathlib import Path
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.inventario import ler_inventario,nome_item

saida=[]
for janela in enumerar_clientes():
    d=None;r={'pid':janela['pid'],'hwnd':janela['hwnd']};saida.append(r)
    try:
        d=DadosInternos(janela=janela);s=d.snapshot();p=s['player'];inv=ler_inventario(d)
        itens=[]
        for i in inv['itens'][:2]:
            itens.append(dict(i,nome=nome_item(d,i) if i['id'] else ''))
        mobs=d.listar_mobs(p['position'],50,p)
        cc=d.estados_controle()
        todos=[dict(i,nome=nome_item(d,i)) for i in inv['itens'] if i['id']]
        r.update(ok=True,nome=p['name'],pos=p['position'],hp=p['hp']/p['hp_max'],ouro=inv['ouro'],itens=itens,itens_ocupados=todos,
                 mobs_50=len(mobs),mais_proximo=min((math.dist(p['position'],m['position']) for m in mobs),default=None),
                 efeitos=cc.get('active_skill_ids'),controle={k:cc.get(k) for k in ('casting','stunned','paralyzed','frozen')},
                 caca_original=d.caca_original_ativa())
    except Exception as e:r.update(ok=False,erro=str(e))
    finally:
        if d:d.close()
(raiz/'build/preflight_giovanni.json').write_text(json.dumps(dict(t=time.time(),clientes=saida),ensure_ascii=False,indent=2),encoding='utf-8')
