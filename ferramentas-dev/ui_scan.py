"""Varre MonoBehaviours (sem typetree) atrás de strings serializadas (int32 len + utf8 + pad4).
Uso: python ui_scan.py <pasta_do_jogo> <saida.json>"""
import json
import os
import re
import struct
import sys

import UnityPy

OK = re.compile(r"^[^\x00-\x08\x0b-\x1f]{2,400}$")


def scan(raw):
    out = []
    i = 0
    n = len(raw)
    while i + 4 <= n:
        ln = struct.unpack_from("<i", raw, i)[0]
        if 2 <= ln <= 400 and i + 4 + ln <= n:
            try:
                s = raw[i + 4:i + 4 + ln].decode("utf-8")
            except UnicodeDecodeError:
                i += 4
                continue
            if OK.match(s) and re.search(r"[A-Za-z]{2}", s):
                pad = (4 - ln % 4) % 4
                if raw[i + 4 + ln:i + 4 + ln + pad] == b"\x00" * pad:
                    out.append((i, s))
                    i += 4 + ln + pad
                    continue
        i += 4
    return out


def main():
    game, outp = sys.argv[1], sys.argv[2]
    d = os.path.join(game, "HushHush_Data")
    bak = os.path.join(game, "_backup_traducao_en", "HushHush_Data")
    names = ["globalgamemanagers", "globalgamemanagers.assets", "resources.assets"] + [f"level{i}" for i in range(5)] + [f"sharedassets{i}.assets" for i in range(5)]
    res = []
    for nm in names:
        p = os.path.join(bak, nm)
        if not os.path.exists(p):
            p = os.path.join(d, nm)
        env = UnityPy.load(p)
        for o in env.objects:
            if o.type.name != "MonoBehaviour":
                continue
            for off, s in scan(o.get_raw_data()):
                res.append({"file": nm, "pid": o.path_id, "off": off, "text": s})
    json.dump(res, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(res), "candidatos")


if __name__ == "__main__":
    main()
