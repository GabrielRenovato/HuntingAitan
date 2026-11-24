# Investigacao do fluxo de renovacao

Estado: cadastro do fluxo; renovacao desativada. Nao ha ainda teste completo de viagem/compra/retorno.

## Evidencia estatica

Executavel `C:\GoLevel\AikaOnline\AIKACL.exe`, SHA-256
`a378297211a51bd0032975b2263c78b962a3a734caf5705a80319d129d246a3b`.
Enderecos sao VAs na base preferencial 0x400000, nao enderecos portaveis.

- O chamador nativo em 0x47D335 consulta 0x47C3B0, rejeita resultado <= -1 e,
  em 0x47D35B, passa esse resultado para 0x4E1F50. Evidencia extraida novamente
  do executavel em `build/analise_renovacao_giovanni/chamador_item.txt`.
- Em 0x4E1F8B, a candidata 0x4E1F50 recebe o primeiro argumento; em 0x4E1FBF
  multiplica por 20 e em 0x4E1FD7 consulta contexto+0x80130, consistente com
  os registros do inventario ja lidos pelo projeto. Tem dois argumentos (ret 8).
  O significado completo do segundo argumento e os ramos especificos de
  pergaminhos nao estao validados. O retorno nao prova chegada ao destino.
- A ponte atual nao expoe essa operacao. Nao executar essa candidata como se
  fosse um contrato confirmado. O fluxo da interface do NPC tambem nao foi
  mapeado/validado nesta investigacao.

## Aplicacao ao projeto

O melhor candidato a investigar e uso pelo slot conferido por ID/nome, seguido
de confirmacao de consumo e mudanca de mapa/posicao. Para chegar ao NPC e voltar
ao farm, aproveitar navegacao pela grade ja existente, validando os trajetos
nesses mapas antes de habilitar. Movimento interno nao prova passagens livres.

A retirada antes de usar o pergaminho da cidade e obrigatoria, com leitura
atual dos mobs e controle do personagem; nunca tratar leitura indisponivel como
area vazia. A selecao de um ponto seguro ainda precisa ser implementada.

As skills 8500, 8501 e 9607 sao candidatas distintas encontradas na exportacao
local. Nao associar automaticamente a opcao `Favor de Giovanni [50000 Oro]`
a uma delas. Comparar os efeitos antes/depois da compra e conferir o saldo,
sem usar um temporizador fixo como prova de que a bencao acabou.

O cadastro `renovacao_giovanni.json` preserva as coordenadas e os dois slots
informados pelo usuario; ele nao ativa o fluxo no motor.

## Teste local em 24/11/2026

`tools/testar_ciclo_giovanni.py` executa uma tentativa separada da caca, somente
na templaria Domination. F12 ou o arquivo `PARAR` na pasta do teste encerram.
O teste atual foi alterado a pedido do usuario para a opcao normal gratuita
`Bendicion de Giovanni`; o Favor de 50000 nao pode ser selecionado por ele.
A confirmacao exige efeito novo reconhecido e saldo preservado.

A leitura confirmou que os pergaminhos estao na segunda bolsa: slot interno
20, ID 4521, retorno ao ponto salvo; slot 21, ID 15521, retorno a cidade.
O usuario vinculou o segundo a F5. A antiga regra Immortal Faith em F5 foi
desativada no perfil da templaria, com copia de seguranca.

O teste enviou F5 em area livre de mobs e confirmou a chegada observada a
Regenshein. A primeira transicao revelou uma corrida entre posicao atualizada
e grade antiga. O teste agora exige dois segundos de leituras com grade
correspondente antes de navegar. A ponte tambem permite probe/remocao sem
acessar cena ou camera, pois elas podem estar ausentes no carregamento.
Duas pontes pendentes foram identificadas pela montagem completa identica e
removidas em ordem, com confirmacao da thread do cliente.

Um percurso de Regenshein ao NPC terminou em aproximadamente 20 segundos e
abriu o menu correto. Ainda nao ha confirmacao de bencao nem de retorno ao
ponto salvo. Esse resultado parcial nao valida o ciclo nem segundo plano.
O teste continua exigindo foco durante operacoes visuais. A rotina interna
candidata de uso de item nao foi adicionada a ponte nem executada.

## Pesquisa de alternativa sem viagem

O catalogo atual foi decifrado novamente com `tools/analisar_gold_npc.py`,
validando o carregador e os nomes. Dos 31000 registros, 23977 tem nome. Nao
foi encontrado item cujo nome corresponda a Favor/Bendicion de Giovanni.
Isso nao exclui itens com outro nome nem funcionalidades do servidor.

Existe o item 5710, `Orden: Bendecir` / `Scroll : Bless`, cuja descricao cita
Shaian, aprendiz da Torre de Giovanni. E apenas candidato a buff portatil:
nao foi confirmado que aplique o mesmo efeito do NPC nem que esteja disponivel
para obter neste servidor. O preco-base do catalogo nao comprova venda.
Coincidencias numericas de 8500/8501/9607 em campos do catalogo nao sao
referencias de skill demonstradas.

Nao foi demonstrada uma chamada de NPC aceita a distancia. A investigacao
foi somente leitura e nao aplicou efeitos nem enviou solicitacoes remotas.
Resumo em `build/analise_renovacao_giovanni/alternativa_sem_viagem.json`.
