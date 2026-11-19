# Alterações

## 0.1.0-beta.6 — 2026-11-19

- Circuito Penza de Termes selecionável no painel, seguindo 3 → 2 → 12 → 18 → 17 e retornando pela mesma faixa.
- Caminhos derivados dos arquivos locais de colisão e altura; oito trechos verificados, com conferência do SHA-256 dos terrenos ao iniciar.
- Busca limitada ao corredor, pausa para combater Penzas e retomada do trecho após abate, com cinco segundos em cada parada.
- Navegação também reconfirma a grade carregada e não avança o ponto se faltar passagem.
- Buffs exclusivos, cura prioritária e fechamento de janelas mantidos. Validação no jogo ainda pendente.

## 0.1.0-beta.5 — 2026-11-19

- Alcance máximo configurável aumentado de 30 para 50, no painel, na validação e na importação de configuração nativa.
- As correções de buffs e fechamento de janelas continuam incluídas.

## 0.1.0-beta.4 — 2026-11-19

- Ciclo de buffs exclusivo: nenhum ataque, TAB ou navegação é enviado entre os cinco atalhos.
- Dano recebido não libera ataques no meio da sequência. Cura de emergência, stun e fechamento de CTE/Elter mantêm prioridade.
- Renovação mantém a pausa entre os vencimentos individuais de cada buff, sem renovar antes do prazo.
- Retomada preserva a seleção e desconta a pausa dos prazos de combate e busca.
- Testes simulam início, renovação durante combate, dano recebido e janela CTE durante os buffs. Validação no jogo ainda pendente.

## 0.1.0-beta.3 — 2026-11-19

- Convites do CTE e da Arena Elter reconhecidos continuamente, por título ou texto do evento e confirmação dos botões.
- Movimento, ataque e cura ficam suspensos enquanto o aviso bloqueia o jogo; a retomada exige duas capturas sem a janela.
- Cliques são reconfirmados na imagem atual, inclusive se a janela mudou de posição.
- O monitor reinicia a captura após falhas temporárias, durante a caça e com o painel ocioso.
- Janelas sem identificação suficiente não recebem clique automático.
- Motor de leitura de texto e modelos incluídos no instalador, sem instalação adicional no PC do usuário.

Reconhecimento validado na captura real anterior do CTE e em testes sintéticos da Arena; o fechamento da Arena em uma aparição real ainda precisa de confirmação.

## 0.1.0-beta.2 — 2026-11-18

- Timing calibrado por habilidade a partir das demonstrações: padrão com 1 antes de W, skill 4 com W antes da tecla e skill 5 com separação de 25 ms.
- Duração e liberação independentes das teclas, em torno de 61–79 ms conforme a ação.
- Cadência mínima de 170 ms no padrão calibrado; a recarga real do cliente continua sendo respeitada.
- Cancelamento vinculado ao ID da habilidade: trocar a barra não aplica o timing a outra skill no mesmo atalho.
- Skills 3 e 6, cura 7 e habilidades sem calibração não recebem W automático.
- Testes de ordem, duração, cadência, falha parcial, perda de foco e suspensão após sair do alcance.

O modo continua experimental e depende da opção de cancelamento estar ativada. As medições não comprovam ganho de dano ou de velocidade.

## 0.1.0-beta.1 — 2026-11-18

- Primeira distribuição versionada com instalador Windows e motor incluído.
- Atualizações pelo GitHub Releases e configurações preservadas.
- Busca com prazo global, aproximação por grade e retorno à base.
- Agenda individual dos buffs, cura prioritária e recargas reais dos atalhos identificados.
- Cancelamento experimental W+ataque e skill+W.
- Testes automatizados do motor, monitor, caminhos portáteis e atualizador.

O comportamento de combate continua experimental. O ganho do cancelamento de animações e a compatibilidade visual com todas as resoluções não estão comprovados.
