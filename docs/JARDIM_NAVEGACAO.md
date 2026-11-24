# Navegação interna do Jardim

Os blocos `Env/z011312` e `Env/z011412` fornecem terreno e alturas. A máscara `jardim_geometria.json` é reproduzida por:

```powershell
python tools/validar_geometria_jardim.py C:\GoLevel\AikaOnline
```

A extração interpretou 1.066 objetos estáticos e registrou 18 formatos não interpretados. Usa as alturas internas dos blocos. Malhas de renderização incluem vegetação atravessável: sua ocupação acrescenta custo ao caminho, sem transformar todas as superfícies em paredes. As flags de colisão do terreno continuam sendo bloqueios rígidos.

`RecuperacaoJardim` registra uma célula à frente de uma tentativa bloqueada e aplica essa exclusão tanto ao plano da DG quanto à grade local atualizada. Uma nova falha pode gerar outro plano mesmo sem deslocamento do personagem. A célula ocupada não é bloqueada. Se não houver desvio, tenta recuar por posições já percorridas.

Somente tempo observado de navegação sem avanço entra no prazo de 25 segundos. Interrupções para combate, habilidades ou foco não são somadas como travamento. Ao exceder o prazo, `jardim_reset` leva o ciclo à saída do grupo e reentrada no Difícil, sem incrementar trechos concluídos. O limite antes dos Shiraz Infernais é preservado.

Regressões reproduzem os pontos `3511,3268` e `3689,3307` da sessão `run_20261122_214931.jsonl`, usando os arquivos reais quando disponíveis. Verificam passagem alternativa, exclusão da célula que falhou, tentativas sucessivas na mesma posição, quina sem W e reinício sem falsa conclusão. Isso não substitui a validação de uma run completa no cliente.
