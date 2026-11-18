"""Traduz os diálogos (TextAssets em StreamingAssets/Windows/universe/gamedata*)."""
import glob
import os
import shutil

import UnityPy

from .core import carregar_dados, h

SEP = "`"
COLS = {"Dialogue - Set-up", "Options", "Response", "Text", "Title",
        "Display / Instructions", "Description", "Hint Subtitle"}


def _traduzir_tabela(texto, tm):
    linhas = texto.split("\n")
    cab = linhas[0].split(SEP)
    hits = 0
    for li in range(1, len(linhas)):
        cel = linhas[li].split(SEP)
        mudou = False
        for ci, c in enumerate(cel):
            nome = cab[ci] if ci < len(cab) else ""
            if nome in COLS and c.strip() and c.strip() != "SKIPPED":
                t = tm.get(h(c))
                if t:
                    cel[ci] = t
                    mudou = True
                    hits += 1
        if mudou:
            linhas[li] = SEP.join(cel)
    return "\n".join(linhas), hits


def bundles(bk):
    pasta = os.path.join(bk.data, "StreamingAssets", "Windows", "universe")
    return [("StreamingAssets/Windows/universe/" + os.path.basename(f)) for f in sorted(glob.glob(os.path.join(pasta, "gamedata*")))]


def aplicar(bk, log=print):
    tm = carregar_dados("dialogos.json")
    rels = bundles(bk)
    if not rels:
        raise SystemExit("Nenhum bundle de diálogos encontrado (gamedata*). A pasta do jogo está correta?")
    total = 0
    for i, rel in enumerate(rels, 1):
        src = bk.original(rel)
        dst = bk.atual(rel)
        env = UnityPy.load(src)
        hits_b = 0
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            d = obj.read()
            s = d.m_Script
            if isinstance(s, bytes):
                s = s.decode("utf-8", "surrogateescape")
            novo, hits = _traduzir_tabela(s, tm)
            if hits:
                d.m_Script = novo
                d.save()
                hits_b += hits
        if hits_b:
            with open(dst, "wb") as fh:
                fh.write(env.file.save(packer="lz4"))
        else:
            shutil.copy2(src, dst)
        bk.registrar(rel)
        total += hits_b
        log(f"  diálogos {i}/{len(rels)}")
    log(f"  {total} falas traduzidas em {len(rels)} arquivos")
