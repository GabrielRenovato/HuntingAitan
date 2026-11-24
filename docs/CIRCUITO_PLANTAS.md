# Quatro Plantas Mutantes na Floresta Ungor

No painel, selecione o personagem em **Básico → Cliente do Aika**. Em **Comportamento → Modo de caça**, selecione **4 Plantas · Floresta Ungor**. Comece na região de **2440, 1360** e clique em **Começar**, com a caça nativa desligada. F12 encerra o nosso motor.

A volta é **7 → 8 → 9 → 10 → 7**, usando os pontos do [mapeamento das Plantas](mapeamento_plantas_ungor/README.md):

| Ponto | X | Y |
| --- | --- | --- |
| 7 | 2430 | 1367 |
| 8 | 2450 | 1378 |
| 9 | 2457 | 1350 |
| 10 | 2426 | 1346 |

O motor inicia no trecho mais próximo, caça apenas **Planta Carnívora Mutante** dentro da faixa de 20 unidades do circuito e mantém o alvo durante a luta. Depois de confirmar o abate, procura outra Planta ou retoma a volta. Busca por cinco segundos em cada parada e repete o circuito, sem um limite de voltas. A duração da sessão continua respeitando o tempo configurado no painel. Recuperações de alvo e de passagem seguem as regras existentes; não se registra morte sem confirmação.

Habilidades, cura, buffs e suprimentos usam os atalhos configurados para o personagem escolhido. O modo não usa IDs fixos de entidades, pois eles mudam no respawn. Não promete exatamente quatro mobs vivos ao mesmo tempo e não exige giros contínuos de câmera: a seleção orienta para os candidatos quando necessário.

Os caminhos foram derivados de `UI/MN.bin`, `UI/MobPos.bin`, `Env/AttributeS01.dat` e `Env/z01.hgt`. As quatro passagens passaram na busca de caminho e na verificação de células adjacentes, com orientação de altura/colisão conferida no tile `z010905`. Hashes das fontes são conferidos antes de iniciar. A grade carregada ainda é reavaliada durante a navegação; objetos e movimentação real exigem validação no jogo.

Para regenerar:

```powershell
python tools/validar_circuito_plantas.py --game-dir "C:\GoLevel\AikaOnline" --out huntingaitan/dados/circuito_ungor_plantas.json
```

Testes automatizados cobrem o filtro exclusivo dos pontos 7–10, recusa de outro local inicial, fechamento e repetição da volta, manutenção da conta e dos atalhos, e simulação de oito abates em duas levas com uma volta completa entre elas, sem TAB enquanto o alvo está vivo.
