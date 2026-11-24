# Recuperacao de colisao nos circuitos assistidos

O log `run_20261123_222620.jsonl` do guerreiro registrou repetidamente a mesma
passagem excluida. A recuperacao marcava a diagonal pelo sinal dos dois eixos,
mas a suavizacao de uma reta quase horizontal atravessava outra aresta. Agora
a exclusao usa o mesmo primeiro passo rasterizado empregado por `linha_livre`.
O destino alternativo continua sujeito a grade, limites da rota e altura.

A falta de deslocamento por dois segundos, confirmada pelo navegador, tambem
pode solicitar a skill configurada em `unstuck_key`: `4` na templaria e `'` no
guerreiro. Exige binding reconhecido e recarga pronta, respeita stun/conjuracao
e limita tentativas a uma a cada tres segundos. Nao troca o alvo. O log separa
aceitacao do comando e deslocamento posterior de pelo menos 0,6 unidade; esse
deslocamento nao prova por si so que a skill causou a recuperacao.

Testes cobrem reta quase horizontal, exclusao efetiva do segmento anterior,
replanejamento, recarga, controle, recusa e confirmacao de movimento.
A recuperacao contra as arvores ainda precisa de observacao no jogo.
