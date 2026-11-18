# Ferramentas de desenvolvimento

Scripts usados para produzir a tradução (não são necessários para instalar).

- `lotes.py` — divide as frases em lotes de 250 (`proximo`) e mescla traduções (`mesclar`).
- `patcher.py`, `fontfix.py`, `ui_*.py`, `metadata_patch.py` — versões de desenvolvimento das etapas de instalação.
- `gerar_dados.py` — converte a memória de tradução (inglês → português) nos arquivos de `dados/`, com chaves em hash do texto original.

A memória de tradução com o texto original em inglês não faz parte do repositório.
