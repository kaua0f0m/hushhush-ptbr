"""Extrai textos visíveis de UI (componentes TextMeshPro/Text) das cenas.
Uso: python ui_extrair.py <pasta_do_jogo> <saida.json>
Cada item: file, pid, off (offset do comprimento da string no raw do MonoBehaviour), text, cls."""
import json
import os
import struct
import sys

import UnityPy

sys.path.insert(0, os.path.dirname(__file__))
from ui_scan import scan

NAMES = ["globalgamemanagers", "globalgamemanagers.assets", "resources.assets"] + [f"level{i}" for i in range(5)] + [f"sharedassets{i}.assets" for i in range(5)]
UI_CLASSES = {"TextMeshProUGUI", "TextMeshPro", "Text"}


def load_env(game):
    d = os.path.join(game, "HushHush_Data")
    bak = os.path.join(game, "_backup_traducao_en", "HushHush_Data")
    paths = []
    for n in NAMES:
        p = os.path.join(bak, n)
        paths.append(p if os.path.exists(p) else os.path.join(d, n))
    return UnityPy.load(*paths)


def script_class(obj, files_by_name, cache):
    raw = obj.get_raw_data()
    fid, pid = struct.unpack_from("<iq", raw, 16)
    sf = obj.assets_file
    if fid != 0:
        ext = sf.externals[fid - 1]
        sf = files_by_name.get(os.path.basename(ext.path))
        if sf is None:
            return None
    key = (id(sf), pid)
    if key not in cache:
        o = sf.objects.get(pid)
        cache[key] = o.read().m_ClassName if o is not None else None
    return cache[key]


def main():
    game, outp = sys.argv[1], sys.argv[2]
    env = load_env(game)
    files_by_name = {}
    for k, f in env.files.items():
        files_by_name[os.path.basename(str(k))] = f
    cache = {}
    res = []
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            cls = script_class(o, files_by_name, cache)
        except Exception:
            continue
        if cls not in UI_CLASSES:
            continue
        for off, s in scan(o.get_raw_data()):
            res.append({"file": os.path.basename(o.assets_file.name), "pid": o.path_id, "off": off, "text": s, "cls": cls})
    json.dump(res, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(res), "textos de UI;", len({r["text"] for r in res}), "unicos")


if __name__ == "__main__":
    main()
