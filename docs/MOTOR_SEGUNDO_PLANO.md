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

Manter o cliente aberto, sem minimizar. Mina e Jardim ainda não permitem o modo em segundo plano. O cancelamento de animações por teclas fica desativado nesse modo. O prazo dos buffs continua configurado pelo perfil: ler o ID ativo não fornece a duração restante. Consumíveis enviados por mensagens ainda não têm a mesma confirmação de aplicação das habilidades.

## Validação local de 23/11/2026

Suíte geral: 587 testes Python e verificações Node aprovados; cinco casos adicionais de validação da barra e efeitos ativos passaram depois, no conjunto direcionado de 21 testes. O emulador x86 verifica preservação de estado, encaminhamento de mensagens e restauração do procedimento original.

Em `build/validacao_estavel_20261123_175654`, a templária confirmou 17 abates em 120 segundos, HP mínimo de 80,7%, um buff pelo efeito ativo e parada normal. Houve 108 chamadas recusadas pelo cliente, registradas como recusas, sem contar como execução. O foco esteve fora da janela da templária na maior parte das amostras. A seleção exata do alvo 6760 foi confirmada e a ponte de teste removida.

O guerreiro não iniciou o farm desse teste: estava fora do circuito de Penzas selecionado. Sua barra foi lida e corresponde às regras atuais. O perfil foi posteriormente trocado, a pedido do usuário, para o circuito dos três Croshu das Cinzas; ele requer início perto de 2882, 1154. Esse circuito não foi validado ao vivo com este novo motor.

O backend empacotado passou em `tools/smoke_backend.py`. Build local: `build/motor-interno-estavel-local/win-unpacked`. Não houve publicação de release. Esses testes curtos não comprovam estabilidade de farm prolongado.
