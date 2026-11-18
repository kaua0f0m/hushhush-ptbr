"""Gerencia lotes de tradução.

  python lotes.py proximo <todas_frases.json> <pasta_traducao> <pasta_lotes> [tamanho]
      -> cria <pasta_lotes>/lote_NNN.en.txt (uma frase por linha, prefixo "i|")
  python lotes.py mesclar <pasta_lotes>/lote_NNN <pasta_traducao>
      -> lê lote_NNN.pt.txt (uma tradução por linha, mesmo número de linhas,
         prefixo "i|" opcional), valida tags e grava <pasta_traducao>/lote_NNN.json
  python lotes.py status <todas_frases.json> <pasta_traducao>
"""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
TAG = re.compile(r"<[^>]+>")
FIRST = ["Main Intro", "Tutorial", "Tutorial Intro", "Achievements", "Schedule", "Stats Info",
         "Jobs Info", "Hobbies Info", "Gameover Descriptions", "Descriptions and Secrets", "Gallery"]


def done(folder):
    tm = {}
    for f in glob.glob(os.path.join(folder, "*.json")):
        tm.update(json.load(open(f, encoding="utf-8")))
    return tm


def order_key(item):
    k, ctx = item
    name, line = ctx.rsplit(":", 2)[0], int(ctx.rsplit(":", 2)[1])
    pri = FIRST.index(name) if name in FIRST else len(FIRST)
    return (pri, name, line)


def pending(allfile, folder):
    allm = json.load(open(allfile, encoding="utf-8"))
    tm = done(folder)
    items = [(k, c) for k, c in allm.items() if k not in tm and re.search(r"[A-Za-z]", k)]
    items.sort(key=order_key)
    return items, len(allm), len(tm)


def proximo(allfile, folder, lotes, size=250):
    os.makedirs(lotes, exist_ok=True)
    items, _, _ = pending(allfile, folder)
    # skip items already in an un-merged batch
    reserved = set()
    for f in glob.glob(os.path.join(lotes, "lote_*.keys.json")):
        if not os.path.exists(f.replace(".keys.json", ".json").replace(lotes, folder)):
            reserved.update(json.load(open(f, encoding="utf-8")))
    items = [i for i in items if i[0] not in reserved]
    if not items:
        print("Nada pendente.")
        return
    batch = items[:size]
    n = len(glob.glob(os.path.join(lotes, "lote_*.keys.json"))) + 1
    base = os.path.join(lotes, f"lote_{n:03d}")
    json.dump([k for k, _ in batch], open(base + ".keys.json", "w", encoding="utf-8"), ensure_ascii=False)
    with open(base + ".en.txt", "w", encoding="utf-8") as fh:
        last = None
        for i, (k, ctx) in enumerate(batch):
            name = ctx.rsplit(":", 2)[0]
            if name != last:
                fh.write(f"## {name}\n")
                last = name
            fh.write(f"{i}|{k}\n")
    print(base)


def mesclar(base, folder):
    keys = json.load(open(base + ".keys.json", encoding="utf-8"))
    lines = [l.rstrip("\n") for l in open(base + ".pt.txt", encoding="utf-8") if l.strip() and not l.startswith("## ")]
    out = {}
    errs = []
    if len(lines) != len(keys):
        raise SystemExit(f"linhas: {len(lines)} != frases: {len(keys)}")
    for i, (k, l) in enumerate(zip(keys, lines)):
        m = re.match(r"^(\d+)\|(.*)$", l)
        if m:
            if int(m.group(1)) != i:
                errs.append(f"{i}: índice {m.group(1)} fora de ordem")
            l = m.group(2)
        if l.startswith("DEIXAR_EM_INGLES:"):
            rest = l[len("DEIXAR_EM_INGLES:"):].strip()
            l = k if rest == k.strip() else rest
        if "`" in l:
            errs.append(f"{i}: contém crase")
        if sorted(TAG.findall(k)) != sorted(TAG.findall(l)):
            errs.append(f"{i}: tags diferentes: {TAG.findall(k)} vs {TAG.findall(l)}")
        if k.strip().startswith("SKIPPED"):
            l = k
        out[k] = l
    if errs:
        raise SystemExit("\n".join(errs))
    dst = os.path.join(folder, os.path.basename(base) + ".json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"ok: {len(out)} -> {dst}")


def status(allfile, folder):
    items, total, ndone = pending(allfile, folder)
    print(f"traduzidas {ndone} / {total}; pendentes {len(items)}")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "proximo":
        proximo(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 250)
    elif c == "mesclar":
        mesclar(sys.argv[2], sys.argv[3])
    elif c == "status":
        status(sys.argv[2], sys.argv[3])
