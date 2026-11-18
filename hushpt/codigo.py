"""Traduz literais de string do código (global-metadata.dat, IL2CPP v24).
Textos mais longos são acrescentados ao fim do blob de literais e as seções seguintes são
deslocadas; o resultado é verificado antes de gravar."""
import struct

from .core import carregar_dados, h

REL = "il2cpp_data/Metadata/global-metadata.dat"
HEADER = 264


def _parse(b):
    magic, ver = struct.unpack_from("<Ii", b, 0)
    if magic != 0xFAB11BAF or ver != 24:
        raise SystemExit("global-metadata.dat com versão inesperada; esta etapa foi ignorada para evitar danos.")
    pares = [struct.unpack_from("<II", b, 8 + i * 8) for i in range((HEADER - 8) // 8)]
    lo, ls = pares[0]
    do, ds = pares[1]
    return pares, lo, ls, do, ds


def _literais(b):
    pares, lo, ls, do, ds = _parse(b)
    out = []
    for i in range(ls // 8):
        ln, di = struct.unpack_from("<II", b, lo + i * 8)
        out.append(b[do + di:do + di + ln])
    return out


def aplicar(bk, log=print):
    pt = carregar_dados("codigo.json")
    b = bytearray(open(bk.original(REL), "rb").read())
    try:
        pares, lo, ls, do, ds = _parse(b)
    except SystemExit as e:
        log("  " + str(e))
        return
    antigos = _literais(b)
    fim = do + ds
    extra = bytearray()
    mudados = {}
    for i, s in enumerate(antigos):
        t = s.decode("utf-8", "replace")
        novo = pt.get(h(t))
        if not novo:
            continue
        nb = novo.encode("utf-8")
        di_ant = struct.unpack_from("<I", b, lo + i * 8 + 4)[0]
        if len(nb) <= len(s):
            b[do + di_ant:do + di_ant + len(s)] = nb + b"\x00" * (len(s) - len(nb))
            struct.pack_into("<II", b, lo + i * 8, len(nb), di_ant)
        else:
            struct.pack_into("<II", b, lo + i * 8, len(nb), ds + len(extra))
            extra += nb
        mudados[i] = novo
    extra += b"\x00" * ((4 - len(extra) % 4) % 4)
    delta = len(extra)
    novo_b = bytearray(b[:fim]) + extra + bytearray(b[fim:])
    if delta:
        struct.pack_into("<I", novo_b, 8 + 8 * 1 + 4, ds + delta)
        for i, (off, sz) in enumerate(pares):
            if i != 1 and off >= fim:
                struct.pack_into("<I", novo_b, 8 + i * 8, off + delta)
    p2, lo2, ls2, do2, ds2 = _parse(novo_b)
    lit2 = _literais(novo_b)
    assert len(lit2) == len(antigos)
    for i, (a, c) in enumerate(zip(antigos, lit2)):
        assert (c.decode("utf-8") == mudados[i]) if i in mudados else (a == c), f"literal {i}"
    for i, ((o1, s1), (o2, s2)) in enumerate(zip(pares, p2)):
        if i not in (0, 1) and s1:
            assert s1 == s2 and b[o1:o1 + s1] == novo_b[o2:o2 + s2], f"seção {i}"
    with open(bk.atual(REL), "wb") as f:
        f.write(novo_b)
    bk.registrar(REL)
    log(f"  {len(mudados)} textos do código traduzidos")
