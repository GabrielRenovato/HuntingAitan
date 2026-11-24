# Buto Mutante na Floresta Cinzenta

Foram extraídos todos os 10 pares XY não vazios do registro **1375**, identificado pelo nome exato **Buto Mutante** em `UI/MN.bin`. Os outros 40 slots de `UI/MobPos.bin` estão vazios. Outras espécies de Buto não foram misturadas neste levantamento.

| Ponto/slot | X | Y |
| --- | --- | --- |
| 1 | 2715 | 1287 |
| 2 | 2731 | 1338 |
| 3 | 2718 | 1425 |
| 4 | 2742 | 1427 |
| 5 | 2767 | 1432 |
| 6 | 2731 | 1297 |
| 7 | 2709 | 1300 |
| 8 | 2612 | 1248 |
| 9 | 2684 | 1172 |
| 10 | 2611 | 1220 |

O setor 13 de `UI/Map.bin` tem limites `(2560, 1024)` a `(3070, 1534)` e nome localizado `Trozo de madera de fresno` neste cliente. Todos os dez pontos pertencem a esse retângulo. Há concentrações próximas a `(2720, 1300)`, `(2740, 1430)` e `(2611, 1234)`, além do ponto 9 ao norte. Esses agrupamentos descrevem proximidade das coordenadas, não caminhos validados.

`buto_floresta.png` mostra os pontos sobre os quatro blocos de minimapa originais do setor. `buto_floresta.csv` contém a tabela; `buto_floresta.json` preserva os slots, flags e hashes SHA-256 de todas as fontes.

A orientação XY dos quatro tiles `z011004.att`, `z011005.att`, `z011104.att` e `z011105.att` foi comparada linha por linha com a grade global `Env/AttributeS01.dat`. Todas as dez células têm a flag de bloqueio estático desativada. Isso não comprova ausência de árvores, objetos ou uma passagem entre os pontos.

Para regenerar a partir da raiz do repositório:

```powershell
python tools/mapear_buto_floresta.py --game-dir "C:\GoLevel\AikaOnline" --out docs/mapeamento_buto
```

São posições cadastradas no cliente, não uma lista de entidades vivas do servidor. Não comprovam quantidade simultânea, tempo de respawn nem possíveis posições adicionais definidas exclusivamente no servidor. Os números seguem a ordem do arquivo e não representam uma rota. Este levantamento não altera o comportamento do hunting.

## Observação no jogo

O usuário relatou três Butos Mutantes próximos e forneceu uma captura com a posição do personagem **(2711, 1292)**. Essa posição fica a aproximadamente 6,4 unidades do ponto 1, 20,6 do ponto 6 e 8,2 do ponto 7. Portanto, a observação é compatível com esse grupo já cadastrado; ela não comprova três spawns adicionais nem identifica individualmente as posições dos mobs. As coordenadas da captura pertencem ao personagem, não a um Buto. A tabela extraída foi preservada.
