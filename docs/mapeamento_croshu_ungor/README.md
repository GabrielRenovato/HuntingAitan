# Croshu mutante na Floresta Ungor

O pedido foi mapear “Croshu azul mutante”. No cadastro local, a espécie mutante com posições em **Bosque de Ungor** é **Cão Mutante Croshu**, registro **1374**. A tabela de nomes não confirma a cor do modelo; a correspondência visual com o apelido “azul” ainda precisa ser conferida no jogo.

Foram extraídos todos os **sete pares XY não vazios** desse registro de `UI/MobPos.bin`, identificado pelo nome exato em `UI/MN.bin`. Os outros 43 slots estão vazios.

| Ponto/slot | X | Y |
| --- | --- | --- |
| 1 | 1954 | 1138 |
| 2 | 1934 | 1152 |
| 3 | 1901 | 1166 |
| 4 | 1952 | 1186 |
| 5 | 1933 | 1183 |
| 6 | 1895 | 1155 |
| 7 | 1950 | 1127 |

Todos pertencem ao setor 14 de `UI/Map.bin`, **Bosque de Ungor**, com limites `(1792, 1024)` a `(2556, 1534)`. O grupo fica no noroeste do setor. Os pares de pontos 1 e 7, 4 e 5, e 3 e 6 ficam próximos; essas relações não comprovam passagem entre eles.

Outros registros não foram misturados: `Croshu Cinzento` (1206) e `Croshu Canino` (1207) têm posições em Ungor, mas não são nomeados mutantes; `Croshu Mutante` (1265) não tem posições cadastradas nessa tabela; `Croshu Mutante das Cinzas` (1376) possui coordenadas fora de Ungor.

`croshu_ungor.png` mostra um recorte ampliado e uma visão geral de Ungor; `croshu_ungor.csv` contém as coordenadas; `croshu_ungor.json` inclui limites, slots, flags, hashes das fontes e a ressalva sobre identificação visual.

A orientação dos seis tiles `z010704.att`, `z010705.att`, `z010804.att`, `z010805.att`, `z010904.att` e `z010905.att` foi conferida linha por linha com `Env/AttributeS01.dat`. As sete células têm o bit de bloqueio estático desativado. Isso não garante ausência de árvores ou outros objetos.

Para regenerar:

```powershell
python tools/mapear_croshu_ungor.py --game-dir "C:\GoLevel\AikaOnline" --out docs/mapeamento_croshu_ungor
```

Esses são todos os pontos dessa espécie cadastrados nos arquivos locais, não uma lista de entidades vivas ou de todos os spawns do servidor. A numeração não define um circuito. O hunting não foi alterado neste levantamento.
