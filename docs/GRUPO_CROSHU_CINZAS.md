# Cinco Croshus Mutantes das Cinzas

No painel, escolha o personagem em **Básico → Cliente do Aika**. Em **Comportamento → Modo de caça**, escolha **5 Croshus · Floresta Cinzenta**. Comece próximo a **2882, 1154** ou **2697, 1106**, com a caça nativa desligada, e clique em **Começar**. F12 encerra o nosso motor. A chave interna `cinzenta_croshu_trio` foi preservada para manter compatibilidade com os perfis existentes.

O modo faz uma busca ativa **7 → 8 → 9 → 11 → 10 → 7**, com caminhos derivados da colisão e da altura locais. Em 24/11/2026 foram acrescentados os pontos 10 e 11, perto da coordenada 2697, 1106 informada pelo usuário. O motor segue para os outros pontos quando não encontra alvos disponíveis no grupo atual. Os pontos vêm do [cadastro de Croshu Mutante das Cinzas](mapeamento_croshu_cinzenta/README.md):

| Ponto | X | Y |
| --- | --- | --- |
| 7 | 2885 | 1196 |
| 8 | 2881 | 1156 |
| 9 | 2905 | 1143 |
| 11 | 2725 | 1102 |
| 10 | 2686 | 1089 |

Os trechos medem aproximadamente 41,66; 29,38; 197,81; 44,38 e 244,15 unidades, respectivamente. A extensão aumenta bastante a volta. Os caminhos passaram na validação estática; objetos dinâmicos e a volta completa ainda precisam de observação no jogo.

O ponto 7 usa a coordenada aproximada informada pelo usuario em 22/11/2026: **2885, 1196**, em vez do cadastro **2881, 1189**. O JSON preserva o cadastro em `pontos_cadastro` e identifica a origem do ajuste; o mapeamento bruto nao foi alterado. Os trechos de ida e volta foram regenerados e validados no terreno. O teste exige continuar andando na coordenada antiga e so iniciar a espera perto da nova.

O filtro aceita apenas **Croshu Mutante das Cinzas** hostil, vivo, dentro da faixa do grupo e a até 50 unidades do personagem. Não confundir com Cão Mutante Croshu de Ungor. Mantém o alvo enquanto luta, confirma o abate pela leitura de vida e procura o próximo. Se não houver alvos acessíveis na posição atual, segue para os outros pontos; busca por cinco segundos em cada parada e repete a volta. As recuperações existentes continuam aplicadas a stun, alvo perdido, ausência de dano e obstáculos.

O personagem aproxima os mobs disponíveis pela grade carregada, e IDs mudam no respawn. O cadastro não garante exatamente cinco mobs vivos simultâneos. Um Croshu que se afaste para fora da faixa deixa de ser elegível. O início é recusado fora da região do grupo, evitando uma viagem involuntária desde outro lugar. Os hashes das fontes do percurso são conferidos antes de iniciar.

O modo preserva cliente escolhido, skills, cura, suprimentos e buffs do painel. Durante o ciclo inicial de buffs, ataques e seleção ficam suspensos até a sequência terminar. A duração da sessão continua respeitando o tempo configurado.

## Correção após a tentativa de dois abates

Na sessão `run_20261121_221250.jsonl`, os dois primeiros abates foram confirmados. O motor encontrou o terceiro candidato (ID 5564) perto de `(2883, 1191)`, aproximou por três segundos e voltou antes de confirmar sua seleção. O alvo chegou a aparecer depois com vida positiva enquanto o estado já era `retornar`. A telemetria antiga não registrava a posição e altura do alvo; não é possível atribuir a perda da lista unicamente ao raio ou à diferença de altura.

O prazo de seleção agora é renovado depois da aproximação ou de uma leitura de candidato que desapareça, e a lista é reconferida. A busca ativa pelos três pontos evita depender exclusivamente da visibilidade da base. A telemetria passou a registrar posição/altura do alvo e sua distância da base para diferenciar futuras exclusões.

Testes verificam o grupo original e a elegibilidade dos pontos 10 e 11 perto de 2697, 1106, excluem NPCs e outras espécies, preservam atalhos e conta, e simulam dois mobs visíveis da base mais um terceiro detectável somente após avançar ao seu ponto. Outro teste reproduz a aproximação após o prazo antigo já ter vencido, com a lista vazia por meio segundo: o motor renova a busca e abate sem retornar prematuramente. O comportamento real ainda precisa ser validado no jogo.

## Ataques sem efeito no terceiro ponto

Na sessão `run_20261121_222335.jsonl`, o motor chegou ao ponto 7 e selecionou o terceiro Croshu, mas sua vida permaneceu em 87435 em várias tentativas. A sessão terminou com o personagem sem vida. Isso comprova ausência de dano nesses intervalos, mas não identifica sozinho a causa do golpe falhar nem atribui toda a morte a uma única falha.

Encontramos um defeito na recuperação: cada animação de habilidade zerava o contador de ataques sem dano. Agora somente stun, paralisia ou congelamento suspendem esse contador; animações continuam respeitadas antes de mover ou atacar, mas não contam como prova de dano. Ao terminar uma animação, também se preserva a suspensão de cancelamento aplicada à luta durante uma recuperação.

O teste de regressão intercala ataques sem efeito e animações, exige reposicionamento no mesmo alvo e só permite abate com vida zero. A lógica antiga, executada apenas em memória, falha nesse teste; a corrigida passa. Isso valida a recuperação simulada, não comprova que o terceiro Croshu foi abatido no cliente real.

Para regenerar os caminhos:

```powershell
python tools/validar_circuito_cinzas.py --game-dir "C:\GoLevel\AikaOnline" --out huntingaitan/dados/circuito_cinzenta_croshu.json
```
