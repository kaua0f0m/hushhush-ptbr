"""Traduz literais de string do código (global-metadata.dat, IL2CPP v24).
Uso: python metadata_patch.py <pasta_do_jogo> [metadata_pt.json]
Textos mais longos são acrescentados ao fim do blob de literais e as seções seguintes são deslocadas.
O original fica em <jogo>/_backup_traducao_en/HushHush_Data/il2cpp_data/Metadata/global-metadata.dat."""
import json
import os
import shutil
import struct
import sys

HEADER = 264


def parse(b):
    magic, ver = struct.unpack_from("<Ii", b, 0)
    assert magic == 0xFAB11BAF and ver == 24, (hex(magic), ver)
    pairs = [struct.unpack_from("<II", b, 8 + i * 8) for i in range((HEADER - 8) // 8)]
    lo, ls = pairs[0]
    do, ds = pairs[1]
    return pairs, lo, ls, do, ds


def literals(b):
    pairs, lo, ls, do, ds = parse(b)
    out = []
    for i in range(ls // 8):
        ln, di = struct.unpack_from("<II", b, lo + i * 8)
        out.append(b[do + di:do + di + ln])
    return out


def main():
    game = sys.argv[1]
    pt = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "metadata_pt.json"), encoding="utf-8"))
    rel = os.path.join("HushHush_Data", "il2cpp_data", "Metadata", "global-metadata.dat")
    dst = os.path.join(game, rel)
    bak = os.path.join(game, "_backup_traducao_en", rel)
    if not os.path.exists(bak):
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        shutil.copy2(dst, bak)
    b = bytearray(open(bak, "rb").read())
    pairs, lo, ls, do, ds = parse(b)
    old = literals(b)
    end = do + ds
    extra = bytearray()
    changed = {}
    for i, s in enumerate(old):
        t = s.decode("utf-8", "replace")
        if t in pt and pt[t] != t:
            nb = pt[t].encode("utf-8")
            if len(nb) <= len(s):
                di = struct.unpack_from("<I", b, lo + i * 8 + 4)[0]
                b[do + di:do + di + len(s)] = nb + b"\x00" * (len(s) - len(nb))
            else:
                di = ds + len(extra)
                extra += nb
            struct.pack_into("<II", b, lo + i * 8, len(nb), di if len(nb) > len(s) else struct.unpack_from("<I", b, lo + i * 8 + 4)[0])
            changed[i] = pt[t]
    pad = (4 - len(extra) % 4) % 4
    extra += b"\x00" * pad
    delta = len(extra)
    new = bytearray(b[:end]) + extra + bytearray(b[end:])
    if delta:
        struct.pack_into("<I", new, 8 + 8 * 1 + 4, ds + delta)
        for i, (off, sz) in enumerate(pairs):
            if i == 1:
                continue
            if off >= end:
                struct.pack_into("<I", new, 8 + i * 8, off + delta)
        # campos soltos do cabeçalho após os pares não são deslocados (v24 só tem pares)
    # verificação
    p2, lo2, ls2, do2, ds2 = parse(new)
    lit2 = literals(new)
    assert len(lit2) == len(old)
    for i, (a, c) in enumerate(zip(old, lit2)):
        if i in changed:
            assert c.decode("utf-8") == changed[i], i
        else:
            assert a == c, i
    for i, ((o1, s1), (o2, s2)) in enumerate(zip(pairs, p2)):
        if i in (0, 1):
            continue
        assert s1 == s2
        if s1:
            assert b[o1:o1 + s1] == new[o2:o2 + s2], f"seção {i} diferente"
    assert len(new) == len(b) + delta
    with open(dst, "wb") as f:
        f.write(new)
    print(len(changed), "literais traduzidos; delta", delta, "bytes")
    for i, t in changed.items():
        print(" ", i, old[i].decode("utf-8", "replace"), "->", t)


if __name__ == "__main__":
    main()
