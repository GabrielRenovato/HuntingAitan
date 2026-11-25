# Seis Croshus roxos perto de 2955, 1311

Em Comportamento → Modo de caça, escolha **6 Croshus roxos · Sul · 2955, 1311**.
Esse modo (`cinzenta_croshu_sul`) e seu arquivo de rota são separados do circuito
anterior de cinco Croshus (`cinzenta_croshu_trio`), que permanece disponível.

| Ordem | Ponto do cadastro | Coordenadas |
| --- | --- | --- |
| 1 | 6 | 2955, 1310 |
| 2 | 2 | 3009, 1321 |
| 3 | 1 | 2982, 1338 |
| 4 | 3 | 2862, 1387 |
| 5 | 5 | 2884, 1350 |
| 6 | 4 | 2866, 1321 |

Volta: **6 → 2 → 1 → 3 → 5 → 4 → 6**. A referência indicada pelo usuário é
2955, 1311, junto ao ponto 6 do cadastro. A volta tem aproximadamente 409
unidades de caminho. Foram conferidos a espécie 1376 (`Croshu Mutante das Cinzas`),
os seis registros de spawn, as alturas e as passagens estáticas dos arquivos locais.

O alcance de seleção continua limitado a 50 unidades do personagem. O circuito
segue até os pontos mais afastados, mantém o alvo durante a luta e retoma o caminho
após o abate. Usa as mesmas recuperações, visitas e transições do outro circuito,
inclusive a ponte interna quando o segundo plano está habilitado. Não modifica
skills, cura ou buffs do perfil e não seleciona os pontos 7–11 do outro grupo.

O cadastro não garante seis mobs vivos simultaneamente. Objetos dinâmicos e uma
volta física completa ainda precisam de observação no jogo. Os testes simulam
duas voltas e seis abates, sem troca de alvo vivo, e verificam a separação das rotas.
O teste do motor também exige movimento, seleção por ID e ataque pela ponte
interna, falhando se o circuito tentar usar o teclado global. Essa simulação
não substitui a validação de uma volta completa com o jogo sem foco.

No teste local de 25/11/2026, a templária realizou três abates em 120 segundos,
avançando da referência 2955, 1311 até 2922, 1361. Houve deslocamento sem foco,
mas não foi completada uma volta durante o teste. O perfil anterior estava com
segundo plano desligado e tentava renovar buffs em Ctrl+1–5 vazios. A agenda
agora ignora slots que a leitura confirma como vazios, preservando itens e
atalhos ainda sem leitura; esses slots podem voltar a participar se preenchidos.

Para regenerar somente esta rota:

```powershell
python tools/validar_circuito_cinzas_sul.py --game-dir "C:\GoLevel\AikaOnline" --out huntingaitan/dados/circuito_cinzenta_croshu_sul.json
```
