HuntingAitan 0.1.0-beta.34

Novos circuitos de Croshus e correções de pausas e uso de habilidades.

- Amplia o circuito da Floresta Cinzenta para cinco Croshus: 7 → 8 → 9 → 11 → 10, incluindo os dois próximos de 2697, 1106.
- Adiciona um circuito separado de seis Croshus roxos ao sul, perto de 2955, 1311. A rota anterior permanece disponível.
- Os circuitos compartilham seleção por identidade, navegação com colisão e transições pela ponte interna quando o segundo plano está habilitado.
- Uma habilidade recusada pelo cliente cede a vez às demais, sem contar como execução nem iniciar uma recarga fictícia.
- Corrige a confirmação de curas de efeito contínuo, como Revitalize: efeito novo e início da recarga confirmam a aplicação mesmo quando o dano recebido mascara a recuperação de HP. Curas conjuradas continuam aguardando o término.
- Buffs em slots confirmados como vazios deixam de suspender o percurso; itens e atalhos sem leitura confirmada são preservados.

Validação: 669 testes Python e verificações Node aprovados, além do teste do motor empacotado. Nos testes curtos da templária, houve três abates por sessão e execução das skills 4 e 5 confirmada por recarga com a janela sem foco.

Limitações: segundo plano segue experimental e exige o Aika aberto, sem minimizar. Mina e Jardim usam o modo normal. Os testes curtos não comprovam estabilidade prolongada ou uma volta completa no circuito sul. A renovação de Giovanni permanece desativada. Perfis pessoais, capturas e diagnósticos locais não acompanham a atualização.

Instalador: HuntingAitan-Setup-0.1.0-beta.34-x64.exe.
