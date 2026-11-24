# Identidade dos mutantes e limpeza proxima da templaria

## Evidencia no cliente

No binario validado, a rotina do assistente em `0x47D3E0` le o ID temporario em entidade+4 e o codigo de especie int16 em entidade+0x474 (`0x47D433`). Ela compara esse codigo com as especies configuradas no assistente. A mesma funcao usa entidade+0x19AC para o nome e entidade+0x134 para o estado hostil. O relatorio de desmontagem esta em `build/analise_hunting_nativo/contratos/validar_alvo_assistente.txt`.

O registro 1378 de `UI/MN.bin` e Verit Mutante. Em `build/identidade_mutantes.json`, a leitura somente leitura conferiu 14 entidades carregadas: todos os codigos corresponderam aos nomes da tabela. Foram observadas as especies 1378 (Verit Mutante), 1244 (Banzul), 1245 (Demonio Esqueleto Vermelho) e 1266 (Tet Chamas Negras). O executavel dessa leitura tem SHA-256 `e286c435100b7e03ec326fba6ae4ec94ea4f9ed17c3e473a2c37a2f3651834b3`.

O leitor agora inclui `template_id`. Para Verit, esse codigo tem prioridade sobre o texto do nome. Replays antigos sem codigo continuam usando o nome. A identidade da luta combina ID temporario e especie; uma referencia atualizada nao permite adotar outro mob.

Threads continuam sendo o meio de executar selecao e movimento no cliente. Elas nao substituem a validacao da especie nem fornecem entidades de areas que o cliente nao carregou. Nenhuma rotina nova e chamada no jogo nesta alteracao; a investigacao acrescenta somente leitura do campo.

## Limpeza local

Somente a templaria no circuito leste com controle interno ativa a limpeza. Tres ou mais hostis vivos a ate cinco unidades e com diferenca de altura de ate tres unidades iniciam um grupo. NPCs, jogadores e Prans nao passam pela classificacao hostil existente. O centro fica fixo na posicao de inicio; a selecao exige que cada mob continue tanto perto desse centro quanto perto da posicao atual.

Durante a limpeza, busca os Verits do grupo primeiro e depois os outros hostis, mantendo o alvo durante cada luta. Continua ate as leituras frescas esvaziarem o grupo, sem exigir tres mobs novamente quando so resta um. Nao persegue um hostil comum que saia do raio. A lista e atualizada tambem durante o combate. Os abates de outros mobs nao entram nas observacoes de respawn de Verit.

Se o grupo estiver inacessivel pela grade, tenta nova leitura por ate dois segundos e suspende aquela limpeza por dez segundos. Isso nao conta como abate nem comprova que os mobs morreram; evita prender o personagem indefinidamente em uma parede.

Tambem foi corrigido um descarte na borda: se o candidato esta fora da janela local da grade, a busca pode usar um trecho parcial confirmado e reconfirmar a continuacao durante o deslocamento. Nao declara uma rota completa apenas com esse trecho.

## Verificacao

O teste integrado simula um Verit e dois hostis proximos: confirma prioridade do mutante, tres abates e movimento do circuito somente depois de todos estarem mortos. Os testes cobrem especies com nome localizado, ID temporario diferente da especie, altura, raio, ancora, saida do grupo, parede, prioridade entre oito outros mobs e alvo na borda da grade. A leitura de identidade foi validada ao vivo; o novo comportamento de limpeza ainda exige acompanhamento no jogo.

A suite completa passou com 622 testes e verificacoes Node. A tentativa de combate real em `build/teste_templaria_20261123_193221` nao iniciou por HP abaixo de 65%. O teste foi ajustado para conferir vida e posicao antes de fechar o painel existente nas proximas tentativas. Compilacao local: `build/templaria-identidade-limpeza-local/win-unpacked`.
