# Formato da tabela de skills do cliente

`SkillData12.bin` (cabeçalho `CL0011S`, 12.000 registros de 720 bytes) é cifrado em disco. O cliente o
decifra ao carregar e mantém a tabela em memória, no mesmo endereço que o leitor usa para os efeitos
de stun/paralisia/congelamento (`effect_table_rva`, passo `0x2d0`).

`tools/exportar_skills.py` copia a tabela da memória (somente leitura) para
`capturas_leitor/skills_memoria.bin`. O decodificador está em `huntingaitan/leitura/skills_cliente.py`.

## Registros e níveis
Cada habilidade tem 16 níveis. Para a skill de id `X` (o id que aparece na barra de atalhos):

- **registro `X-1`** guarda o *cabeçalho*: nome, classe, custo de mana e recarga;
- **registro `X`** guarda o *efeito*: descrição, tipos e magnitudes dos efeitos e tempo de conjuração.

Os ids de uma habilidade vão de `16k+1` a `16k+16`; `nível = (X-1) % 16 + 1`. O grupo de recarga lido pelo
cliente é `((X-1) % 960) // 16`, o que confirma esse alinhamento.

## Campos conhecidos (offsets dentro do registro)
| Offset | Registro | Conteúdo |
|---|---|---|
| `+0x00`, `+0x10` | efeito | 4 tipos de efeito (int32) e 4 magnitudes (int32) |
| `+0x3c` | efeito | tempo de conjuração, em ms |
| `+0xa8` | efeito | descrição (cp1252, até 312 bytes) |
| `+0x1e0` | cabeçalho | nome interno em inglês (64 bytes) |
| `+0x220` | cabeçalho | nome exibido, no idioma do cliente (64 bytes) |
| `+0x268` | cabeçalho | classe: 1, 11, 21, 31, 41, 51 (e o mesmo dígito com sufixo 2 ou 3 para variantes) |
| `+0x278` | cabeçalho | custo de mana |
| `+0x284` | cabeçalho | recarga, em ms |

Classes confirmadas: **11 = Templário** (Pericia con Escudo, Remediar, Incitar a la Multitud…) e
**51 = Clérigo** (Cure, Bless, Purification…). As demais (1, 21, 31, 41) ainda não têm nome confirmado.

Campos ainda sem significado confirmado: `+0x40`, `+0x44`, `+0x264` (valores que crescem por nível), `+0x268`
com valores acima de 53, `+0x28c`, `+0x294`, `+0x298`, `+0x2a8`.

## Tipo sugerido
`classificar()` sugere o tipo da skill (cura, defesa, ameaça, buff, ataque, passiva, utilidade) pelas palavras
da descrição em espanhol. É só uma sugestão para o painel: o usuário pode trocar o tipo de cada tecla.

## Barra de atalhos
`ler_slots()` lê os 40 slots do personagem (tipo nos 4 bits baixos, id da skill nos 17 seguintes). Tipo 2 é
skill; itens e slots vazios têm outros valores. `tools/ler_barra.py` mostra cada slot com a skill decodificada.

A tabela e as descrições são dados do jogo: mantenha as exportações locais e fora do Git.
