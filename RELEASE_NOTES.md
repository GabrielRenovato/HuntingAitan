HuntingAitan 0.1.0-beta.37

Jardim em segundo plano, objetivo Seridunn e preservação dos perfis.

- Adiciona suporte experimental ao Jardim em segundo plano: captura da janela selecionada, saída do grupo, retorno ao altar e entrada no Difícil. Mantenha o Aika aberto, sem minimizar. A Mina continua no modo normal.
- Confirma o altar pelo objeto reconhecido sob o cursor antes do duplo clique, evitando clicar no texto e fazer o personagem andar. Reconfirma a identidade antes de cada pressão do mouse.
- Corrige a barra de grupo, a prioridade do painel final de entrada e o destino curto na quina do retorno. Aguarda a thread e o mapa responderem antes de reconectar o motor após carregamento.
- Adiciona o objetivo Seridunn, que segue o terreno até a área final, ignora hostis laterais e combate bloqueadores próximos ou por defesa. O chefe tem prioridade e só o abate confirmado permite concluir. O objetivo é o padrão para perfis sem essa opção; o trecho curto antes dos Shiraz continua selecionável.
- Preserva configurações quando o arquivo não pode ser lido ou validado, em vez de carregar padrões silenciosamente. Bloqueia gravações após esse erro e cria profile.json.bak antes de substituir um perfil existente.
- Inclui ferramentas locais de análise da interação e auditoria estática de compatibilidade. Não adiciona suporte ao Aika Brasil.

Validação: 707 testes Python e verificações Node aprovados, testes no painel Electron real e smoke do motor empacotado. Na validação real do Jardim, saída, retorno e reentrada no Difícil foram confirmados com 280 amostras sem foco e HP mínimo de 100%; o motor reconectou após carregar. Um teste anterior de combate confirmou 25 abates em 120 segundos.

Limites: a travessia inteira até Seridunn, seu abate e várias repetições completas ainda não foram validados no jogo. A posição do altar é uma referência da área final, não um spawn comprovado do chefe. O serviço no NPC ao fundo foi verificado por simulação. Hashes de terreno, objetos e layouts continuam protegidos; arquivos diferentes ainda exigem revalidação. Perfis e configurações pessoais não fazem parte da release.

Instalador: HuntingAitan-Setup-0.1.0-beta.37-x64.exe.
