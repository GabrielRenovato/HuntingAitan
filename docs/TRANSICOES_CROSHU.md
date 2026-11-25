# Transicoes rapidas no circuito dos Croshus das Cinzas

O modo `cinzenta_croshu_trio` com `background_keys` ativo passa a compartilhar as quatro transicoes da templaria: proximo ID depois da morte confirmada, confirmacao de habilidade pelo estado do cliente, passagem continua por revisitas vazias e nova busca no mesmo ciclo quando uma passagem e excluida.

A rota ampliada em 24/11 segue 7 → 8 → 9 → 11 → 10 → 7, incluindo a coordenada corrigida do ponto 7 em 2885, 1196 e os dois Croshus perto de 2697, 1106. O modo continua aceitando somente Croshu Mutante das Cinzas. Skills, cura, buffs, cancelamento e protecoes do guerreiro conservam sua configuracao. Nao ativa a limpeza de outros hostis nem o controle de ataque normal especificos da templaria.

`EscolhaPorCaminho` compartilha validacao de caminho e selecao direta. `VisitasCircuito` compartilha observacao das paradas, invalidacao quando um mob reaparece e transicao antecipada apenas de pontos conhecidos com leitura fresca. A primeira visita ainda confere a parada. Os dois componentes tambem sao usados no circuito Verit leste, evitando manter duas implementacoes das mesmas transicoes.

Validacao: 642 testes Python e verificacoes Node passaram, assim como o smoke test do backend empacotado. O teste integrado dos Croshus confirma tres abates e duas trocas diretas, sem ativar limpeza de outros mobs. Os testes preservam a visita ao terceiro ponto e bloqueiam a marca de vazio quando um Croshu reaparece.

No teste real `build/teste_guerreiro_20261123_201214`, alfeim percorreu quatro voltas e confirmou dois abates em cerca de 120 segundos. Terminou normalmente com codigo zero, HP minimo de 82,69% e sem erros. Nao houve oportunidade registrada de troca direta para outro alvo nesse intervalo; essa transicao foi verificada por simulacao. Houve 179 recusas de chamadas pelo cliente, registradas separadamente de acao aceita. O teste curto nao comprova estabilidade prolongada.

Compilacao local: `build/croshu-transicoes-local/win-unpacked`. O painel do guerreiro usa o perfil separado `aika-caca-automatica-segundo`; o da templaria foi preservado.

Em 25/11/2026, o log do guerreiro mostrou duas falsas falhas de Revitalize
(skill 49): o efeito novo estava ativo e a recarga tinha iniciado, mas o dano
recebido mascarava a recuperacao de HP. A confirmacao passa a aceitar esse par
de evidencias para curas de efeito continuo, sem liberar antecipadamente as
curas conjuradas de Remediar. Efeito antigo ou sem inicio de recarga nao basta.

Outra correcao impede que uma skill recusada monopolize a fila. A tentativa
cede a vez, sem contar como execucao nem iniciar a recarga configurada. No teste
local da templaria, foram observados inicio de recarga de Emision Divina (4) e
Thymos (5) com a janela sem foco. Isso confirma essas execucoes; nao comprova
que toda habilidade esteja utilizavel em qualquer estado do cliente.
