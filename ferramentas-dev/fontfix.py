"""Hush Hush - adiciona glifos acentuados (PT-BR) às fontes TextMeshPro Futura do jogo.

Uso:
  python fontfix.py aplicar   <pasta_do_jogo> [pasta_previa]
  python fontfix.py restaurar <pasta_do_jogo>

As fontes (TMP 1.1, sem typetree) são editadas em binário:
  - o atlas SDF (Alpha8) ganha mais 512 linhas no topo (512x512 -> 512x1024);
  - glifos novos são compostos com "max" de SDFs: letra base + acento recortado
    de um glifo existente (á, è, ~, ^, ç);
  - entradas novas são acrescentadas à glyph table, character table e used rects.
Os .assets originais ficam em <pasta_do_jogo>/_backup_traducao_en.
"""
import os
import shutil
import struct
import sys

import numpy as np
import UnityPy
from PIL import Image

FILES = ["sharedassets1.assets", "sharedassets2.assets"]
GLYPH_FMT = "<I5f4ifi"  # index, w,h,bx,by,adv, x,y,w,h, scale, atlasIndex
GSZ = struct.calcsize(GLYPH_FMT)
EXTRA_H = 512

LOWER = {
    "à": ("a", "grave"), "â": ("a", "circ"), "ã": ("a", "tilde"), "á": ("a", "acute"),
    "é": ("e", "acute"), "ê": ("e", "circ"), "è": ("e", "grave"),
    "í": ("i", "acute"), "ó": ("o", "acute"), "ô": ("o", "circ"), "õ": ("o", "tilde"),
    "ú": ("u", "acute"), "ü": ("u", "diaer"), "ç": ("c", "cedil"),
}
UPPER = {k.upper(): (v[0].upper(), v[1]) for k, v in LOWER.items()}
TARGETS = {**LOWER, **UPPER}


class FontAsset:
    def __init__(self, raw):
        self.raw = raw
        I = lambda off: struct.unpack_from("<i", raw, off)[0]
        ct = None
        for off in range(0, len(raw) - 20, 4):
            cnt = I(off)
            if 20 <= cnt <= 5000 and off + 4 + cnt * 16 <= len(raw):
                if all(struct.unpack_from("<I", raw, off + 4 + i * 16)[0] == 1 and
                       struct.unpack_from("<f", raw, off + 16 + i * 16)[0] == 1.0 for i in range(cnt)):
                    ct = off
                    break
        assert ct is not None, "character table não encontrada"
        nc = I(ct)
        gt = None
        for n in range(1, 5000):
            off = ct - 4 - n * GSZ
            if off < 0:
                break
            if I(off) == n:
                gt = off
                break
        assert gt is not None, "glyph table não encontrada"
        ng = I(gt)
        self.head = raw[:gt]
        self.glyphs = [list(struct.unpack_from(GLYPH_FMT, raw, gt + 4 + i * GSZ)) for i in range(ng)]
        self.chars = [list(struct.unpack_from("<IIIf", raw, ct + 4 + i * 16)) for i in range(nc)]
        p = ct + 4 + nc * 16
        # atlasTextures (count=1 + PPtr 12) + 3 ints
        assert I(p) == 1
        self.mid = raw[p:p + 28]
        p += 28
        nu = I(p)
        self.used = [list(struct.unpack_from("<4i", raw, p + 4 + i * 16)) for i in range(nu)]
        p += 4 + nu * 16
        self.tail = bytearray(raw[p:])
        self.atlas_pid = struct.unpack_from("<q", self.mid, 8)[0]
        # padding / dims: first "512,512,pad" run in tail
        t = self.tail
        for off in range(0, len(t) - 12, 4):
            w, h, pad = struct.unpack_from("<iii", t, off)
            if w in (256, 512, 1024, 2048) and h in (256, 512, 1024, 2048) and 0 < pad < 32:
                self.dim_off = off
                self.width, self.height, self.padding = w, h, pad
                break

    def charmap(self):
        # copies with metrics rounded to whole pixels (glyph space == atlas pixels)
        g = {gl[0]: [gl[0]] + [int(round(v)) for v in gl[1:6]] + gl[6:] for gl in self.glyphs}
        return {c[1]: g[c[2]] for c in self.chars if c[2] in g}

    def set_height(self, newh):
        t = self.tail
        oldh = self.height
        # int pairs (w, oldh) and float pairs
        for off in range(0, len(t) - 8, 4):
            a, b = struct.unpack_from("<ii", t, off)
            if a == self.width and b == oldh:
                struct.pack_into("<i", t, off + 4, newh)
            fa, fb = struct.unpack_from("<ff", t, off)
            if fa == float(self.width) and fb == float(oldh):
                struct.pack_into("<f", t, off + 4, float(newh))
        self.height = newh

    def build(self):
        out = bytearray(self.head)
        out += struct.pack("<i", len(self.glyphs))
        for g in self.glyphs:
            out += struct.pack(GLYPH_FMT, *g)
        out += struct.pack("<i", len(self.chars))
        for c in self.chars:
            out += struct.pack("<IIIf", *c)
        out += self.mid
        out += struct.pack("<i", len(self.used))
        for u in self.used:
            out += struct.pack("<4i", *u)
        out += self.tail
        return bytes(out)


def region(atlas, g, pad):
    """SDF region of glyph g (with padding) as float array, row 0 = top. Returns (arr, left, top) in glyph space."""
    _, w, h, bx, by, adv, x, y, rw, rh, _, _ = g
    H = atlas.shape[0]
    # atlas is top-down image; glyph rect y is from bottom
    top_row = H - (y + rh) - pad
    arr = atlas[top_row:top_row + rh + 2 * pad, x - pad:x + rw + pad].astype(np.float32)
    return arr, bx - pad, by + pad  # left x, top y (y up) in glyph space


def ink_rows(arr):
    return np.where((arr >= 128).any(axis=1))[0]


def ink_cols(arr):
    return np.where((arr >= 128).any(axis=0))[0]


def accent_from(atlas, cm, pad, acc_char, base_char, below=False):
    """Cut the accent part of an accented glyph (e.g. á minus a). Returns (arr, left, top)."""
    arr, left, top = region(atlas, cm[ord(acc_char)], pad)
    _, btop = region(atlas, cm[ord(base_char)], pad)[1:]
    base_g = cm[ord(base_char)]
    base_top_y = base_g[4]  # bearingY (top of ink)
    rows = ink_rows(arr)
    # row index of y: row = top - y
    if not below:
        cut_row = top - base_top_y  # row of base letter top
        # find gap: last ink row of accent above base top
        acc_rows = [r for r in rows if r < cut_row - 1]
        acc_bottom = max(acc_rows)
        mid = (acc_bottom + cut_row) // 2 + 1
        out = arr[:mid].copy()
        return out, left, top
    else:
        base_bottom_y = base_g[4] - base_g[2]
        cut_row = top - base_bottom_y
        acc_rows = [r for r in rows if r > cut_row + 1]
        acc_top = min(acc_rows)
        mid = (acc_top + cut_row) // 2
        out = arr[mid:].copy()
        return out, left, top - mid


def scaled_mark(atlas, cm, pad, ch, target_w, target_h):
    arr, left, top = region(atlas, cm[ord(ch)], pad)
    cols = ink_cols(arr)
    rows = ink_rows(arr)
    ink_w = cols.max() - cols.min() + 1
    ink_h = rows.max() - rows.min() + 1
    s = min(target_w / ink_w, target_h / ink_h)
    im = Image.fromarray(arr.astype(np.uint8))
    nw, nh = max(1, round(arr.shape[1] * s)), max(1, round(arr.shape[0] * s))
    im = im.resize((nw, nh), Image.BILINEAR)
    a = np.asarray(im).astype(np.float32)
    # rescale distance falloff so the padding stays similar: push values away from 0.5
    a = np.clip((a - 127.5) / s + 127.5, 0, 255)
    return a


def compose(atlas, cm, pad, ch, base, kind):
    """Return (arr, left, top, advance) in glyph space."""
    bg = cm[ord(base)]
    barr, bleft, btop = region(atlas, bg, pad)
    adv = bg[5]
    upper = base.isupper()
    lower_ref = cm[ord("a")]
    x_top = lower_ref[4]
    base_top = bg[4]
    lift = base_top - x_top  # extra lift for capitals / tall letters
    pieces = [(barr, bleft, btop)]
    if base in "iI" and base == "i":
        # remove the dot: keep only rows from x-height down
        cut = btop - x_top - 2
        rows = ink_rows(barr)
        dot_rows = [r for r in rows if r < cut]
        if dot_rows:
            gap_end = max(dot_rows)
            stem_rows = [r for r in rows if r > gap_end]
            mid = (gap_end + min(stem_rows)) // 2 + 1
            barr = barr[mid:].copy()
            pieces = [(barr, bleft, btop - mid)]
        lift = 0
    bcols = ink_cols(pieces[0][0])
    bcenter = pieces[0][1] + (bcols.min() + bcols.max() + 1) / 2

    if kind == "cedil":
        acc, aleft, atop = accent_from(atlas, cm, pad, "ç", "c", below=True)
        ccols = ink_cols(acc)
        acenter = aleft + (ccols.min() + ccols.max() + 1) / 2
        # cedilla anchored at base bottom (baseline): keep its vertical pos
        pieces.append((acc, aleft + round(bcenter - acenter), atop))
        return pieces, adv

    if kind == "acute":
        acc, aleft, atop = accent_from(atlas, cm, pad, "á", "a")
    elif kind == "grave":
        acc, aleft, atop = accent_from(atlas, cm, pad, "è", "e")
    elif kind == "diaer":
        acc, aleft, atop = accent_from(atlas, cm, pad, "ä", "a")
    else:
        ref, rleft, rtop = accent_from(atlas, cm, pad, "á", "a")
        rcols = ink_cols(ref)
        rrows = ink_rows(ref)
        acute_w = rcols.max() - rcols.min() + 1
        acute_h = rrows.max() - rrows.min() + 1
        acute_bottom_y = min(rtop - rrows.max(), x_top + 5)
        base_w = bcols.max() - bcols.min() + 1
        acc = scaled_mark(atlas, cm, pad, "~" if kind == "tilde" else "^",
                          base_w * 0.95 if kind == "tilde" else acute_w * 1.3,
                          acute_h * 1.3 if kind == "tilde" else acute_h * 0.95)
        arows = ink_rows(acc)
        # place so that ink bottom sits at the acute's ink bottom
        atop = acute_bottom_y + arows.max()
        aleft = 0
    acols = ink_cols(acc)
    acenter = aleft + (acols.min() + acols.max() + 1) / 2
    rise = (2 if upper else 0) + ((6 if upper else 3) if kind == "tilde" else 0)
    pieces.append((acc, aleft + round(bcenter - acenter), atop + lift + rise))
    return pieces, adv


def rasterize(pieces):
    left = min(p[1] for p in pieces)
    top = max(p[2] for p in pieces)
    right = max(p[1] + p[0].shape[1] for p in pieces)
    bottom = min(p[2] - p[0].shape[0] for p in pieces)
    W, H = right - left, top - bottom
    canvas = np.zeros((H, W), np.float32)
    for arr, l, t in pieces:
        r0, c0 = top - t, l - left
        sub = canvas[r0:r0 + arr.shape[0], c0:c0 + arr.shape[1]]
        np.maximum(sub, arr, out=sub)
    return canvas, left, top


def fix_font(fa, atlas_img, preview=None, name=""):
    atlas = np.asarray(atlas_img).astype(np.uint8)
    if atlas.ndim == 3:
        atlas = atlas[..., -1]
    pad = fa.padding
    cm = fa.charmap()
    missing = [c for c in TARGETS if ord(c) not in cm]
    if not missing:
        return None
    H0, W = atlas.shape
    newH = H0 + EXTRA_H
    big = np.zeros((newH, W), np.uint8)
    big[EXTRA_H:, :] = atlas  # existing content stays at the bottom (Unity y unchanged)
    next_index = max(g[0] for g in fa.glyphs) + 1000
    cx, cy_top, row_h = 0, 0, 0  # packing in the new top area (image rows 0..EXTRA_H)
    added = []
    for ch in missing:
        base, kind = TARGETS[ch]
        if ord(base) not in cm:
            continue
        pieces, adv = compose(atlas, cm, pad, ch, base, kind)
        canvas, left, top = rasterize(pieces)
        h, w = canvas.shape
        if cx + w > W:
            cx, cy_top, row_h = 0, cy_top + row_h + 1, 0
        assert cy_top + h <= EXTRA_H, "sem espaço no atlas"
        big[cy_top:cy_top + h, cx:cx + w] = np.clip(canvas, 0, 255).astype(np.uint8)
        # glyph rect (without padding), Unity y from bottom
        rx, rw = cx + pad, w - 2 * pad
        rh = h - 2 * pad
        ry = newH - (cy_top + pad + rh)
        gw, gh = float(rw), float(rh)
        bx, by = float(left + pad), float(top - pad)
        fa.glyphs.append([next_index, gw, gh, bx, by, float(adv), rx, ry, rw, rh, 1.0, 0])
        fa.chars.append([1, ord(ch), next_index, 1.0])
        fa.used.append([cx, newH - (cy_top + h), w, h])
        added.append(ch)
        next_index += 1
        cx += w + 1
        row_h = max(row_h, h)
    fa.set_height(newH)
    img = Image.fromarray(big, "L")
    if preview:
        prev = np.where(big >= 128, 0, 255).astype(np.uint8)
        Image.fromarray(prev[:cy_top + row_h + 2]).save(os.path.join(preview, name + "_novos.png"))
    return img, added


def game_data(game):
    return os.path.join(game, "HushHush_Data")


def aplicar(game, preview=None, write=True):
    bd = os.path.join(game, "_backup_traducao_en")
    os.makedirs(bd, exist_ok=True)
    for f in FILES:
        src = os.path.join(game_data(game), f)
        bk = os.path.join(bd, f)
        if not os.path.exists(bk):
            shutil.copy2(src, bk)
    for f in FILES:
        env = UnityPy.load(os.path.join(bd, f))
        objs = {o.path_id: o for o in env.objects}
        changed = False
        for o in list(env.objects):
            if o.type.name != "MonoBehaviour":
                continue
            raw = o.get_raw_data()
            if len(raw) < 2000 or b"Futur" not in raw[:80]:
                continue
            try:
                fa = FontAsset(raw)
            except AssertionError:
                continue
            tex_obj = objs.get(fa.atlas_pid)
            if tex_obj is None or tex_obj.type.name != "Texture2D":
                continue
            tex = tex_obj.read()
            name = tex.m_Name
            res = fix_font(fa, tex.image, preview, name)
            if not res:
                continue
            img, added = res
            print(f"{f}: {name}: +{len(added)} glifos ({''.join(added)})")
            if not write:
                continue
            o.set_raw_data(fa.build())
            tex.set_image(_alpha_rgba(img))
            tex.save()
            changed = True
        if changed:
            for o in env.objects:
                if o.type.name == "Material":
                    m = o.read_typetree()
                    floats = m["m_SavedProperties"]["m_Floats"]
                    touched = False
                    for i, (k, v) in enumerate(floats):
                        if k == "_TextureHeight" and v == 512.0:
                            floats[i] = (k, 1024.0)
                            touched = True
                    if touched:
                        o.save_typetree(m)
            data = env.file.save()
            with open(os.path.join(game_data(game), f), "wb") as fh:
                fh.write(data)


def _alpha_rgba(img_l):
    a = img_l
    white = Image.new("L", a.size, 255)
    return Image.merge("RGBA", (white, white, white, a))


def restaurar(game):
    bd = os.path.join(game, "_backup_traducao_en")
    for f in FILES:
        if os.path.exists(os.path.join(bd, f)):
            shutil.copy2(os.path.join(bd, f), os.path.join(game_data(game), f))
    print("Fontes originais restauradas.")


if __name__ == "__main__":
    if sys.argv[1] == "aplicar":
        aplicar(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif sys.argv[1] == "previa":
        aplicar(sys.argv[2], sys.argv[3], write=False)
    elif sys.argv[1] == "restaurar":
        restaurar(sys.argv[2])
    else:
        raise SystemExit(__doc__)
