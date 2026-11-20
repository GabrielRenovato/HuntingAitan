# Cancelamento do padrão e calibração de skills

Em 20/11/2026, o padrão foi atualizado por instrução do usuário para **1 → R → R → 1 → W → W**, sem chamadas de espera entre as teclas. Cada tecla recebe pressionamento e liberação; o tempo real de processamento depende do Windows e do jogo. A tecla de ataque configurada substitui o 1 se ela for alterada.

Para as skills, dois trechos locais de demonstração de 18/11/2026 foram analisados: aproximadamente 15 segundos de padrão e 56 segundos com habilidades. As capturas brutas e os dados da sessão não fazem parte do repositório ou do instalador.

| Ação identificada | Ordem | Separação | Tecla pressionada | W pressionado |
| --- | --- | ---: | ---: | ---: |
| Ataque normal, ID 1 | 1 → R → R → 1 → W → W | sem espera | sem espera | sem espera |
| Skill ID 177, observada na tecla 4 | W → skill | 3,5 ms | 73 ms | 61 ms |
| Skill ID 273, observada na tecla 5 | W → skill | 25 ms | 61 ms | 79 ms |

São valores nominais aproximados a partir das medianas observadas. O Windows e o jogo introduzem variação; não são garantias de precisão de 1 ms em execução real. Os encerramentos de cada tecla têm seus próprios instantes.

Não houve evidência suficiente para um W imediato uniforme nas skills 3 e 6. A cura 7 também fica sem esse toque. O tempo de pressão simples é aproximadamente 78 ms para IDs 113 e 289 e 76 ms para ID 49. Outras habilidades conservam o envio simples de 45 ms.

O perfil de combo é selecionado pelo ID nativo, não só pela posição na barra. O modo precisa estar ativado e exige alvo vivo, dano previamente observado e distância de até 2,2 unidades. Continua suspenso para o alvo se houver perda de alcance ou recuperação de ataque sem progresso. Itens, buffs e cura não recebem o combo ofensivo.

## Repetição sem perfil externo

A pausa entre teclas e o intervalo entre sequências são separados no painel. Pausa entre teclas em 0 preserva a sequência sem esperas programadas. O envio também desativa a pausa interna da biblioteca de entrada, preservando seu wrapper de fail-safe.

Intervalo entre sequências em 0 consulta `SPI_GETKEYBOARDSPEED` e estima o período correspondente entre 2,5 e 30 repetições/s. É uma aproximação; os tempos reais do Windows variam com hardware e escalonamento. Um valor positivo no painel define o intervalo manualmente, sem consultar essa preferência. Se a consulta falhar, usa 30 Hz e registra o fallback no log.

O objetivo é reproduzir o modo comum de repetição de uma sequência enquanto o combate permanece válido, sem exigir arquivo do X-Mouse. Não foi demonstrada equivalência ao perfil específico de outro usuário. A interpretação de Auto repeat delay em 0 no XMBC está no [manual oficial](https://www.highrez.co.uk/downloads/X-Mouse%20Button%20Control%20User%20Guide.pdf); os limites e a variação de velocidade do Windows estão na [API SystemParametersInfoW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfow).

O repetidor começa após dano confirmado e dentro de 2,2 unidades do alvo. A leitura visual de recarga do ataque normal não bloqueia o envio repetido da sequência; o jogo decide quais golpes efetivar. Skills, cura e buffs mantêm suas recargas e exclusividade. Perda de foco, stun, distância ou recuperação por ausência de dano interrompem o padrão. A agenda calcula a próxima sequência a partir do fim da anterior e não acumula uma fila de envios atrasados.

A cadência do ataque simples, sem combo, permanece separada.

O primeiro trecho registrou 66 comandos de ataque e 12 quedas de HP; isso não equivale a 66 golpes. As medições não comprovam autoria de cada dano nem aumento de desempenho por cancelamento. Os testes automatizados validam a sequência de entrada e as proteções, sem demonstrar ganho de combate ao vivo.
