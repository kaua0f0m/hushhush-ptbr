"""Aplica a tradução de UI (ui_pt.json) nas cenas do jogo.
Uso: python ui_aplicar.py <pasta_do_jogo> [ui_pt.json]
Originais ficam em <jogo>/_backup_traducao_en/HushHush_Data/ e são sempre a fonte."""
import json
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ui_extrair import NAMES, UI_CLASSES, load_env, script_class
from ui_scan import scan


def main():
    game = sys.argv[1]
    pt_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "ui_pt.json")
    pt = json.load(open(pt_path, encoding="utf-8"))
    d = os.path.join(game, "HushHush_Data")
    bak = os.path.join(game, "_backup_traducao_en", "HushHush_Data")
    os.makedirs(bak, exist_ok=True)
    for n in NAMES:
        if not os.path.exists(os.path.join(bak, n)):
            shutil.copy2(os.path.join(d, n), os.path.join(bak, n))
    env = load_env(game)
    files_by_name = {os.path.basename(str(k)): f for k, f in env.files.items()}
    cache = {}
    touched = {}
    count = 0
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            cls = script_class(o, files_by_name, cache)
        except Exception:
            continue
        if cls not in UI_CLASSES:
            continue
        raw = o.get_raw_data()
        hits = [(off, s) for off, s in scan(raw) if s in pt and pt[s] != s]
        if not hits:
            continue
        raw = bytearray(raw)
        for off, s in sorted(hits, reverse=True):
            ln = len(s.encode("utf-8"))
            old_end = off + 4 + ln + (4 - ln % 4) % 4
            nb = pt[s].encode("utf-8")
            new = struct.pack("<i", len(nb)) + nb + b"\x00" * ((4 - len(nb) % 4) % 4)
            raw[off:old_end] = new
            count += 1
        o.set_raw_data(bytes(raw))
        touched[os.path.basename(o.assets_file.name)] = o.assets_file
    for name, sf in touched.items():
        data = sf.save()
        with open(os.path.join(d, name), "wb") as f:
            f.write(data)
        print("gravado", name, len(data))
    print(count, "textos de UI traduzidos")


if __name__ == "__main__":
    main()
