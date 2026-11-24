# Retencao do Verit e retomada do padrao

O log `run_20261123_193444.jsonl` registrou Verit selecionado sem perda de HP, recusas mesmo perto do player e abandono depois de conjuracoes. O usuario informou tambem que repetir o ataque enquanto o mob se move pode cancelar o padrao neste Aika.

## Conferencia do binario

`0x4EE0D0` consulta `0x4ED920`, verifica a recarga e chama `0x4F1C90`. O retorno desta ultima e convertido de AL para EAX booleano em `0x4EE1E5..0x4EE1EC`; o adaptador ja usava esse retorno normalizado. A recusa nao e equivalente a ausencia de alvo.

`0x4ED920` verifica player vivo, flags de paineis (`scene+0x4110/0x4128`, byte +0x29), operacoes pendentes, estado de acao e conjuracao. `0x4F1C90` tambem possui uma verificacao de tempo da acao. Nao foi isolada qual dessas condicoes produziu cada recusa do log; nao ha tentativa de remover essas validacoes.

As funcoes `0x5D1530/0x5D1550`, chamadas pela validacao, consultam animacao em player+0x1E0. As faixas gerais de execucao incluem 5..22 e 44..58. Sao sinais de execucao, nao prova isolada de um golpe do ataque normal. Desmontagens de apoio ficam em `build/analise_hunting_nativo/recusas` e `contratos`.

## Comportamento da templaria

- Verit Mutante hostil vivo, a ate cinco unidades e com altura compativel, permanece travado mesmo sem dano ou apos ciclos de recuperacao. Nao vai para a lista de ignorados por essas causas. Morte, perda real da entidade, distancia, Parar/F12 e protecoes de sobrevivencia continuam sendo tratados.
- Perda de selecao com o mesmo Verit proximo ainda legivel renova a recuperacao do mesmo ID. Nao busca outro com TAB.
- Recuperacoes sao espacadas por pelo menos 4,5 segundos e reconfirmam o ID. Um reposicionamento mantem a verificacao de grade; nao gira por teclas de segundo plano que nao foram validadas. Nao ha novas chamadas internas na ponte.
- O tempo gasto na confirmacao de uma habilidade deixa de consumir o prazo de ataque sem dano. Buffs comuns de combate e skills ofensivas aguardam o primeiro dano; cura, defesa e consumiveis continuam prioritarios.
- O padrao espera pelo menos 0,4 segundo apos movimento detectado do alvo. Cada pedido de normal fica espaçado por pelo menos 2,5 segundos. Dano recente junto de animacao de execucao suspende novos pedidos; dano da Pran com o player ocioso nao basta para suspende-los indefinidamente.
- Apos confirmar uma conjuracao, aguarda 0,4 segundo antes de rearmar o normal. O relato de cancelamento por mob em movimento motivou esse controle; ele ainda precisa de validacao de combate nesta revisao.

O cancelamento `1rr1ww` continua desativado no modo interno. Esta alteracao busca preservar o ataque normal existente, sem burlar recargas nem alterar atributos.

## Testes

O teste integrado recusa os ataques durante 12 segundos e depois permite dano: o mesmo Verit e mantido e morto, os dois hostis proximos sao eliminados e so entao ha movimento de circuito. Testes adicionais verificam movimento, dano com animacao, dano externo com player ocioso, pausa de conjuracao e prazo entre pedidos.

A tentativa ao vivo em `build/teste_templaria_20261123_195020` encontrou a templaria com 46,96% de HP e nao iniciou; o painel e a caca existentes foram preservados.

A suite completa passou com 630 testes e verificacoes Node. O backend empacotado passou no smoke test. A compilacao local desta revisao fica em `build/templaria-padrao-estavel-local/win-unpacked`. O perfil do guerreiro nao foi alterado.
