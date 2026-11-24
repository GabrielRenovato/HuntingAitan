# HuntingAitan

Painel experimental de caça automática para Aika, com motor Python e interface Electron. Este repositório é a fonte das próximas versões. O projeto ainda tem limitações de combate e não garante que o personagem sobreviva sem acompanhamento.

## Baixar e testar

Abra [Releases](https://github.com/GabrielRenovato/HuntingAitan/releases) e baixe `HuntingAitan-Setup-<versão>-x64.exe`. O instalador inclui o motor; o usuário não precisa instalar Python, Node ou UoPilot. Execute o aplicativo como administrador, abra o Aika, configure os atalhos de acordo com a sua barra e teste primeiro com acompanhamento. O F12 original deve estar desligado; F12 encerra a nossa caça.

O leitor só aceita o executável do Aika com SHA-256 `a378297211a51bd0032975b2263c78b962a3a734caf5705a80319d129d246a3b`. Outra versão do jogo precisa de validação do layout; não basta desativar a conferência. A leitura interna de posição, HP e alvo não depende da resolução. A detecção visual de convites e conversas depende da escala do HUD e ainda não foi validada em todas as resoluções.

## Atualizações

O aplicativo instalado consulta GitHub Releases ao abrir e a cada 30 minutos. Baixa a nova versão em segundo plano. Com a caça parada, oferece reiniciar para instalar; durante a caça, preserva a sessão e instala ao fechar o aplicativo. Não funciona como atualizador na execução de desenvolvimento. As versões beta recebem o canal beta. Configurações e diagnósticos ficam em `%APPDATA%/aika-caca-automatica`, separados da instalação e preservados nas atualizações. Sem conexão, o aplicativo continua funcionando.

## Desenvolvimento no Windows

Use Python 3.12 e Node 22. No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-build.txt
npm ci
npm ci --prefix aika_hunt_app
npm test
npm start
```

O Python no PATH é usado no desenvolvimento. Para outro interpretador, defina `AIKA_PYTHON` ou crie `aika_hunt_app/runtime.local.json` com `{"python":"C:/caminho/python.exe"}`. Esse arquivo é ignorado pelo Git. Não rode a cópia de desenvolvimento e a instalada controlando o jogo ao mesmo tempo.

## Publicar uma correção

A beta.33 acrescenta seletor de cliente, editor visual de regras, circuitos e motor experimental em segundo plano. O jogo precisa permanecer aberto e sem minimizar; Mina, Jardim e renovação da bênção não estão validados em segundo plano. A renovação de Giovanni continua desativada. Consulte [as notas da versão](RELEASE_NOTES.md) e [a documentação do motor](docs/MOTOR_SEGUNDO_PLANO.md) antes de ativar esse modo.

1. Faça a alteração, atualize `CHANGELOG.md` e rode `npm test`.
2. Ajuste a mesma versão nos dois `package.json` e nos respectivos lockfiles. Exemplo: `0.1.0-beta.29` para a próxima beta.
3. Atualize `RELEASE_NOTES.md`, faça commit e push.
4. Crie a tag correspondente e envie: `git tag v0.1.0-beta.29` e `git push origin v0.1.0-beta.29`.

O workflow verifica a versão, executa os testes, empacota o backend, gera o instalador NSIS e publica instalador, blockmap e metadados YAML na release. O token vem do GitHub Actions; não deve ser colocado no aplicativo. O workflow falha sem publicar se um desses passos falhar. Tags com sufixo beta são publicadas como pré-release.

Para gerar o instalador localmente: `npm run build`. Saída em `release/`. O teste `python tools/smoke_backend.py` valida o motor empacotado sem iniciar a caça. O executável não recebe assinatura Authenticode sem um certificado configurado no ambiente de build.

As ferramentas opcionais de análise dos arquivos locais e o emulador da ponte usam `python -m pip install -r requirements-dev.txt`. Elas não são necessárias para executar o instalador. Dumps e resultados dessas ferramentas ficam locais e ignorados pelo Git.

## Conteúdo versionado

Código, testes e recortes genéricos da interface usados pelo painel/detector. Não inclui o executável do jogo, contas, conversas, capturas de sessões, logs, credenciais, perfis pessoais ou scripts históricos de outras rotas. A instalação distribuída contém apenas o motor por dados internos; o modo visual legado não faz parte desta release.

Para reportar um problema, informe a versão mostrada no painel e envie apenas o trecho relevante do diagnóstico, revisando os dados pessoais antes de compartilhar. Recursos e marcas do Aika pertencem aos respectivos titulares; este é um projeto independente.

Manutenção do leitor após atualizações do jogo, verificação de layout e replay offline de sessões: [docs/MANUTENCAO_DO_LEITOR.md](docs/MANUTENCAO_DO_LEITOR.md).

A calibração do cancelamento e suas limitações estão em [docs/CALIBRACAO.md](docs/CALIBRACAO.md). Ative **Padrão 1RR1WW e skills calibradas** na aba Comportamento para usar esse modo.

O fechamento de CTE, Arena Elter e conversas está descrito em [docs/JANELAS.md](docs/JANELAS.md), incluindo o que foi validado e as limitações.

Circuito de Termes: veja [as instruções e a validação das passagens](docs/CIRCUITO_TERMES.md).

Mina L’Enfer → Malik, com repetição opcional no Elite e retorno do save até a entrada: veja [o modo e a validação](docs/MINA_LENFER.md).

Jardim Aéreo de Mirza no Difícil, até antes dos Lazapas finais e saída do grupo: [modo e validação](docs/JARDIM_AEREO.md).

Em **Comportamento → Escala da interface**, mantenha **Detectar escala da dificuldade automaticamente** ativado ao trocar de resolução, monitor ou computador. A opção adapta a leitura do indicador da DG; o Jardim continua exigindo Difícil e o ciclo da Mina, Elite.

Se o Jardim informar indicador ilegível, use **Comportamento → Escala da interface → Abrir diagnósticos**. A pasta contém o recorte `jardim_dificuldade_*.png` e o JSON com as tentativas, salvos antes do primeiro OCR e atualizados em cada tentativa.

No cliente em inglês, o indicador **Hard** é aceito como **Difícil** no Jardim; a escolha das demais dificuldades continua sendo verificada.

Em **Comportamento → Ataque normal**, configure **Pausa entre teclas** e **Intervalo entre sequências** separadamente. Os padrões são 0 ms entre teclas e repetição estimada do Windows (valor 0). Os controles permitem ajustar o ritmo sem importar um perfil do X-Mouse.
