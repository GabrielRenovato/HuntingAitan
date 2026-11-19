# Alterações

## 0.1.0-beta.18 — 2026-11-19

- Modo Jardim Aéreo de Mirza no Difícil, com caminho pelos dois blocos de terreno até o altar de Seridunn.
- Confere a dificuldade no indicador do jogo e os hashes dos arquivos usados na rota.
- Combate no trajeto e prioriza Seridunn, exigindo abate por vida zero e área final limpa para concluir.
- Inicialização dentro da DG; entrada e repetição externa do Jardim ainda não automatizadas.

## 0.1.0-beta.17 — 2026-11-19

- Busca sem seleção de hostis comuns na Mina limitada a 2,5 segundos antes de retomar o percurso.
- TAB e orientação com intervalos menores na Mina; luta já iniciada e prioridade de Malik preservadas.
- Bloqueio da rota interna recalcula o trecho com destino mais próximo, sem espera repetida de dois segundos.
- Buffs exclusivos e confirmação final continuam com suas esperas necessárias.

## 0.1.0-beta.16 — 2026-11-19

- Libera o mob hostil colado ao portal antes da tentativa de entrada, sem exigir dano recebido.
- Combate limitado a hostis vivos a até três unidades do jogador e seis da entrada.
- Inclui o caminho externo com a ocupação dos modelos estáticos e condução pelo eixo da estrada.

## 0.1.0-beta.15 — 2026-11-19

- A condução aplica a ocupação dos objetos também à grade carregada; as curvas não são encurtadas atravessando a geometria.
- Inclui o percurso pelo eixo da estrada e a leitura das malhas e posições do cliente.

## 0.1.0-beta.14 — 2026-11-19

- Percurso externo pelo eixo da estrada, evitando o pátio das caixas e da caixa-d’água.
- Ocupação adicional derivada das malhas MS3 e dos objetos posicionados nos DAT, cruzada com a altura do terreno.
- A célula da colisão observada nas pedras em 2683,1714 é bloqueada no planejamento.
- Fontes da geometria conferidas por SHA-256 antes da navegação e incluídas na distribuição.

## 0.1.0-beta.13 — 2026-11-19

- Retorno ao portal desvia do canto das caixas e barris em 2713,1682.
- Colisão física confirmada gera recuo para passagem conhecida e um novo caminho, com exclusão temporária da área bloqueada.
- A recuperação muda a referência de navegação para evitar insistir indefinidamente na mesma tentativa.
- Busca e combate no retorno continuam restritos aos bloqueadores junto da entrada.

## 0.1.0-beta.12 — 2026-11-19

- Corrige travamento do executável nas transições de entrada e saída da Mina.
- Reconhecimento visual preparado na thread principal antes do monitor, evitando disputa no carregamento de OpenCV/NumPy.
- Bibliotecas de imagem carregadas antes dos hooks de teclado e das threads de controle.
- Botão Entrar do grupo reconhecido também com o fundo realçado, sem precisar mover o mouse manualmente.
- Progresso de preparação da interface exibido no painel.
- Teste do monitor e da interface em processo novo incluído na verificação do motor empacotado.
- Ciclo completo validado ao vivo no executável: entrada Elite, Malik, saída, retorno e nova entrada Elite; sem ataques no trajeto externo.

## 0.1.0-beta.11 — 2026-11-19

- Início do ciclo da Mina sem carregar antecipadamente as bibliotecas de reconhecimento do portal.
- Busca de hostis comuns a até 12 unidades caminháveis, preservando o alcance de Malik.
- Atualização dos candidatos a cada 200 ms e abertura com ataque normal ao chegar ao alcance.
- Intervalos, recargas, cura, buffs exclusivos e retorno externo sem caça preservados.

## 0.1.0-beta.10 — 2026-11-19

- Modo Mina L’Enfer → Malik: caminho direto da posição atual até a sala final, com combate no trajeto.
- Rota derivada dos arquivos de colisão e altura, com grade da entrada conferida ao vivo em 2.009 células.
- Alvos laterais são filtrados pela faixa e distância caminhável; Malik recebe prioridade quando reconhecido.
- Conclusão exige o abate confirmado de Malik e verificação da área final. Não depende de capturas do minimapa.
- Retorno externo direto: ignora mobs no caminho; combate apenas bloqueadores junto do portal.
- Repetição opcional no Elite: sair do grupo, confirmar, retornar do save ao portal e conferir a nova entrada.
- Limite de DGs por sessão, contagem apenas após Malik confirmado e agenda de buffs preservada nas transições.
- Abate de Malik, saída, retorno ao portal e nova entrada Elite validados em testes ao vivo separados.
- Cura, buffs exclusivos, recargas, avisos e movimento suave mantidos.

## 0.1.0-beta.8 — 2026-11-19

- Movimento contínuo nas curvas suaves, com conferência de colisão e limites à frente.
- Destinos antecipados e condução preservada ao avançar dentro do mesmo trecho do circuito.
- Pulsos menores de giro e espera curta pela resposta antes de corrigir novamente.
- Correções pequenas perto de obstáculos continuam permitidas para evitar ficar parado.
- Testes de curvas, paredes, borda da região, aproximação e bloqueio físico. Fluidez no jogo ainda precisa ser confirmada.

## 0.1.0-beta.7 — 2026-11-19

- Circuito de Penza alterado para os pontos 4, 5, 6, 7, 8 e 9 do novo recorte.
- Ordem de ida: 6 → 5 → 4 → 7 → 8 → 9; retorno pelos mesmos pontos.
- Dez passagens recalculadas e verificadas nos arquivos de colisão e altura.
- Orientações do painel e testes atualizados para a nova região.

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
