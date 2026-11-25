# Motor de caça em segundo plano

O modo `background_keys` vincula leitura e comandos ao mesmo PID e HWND. A ponte temporária executa câmera, seleção, habilidade e movimento na thread da janela do cliente com hash validado. Itens e cliques ainda usam mensagens da janela. O executável do jogo em disco não é modificado.

## Regras de execução

- A recuperação de alvo usa a referência e o ID do hostil vivo anterior. Não percorre outros alvos com TAB durante essa recuperação.
- A ausência do painel não confirma morte. São necessárias leituras de vida zero; regeneração não é contabilizada como dano.
- O navegador usa a grade carregada e bloqueia temporariamente a passagem que não produziu avanço, para procurar outro caminho. Destinos próximos não reiniciam continuamente um movimento em andamento.
- Parada e janelas modais bloqueiam novos comandos. A confirmação de uma conjuração impede ataques e deslocamento concorrentes; consumíveis de emergência configurados podem ter prioridade.
- A agenda confirma buffs pelo ID do efeito ativo. Sem confirmação, adia aquela tecla e libera as demais. Stun e cura urgente interrompem a espera sem contabilizar sucesso.
- Regras de habilidades são comparadas com a barra do personagem. Níveis da mesma habilidade são atualizados apenas na sessão; outra habilidade gera erro. Slots vazios da agenda são ignorados com aviso.
- `session_summary` registra abates, recuperações, buffs confirmados, recusas e desvios. Uma chamada aceita não prova dano; os eventos mantêm essa distinção.

## Limites

Manter o cliente aberto, sem minimizar. A Mina ainda não permite o modo em segundo plano. O Jardim tem suporte experimental na compilação local descrita abaixo. O cancelamento de animações por teclas fica desativado nesse modo. O prazo dos buffs continua configurado pelo perfil: ler o ID ativo não fornece a duração restante. Consumíveis enviados por mensagens ainda não têm a mesma confirmação de aplicação das habilidades.

## Jardim experimental — 25/11/2026

O ciclo transmite a opção de segundo plano às operações de entrada, saída de
grupo e serviço no NPC. Percurso, seleção e habilidades usam a ponte interna;
as etapas de interface usam Windows Graphics Capture e mensagens destinadas ao
HWND selecionado. A leitura inicial de Difícil também usa a captura dessa janela,
sem depender da imagem do desktop. O modo normal conserva a implementação anterior.

Validação automatizada: 696 testes Python, verificações Node e smoke do motor
empacotado aprovados. Os testes cobrem entrada no Difícil, saída, reparo/venda
pela janela, espera pelo carregamento, barra de grupo e quina do retorno.

No primeiro teste real de 120 segundos, a templária confirmou 25 abates, HP
mínimo de 99,90% e 136 de 239 amostras sem foco. A interação 3D do altar falhou
nas tentativas iniciais. A investigação dos binários e a comparação manual
mostraram que o ponto sobre o nome não identificava o altar sob o cursor,
embora o cursor interno e o raio de seleção atualizassem ao fundo.

A correção movimenta apenas o cursor virtual da janela e confere nome, posição
cadastrada e duas leituras da mesma entidade antes do duplo clique. A identidade
é reconfirmada antes de cada mouseDown. Nenhum candidato da busca é clicado
sem essa confirmação; não foram adicionadas chamadas nativas novas à ponte.

Em `build/jardim_interface_fundo_20261125_144846`, o teste confirmou saída do grupo,
retorno ao altar e reentrada automática no Difícil por posição e indicador.
Foram 280 amostras sem foco no Aika, com HP mínimo 100%, sem clique manual nessa
rodada. A thread respondeu após o carregamento e o motor reconectou; o teste
curto seguinte terminou normalmente em nove segundos, durante o ciclo de buffs,
sem abates. Isso não valida uma DG inteira nem estabilidade por várias repetições.
Serviço no NPC ao fundo continua validado somente por simulação.

Detalhes e evidências em `docs/INTERACAO_JARDIM.md`. Compilação local:
`build/jardim-segundo-plano-corrigido/win-unpacked`. Alterações incluídas na beta.37. A beta.36 mantém a restrição anterior.

## Validação local de 23/11/2026

Suíte geral: 587 testes Python e verificações Node aprovados; cinco casos adicionais de validação da barra e efeitos ativos passaram depois, no conjunto direcionado de 21 testes. O emulador x86 verifica preservação de estado, encaminhamento de mensagens e restauração do procedimento original.

Em `build/validacao_estavel_20261123_175654`, a templária confirmou 17 abates em 120 segundos, HP mínimo de 80,7%, um buff pelo efeito ativo e parada normal. Houve 108 chamadas recusadas pelo cliente, registradas como recusas, sem contar como execução. O foco esteve fora da janela da templária na maior parte das amostras. A seleção exata do alvo 6760 foi confirmada e a ponte de teste removida.

O guerreiro não iniciou o farm desse teste: estava fora do circuito de Penzas selecionado. Sua barra foi lida e corresponde às regras atuais. O perfil foi posteriormente trocado, a pedido do usuário, para o circuito dos três Croshu das Cinzas; ele requer início perto de 2882, 1154. Esse circuito não foi validado ao vivo com este novo motor.

O backend empacotado passou em `tools/smoke_backend.py`. Build local: `build/motor-interno-estavel-local/win-unpacked`. Não houve publicação de release. Esses testes curtos não comprovam estabilidade de farm prolongado.
