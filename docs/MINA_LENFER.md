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

O caminho estático desde a entrada tem 534 células e aproximadamente 560,75 unidades na grade. O arquivo `mina_lenfer_rota.json` contém a referência e os SHA-256 necessários. Ao iniciar em outro ponto da mesma área, o caminho é recalculado. A execução também reconfirma a grade carregada, inclusive diante de objetos ou bloqueios dinâmicos.

Monstros fora da faixa do trajeto são desconsiderados. A distância caminhável na grade filtra alvos próximos em linha reta mas separados por paredes. Ao reconhecer Malik, a busca prioriza esse alvo. Atordoamento, cura, buffs exclusivos, recargas e fechamento de avisos usam o motor já existente.

## Conclusão

A chegada à sala não conclui a execução. É necessário reconhecer Malik, confirmar o abate por duas leituras de vida zero e verificar a área final por quinze segundos sem hostis selecionáveis. Uma nova fase ou luta reinicia a verificação. Ulman e Guarda-Costas do Malik não contam como Malik.

A conclusão corresponde a essas condições locais. Não representa leitura da recompensa ou da flag de missão do servidor. F12 interrompe e libera as teclas.

## Repetição no Elite

No painel, selecione **Mina L’Enfer → Malik** e marque **Repetir a Mina no Elite**. O limite de DGs aceita zero para repetir sem limite, respeitando o tempo total da sessão. Sem essa opção, começa dentro da primeira área e encerra ao concluir a DG.

Após confirmar Malik e a área final, abre o menu com o botão direito no quadro do grupo, seleciona **Sair do Grupo** e confirma **Sair do grupo?**. A navegação começa na posição real de chegada ao save. Os arquivos `Env/AttributeS01.dat` e `Env/z01.hgt` fornecem a colisão e altura do caminho até o portal da primeira área, em 2716,1611. O retorno não depende da rota gravada antiga.

A entrada reconhece o nome do portal, a opção da primeira área, Elite e os botões das duas janelas seguintes. Exige a posição de entrada e o indicador **Elite** no minimapa antes de liberar outra DG. Se essa confirmação falhar, sai e tenta novamente sem contar conclusão. Uma falha de saída mantém a etapa; não repete a DG já concluída. Janelas desconhecidas não autorizam cliques. Os vencimentos dos cinco buffs são preservados entre etapas, e não reiniciados em cada transição.

O retorno está limitado à região do save validada junto à entrada. Saves de outros mapas, cliente alterado ou ausência de passagem produzem erro explícito, sem navegação às cegas. Morte e parada manual encerram o ciclo.

## Verificação ao vivo de 19/11/2026

O motor chegou ao final e confirmou Malik (59.480 HP máximos) por vida zero, seguido da verificação da área. Em testes sequenciais das transições, saiu pelo menu do grupo, confirmou a chegada ao save em 2628,4 / 1792,4, caminhou aproximadamente 227,3 unidades até o portal e entrou novamente na primeira área. A nova posição 2850,4 / 3344,4 e o indicador Elite foram confirmados. Essas etapas foram executadas por testes separados; a repetição contínua por várias DGs ainda requer acompanhamento.

## Regeneração

```powershell
python tools/validar_mina_lenfer.py --game-dir "C:\GoLevel\AikaOnline" --out mina_lenfer_rota.json
```
