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
