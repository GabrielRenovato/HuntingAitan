HuntingAitan 0.1.0-beta.35

Menos paradas no circuito leste dos sete Verits e correção da validação de coordenadas.

- O circuito leste confere pontos vazios durante a aproximação. Duas leituras recentes, sem alvo próximo, permitem seguir para o próximo trecho sem esperar cinco segundos, inclusive na primeira visita. Leituras antigas ou um mob reaparecendo impedem essa transição.
- Selecionar um alvo por ID pela ponte interna preserva o deslocamento. Habilidades, pausas e encerramento continuam com suas paradas explícitas.
- Corrige os erros de X/Y causados por campos de coordenadas escondidos: a base manual só é validada quando está em uso.
- Coordenadas decimais lidas do jogo preenchem a base manual com valores inteiros. A validação de limites permanece ativa.

Validação: 673 testes Python e verificações Node aprovados, além do teste no painel Electron e do motor empacotado. Uma sessão de 90 segundos da templária terminou normalmente com dois abates; a espera observada num ponto vazio foi de aproximadamente 0,17 segundo, contra 5,2 segundos num registro anterior. São sessões distintas, não um benchmark controlado.

Limitações: segundo plano continua experimental, exige a opção ativa no perfil e o Aika aberto, sem minimizar. Mina e Jardim usam o modo normal. A passagem antecipada na primeira visita foi aplicada ao circuito leste dos sete Verits; os outros circuitos mantêm sua regra anterior. O teste curto não valida uma volta completa nem farm prolongado.

Instalador: HuntingAitan-Setup-0.1.0-beta.35-x64.exe.
