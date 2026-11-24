# Croshu Mutante das Cinzas na Floresta Cinzenta

O cadastro mutante de Croshu com posições na Floresta Cinzenta é **Croshu Mutante das Cinzas**, registro **1376** de `UI/MN.bin`. O usuário o chamou de “Croshu roxo mutante”; a tabela de nomes não confirma a cor do modelo.

Foram extraídos todos os **11 pares XY não vazios** desse registro de `UI/MobPos.bin`; os outros 39 slots estão vazios.

| Ponto/slot | X | Y |
| --- | --- | --- |
| 1 | 2982 | 1338 |
| 2 | 3009 | 1321 |
| 3 | 2862 | 1387 |
| 4 | 2866 | 1321 |
| 5 | 2884 | 1350 |
| 6 | 2955 | 1310 |
| 7 | 2881 | 1189 |
| 8 | 2881 | 1156 |
| 9 | 2905 | 1143 |
| 10 | 2686 | 1089 |
| 11 | 2725 | 1102 |

Todos os pontos ficam no setor 13 de `UI/Map.bin`, com limites `(2560, 1024)` a `(3070, 1534)`, o mesmo setor da Floresta Cinzenta usado no levantamento dos Butos Mutantes. Não foram misturados os registros de Cão Mutante Croshu, de Ungor, nem Croshu Mutante, sem posições cadastradas.

Há pares próximos nos pontos 10 e 11, um grupo nos pontos 7–9 e outro nos pontos 1–6. São descrições da distribuição espacial, não caminhos validados.

`croshu_cinzenta.png` mostra os 11 pontos sobre os quatro blocos originais do minimapa. `croshu_cinzenta.csv` contém a tabela; `croshu_cinzenta.json` inclui os slots, flags de terreno, limites, identificação e hashes SHA-256 das fontes.

A orientação dos tiles `z011004.att`, `z011005.att`, `z011104.att` e `z011105.att` foi comparada linha por linha com `Env/AttributeS01.dat`. A flag de bloqueio de cada ponto está na tabela exportada. Células livres não comprovam ausência de árvores, objetos ou passagem entre elas.

Para regenerar:

```powershell
python tools/mapear_croshu_cinzenta.py --game-dir "C:\GoLevel\AikaOnline" --out docs/mapeamento_croshu_cinzenta
```

São posições cadastradas no cliente, não uma lista de mobs vivos nem garantia de quantidade simultânea ou respawn. O servidor pode definir posições adicionais. Os números seguem a ordem dos slots e não são um circuito; o hunting não foi alterado neste levantamento.
