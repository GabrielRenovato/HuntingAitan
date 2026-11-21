# Manutenção do leitor e validação offline

Ferramentas para manter o leitor de dados internos quando o Aika for atualizado e para validar
mudanças no motor sem o jogo aberto. Tudo é somente leitura.

## Layouts por versão do cliente

`huntingaitan/dados/native_layout.json` contém uma lista de layouts. O leitor calcula o SHA-256 do
`AIKACL.exe` aberto e usa o layout com o mesmo hash. Um arquivo com um único layout continua válido.

Para suportar uma nova versão sem perder a anterior, adicione uma entrada em `layouts` com o novo
`sha256` e os valores revalidados. Qualquer chave de `PADROES` em
`huntingaitan/leitura/dados_internos.py` pode ser sobrescrita no layout: RVAs (`context_rva`,
`bar_manager_rva`, `effect_table_rva`, `mob_flag_rva`) e offsets da entidade (`ent_id`, `ent_pos`,
`ent_rot`, `ent_status`, `ent_hpmp`, `ent_nome`). Offsets de cena e de contexto ainda estão no código.

Se a versão do cliente for desconhecida, a mensagem de erro informa o SHA-256 encontrado e os
hashes conhecidos.

## Verificar o layout depois de um patch

Com o jogo aberto, no mapa e com o aplicativo como administrador:

```powershell
python tools/verificar_layout.py
```

Cada leitura é testada. Falhas em **jogador e alvo** ou **cena ativa** são críticas e a saída é 1.
As demais (estados de controle, recargas, câmera, lista de mobs, caça original) aparecem como aviso
e indicam qual recurso perde precisão.

## Gravar e reproduzir uma sessão

1. Defina `AIKA_GRAVAR_SESSAO=1` antes de abrir o painel. Cada caça grava as leituras do cliente em
   `app_sessions/leituras_AAAAMMDD_HHMMSS.jsonl`, que já está no `.gitignore`.
2. Reproduza a gravação no motor, sem o jogo:

   ```powershell
   python tools/reproduzir_sessao.py app_sessions/leituras_20261121_120000.jsonl --saida traco_novo.json
   ```
3. Para comparar duas versões do código, gere um traço em cada uma, com a mesma gravação, e compare:

   ```powershell
   python tools/reproduzir_sessao.py --comparar traco_antigo.json traco_novo.json
   ```

A saída informa a primeira divergência em teclas ou eventos. O relógio, o teclado e a janela são
simulados, então o resultado é determinístico.

Limites: a navegação por grade depende dos arquivos do jogo e não é reproduzida; o replay valida as
decisões de combate, cura, buffs e seleção de alvo. As leituras são devolvidas na ordem gravada, então
uma mudança de comportamento que altere a ordem das chamadas aparece como divergência.

As gravações contêm o nome do personagem e posições. Revise antes de compartilhar.

## Descobrir campos novos no cliente

Para trocar a leitura visual por leitura de estado (janela ou convite aberto, dificuldade da DG),
ler a duração de buffs ou saber quais mobs atacam o personagem, é preciso achar onde o cliente guarda
essas informações. `tools/capturar_estado.py` ajuda a achar candidatos, sempre só lendo a memória, em
objetos que o projeto já usa: cena, contexto, jogador, alvo e, com `--mob`, o mob mais próximo.

1. Com o jogo aberto, no mapa e com o aplicativo como administrador, capture cada estado 5 vezes,
   com o personagem parado:

   ```powershell
   python tools/capturar_estado.py capturar dialogo_fechado --n 5
   python tools/capturar_estado.py capturar dialogo_aberto --n 5
   ```
2. Compare. Ficam as palavras de 4 bytes estáveis dentro de cada grupo e diferentes entre eles; posição,
   timers e contadores variam dentro do grupo e são descartados:

   ```powershell
   python tools/capturar_estado.py comparar dialogo_fechado dialogo_aberto
   ```
   Os candidatos saem ordenados: `flag 0/1`, depois `nulo <-> ponteiro` (um objeto de interface passa a
   existir), depois `zero <-> valor`.
3. Para ver o que um ponteiro candidato aponta, capture de novo com `--extra cena+0x1a8->0x400`
   (região `+` offset do ponteiro `->` bytes a ler, no máximo `0x2000`) e compare a região
   `cena+0x1a8`.
4. Confirme: repita a troca de estado e capture um terceiro par. Um campo verdadeiro muda sempre, e só
   com o estado. Com o offset confirmado, ele entra no layout e vira um método do leitor.

Sugestões de pares: **convite/janela**: fechada × aberta. **Buff**: sem × com. **Perigo**: mob parado ×
atacando o personagem (use `--mob`, mantendo o mesmo mob nos dois grupos).

Com menos de 2 capturas por estado o ruído não é filtrado. As capturas ficam em `capturas_leitor/`,
ignorada pelo Git, e contêm dados do processo do jogo (nomes, textos): não as compartilhe.
