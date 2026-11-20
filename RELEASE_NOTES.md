Recuperação da borda de objetos no caminho até a Mina.

Corrige a repetição indefinida de sem_caminho observada em 2682,1758. O terreno permitia a posição ocupada pelo personagem, enquanto nossa máscara adicional bloqueava a célula inteira.

Agora o navegador pode sair apenas dessa célula ocupada e retomar o percurso. Nenhum bloqueio nativo do terreno é removido; as demais células dos objetos continuam bloqueadas. Também funciona ao iniciar o retorno nessa posição.

269 testes Python e verificações do painel e atualizador passaram. O planejamento com os arquivos reais encontrou 145 pontos até o portal a partir da posição observada. A recuperação ainda precisa ser validada ao vivo.

Instalador: HuntingAitan-Setup-0.1.0-beta.21-x64.exe.
