# Comparacao isolada do cancelamento da templaria

`tools/comparar_cancelamento_templaria.py` compara o ataque normal com `1rr1ww`, alternando normal/sequencia/sequencia/normal duas vezes. Nao modifica o perfil e nao habilita cancelamento na caca. O ataque 1 usa a ponte interna existente; R/W usam mensagens destinadas ao HWND. Ainda nao ha equivalencia comprovada entre essa combinacao e o XButton com entrada fisica.

O experimento identifica o cliente do perfil da templaria, exige Verit Mutante vivo selecionado a ate 2,4 unidades e HP inicial de pelo menos 85%, sem conjuracao/stun e sem caca original. Antes desses requisitos, nao encerra o painel existente. Somente depois fecha esse painel, testa, remove a ponte e reabre o mesmo executavel. O guerreiro nao participa.

F12 encerra o teste. Troca de alvo, vida abaixo de 65%, stun, conjuracao ou deslocamento maior que 0,7 interrompem a amostra. Nao ha espera programada entre as seis teclas; os tempos reais das chamadas ficam registrados em milissegundos. Uma recarga que recuse o segundo 1 nao elimina o restante da sequencia; a recusa do primeiro 1 impede R/W.

Os resultados ficam em `build/comparacao_combo_*/resultado.json`. Registra dano observado pela queda de HP, ataques aceitos, tempos e interrupcoes. Queda de HP nao identifica autoria: Pran, efeitos persistentes e outros jogadores podem contribuir. Rodada sem ataque aceito nao entra na comparacao. Sao exigidas quatro rodadas validas por modo para indicar um candidato a mais validacao; nem um ganho aparente de 15% liga o combo automaticamente.

O cancelamento segue desativado no modo interno ate haver validacao real. Este teste nao altera cooldown, velocidade do servidor nem arquivos do jogo.

## Primeira tentativa ao vivo

Em `build/comparacao_combo_20261123_190303`, o ataque automatico ja em andamento continuou causando dano mesmo com novos comandos de ataque recusados. A janela inicial registrou aproximadamente 5119 de dano observado por segundo; as duas janelas seguintes, com apenas uma sequencia completa em cada, registraram aproximadamente 3823 e 3550. As seis chamadas levaram cerca de 10,5 e 11,8 ms, apesar de nao haver espera programada. Esses numeros nao isolam criticos, duplos ou a autoria do dano.

O alvo morreu antes de completar as oito rodadas. Nao houve evidencia suficiente para habilitar cancelamento. A ponte foi removida e o painel reaberto. A instrumentacao ainda precisa distinguir um ataque automatico existente da recusa em iniciar um ataque novo; neste teste, a janela normal sem novo ataque aceito foi descartada da avaliacao automatica. Os valores brutos permanecem no relatorio, sem promover o combo.
