# Escolher o cliente do Aika

Na aba **Básico**, use **Cliente do Aika → Atualizar**. A lista mostra o nome do personagem lido em cada processo e seu PID. Selecione a conta desejada antes de clicar em **Começar**. O campo **Personagem controlado** é separado de **Alvo atual**; selecionar outro jogador no Aika não muda a conta escolhida no painel.

A escolha salva o par `client_pid`/`client_hwnd`. Leitura de posição, combate, buffs, captura de avisos, monitor ocioso e etapas de dungeon usam essa seleção. Trocar de janela pausa o envio de comandos. A escolha não muda enquanto a caça estiver rodando. Caso o cliente seja fechado, o hunting pede para atualizar e selecionar novamente, sem assumir outra conta automaticamente. Após reiniciar o jogo, o PID pode mudar.

**Automático** mantém o comportamento para uma única instância. Com duas contas abertas, selecione explicitamente a conta no painel.

O leitor continua validando o executável por SHA-256. Esta versão inclui o original e a cópia local `AIKACL-multiinstancia-teste.exe`, cujo hash é `e286c435100b7e03ec326fba6ae4ec94ea4f9ed17c3e473a2c37a2f3651834b3`. A comparação local confirmou mesmo tamanho e apenas um byte diferente, no offset de arquivo `0x5627`, alterando a checagem de instância; offsets e estruturas de dados permanecem iguais. Isso não libera executáveis desconhecidos. Falhas de leitura, carregamento ou versão aparecem individualmente na lista.

Os atalhos de habilidades, cura e buffs continuam sendo os configurados no painel; confira a correspondência com a barra do personagem escolhido. Selecionar outra conta não importa nem substitui seus atalhos automaticamente.
