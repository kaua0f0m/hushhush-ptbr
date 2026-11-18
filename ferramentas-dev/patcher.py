"""Hush Hush - patcher de tradução PT-BR.

Uso:
  python patcher.py aplicar  <pasta_do_jogo> <pasta_traducao>
  python patcher.py restaurar <pasta_do_jogo>
  python patcher.py exportar <pasta_do_jogo> <saida.json>

A tradução é uma memória "inglês -> português" (arquivos *.json na pasta de tradução).
Ela é aplicada em todas as variantes dos bundles universe/gamedata*, então funciona
independente de qual variante (base ou DLC/nsfw) o jogo carregar.
Os originais ficam em <pasta_do_jogo>/_backup_traducao_en e são sempre a fonte do patch.
"""
import glob
import json
import os
import shutil
import sys

import UnityPy

COLS = {"Dialogue - Set-up", "Options", "Response", "Text", "Title",
        "Display / Instructions", "Description", "Hint Subtitle"}
KEEP = {"SKIPPED", ""}
SEP = "`"


def universe(game):
    return os.path.join(game, "HushHush_Data", "StreamingAssets", "Windows", "universe")


def backup_dir(game):
    return os.path.join(game, "_backup_traducao_en")


def bundles(game):
    return sorted(glob.glob(os.path.join(universe(game), "gamedata*")))


def ensure_backup(game):
    bd = backup_dir(game)
    os.makedirs(bd, exist_ok=True)
    for f in bundles(game):
        dst = os.path.join(bd, os.path.basename(f))
        if not os.path.exists(dst):
            shutil.copy2(f, dst)
    return bd


def iter_cells(text):
    """Yield (line_idx, col_idx, header_name, cell) for translatable cells."""
    lines = text.split("\n")
    header = lines[0].split(SEP)
    for li, line in enumerate(lines[1:], 1):
        cells = line.split(SEP)
        for ci, c in enumerate(cells):
            name = header[ci] if ci < len(header) else ""
            if name in COLS and c.strip() not in KEEP:
                yield li, ci, name, c


def translate_table(text, tm):
    lines = text.split("\n")
    header = lines[0].split(SEP)
    hits = 0
    for li in range(1, len(lines)):
        cells = lines[li].split(SEP)
        changed = False
        for ci, c in enumerate(cells):
            name = header[ci] if ci < len(header) else ""
            if name in COLS and c in tm and tm[c]:
                cells[ci] = tm[c]
                changed = True
                hits += 1
        if changed:
            lines[li] = SEP.join(cells)
    return "\n".join(lines), hits


def load_tm(folder):
    tm = {}
    for f in sorted(glob.glob(os.path.join(folder, "*.json"))):
        data = json.load(open(f, encoding="utf-8"))
        for k, v in data.items():
            if "`" in v or "\n" in v:
                raise SystemExit(f"{f}: tradução contém crase ou quebra de linha: {k!r}")
            tm[k] = v
    return tm


def aplicar(game, folder):
    tm = load_tm(folder)
    bd = ensure_backup(game)
    total = 0
    for f in bundles(game):
        src = os.path.join(bd, os.path.basename(f))
        env = UnityPy.load(src)
        hits_b = 0
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            d = obj.read()
            s = d.m_Script
            if isinstance(s, bytes):
                s = s.decode("utf-8", "surrogateescape")
            new, hits = translate_table(s, tm)
            if hits:
                d.m_Script = new
                d.save()
                hits_b += hits
        if hits_b:
            data = env.file.save(packer="lz4")
            with open(f, "wb") as fh:
                fh.write(data)
        else:
            shutil.copy2(src, f)
        total += hits_b
        print(f"{os.path.basename(f)}: {hits_b} células traduzidas")
    print(f"Total: {total} células; {len(tm)} entradas na memória de tradução.")


def restaurar(game):
    bd = backup_dir(game)
    for f in glob.glob(os.path.join(bd, "gamedata*")):
        shutil.copy2(f, os.path.join(universe(game), os.path.basename(f)))
    print("Originais em inglês restaurados.")


def exportar(game, out):
    """Exporta todas as frases únicas (inglês) com contexto, a partir dos originais."""
    bd = backup_dir(game)
    srcs = sorted(glob.glob(os.path.join(bd, "gamedata*"))) or bundles(game)
    seen = {}
    for f in srcs:
        env = UnityPy.load(f)
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            d = obj.read()
            s = d.m_Script
            if isinstance(s, bytes):
                s = s.decode("utf-8", "surrogateescape")
            for li, ci, name, c in iter_cells(s):
                seen.setdefault(c, f"{d.m_Name}:{li}:{name}")
    json.dump(seen, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(seen)} frases exportadas para {out}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "aplicar":
        aplicar(sys.argv[2], sys.argv[3])
    elif cmd == "restaurar":
        restaurar(sys.argv[2])
    elif cmd == "exportar":
        exportar(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
