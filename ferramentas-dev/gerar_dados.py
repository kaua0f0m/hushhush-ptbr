"""Gera os arquivos de dados do instalador a partir da memória de tradução.
As chaves são hashes do texto original em inglês (sha1[:20]); o texto original não é distribuído.
Uso: python gerar_dados.py <saida_dados>"""
import glob
import hashlib
import json
import os
import sys

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs(out, exist_ok=True)


def h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:20]


def conv(src, nome):
    res, ident = {}, 0
    for k, v in src.items():
        if v == k or not v:
            ident += 1
            continue
        hk = h(k)
        assert res.get(hk, v) == v, k
        res[hk] = v
    json.dump(res, open(os.path.join(out, nome), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(nome, len(res), "entradas;", ident, "ignoradas (iguais ao original)")


dlg = {}
for f in sorted(glob.glob(os.path.join(base, "traducao", "*.json"))):
    dlg.update(json.load(open(f, encoding="utf-8")))
conv(dlg, "dialogos.json")
conv(json.load(open(os.path.join(base, "ferramentas", "ui_pt.json"), encoding="utf-8")), "interface.json")
conv(json.load(open(os.path.join(base, "ferramentas", "metadata_pt.json"), encoding="utf-8")), "codigo.json")
