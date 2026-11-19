# Jardim Aéreo de Mirza · Difícil

Selecione o modo no painel com o personagem já dentro do Jardim no Difícil. O modo confere a dificuldade no indicador do jogo, percorre as plataformas combatendo os hostis do trajeto e prioriza Seridunn quando alcançável. F12 interrompe. A cura, as recargas e a exclusividade dos cinco buffs usam o motor existente.

## Fontes locais

- `UI/Dungeon.bin`, título de índice 5: Jardim Aéreo de Mirza; a descrição cita Seridunn.
- `UI/Dun.bin`, registros 20–23: origem 3328,3072 e entrada 3351,3295. O registro 21 corresponde à segunda dificuldade; o indicador Difícil é reconfirmado na tela.
- `Env/z011312.att/.hgt/.dat` e `Env/z011412.att/.hgt/.dat`: dois blocos de 256×256, combinados numa grade de 512×256.
- `Objects/mirzaF0099.MS3`, instância ID 3721 no segundo bloco: referência do altar de Seridunn, em 3633,5 / 3212,5.

O arquivo `jardim_aereo_rota.json` registra as fontes e seus hashes. O caminho estático contém 2.408 células e aproximadamente 2.634 unidades, com todos os passos adjacentes e as transições conferidas. Ao iniciar em outra posição dentro da DG, recalcula a rota até o altar. A grade carregada no cliente continua sendo reconfirmada durante a navegação.

## Conclusão e limitações

A chegada ao altar não conclui a DG. É necessário reconhecer o nome Seridunn, confirmar sua vida zero por duas leituras e aguardar quinze segundos sem hostis na região final. Malik, portões, administradores e Seridunn Corrompido não contam como esse chefe.

A conectividade estática não comprova que um portão está aberto nem substitui a validação das fases no jogo. A validação ao vivo está em andamento. Este modo começa dentro da DG e ainda não automatiza saída, retorno externo e nova entrada do Jardim; a opção de repetição da Mina não se aplica a ele. Não se deve usar o portal ou a dificuldade da Mina para esta DG.

## Regeneração

```powershell
python tools/validar_jardim_aereo.py --game-dir "C:\GoLevel\AikaOnline" --out jardim_aereo_rota.json
```
