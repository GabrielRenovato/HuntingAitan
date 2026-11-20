# Jardim Aéreo de Mirza · Difícil

Comece dentro do Jardim no Difícil (Hard no cliente em inglês). O modo combate nas áreas anteriores e encerra o percurso antes do primeiro grupo de Lazapas Tempestuosos do trecho final. Os Lazapas da Fúria das áreas iniciais continuam permitidos. F12 interrompe; cura, recargas e buffs exclusivos usam o motor existente.

## Limite e saída

O limite estático fica em 3775,5 / 3131,5, aproximadamente 25 unidades de percurso antes da primeira aquisição de Lazapa Tempestuosa registrada nos logs em 3756,95 / 3146,52. Essa referência é uma posição observada do personagem, não uma tabela de spawns do servidor.

No trecho final, detectar um Lazapa a até 25 unidades por caminho alcançável antecipa a saída. O filtro de combate protege esse grupo e Seridunn; não envia TAB, ataque ou skill ao Lazapa final. Ao atingir o limite, o motor libera as teclas, abre o menu do grupo, escolhe sair e confirma. Só encerra a etapa após três leituras da posição fora do Jardim. Uma falha de reconhecimento mantém a etapa de saída; F12 e Parar continuam disponíveis.

Esse trecho não conta como DG completa nem como abate de Seridunn. Não retorna automaticamente à entrada do Jardim.

## Fontes locais e validação

- `UI/Dungeon.bin` identifica o Jardim e Seridunn; `UI/Dun.bin`, registros 20–23, identifica origem 3328,3072 e entrada 3351,3295.
- `Env/z011312.att/.hgt/.dat` e `Env/z011412.att/.hgt/.dat` formam uma grade de 512×256.
- A referência do altar em `Objects/mirzaF0099.MS3` identifica a rota completa original, da qual o trecho atual foi recortado.

O JSON registra fontes, hashes e 2.266 células até o limite. O caminho foi reconferido nos arquivos locais. A saída tem templates em português e fallback de texto para os controles correspondentes em inglês/espanhol. Testes automatizados verificam os filtros, a interrupção antes de atacar e a confirmação de saída; o percurso e os cliques completos precisam de validação ao vivo.

## Regeneração

```powershell
python tools/validar_jardim_aereo.py --game-dir "C:\GoLevel\AikaOnline" --out jardim_aereo_rota.json
```
