# Transicoes da templaria no circuito leste

Esta revisao reduz esperas do motor, preservando confirmacao de morte, conjuracao, cura e verificacao da grade. Inicialmente ativadas na templaria no circuito leste, as quatro transicoes agora tambem sao compartilhadas com o circuito dos Croshus das Cinzas em segundo plano. As regras especificas de ataque e limpeza da templaria continuam separadas. Ver `TRANSICOES_CROSHU.md`.

## Abate para proximo alvo

Apos as duas leituras de HP zero e o intervalo de confirmacao existente, o motor atualiza a lista e o custo de caminho e pode selecionar o proximo ID no mesmo ciclo. O candidato passa pela validacao da ponte. Nao envia ataque nessa transicao: recarga, prioridade de cura e o controle contra cancelamento do normal continuam independentes. `target_handoff` registra o ID e a latencia entre confirmacao e selecao, em milissegundos.

## Fim da habilidade

Na confirmacao rapida da templaria, o fim de um cast observado junto de gasto/recarga dispensa a margem extra fixa. A cura nao e liberada pelo simples inicio do cast; cast ativo continua bloqueando movimento. Os outros modos mantem a regra anterior. A protecao de 0,4 segundo para repetir ataque normal apos conjuracao continua existindo; ela nao bloqueia o movimento.

## Pontos vazios

Uma revisita vazia com leitura recente pode mudar para o proximo trecho a ate 3,5 unidades da parada, sem mandar parar no centro do ponto. No circuito leste dos sete Verits, duas leituras consecutivas e recentes da lista, feitas durante a aproximacao (ate 10 unidades da parada) e sem alvo ate 20 unidades do personagem, tambem liberam a primeira visita sem esperar cinco segundos. A troca de trecho continua limitada a 3,5 unidades da parada. Uma leitura isolada, antiga ou com alvo proximo nao basta. Mob reaparecido remove a marca de vazio e tem prioridade sobre o percurso. Os outros circuitos conservam a espera na primeira visita.

A selecao de um ID pela ponte preserva o deslocamento ja confirmado. O envio de habilidade continua parando o movimento; pausa, modal e encerramento tambem conservam suas paradas explicitas.

## Bloqueio

Quando o navegador exclui uma passagem que nao produziu avanco, executa uma unica nova busca naquele ciclo. Havendo alternativa validada, envia o novo destino imediatamente, inclusive quando ele e semelhante ao destino anterior; a deduplicacao temporal nao suprime esse desvio. Sem caminho confirmado, o motor para e reconfirma a grade. A tentativa sem alternativa usa revisao curta, em vez da espera antiga de dois segundos. Colisoes e limites nao sao removidos.

## Validacao

Os testes verificam duas selecoes imediatas apos os tres abates da limpeza, transicao antes de chegar ao centro de uma revisita, espera na primeira visita, cura com cast encerrado versus cast ativo, exclusao e recalculo no mesmo instante e envio do desvio sem aguardar o destino anterior. Latencias de simulacao nao representam desempenho medido no jogo.

A suite completa passou com 637 testes e verificacoes Node. O backend empacotado tambem passou no smoke test. No teste real `build/teste_templaria_20261123_200102`, cerca de 180 segundos terminaram com codigo zero: 10 abates confirmados, quatro limpezas locais, uma recuperacao de alvo, um buff confirmado e um desvio com alternativa encontrada no mesmo ciclo. Quatro trocas diretas registraram 15, 16, 31 e 32 ms; nao sao garantia para outras maquinas ou situacoes. HP minimo: 61,89%, com recuperacao durante a sessao. Nao houve abandono por falta de dano. Foram registradas 170 recusas de chamadas pelo cliente; elas continuam distinguindo tentativa de acao aceita.

O teste nao completou uma volta inteira e nao valida farm prolongado. A compilacao local desse teste foi `build/templaria-transicoes-local/win-unpacked`; a compilacao que acrescenta as mesmas transicoes aos Croshus esta descrita em `TRANSICOES_CROSHU.md`.

Em 25/11/2026, o teste de 90 segundos da passagem continua terminou com codigo
zero, dois abates, uma recuperacao de alvo, HP minimo de 73,56% e movimento
sem foco. A primeira parada vazia conferida mudou de trecho em aproximadamente
0,17 segundo entre amostras de telemetria; o log anterior tinha uma parada vazia
de 5,2 segundos. Sao observacoes de sessoes distintas, nao um benchmark controlado.
