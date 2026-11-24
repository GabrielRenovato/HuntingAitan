# Plantas Mutantes na Floresta Ungor

Foram extraídos todos os **10 pares XY não vazios** do registro **1373**, identificado pelo nome exato **Planta Carnívora Mutante** em `UI/MN.bin`. Os outros 40 slots de `UI/MobPos.bin` estão vazios. A busca na tabela de nomes não encontrou outra espécie com nome contendo “Planta”.

| Ponto/slot | X | Y |
| --- | --- | --- |
| 1 | 1957 | 1435 |
| 2 | 1972 | 1423 |
| 3 | 2108 | 1396 |
| 4 | 2146 | 1346 |
| 5 | 2179 | 1261 |
| 6 | 2274 | 1235 |
| 7 | 2430 | 1367 |
| 8 | 2450 | 1378 |
| 9 | 2457 | 1350 |
| 10 | 2426 | 1346 |

O setor 14 de `UI/Map.bin` tem o nome **Bosque de Ungor** e os limites `(1792, 1024)` a `(2556, 1534)`. Todos os pontos pertencem a esse retângulo. Os pontos 1–2 formam um grupo próximo no sudoeste; 7–10 formam outro a sudeste. Os pontos 3–6 ficam espalhados entre esses grupos. Essas relações descrevem proximidade, não rotas validadas.

`plantas_ungor.png` mostra a distribuição sobre os seis blocos originais do minimapa. `plantas_ungor.csv` contém a tabela de coordenadas. `plantas_ungor.json` inclui os slots, flags de terreno, limites e hashes SHA-256 das fontes.

Os tiles de colisão `z010704.att`, `z010705.att`, `z010804.att`, `z010805.att`, `z010904.att` e `z010905.att` foram comparados linha por linha com a grade global `Env/AttributeS01.dat` para conferir a orientação XY. Todas as dez células têm a flag de bloqueio estático desativada. Isso não comprova ausência de árvores, objetos ou passagem entre os pontos.

Para regenerar a partir da raiz do repositório:

```powershell
python tools/mapear_plantas_ungor.py --game-dir "C:\GoLevel\AikaOnline" --out docs/mapeamento_plantas_ungor
```

Este levantamento cobre todas as posições dessa espécie cadastradas nesses arquivos do cliente. Não identifica plantas vivas, quantidade simultânea, tempo de respawn nem posições extras definidas exclusivamente pelo servidor. A numeração segue a ordem dos slots e não é um circuito. O hunting não foi alterado para caçá-las.
