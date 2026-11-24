# Circuito Verit Mutante de Termes

## Regiao leste: sete pontos sem os grupos de Verit normal

A opcao **Verits · Termes leste · 7 pontos** cobre os slots 15 → 14 → 7 → 17 → 16 → 6 → 11 → 15. Comece perto de 2864, 821 ou 2889, 794, ou de outro trecho dessa regiao. Ela fica separada do circuito oeste descrito abaixo e filtra somente Verit Mutante.

Os sete trechos foram gerados com a colisao e as alturas locais, incluindo o fechamento. A navegacao reconfirma a grade carregada. Com `background_keys` ligado, usa o movimento por destinos na thread do cliente, evita reiniciar trechos semelhantes e exclui temporariamente uma passagem sem progresso. Isso nao garante ausencia de bloqueios por objetos dinamicos. Uma volta completa deste circuito ainda precisa ser validada no jogo.

```powershell
python tools/validar_circuito_verit.py --game-dir "C:\GoLevel\AikaOnline" --leste --out huntingaitan/dados/circuito_termes_verit_leste.json
```

Os pontos 9, 8, 10, 12 e 13 foram retirados por ficarem de 6 a 11 unidades de Verits normais cadastrados. A geracao e a grade usada ao vivo aplicam afastamento de 25 unidades desses cadastros. O filtro tambem recusa alvos dentro dessas zonas. Os mobs vivos podem se deslocar; a margem nao garante ausencia de Verits normais em movimento.

### Melhorias da templaria no circuito leste

Com movimento interno e ataque normal da familia de templario na barra, a sessao ativa decisoes especificas, sem alterar o perfil do guerreiro:

- Ordena ate oito candidatos por comprimento do caminho na grade e proximidade de paredes. Candidato sem passagem completa local e suspenso por tres segundos. O custo tem cache curto; regiao vazia nao calcula caminhos de candidatos.
- Seleciona o ID do candidato acessivel, em vez de percorrer mobs com TAB. Sem confirmacao em dois segundos, permite procurar outro candidato; nao registra abate.
- Apos stun ou referencia invalida, procura o mesmo ID e nome no pool. O desaparecimento nao confirma morte.
- Skills ofensivas aguardam distancia de combate de ate 2,4 unidades. Esse limite e uma regra do motor, nao um alcance extraido da tabela de skills. Cura, defesa e consumiveis mantem a prioridade configurada.
- Depois de um abate confirmado, reancora no trecho atual mais proximo da posicao real. A primeira visita vazia espera cinco segundos; revisitas conhecidas vazias seguem sem repetir toda a espera somente com leitura recente, feita perto da parada. Mob reaparecido invalida o estado vazio.
- `spawn_observed` registra o intervalo entre abate confirmado e uma nova observacao naquele ponto. Esse intervalo observado nao garante o prazo do respawn no servidor nem troca ausencia por morte.

Validacao: 604 testes da suite passaram. O teste ao vivo das melhorias nao iniciou porque a templaria estava abaixo de 65% de HP. Nao ha validacao de volta completa desta revisao.

## Regiao oeste: oito pontos

No painel: **Comportamento → Modo de caça → Circuito Verit · Termes**. Comece perto de 2748, 833 ou de outro trecho do circuito.

A volta segue os pontos do mapeamento: **1 → 5 → 20 → 18 → 4 → 19 → 2 → 3 → 1**, repetindo. Coordenadas: 2748/833; 2779/844; 2786/847; 2783/877; 2705/922; 2699/892; 2708/867; 2672/850.

O motor usa a posicao interna, a lista de entidades e a grade de colisao carregada. Somente Verit Mutante dentro da faixa do circuito e do alcance configurado e aceito. Pausa a navegacao para lutar, mantem o alvo ate o abate ou recuperacao por falha de progresso, procura outros Verits elegiveis e retoma o trecho. Ha busca de cinco segundos em cada ponto; a luta e as pausas nao consomem essa espera. A entrada pode ocorrer perto de qualquer trecho, sem exigir voltar ao ponto 1.

Os oito caminhos foram derivados de `UI/MN.bin`, `UI/MobPos.bin`, `Env/AttributeS01.dat` e `Env/z01.hgt`, conferindo a orientacao das grades pelos tiles locais. Os hashes dessas fontes ficam em `huntingaitan/dados/circuito_termes_verit.json` e sao verificados antes de iniciar. O registro de Verit Mutante e 1378; os numeros da rota correspondem aos slots do mapeamento cadastrado.

```powershell
python tools/validar_circuito_verit.py --game-dir "C:\GoLevel\AikaOnline" --out huntingaitan/dados/circuito_termes_verit.json
```

Passagens estaticas e simulacoes de navegacao/combate foram validadas. Isso nao comprova uma volta fisica no jogo: objetos, entidades, latencia e mudancas no servidor podem afetar a navegacao. Os pontos cadastrados nao garantem monstros vivos. Sem passagem local o motor aguarda e rele a grade, sem pular o ponto.

O circuito preserva cura, buffs, controle de stun, fechamento de avisos, interrupcao por perda de foco e recuperacao de ataques sem dano da beta.31. O circuito Penza permanece separado.
