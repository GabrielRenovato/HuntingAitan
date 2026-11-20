Diagnóstico do Jardim disponível antes da primeira leitura.

Corrige a ausência do PNG enquanto o OCR demora: antes, o recorte só era salvo após quatro leituras sem confirmação. Agora o PNG e o JSON são criados antes da primeira chamada ao OCR e atualizados nas tentativas seguintes, mantendo apenas um par de arquivos por sessão.

Após clicar em Começar com o Aika em foco, abra Comportamento → Escala da interface → Abrir diagnósticos. Envie o par mais recente jardim_dificuldade_*.png e .json. Se a leitura ficar pendente ou falhar, o recorte já estará disponível.

289 testes Python e verificações do painel e atualizador passaram, incluindo a existência do PNG antes de um OCR que falha. Esta versão melhora a coleta de evidências; a causa específica da leitura ilegível no PC do amigo ainda precisa ser analisada com o recorte real.

Instalador: HuntingAitan-Setup-0.1.0-beta.25-x64.exe.
