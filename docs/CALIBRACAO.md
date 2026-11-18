# Calibração de 18/11/2026

Dois trechos locais de demonstração foram analisados: aproximadamente 15 segundos de padrão e 56 segundos com habilidades. As capturas brutas e os dados da sessão não fazem parte do repositório ou do instalador.

| Ação identificada | Ordem | Separação | Tecla pressionada | W pressionado |
| --- | --- | ---: | ---: | ---: |
| Ataque normal, ID 1 | ataque → W | 3 ms | 65 ms | 66 ms |
| Skill ID 177, observada na tecla 4 | W → skill | 3,5 ms | 73 ms | 61 ms |
| Skill ID 273, observada na tecla 5 | W → skill | 25 ms | 61 ms | 79 ms |

São valores nominais aproximados a partir das medianas observadas. O Windows e o jogo introduzem variação; não são garantias de precisão de 1 ms em execução real. Os encerramentos de cada tecla têm seus próprios instantes.

Não houve evidência suficiente para um W imediato uniforme nas skills 3 e 6. A cura 7 também fica sem esse toque. O tempo de pressão simples é aproximadamente 78 ms para IDs 113 e 289 e 76 ms para ID 49. Outras habilidades conservam o envio simples de 45 ms.

O perfil de combo é selecionado pelo ID nativo, não só pela posição na barra. O modo precisa estar ativado e exige alvo vivo, dano previamente observado e distância de até 2,2 unidades. Continua suspenso para o alvo se houver perda de alcance ou recuperação de ataque sem progresso. Itens, buffs e cura não recebem o combo ofensivo.

No padrão calibrado, o limite mínimo entre tentativas é 170 ms, contado a partir do início do envio. O cliente precisa indicar que a recarga do ataque está liberada; não se repetem comandos durante uma recarga bloqueada. Sem combo, a cadência anterior é preservada.

O primeiro trecho registrou 66 comandos de ataque e 12 quedas de HP; isso não equivale a 66 golpes. As medições não comprovam autoria de cada dano nem aumento de desempenho por cancelamento. Os testes automatizados validam a sequência de entrada e as proteções, sem demonstrar ganho de combate ao vivo.
