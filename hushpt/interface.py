"""Traduz os textos de interface (componentes TextMeshPro/Text nas cenas do jogo).
O jogo é IL2CPP e os MonoBehaviours não têm typetree, então as strings são localizadas
no binário (int32 de tamanho + UTF-8 + alinhamento de 4 bytes) e regravadas no lugar."""
import os
import re
import struct

import UnityPy

from .core import carregar_dados, h

NAMES = ["globalgamemanagers", "globalgamemanagers.assets", "resources.assets"] + [f"level{i}" for i in range(5)] + [f"sharedassets{i}.assets" for i in range(5)]
UI_CLASSES = {"TextMeshProUGUI", "TextMeshPro", "Text"}
_OK = re.compile(r"^[^\x00-\x08\x0b-\x1f]{2,400}$")


def varrer(raw):
    out = []
    i, n = 0, len(raw)
    while i + 4 <= n:
        ln = struct.unpack_from("<i", raw, i)[0]
        if 2 <= ln <= 400 and i + 4 + ln <= n:
            try:
                s = raw[i + 4:i + 4 + ln].decode("utf-8")
            except UnicodeDecodeError:
                i += 4
                continue
            if _OK.match(s) and re.search(r"[A-Za-z]{2}", s):
                pad = (4 - ln % 4) % 4
                if raw[i + 4 + ln:i + 4 + ln + pad] == b"\x00" * pad:
                    out.append((i, s))
                    i += 4 + ln + pad
                    continue
        i += 4
    return out


def _classe_do_script(obj, por_nome, cache):
    raw = obj.get_raw_data()
    fid, pid = struct.unpack_from("<iq", raw, 16)
    sf = obj.assets_file
    if fid != 0:
        sf = por_nome.get(os.path.basename(sf.externals[fid - 1].path))
        if sf is None:
            return None
    chave = (id(sf), pid)
    if chave not in cache:
        o = sf.objects.get(pid)
        cache[chave] = o.read().m_ClassName if o is not None else None
    return cache[chave]


def aplicar(bk, log=print):
    pt = carregar_dados("interface.json")
    caminhos = []
    for n in NAMES:
        if n == "sharedassets2.assets":
            # as fontes já foram corrigidas neste arquivo; partimos da versão atual
            caminhos.append(bk.atual(n))
        else:
            caminhos.append(bk.original(n))
    env = UnityPy.load(*caminhos)
    por_nome = {os.path.basename(str(k)): f for k, f in env.files.items()}
    cache = {}
    tocados = {}
    total = 0
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            cls = _classe_do_script(o, por_nome, cache)
        except Exception:
            continue
        if cls not in UI_CLASSES:
            continue
        raw = o.get_raw_data()
        achados = [(off, s, pt[h(s)]) for off, s in varrer(raw) if h(s) in pt]
        if not achados:
            continue
        raw = bytearray(raw)
        for off, s, novo in sorted(achados, reverse=True):
            ln = len(s.encode("utf-8"))
            fim = off + 4 + ln + (4 - ln % 4) % 4
            nb = novo.encode("utf-8")
            raw[off:fim] = struct.pack("<i", len(nb)) + nb + b"\x00" * ((4 - len(nb) % 4) % 4)
            total += 1
        o.set_raw_data(bytes(raw))
        tocados[os.path.basename(o.assets_file.name)] = o.assets_file
    for nome, sf in tocados.items():
        dados = sf.save()
        with open(bk.atual(nome), "wb") as f:
            f.write(dados)
        bk.registrar(nome)
    log(f"  {total} textos de interface traduzidos em {len(tocados)} arquivos")
