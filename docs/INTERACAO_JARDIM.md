# Interação com o altar — investigação de 25/11/2026

A investigação encontrou uma dependência do clique 3D que o teste de mensagens
não media: a direção de seleção calculada pelo cliente e a entidade reconhecida
sob o cursor. A comparação ao vivo, descrita abaixo, mostrou que essa direção
é atualizada ao fundo, mas o ponto do texto escolhido pelo script não identifica
o altar no mundo 3D.

## Evidência reproduzida

`python tools/analisar_interacao_jardim.py` analisa o PE em disco, sem executar
suas funções. Gera `build/analise_interacao_jardim/manifesto.json`, tabelas RTTI,
referências de APIs e trechos de desmontagem. O manifesto inclui os hashes de
cada trecho e a comparação com a variante de múltiplas instâncias. Os dez
trechos investigados são idênticos nas duas variantes locais.

Cliente original: SHA-256
`a378297211a51bd0032975b2263c78b962a3a734caf5705a80319d129d246a3b`.
Cliente em execução: SHA-256
`e286c435100b7e03ec326fba6ae4ec94ea4f9ed17c3e473a2c37a2f3651834b3`.
Os VAs abaixo usam a base preferencial `0x400000`; não são endereços absolutos
da sessão. A leitura real confirmou base `0xf70000` e método de mouse no RVA
`0x96130`, correspondente à classe `JFieldScene`.

| Etapa | Evidência |
| --- | --- |
| Recepção de mensagens | `0x40f0c6` extrai X/Y do LPARAM de WM_MOUSEMOVE. Os ramos seguintes encaminham cliques e duplo clique para `0x46c8d0`. |
| Despacho | `0x46c8d0` encaminha X/Y ao gerenciador de interface e chama o método virtual da cena no deslocamento `0x28`. |
| Cena real | RTTI: `JFieldScene`, vtable `0x72bfdc`, método `0x496130`. A leitura da templária confirmou o mesmo RVA. |
| Clique inicial | Em `0x4962d7`, chama `0x5754c0`. Essa função consulta terreno por `0x5a0820` e prepara um destino de movimento. Não usa os X/Y do evento para recalcular o raio nesse trecho. |
| Duplo clique | Em `0x4963c1`, o ramo WM_LBUTTONDBLCLK chama `0x50f640`, que consulta campos da cena `+0x90` e `+0x108` e chama as rotinas de seleção/ação. A coordenada do evento não substitui esses campos automaticamente. |
| Seleção 3D | `0x5a0820` chama `0x59f6d0` no modo correspondente. `0x59f6d0` lê os vetores já armazenados no gerenciador gráfico em `+0x5c0` e `+0x5cc`. |
| Atualização da direção | `0x4771e0` transforma o cursor interno do gerenciador de interface (`+0x3c/+0x3e`) usando projeção e câmera. O laço em `0x40e1bf` chama essa rotina para preencher os vetores usados pela seleção. |
| Mouse contínuo | `0x46bb00` chama GetActiveWindow e retorna antecipadamente se não corresponde ao HWND do cliente. Depois lê o dispositivo por GetDeviceState. Esse bloqueio existe, mas não demonstra sozinho que o despacho de cliques acima seja bloqueado pelo foco. |

`tools/ler_contexto_interacao_jardim.py` leu a tabela virtual da templária por
PID/HWND selecionados, sem instalar ponte ou enviar comandos. Resultado em
`build/analise_interacao_jardim/contexto.json`. A primeira tentativa sem elevação
foi recusada; a leitura elevada confirmou a classe e o método.

## Conclusão e aplicação

Dois cliques e até WM_LBUTTONDBLCLK não garantem interação com o objeto desejado.
É necessário conferir se o estado de seleção 3D corresponde ao altar no momento
do clique. A hipótese a testar é a desatualização ou divergência entre cursor,
raio e entidade sob o cursor quando a janela está ao fundo. Outra possibilidade
é o ponto reconhecido sobre o texto não atingir a geometria clicável do altar.

O teste seguinte deve registrar esses estados antes/depois de um movimento de
cursor destinado à janela e comparar com a interação manual que funciona.
Só então cabe adaptar a ponte para a preparação da seleção na thread correta,
preservando o cursor do usuário e confirmando o menu aberto por captura atual.
A rotina `0x4771e0` é candidata para essa preparação, não uma operação validada
de abertura de NPC. Não foi adicionada à ponte nesta investigação.

Não houve alteração do executável do jogo nem execução de chamadas internas
novas. Na conclusão da etapa estática, a reentrada ainda não havia sido validada. O
reconhecimento do indicador Difícil após mudança de posição permanece necessário;
retorno de função ou clique enviado não confirma entrada.

## Comparação ao vivo

Em `build/comparacao_altar_20261125_144248`, a leitura inicial do cursor interno
em (1032,342) reconhecia a entidade 2258, nome `Altar da Ascensão`. O script
enviou uma tentativa em (790,248), centro do texto encontrado na imagem. A
leitura seguinte confirmou o cursor nessa coordenada e o raio atualizado, mas
a referência sob o cursor passou a zero. O menu não abriu. Portanto, a hipótese
de raio obrigatoriamente congelado ao fundo não explica esta tentativa.

Na interação manual solicitada, em torno de 59 segundos, o cursor interno
(1045,566) reconheceu novamente a mesma entidade. O quadro 67 mostra o menu
`Entrar Jardim Aéreo` aberto. A posição do personagem permaneceu
(1840.3422,1091.1405), com HP 100%. A amostragem não registrou troca de foco,
portanto não é uma comparação válida entre foreground e background; é uma
comparação entre pontos de interação diferentes, com abertura manual confirmada.

A correção local em `interacao_altar.py` usa o texto apenas como região inicial.
Movimenta somente o cursor virtual da janela e exige duas leituras consecutivas
da mesma referência/ID com nome de altar e posição próxima ao cadastro. Não
envia cliques nos candidatos da busca. O duplo clique só ocorre após a identidade
ser reconfirmada; se nenhum ponto corresponder ao altar, a etapa permanece sem
clicar. Não foi necessário adicionar chamadas nativas novas à ponte.

Os testes cobrem entidade diferente, posição incorreta, parada, troca da entidade
entre leituras e coordenadas em monitor à esquerda. A identidade também é
reconfirmada imediatamente antes de cada mouseDown.

## Validação da correção

`build/jardim_interface_fundo_20261125_144846/resultado.json` confirmou saída de
grupo, retorno ao altar, abertura automática do altar, seleção de Difícil e nova
entrada validada por posição e indicador. As 280 amostras foram sem foco no
Aika, HP mínimo 100%, sem clique manual nessa execução. O clique no altar só
foi registrado após a confirmação do NPC 2258 sob o cursor. A prontidão da thread
após reentrada foi confirmada, e o motor reconectou e encerrou normalmente por
`tempo_encerrado` no teste curto de nove segundos. Nesse trecho ele estava no
estado de rebufar, sem abates; não é evidência de uma nova DG completa.

A suíte geral passou com 696 testes Python e as verificações Node. O motor
empacotado passou no smoke. Compilação local:
`build/jardim-segundo-plano-corrigido/win-unpacked`. Alterações incluídas na beta.37.
