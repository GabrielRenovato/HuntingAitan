Correção do indicador Hard no cliente em inglês.

O print enviado confirmou a diferença de idioma: o jogo exibe Hard, enquanto o leitor aceitava apenas Difícil. Também foi reproduzida uma falha de orientação do OCR: o classificador girava esse texto em 180 graus e retornava uma palavra incorreta.

Agora Hard é normalizado como Difícil e o OCR do indicador preserva a orientação horizontal do HUD. Normal, Easy e Elite continuam sendo rejeitados quando o modo exige Difícil. O diagnóstico registra o texto original reconhecido.

A correção reconheceu Hard no print real fornecido com confiança de 1,0. 291 testes Python e verificações do painel e atualizador passaram. A execução completa no notebook ainda precisa ser validada.

Mantém o PNG/JSON salvo antes do OCR e o botão Abrir diagnósticos.

Instalador: HuntingAitan-Setup-0.1.0-beta.26-x64.exe.
