# Grupo de três Butos na Floresta Cinzenta

No painel, selecione **3 Butos · Floresta Cinzenta** em **Modo de caça**. Comece próximo a **2711, 1292**, com o F12 original desligado, e clique em **Começar**. F12 encerra o nosso motor.

O modo usa o motor existente, com centro fixo em `(2711, 1292)`, raio de 30 unidades e filtro exclusivo **Buto Mutante**. O raio contém os pontos 1, 6 e 7 do [mapeamento](mapeamento_buto/README.md), excluindo os outros sete pontos cadastrados. Não fixa IDs de entidades: eles mudam no respawn. Um Buto que se afaste para fora da região pode deixar de ser elegível; também não se promete exatamente três entidades simultâneas.

O motor seleciona um alvo elegível, mantém a seleção durante o combate e confirma o abate pela leitura de vida. Depois procura outro Buto na região. Volta ao centro quando não restam alvos acessíveis e aguarda novos alvos. As recuperações existentes continuam aplicadas para stun, alvo perdido, ausência de dano e passagem bloqueada; nenhuma delas registra um abate sem confirmação.

Habilidades, cura, suprimentos, buffs e fechamento de avisos usam a configuração atual do painel. O modo não muda esses atalhos. O início é recusado se o personagem estiver a mais de 35 unidades do centro, para evitar uma viagem involuntária de outro local.

Validação automatizada: filtro dos dez pontos cadastrados (aceita somente 1, 6 e 7), rejeição de NPCs e outras espécies, preservação de atalhos, simulação de dois grupos sucessivos com seis abates, ausência de TAB durante um alvo vivo e retorno apenas depois de limpar cada grupo. Isso não substitui uma sessão de validação no jogo.

## Duas janelas do Aika

Use o [seletor de cliente](SELETOR_CLIENTE.md) na aba Básico para escolher o personagem. Leitura, foco e captura usam a janela selecionada, não apenas o título `AikaClient`, que é compartilhado por várias contas. O original e a cópia local de teste possuem layouts identificados por hash nesta versão. Se outra janela estiver em primeiro plano, o envio de teclas pausa; ao começar, o painel tenta trazer a janela vinculada para a frente. O log identifica o HWND, PID e personagem lido para permitir conferir a conta correta.

Diagnóstico da tentativa `run_20261121_134020.jsonl`: 186 leituras com três Butos elegíveis, mas alvo lido sempre `Domination` (não hostil), sem ataques enviados. Havia dois processos do Aika abertos. O código anterior permitia que o foco de uma janela com o mesmo título autorizasse entradas enquanto se lia outra instância. A correção impede essa mistura, mas ainda é necessário repetir a sessão real para confirmar se ela explica toda a falha observada.

Na tentativa posterior `run_20261121_134759.jsonl`, a janela estava vinculada a `DilmaRusef`; `Domination` era o alvo selecionado. Essa sessão terminou após 11,7 segundos, durante o quarto buff, sem concluir o ciclo inicial de buffs. Essa observação isolada não demonstra mistura de leitura e controle.
