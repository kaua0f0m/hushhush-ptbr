# Hush Hush — Tradução PT-BR

Tradução para português do Brasil do jogo **Hush Hush - Only Your Love Can Save Them** (Sad Panda Studios, Steam).

> O jogo é indicado para **maiores de 16 anos** na Steam; as cenas adultas ficam na **DLC de conteúdo NSFW (18+)**. Esta é uma tradução de fãs, sem fins lucrativos e sem vínculo com a Sad Panda Studios, **feita por IA (Claude Code, Sonnet) com curadoria do criador**. Você precisa ter o jogo original na Steam; o instalador **não contém nem distribui nenhum arquivo do jogo**, ele altera a sua cópia local.

## O que está traduzido

- Todos os diálogos, opções de resposta, mensagens de celular, dicas e conquistas (~24 mil frases), em todas as variantes do jogo (normal e 18+).
- Menus e interface: menu principal, configurações, save/load, agenda, habilidades, trabalhos, mapa, galeria e créditos.
- Textos fixos do código (por exemplo, a estação mostrada no relógio e nos slots de save).
- **Acentos funcionando no jogo:** as fontes originais não têm `ã õ ê í ó ú ç`, então o instalador gera esses glifos nas fontes do jogo.

## Instalação (Windows)

1. Baixe o `HushHush-PTBR-vX.Y.Z.zip` na aba **Releases** e extraia.
2. Feche o jogo.
3. Execute `Instalar-HushHush-PTBR.exe` e escolha **1 — Instalar**. Leva cerca de 1 minuto.
4. Abra o jogo normalmente pela Steam.

O instalador encontra o jogo sozinho (biblioteca Steam); se não achar, ele pede a pasta que contém `HushHush.exe`.

**Desinstalar:** rode o instalador de novo e escolha **2 — Restaurar**, ou use *Propriedades > Arquivos instalados > Verificar integridade* na Steam.

**Depois de uma atualização do jogo:** rode o instalador de novo. Ele percebe que a Steam trocou os arquivos e refaz o backup sozinho.

### Aviso do Windows / antivírus

O `.exe` não é assinado digitalmente (assinatura custa caro para projetos de fãs). O Windows SmartScreen pode mostrar "O Windows protegeu o computador": clique em **Mais informações > Executar assim mesmo**. Alguns antivírus marcam programas empacotados com PyInstaller por engano. Se preferir não rodar o `.exe`, use o código-fonte abaixo, que faz exatamente a mesma coisa.

## Rodando pelo código-fonte

Requer Python 3.11+ no Windows.

```bash
pip install -r requirements.txt
python instalar.py                 # menu interativo
python instalar.py instalar --jogo "C:\Program Files (x86)\Steam\steamapps\common\Hush Hush"
python instalar.py restaurar
```

Para gerar o `.exe`: `compilar.bat`.

## Como funciona

| Etapa | O que faz |
|---|---|
| Diálogos | Os textos ficam em tabelas (TextAssets) dentro de `StreamingAssets/Windows/universe/gamedata*`. O instalador troca cada célula pelo equivalente em português e regrava os bundles. |
| Fontes | Compõe os glifos acentuados a partir das letras e acentos já existentes nas fontes TextMeshPro (SDF) e amplia o atlas. |
| Interface | O jogo é IL2CPP e os componentes de UI não têm *typetree*; as strings são localizadas no binário das cenas (`level*`) e regravadas. |
| Código | Textos fixos em `global-metadata.dat` são trocados (o blob de literais é estendido e as seções seguintes deslocadas, com verificação antes de gravar). |

Os originais ficam em `_backup_ptbr` dentro da pasta do jogo (cerca de 60 MB). As chaves de tradução são *hashes* do texto original, então o texto em inglês do jogo não é distribuído.

## Problemas conhecidos

- Os nomes dos meses e dos dias da semana vêm do sistema e continuam em inglês.
- Algumas imagens com texto desenhado não podem ser traduzidas por este método.
- Os rótulos do mapa foram traduzidos; se algum lugar não abrir, abra uma *issue* dizendo qual.
- Testado na build `26470028` da Steam (17/11/2026). Atualizações do jogo podem exigir uma nova versão da tradução.

## Autoria e manutenção

- **Criador:** kaua0f0m
- **Tradução:** Claude Code (Sonnet), modelo de IA da Anthropic, em colaboração com o criador, que revisou, corrigiu e testou.
- **Jogo original:** Sad Panda Studios

**O criador não vai conseguir manter a tradução quando o jogo atualizar.** Se uma atualização quebrar algo, você tem duas saídas:

1. **Fazer um fork e atualizar com a ajuda de uma IA.** O repositório inclui as ferramentas usadas para gerar a tradução (`ferramentas-dev/`) e este código é pequeno o bastante para uma IA entender e ajustar.
2. **Baixar a versão compatível do jogo pelos depots da Steam** (você precisa ter o jogo na sua conta). Esta tradução foi testada na build `26470028`, cujos manifests são:

| Conteúdo | AppID | Depot | Manifest |
|---|---|---|---|
| Jogo base | 782250 | 782251 | `5155249699670900129` |
| DLC | 2070760 | 2070763 | `6224966165265546425` |
| DLC | 2070900 | 2070901 | `484771098001674209` |

No console da Steam (`steam://open/console` no navegador):

```
download_depot 782250 782251 5155249699670900129
download_depot 2070760 2070763 6224966165265546425
download_depot 2070900 2070901 484771098001674209
```

Os arquivos vão para `steamapps/content/app_<AppID>/depot_<Depot>/`. Copie o conteúdo por cima da pasta do jogo e rode o instalador. Alternativa: o [DepotDownloader](https://github.com/SteamRE/DepotDownloader) (`-app`, `-depot`, `-manifest`). Confira os IDs no SteamDB se algo não baixar.

Dica: para impedir que a Steam atualize sozinha, em *Propriedades > Atualizações* escolha "Atualizar este jogo somente quando eu o iniciar", ou desative as atualizações automáticas.

## Licença

- Código do instalador: [MIT](LICENSE).
- Textos traduzidos (`dados/`): veja [LICENSE-TRADUCAO.txt](LICENSE-TRADUCAO.txt).

---

Todo o texto foi traduzido por IA (Claude Code, Sonnet), exceto linhas com copyright e uma piada de cunho duvidoso, traduzidas à mão pelo criador.
