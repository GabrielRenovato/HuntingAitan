Repetição do padrão sem arquivo do X-Mouse.

Em Comportamento → Ataque normal, ative o padrão e ajuste separadamente Pausa entre teclas e Intervalo entre sequências. Pausa em 0 envia 1RR1WW sem esperas programadas; intervalo de repetição em 0 estima o ritmo do teclado do Windows. Um valor positivo define a repetição manualmente.

O padrão usa a tecla de ataque configurada, começa após o primeiro dano e permanece condicionado ao alvo e alcance. A repetição de entradas não fica bloqueada pela indicação visual de recarga do normal; o jogo continua responsável pelos golpes efetivos. Skills, cura e buffs mantêm suas recargas e prioridade; foco, stun e recuperação de ataque continuam interrompendo o padrão.

Remove a chamada interna de pausa da biblioteca de entrada e o limite antigo de 170 ms entre sequências. O próximo envio considera o intervalo configurado sem acumular comandos atrasados.

316 testes Python e verificações do painel e atualizador passaram. Foram testados o ritmo de 40 ms no motor, repetição após o primeiro dano, preservação das skills e fail-safe. O efeito no combate e a equivalência ao perfil exato de XMBC de terceiros ainda não foram validados ao vivo.

Mantém o Jardim até antes dos Lazapas finais e a saída do grupo da beta.27.

Instalador: HuntingAitan-Setup-0.1.0-beta.28-x64.exe.
