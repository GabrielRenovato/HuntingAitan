# Circuito Penza de Termes

No painel, abra **Comportamento → Modo de caça → Circuito Penza · Termes**.
Comece dentro da faixa, por exemplo perto de **2584, 587** ou **2592, 697**.
O modo seleciona somente **Penza Poderosa Mutante**. A caça em torno da base
continua disponível como modo separado e permanece padrão nas instalações existentes.

O circuito percorre **6 → 5 → 4 → 7 → 8 → 9 → 8 → 7 → 4 → 5 → 6** e repete.
A entrada pode ocorrer perto de qualquer trecho da faixa; não exige voltar ao ponto 6.
Os destinos são 2584,587; 2585,654; 2577,674; 2592,697; 2584,712; 2612,748.
O personagem aguarda cinco segundos em cada parada e procura candidatos pela lista
de entidades carregadas. O alcance configurado limita a distância de seleção ao
personagem. A região permitida acompanha o trajeto numa faixa de 20 unidades;
o raio da base inicial não limita o circuito inteiro.

Ao encontrar um Penza válido, pausa o percurso e usa o combate existente.
Após o abate confirmado, procura outros Penzas próximos e retoma o trecho atual.
O ciclo de buffs permanece exclusivo. Controle de atordoamento, cura prioritária
e fechamento de CTE/Elter continuam ativos. O painel mostra o ponto de destino e
o número de voltas. Se uma passagem deixa de existir na grade atual, aguarda e
relê a colisão, sem marcar o ponto como concluído.

## Validação dos arquivos locais

A ferramenta `tools/validar_circuito_termes.py` lê `Env/AttributeS01.dat` e
`Env/z01.hgt`. São grades de 4096 × 4096; a tabela de alturas tem quatro bytes
de cabeçalho. O encaixe XY foi conferido linha por linha com os tiles
`z011002.att/.hgt`.

O A* usa as mesmas regras de bloqueio, quinas e desnível do navegador local,
limitado à faixa do circuito. Cada transição da rota gerada é conferida.
Todos os dez trechos possuem passagem nos arquivos analisados:

| Trecho | Células | Distância na grade |
| --- | ---: | ---: |
| 6 → 5 | 68 | 68,24 |
| 5 → 4 | 21 | 23,31 |
| 4 → 7 | 24 | 29,21 |
| 7 → 8 | 16 | 18,31 |
| 8 → 9 | 37 | 47,60 |
| 9 → 8 | 37 | 47,60 |
| 8 → 7 | 16 | 18,31 |
| 7 → 4 | 24 | 29,21 |
| 4 → 5 | 21 | 23,31 |
| 5 → 6 | 68 | 67,41 |

`huntingaitan/dados/circuito_termes_penza.json` contém os caminhos derivados e os SHA-256 dos dois
arquivos de terreno. Ao iniciar, o aplicativo exige que os arquivos locais
correspondam à validação. Uma atualização do terreno exige gerar e conferir
o circuito novamente. A ferramenta não modifica o cliente nem controla o personagem.

Exemplo de regeneração, a partir da raiz do projeto:

```powershell
python tools/validar_circuito_termes.py --game-dir "C:\GoLevel\AikaOnline" --out huntingaitan/dados/circuito_termes_penza.json
```

## Limites da validação

Passagens e alturas estáticas foram validadas nos arquivos, e a integração foi
testada por simulação de navegação e combate. Isso não comprova uma volta real
completa: objetos carregados, colisões dinâmicas, latência e regras do servidor
podem alterar o resultado. Por isso cada movimento também é planejado pela grade
carregada no cliente. Os pontos de monstros cadastrados não garantem spawn ativo.

O início fora da faixa é rejeitado com uma orientação de reposicionamento.
Um deslocamento curto para fora permite tentar reentrar por uma passagem local
com colisão válida. Uma saída distante da região interrompe o circuito.

## Condução nas curvas

O navegador antecipa os destinos e mantém o avanço em curvas suaves quando a projeção à frente respeita a colisão e os limites. A condução não reinicia a cada pequeno destino do mesmo trecho. Correções pequenas usam pulsos mais curtos e aguardam a resposta antes de repetir. Curvas fechadas, obstáculos, combate, buffs e paradas de busca ainda podem interromper o avanço. A fluidez visual precisa ser confirmada no jogo.
