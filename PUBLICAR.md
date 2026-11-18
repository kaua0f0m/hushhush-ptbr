# Como publicar no GitHub

Nada foi publicado ainda. O repositório local já está commitado; falta criar o repositório no GitHub e a Release.

## 1. Preparar (uma vez)

```bash
winget install GitHub.cli
gh auth login
```

## 2. Criar o repositório e enviar o código

```bash
cd HushHush-PTBR
gh repo create kaua0f0m/hushhush-ptbr --public --source . --push \
  --description "Tradução PT-BR (feita por IA, com curadoria do criador em certas linhas) de Hush Hush - Only Your Love Can Save Them"
```

## 3. Criar a Release com o zip e as somas

```bash
gh release create v1.0.0 ../saida/HushHush-PTBR-v1.0.0.zip ../saida/SHA256SUMS.txt \
  --title "Tradução PT-BR v1.0.0" --notes-file NOTAS-DA-VERSAO.md
```

Na descrição do repositório (campo "About") e no fim da página, mantenha o aviso de que a tradução é feita por IA, exceto as linhas com copyright e uma piada de cunho duvidoso, traduzidas à mão pelo criador.

### Atenção sobre os dados da tradução

`dados/*.json` está no `.gitignore`: os dados (que contêm todo o texto, inclusive cenas adultas) vão apenas dentro do zip da Release. O GitHub proíbe conteúdo sexualmente explícito em repositórios e pode derrubar o projeto; manter os textos fora do repositório reduz esse risco, mas não o elimina. Se preferir versionar os dados, apague a última linha do `.gitignore`. Sem os dados, quem clonar o repositório não consegue rodar pelo código-fonte; para isso existe o `HushHush-PTBR-codigo-v1.0.0.zip` (opcional na Release).

## Antes de divulgar

- Envie o `.exe` para o VirusTotal e confira o resultado; alguns antivírus marcam por engano executáveis feitos com PyInstaller.
- Confirme a soma SHA-256 publicada com `certutil -hashfile HushHush-PTBR-v1.0.0.zip SHA256`.
- Teste a instalação numa máquina limpa com o jogo recém-instalado.

## Próximas versões

1. Atualize a tradução (`ferramentas-dev/gerar_dados.py <pasta_dados>`).
2. Aumente `VERSAO` em `hushpt/__init__.py`, atualize `CHANGELOG.md` e `LEIA-ME.txt`.
3. Rode `compilar.bat` e gere o zip e o `SHA256SUMS.txt` de novo.
