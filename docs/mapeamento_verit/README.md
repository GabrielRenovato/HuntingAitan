# Verit Mutante em Termes

Foram extraidos 20 pares XY do registro 1378 de `UI/MobPos.bin`, identificado pelo nome exato Verit Mutante em `UI/MN.bin`. Cada registro de posicoes tem 416 bytes: ID, codigo MOB de 12 bytes e 50 slots de coordenadas. Os slots vazios foram descartados; a numeracao preserva a ordem original e nao representa um percurso.

`verit_termes.png` mostra os pontos sobre quatro texturas locais de minimapa JT31/DXT1. `verit_termes.csv` permite abrir a tabela no Excel. `verit_termes.json` inclui os slots, flags de terreno e hashes SHA-256 das fontes.

As 20 celulas estao livres segundo o bit de colisao de `Env/AttributeS01.dat`. A orientacao XY foi conferida linha por linha contra os quatro tiles `z011002.att`, `z011003.att`, `z011102.att` e `z011103.att`. Como verificacao independente do formato, os seis pontos do circuito Penza existente tambem pertencem ao registro 1377 de MobPos.bin.

Para regenerar:

```powershell
python tools/mapear_verit_termes.py --game-dir "C:\GoLevel\AikaOnline" --out docs/mapeamento_verit
```

Esses sao pontos cadastrados no cliente. Nao representam a lista de monstros vivos do servidor, tempo de respawn ou garantia de alcance. A flag livre valida a celula estatica, sem garantir ausencia de objetos, acesso entre os pontos ou circulacao segura. Este levantamento nao adiciona nem ativa um circuito de navegacao no aplicativo.
