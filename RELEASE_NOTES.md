HuntingAitan 0.1.0-beta.36

Corrige o bloqueio do Jardim em clientes com outro idioma.

- UI/Dungeon.bin passa a ser validado pelo formato da tabela e pelo nome do Jardim no registro esperado, aceitando Jardim Aéreo de Mirza e Kynari Aviary.
- Diferenças nos textos localizados deixam de exigir a revalidação da rota inteira.
- Arquivos de terreno, alturas, objetos e cadastro da DG continuam sujeitos à conferência por hash. A alteração de um desses arquivos ainda bloqueia o percurso e informa qual precisa de revalidação.
- O gerador de rota também reconhece as duas traduções.

Validação: 677 testes Python e verificações Node. Regressões cobrem português/inglês, outra DG, tabela vazia ou truncada, arquivo ausente e terreno alterado. Os arquivos locais do Jardim foram reconferidos. O PC do amigo ainda precisa confirmar o funcionamento após atualizar.

Mantém as correções da beta.35 para pausas dos sete Verits e campos X/Y. Jardim e Mina continuam exigindo o modo normal, com o jogo em primeiro plano.

Instalador: HuntingAitan-Setup-0.1.0-beta.36-x64.exe.
