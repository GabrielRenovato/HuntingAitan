# Mina L’Enfer → Malik

O modo calcula o caminho da posição atual até a referência da sala final da primeira área. O objetivo é Malik. Combate hostis no trajeto e prioriza Malik quando reconhecido, preservando uma luta já iniciada até o abate.

## Arquivos e validação

- `UI/Dun.bin`, registros 16–19: origem 2816,3328 e entrada 2850,3344.
- `Env/z011113.dat`: objetos posicionados no tile 11,13.
- `Env/z011113.att`: atributos de colisão.
- `Env/z011113.hgt`: alturas.
- `Env/MMZ011113.jit`: minimapa original JT31/DXT1.
- `Objects/ilenfF*.MS3`: partes do interior, incluindo a referência da sala final.
- `UI/Dungeon.bin`: a descrição da primeira área identifica Malik.

Na conferência ao vivo de 19/11/2026, a posição de entrada foi 2850,3999 / 3344,3999, com altura 21,0773. A cena reportou 30005. Nas 2.009 células comparáveis, os bits de colisão coincidiram integralmente com os arquivos, e a diferença de alturas foi zero.

O caminho estático desde a entrada tem 534 células e aproximadamente 560,75 unidades na grade. O arquivo `dados/mina_lenfer_rota.json` contém a referência e os SHA-256 necessários. Ao iniciar em outro ponto da mesma área, o caminho é recalculado. A execução também reconfirma a grade carregada, inclusive diante de objetos ou bloqueios dinâmicos.

Monstros fora da faixa do trajeto são desconsiderados. A busca dos mobs comuns fica limitada a 12 unidades caminháveis, para seguir o caminho sem interromper a marcha para perseguir alvos a 20–50 unidades. Malik conserva o alcance configurado. A distância caminhável na grade filtra alvos separados por paredes. Ao reconhecer Malik, a busca prioriza esse alvo. A lista é atualizada a cada 200 ms fora de combate. Ao chegar ao alcance, abre a luta com ataque normal e depois libera as habilidades, respeitando recargas, execução e intervalos. Atordoamento, cura, buffs exclusivos e fechamento de avisos mantêm prioridade.

O início do ciclo não carrega mais o reconhecimento visual do portal antes da navegação. Esse carregamento antecipado atrasava a inicialização no executável instalado. O painel informa a conferência de posição antes da primeira etapa.

As extensões de imagem do monitor são preparadas na thread principal antes dos controles de teclado e das threads de leitura. Na investigação do executável instalado, a transição para entrada ficou bloqueada no carregamento nativo do NumPy, e a interface aguardou o carregador do OpenCV. A verificação do motor empacotado inclui agora monitor e interface em processo novo, além do teste da ordem de inicialização da ponte.

O botão Entrar do grupo é comparado pela faixa do texto, dentro da janela de mazmorra reconhecida. A borda e o fundo variam com o realce; o recorte anterior rejeitava um estado real do botão. O teste de regressão usa somente esse botão recortado, sem nomes ou dados do jogador.

## Conclusão

A chegada à sala não conclui a execução. É necessário reconhecer Malik, confirmar o abate por duas leituras de vida zero e verificar a área final por quinze segundos sem hostis selecionáveis. Uma nova fase ou luta reinicia a verificação. Ulman e Guarda-Costas do Malik não contam como Malik.

A conclusão corresponde a essas condições locais. Não representa leitura da recompensa ou da flag de missão do servidor. F12 interrompe e libera as teclas.

## Repetição no Elite

No painel, selecione **Mina L’Enfer → Malik** e marque **Repetir a Mina no Elite**. O limite de DGs aceita zero para repetir sem limite, respeitando o tempo total da sessão. Sem essa opção, começa dentro da primeira área e encerra ao concluir a DG.

Após confirmar Malik e a área final, abre o menu com o botão direito no quadro do grupo, seleciona **Sair do Grupo** e confirma **Sair do grupo?**. A navegação começa na posição real de chegada ao save. Os arquivos `Env/AttributeS01.dat` e `Env/z01.hgt` fornecem a colisão e altura do caminho até o portal da primeira área, em 2716,1611. O retorno não depende da rota gravada antiga.

No trajeto externo, ignora os mobs, inclusive alvos já selecionados. Junto ao portal, confere os hostis vivos a cada 400 ms. Se houver um mob a até três unidades do personagem e seis do portal, libera esse bloqueador antes de tentar a entrada, sem depender de receber dano. Também pode liberar a entrada após bloqueio físico confirmado ou se a interação ficar cinco segundos sem avançar com dano recente. Restringe o combate aos IDs identificados como bloqueadores. Se deixarem a região da entrada, retoma o portal sem persegui-los.

A entrada reconhece o nome do portal, a opção da primeira área, Elite e os botões das duas janelas seguintes. Exige a posição de entrada e o indicador **Elite** no minimapa antes de liberar outra DG. Se essa confirmação falhar, sai e tenta novamente sem contar conclusão. Uma falha de saída mantém a etapa; não repete a DG já concluída. Janelas desconhecidas não autorizam cliques. Os vencimentos dos cinco buffs são preservados entre etapas, e não reiniciados em cada transição.

O retorno está limitado à região do save validada junto à entrada. Saves de outros mapas, cliente alterado ou ausência de passagem produzem erro explícito, sem navegação às cegas. Morte e parada manual encerram o ciclo.

### Objetos e estrada externa

A grade do chão não contém toda a ocupação das pedras, caixas e construções. O planejamento externo cruza os objetos posicionados nos arquivos DAT dos tiles próximos com as malhas MS3, aplicando posição, escala e rotação. O leitor suporta os modelos com e sem lightmap, verifica o tamanho dos blocos e os índices dos triângulos. O inventário registra 379 instâncias que acrescentam ocupação e nenhum modelo com formato não lido nessa região.

Os triângulos inclinados ou verticais são recortados à faixa entre 0,35 e 1,8 acima do terreno, com margem horizontal de 0,6. Pisos e rampas são excluídos desse bloqueio. Essa é uma aproximação conservadora para navegação baseada na geometria visível, não a reprodução exata da colisão interna do servidor. Instâncias animadas ficam fora da máscara. O arquivo `dados/entrada_mina_geometria.json` contém máscara, inventário e hashes SHA-256 dos arquivos usados; a execução reconfirma essas fontes.

O eixo da estrada passa por 2696,5 / 1715,5 e 2699,5 / 1675,5 antes de subir até o portal. As guias restringem o caminho ao centro da estrada, sem cortar o pátio da caixa-d'água em 2713,1682. A célula observada da colisão nas pedras em 2683,1714 passa a ser bloqueada. A máscara de objetos vale tanto para o caminho estático quanto para a condução com a grade carregada.

Na validação dessa condução em 19/11/2026, o retorno completo de 2627,4 / 1792,4 até 2715,8 / 1614,8 levou 28 segundos, com HP cheio e sem eventos de bloqueio. Também foi confirmada uma passagem iniciada mais à frente no caminho. Isso valida o trecho observado; outros objetos dinâmicos continuam sujeitos à reconfirmação durante a execução.

Em outros bloqueios físicos do retorno, a falta de deslocamento com avanço enviado informa o ponto tentado. O controlador volta a uma passagem já percorrida, exclui temporariamente uma pequena área à frente e calcula outro caminho. A revisão muda a referência de navegação, evitando repetir indefinidamente a mesma rota. Essa recuperação é restrita ao retorno externo; a navegação da DG e do circuito de Termes mantém o comportamento anterior.

Para regenerar o inventário após revalidar uma alteração no cliente:

```powershell
python tools/validar_entrada_mina.py --game-dir "C:\GoLevel\AikaOnline" --out dados/entrada_mina_geometria.json
```

## Verificação ao vivo de 19/11/2026

O motor chegou ao final e confirmou Malik (59.480 HP máximos) por vida zero, seguido da verificação da área. Em testes sequenciais das transições, saiu pelo menu do grupo, confirmou a chegada ao save em 2628,4 / 1792,4, caminhou aproximadamente 227,3 unidades até o portal e entrou novamente na primeira área.

Após corrigir o carregamento nativo e o reconhecimento do botão, o ciclo completo também foi executado no motor empacotado: save → portal → Elite → Malik confirmado → saída do grupo → save → portal → nova entrada Elite. A nova posição 2850,4 / 3344,4 e o indicador Elite foram confirmados nas duas entradas. Nenhum ataque ou TAB foi enviado nos trajetos externos dessa execução. O teste encerrou na entrada da próxima DG, com uma conclusão contabilizada. A validação cobre uma DG e a entrada da próxima.

## Regeneração

```powershell
python tools/validar_mina_lenfer.py --game-dir "C:\GoLevel\AikaOnline" --out dados/mina_lenfer_rota.json
```
