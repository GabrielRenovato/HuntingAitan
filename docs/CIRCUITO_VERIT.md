# Circuito Verit Mutante de Termes

No painel: **Comportamento → Modo de caça → Circuito Verit · Termes**. Comece perto de 2748, 833 ou de outro trecho do circuito.

A volta segue os pontos do mapeamento: **1 → 5 → 20 → 18 → 4 → 19 → 2 → 3 → 1**, repetindo. Coordenadas: 2748/833; 2779/844; 2786/847; 2783/877; 2705/922; 2699/892; 2708/867; 2672/850.

O motor usa a posicao interna, a lista de entidades e a grade de colisao carregada. Somente Verit Mutante dentro da faixa do circuito e do alcance configurado e aceito. Pausa a navegacao para lutar, mantem o alvo ate o abate ou recuperacao por falha de progresso, procura outros Verits elegiveis e retoma o trecho. Ha busca de cinco segundos em cada ponto; a luta e as pausas nao consomem essa espera. A entrada pode ocorrer perto de qualquer trecho, sem exigir voltar ao ponto 1.

Os oito caminhos foram derivados de `UI/MN.bin`, `UI/MobPos.bin`, `Env/AttributeS01.dat` e `Env/z01.hgt`, conferindo a orientacao das grades pelos tiles locais. Os hashes dessas fontes ficam em `circuito_termes_verit.json` e sao verificados antes de iniciar. O registro de Verit Mutante e 1378; os numeros da rota correspondem aos slots do mapeamento cadastrado.

```powershell
python tools/validar_circuito_verit.py --game-dir "C:\GoLevel\AikaOnline" --out circuito_termes_verit.json
```

Passagens estaticas e simulacoes de navegacao/combate foram validadas. Isso nao comprova uma volta fisica no jogo: objetos, entidades, latencia e mudancas no servidor podem afetar a navegacao. Os pontos cadastrados nao garantem monstros vivos. Sem passagem local o motor aguarda e rele a grade, sem pular o ponto.

O circuito preserva cura, buffs, controle de stun, fechamento de avisos, interrupcao por perda de foco e recuperacao de ataques sem dano da beta.31. O circuito Penza permanece separado.
