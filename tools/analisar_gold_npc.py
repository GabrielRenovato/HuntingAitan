"""Extrai o catalogo e precos-base locais; nao altera o jogo nem presume drops."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
import pefile

REGISTRO=0x1d0
TAMANHO=31000*REGISTRO

def analisar(pasta,destino):
    pasta=Path(pasta);destino=Path(destino);destino.mkdir(parents=True,exist_ok=True)
    exe=(pasta/'AIKACL.exe').read_bytes();arquivo=(pasta/'ItemList12.bin').read_bytes()
    pe=pefile.PE(data=exe)
    # Enderecos da rotina lida no cliente local (VA 0x415530..0x41554a).
    if pe.OPTIONAL_HEADER.ImageBase!=0x400000 or len(arquivo)!=12+TAMANHO+4 or arquivo[:8]!=b'TK00003I':
        raise ValueError('Formato diferente do cliente analisado; revalide o carregador.')
    trecho=pe.get_data(0x15530,0x20)
    if b'\x90\x3a\x75\x00' not in trecho or b'\x80\x7b\xdb\x00' not in trecho:
        raise ValueError('Rotina de decifragem diferente; nenhuma tabela exportada.')
    chave=pe.get_data(0x353a90,256).split(b'\0')[0]
    if len(chave)!=102:raise ValueError('Chave do catalogo divergente.')
    bruto=arquivo[12:12+TAMANHO];i=np.arange(TAMANHO,dtype=np.uint32)
    tabela=((np.frombuffer(bruto,dtype=np.uint8).astype(np.int16)-np.frombuffer(chave,dtype=np.uint8)[i%len(chave)]-(i%256))%256).astype(np.uint8).tobytes()
    itens=[]
    for id_ in range(31000):
        r=tabela[id_*REGISTRO:(id_+1)*REGISTRO]
        texto=lambda a,b:r[a:b].split(b'\0')[0].decode('cp1252',errors='replace')
        nome=texto(0,64)
        if not nome:continue
        compra,venda=struct.unpack_from('<ii',r,0x124)
        itens.append(dict(id=id_,nome=nome,nome_ingles=texto(64,128),descricao=texto(128,256),
                          preco_compra_base_cliente=compra,preco_venda_base_cliente=venda))
    por_id={r['id']:r for r in itens}
    if 'Potion' not in por_id.get(4380,{}).get('nome',''):raise ValueError('Catalogo decifrado nao passou pela conferencia de nomes.')
    resumo=dict(fontes={n:hashlib.sha256((pasta/n).read_bytes()).hexdigest() for n in ['AIKACL.exe','ItemList12.bin','UI/MobPos.bin']},
                registros=31000,registros_com_nome=len(itens),registros_preco_base_positivo=sum(r['preco_venda_base_cliente']>0 for r in itens),
                formato=dict(tamanho_registro=REGISTRO,offset_preco_compra='0x124',offset_preco_venda='0x128',
                             carregador='VA 0x415506..0x41554a',calculo_valor_item='VA 0x429df0..0x429e63',
                             observacao='O calculo usa o preco-base e pode ajustar pela durabilidade. Chamadores aplicam coeficientes adicionais. O valor final precisa ser conferido no NPC.'),
                exemplos=[por_id[k] for k in [4186,4796,5100,2530]],
                limite='Nao foi validada uma tabela de drop por monstro, taxa de drop, respawn efetivo ou gold/hora. Presenca no catalogo e preco-base nao comprovam que um item seja farmavel ou vendavel no servidor.',
                ranking_locais=None)
    (destino/'precos_npc_cliente.json').write_text(json.dumps(itens,ensure_ascii=False,indent=2),encoding='utf-8')
    (destino/'resumo_gold_npc.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2),encoding='utf-8')
    return resumo

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--game-dir',required=True);p.add_argument('--out',default='build/analise_gold');a=p.parse_args()
    r=analisar(a.game_dir,a.out)
    print(json.dumps({k:r[k] for k in ['registros','registros_com_nome','registros_preco_base_positivo','ranking_locais']},ensure_ascii=False))
    for item in r['exemplos']:print(item['id'],item['nome'],item['preco_venda_base_cliente'])
