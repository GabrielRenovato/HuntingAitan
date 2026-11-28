HuntingAitan 0.1.0-beta.43

Correção do fechamento do Season Pass.

- Envia apenas um `Esc` por aparição do passe.
- Aguarda duas capturas sem o passe antes de retomar o combate, evitando abrir o menu Sistema com um segundo `Esc`.

Validação: 12 testes de avisos e Season Pass aprovados.

Instalador: HuntingAitan-Setup-0.1.0-beta.43-x64.exe.

---

HuntingAitan 0.1.0-beta.42

Correção do início da caça e isolamento dos perfis.

- Corrige a falha `alvo_tecla_enviada` que impedia iniciar a caça com a opção de alvo em movimento.
- Mantém Domination, alfeim e SweThc separados na barra de tarefas e identifica cada janela pelo personagem.
- Compatibiliza a identificação de perfil com os testes e ambientes sem argumentos do processo.

Validação: 718 testes Python e verificações Node aprovados localmente.

Instalador: HuntingAitan-Setup-0.1.0-beta.42-x64.exe.

---

HuntingAitan 0.1.0-beta.41

Correcao do leitor do cliente atualizado e fechamento do Season Pass.

- Corrige os enderecos da cena, contexto, barra, efeitos e entidades para o hash do AIKACL.exe de 25/11/2026. Os enderecos anteriores permanecem nos layouts dos clientes antigos.
- Distingue tela de login de cena desconhecida. As falhas de leitura agora informam PID, hash e endereco para diagnostico.
- Reconhece o Season Pass por titulo e abas na mesma janela, reconfirma a captura e envia ESC ao cliente selecionado. Suspende o combate enquanto o painel estiver aberto e aguarda duas capturas livres antes de retomar. Inclui o monitor ocioso e as operacoes de entrada, saida e NPC.
- Inclui as alteracoes anteriores das betas.38 a .40: reconhecimento do novo hash, cursor configuravel e mensagem do atualizador.

Validacao: 718 testes Python e verificacoes Node aprovados localmente, incluindo reconhecimento visual em escalas e posicoes diferentes, liberacao do ESC e preservacao das barreiras de combate. O workflow repete a suite e confere o motor empacotado.

Limites: os novos globais foram conferidos estaticamente nos binarios; o combate completo no executavel atualizado ainda nao foi validado ao vivo. A ponte de comandos em segundo plano continua restrita aos hashes anteriormente validados. Nao adiciona suporte ao Aika Brasil nem remove validacoes de compatibilidade. O fechamento do passe foi validado com a captura fornecida e simulacoes; exige nova captura disponivel da janela. Nao altera os arquivos do jogo nem os perfis pessoais.

Instalador: HuntingAitan-Setup-0.1.0-beta.41-x64.exe.
