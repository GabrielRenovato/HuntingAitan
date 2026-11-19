# Convites e janelas que interrompem o combate

O monitor da beta 3 verifica os avisos continuamente, não só no minuto 57. O horário é uma indicação do usuário; não é usado para clicar sem que uma janela esteja visível.

O CTE mantém o reconhecimento do título conhecido e do botão Cancelar. Para a Arena Elter e variações do convite, o detector procura um par Confirmar/Cancelar alinhado e confere o texto do evento. A leitura de texto exige identificação de Elter e conteúdo compatível com convite, como início em breve ou tempo restante. A presença isolada de Cancelar não autoriza o clique.

Ao identificar uma possível janela modal, o monitor suspende as entradas do hunting antes de completar a classificação. Se a janela é permitida, uma captura nova reconfirma o botão e a identidade visual antes do clique. A caça só retoma após duas capturas válidas consecutivas sem o aviso. Cliques são espaçados e sempre reconfirmados; clicar uma vez não é registrado como fechamento concluído.

Uma janela desconhecida com os dois botões pausa o teclado do programa e gera aviso, mas não recebe clique arbitrário. O programa não usa ESC nem clica em Confirmar. O monitor não intercepta o teclado manual do usuário.

Falhas temporárias de captura não encerram a thread de vigilância: o monitor reabre a captura e exige imagem válida antes de liberar entradas. O painel ocioso usa o mesmo reconhecimento, sem executar o combate.

O instalador contém os modelos de OCR. O teste do motor empacotado realiza inferência em texto sintético, sem abrir o jogo ou enviar comandos. Os testes cobrem movimentos de janela, escalas 0,8/1,25, dois formatos de captura, botões incompletos, janelas desconhecidas e falhas transitórias. A captura real fornecida do CTE foi reconhecida. A Arena foi testada com imagem sintética baseada nos textos existentes neste cliente; isso não comprova o fechamento de todas as aparições reais ou de todos os layouts e resoluções.

Os diagnósticos registram detecção, tipo de aviso, tentativas de clique e confirmação do desaparecimento. Texto OCR e capturas do jogo não são enviados ao GitHub.
