# Jardim Aéreo de Mirza · Difícil

O objetivo padrão agora é **Seridunn**, com combate restrito ao necessário.
A opção **Trecho curto · sair antes dos Shiraz** preserva o comportamento anterior.
O modo mantém o transporte em segundo plano já validado para saída e reentrada.
F12 e Parar continuam interrompendo a execução.

## Caminho até a área final

`tools/mapear_rota_seridunn.py` deriva a rota de `Env/z011312.att/.hgt/.dat` e
`Env/z011412.att/.hgt/.dat`, combinados numa grade de 512 × 256. As flags e
alturas impedem atravessar paredes, abismos ou desníveis não permitidos. A
geometria de objetos acrescenta custo para evitar passagens apertadas; colisões
observadas no jogo são excluídas pelo replanejamento existente.

O cadastro `UI/Dun.bin`, registros 20–23, confirma a entrada (3351,3295).
O objeto 3721 do segundo bloco, correspondente ao altar da área final, fornece
a referência (3633,5;3212,5). O traçado termina numa célula alcançável a até oito
unidades dessa referência: (3640,5;3209,5). Contém 2.452 células adjacentes e
2.701,18 unidades de percurso no terreno. O algoritmo minimiza distância e
penalidades de paredes/geometria; não há garantia de ser a rota com menos mobs.

O mapa gerado fica em `build/rota_seridunn.png`. Ele mostra o terreno, a entrada,
o traçado e o altar. Não representa spawns do servidor.

## Seridunn e combate

O catálogo `UI/MN.bin` identifica Seridunn, mas seus registros em `UI/MobPos.bin`
estão vazios. A posição do altar não é tratada como spawn confirmado do chefe.
Ao chegar à área final, o motor aguarda Seridunn reconhecido ao vivo; não sai da
DG nem registra conclusão apenas por chegar à coordenada.

- Hostis comuns a mais de 3,5 unidades, ou fora do trecho imediato do corredor,
  não interrompem a marcha normal.
- Mobs muito próximos que bloqueiam o próximo segmento podem ser enfrentados.
  Um bloqueio físico observado também libera a avaliação de hostis próximos.
- Sob dano, vida baixa ou controle de grupo, a defesa continua ativa e considera
  apenas hostis alcançáveis a até oito unidades. Cura e buffs permanecem no motor.
- Seridunn tem prioridade quando reconhecido e alcançável. A seleção atual também
  passa pelo filtro da rota; um alvo lateral previamente selecionado não autoriza
  perseguir outros grupos.
- Um hostil comum que sai da passagem não é perseguido. Seridunn mantém a luta.
- O abate é registrado após leituras confirmadas de vida zero. Só esse registro
  libera conclusão, saída, serviço no NPC se configurado e nova entrada.

Esse modo não garante passagem sem combates. A instalação local não contém uma
lista completa validada de gatilhos do servidor, portões ou requisitos para
habilitar Seridunn; o cliente não permite concluir que todas as lutas são opcionais.

## Validação

O caminho completo foi reconferido na grade e nos objetos locais. Testes cobrem
preservação do trecho curto, passagem adjacente, hostis laterais, defesa próxima,
chefe atrás de parede, prioridade de Seridunn e ausência de conclusão sem abate.
Um teste do motor simula a seleção, ataque e confirmação de vida zero do chefe
antes de emitir a conclusão. O seletor de objetivo foi salvo e recarregado pela
interface Electron real em perfil de teste separado.

A suíte geral passou com 707 testes Python e verificações Node. Compilação local:
`build/jardim-seridunn-local/win-unpacked`. Alterações incluídas na beta.37.

O primeiro teste real desta alteração não enviou comandos: o cliente selecionado
estava na tela de login. A travessia até Seridunn e os requisitos do servidor
continuam pendentes de validação no jogo. A saída/reentrada ao fundo validada
anteriormente não demonstra o percurso inteiro nem o abate do chefe.

## Regeneração

```powershell
python tools/mapear_rota_seridunn.py --game-dir "C:\GoLevel\AikaOnline" --out huntingaitan/dados/jardim_seridunn_rota.json --imagem build/rota_seridunn.png
```

O script antigo `tools/validar_jardim_aereo.py` continua regenerando somente
`jardim_aereo_rota.json`, usado pela opção de trecho curto.
