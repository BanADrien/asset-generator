"""Mesures objectives d'un sprite (etape 1 de la notation). Pillow seul.

Usage : python -I measure.py SPRITE.png --height 24 [--width 32] [--palette P.hex] [--json OUT.json]

Chaque test a un seuil ; un seul echec => "plafond": 5 (la note finale ne peut pas depasser 5).
Seuils expliques dans references/rubric.md (partie A).
"""
import argparse, json, os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import load_palette, lab, lum, components, N4, N8, PALETTE


def measure(path, th, tw, palette):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    pal = set(load_palette(palette))
    ops = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 255]
    n = max(1, len(ops))
    semi = sum(1 for y in range(h) for x in range(w) if 0 < px[x, y][3] < 255)
    used = {}
    for x, y in ops:
        used[px[x, y][:3]] = used.get(px[x, y][:3], 0) + 1
    off = sum(c for k, c in used.items() if k not in pal)

    def op(x, y):
        return 0 <= x < w and 0 <= y < h and px[x, y][3] == 255

    isolated = sum(1 for x, y in ops if not any(op(x + dx, y + dy) for dx, dy in N8))
    # orphelins de couleur : aucun voisin 8-connexe de la meme couleur (bruit, "poussiere")
    orph = sum(1 for x, y in ops if not any(op(x + dx, y + dy) and px[x + dx, y + dy][:3] == px[x, y][:3] for dx, dy in N8))
    edge = [(x, y) for x, y in ops if any(not op(x + dx, y + dy) for dx, dy in N4)]
    lums = sorted(lum(px[x, y]) for x, y in ops) or [0]
    lo, hi = lums[0], lums[-1]
    dark_thr = lo + 0.35 * (hi - lo)
    outline_cov = sum(1 for x, y in edge if lum(px[x, y]) <= dark_thr) / max(1, len(edge))
    comps = components(px, w, h)
    frag = sum(len(c) for c in comps[1:])
    bb = im.getchannel("A").getbbox() or (0, 0, w, h)
    fill = n / max(1, (bb[2] - bb[0]) * (bb[3] - bb[1]))
    pairs = diff = 0
    for x, y in ops:
        for dx, dy in ((1, 0), (0, 1)):
            if op(x + dx, y + dy):
                pairs += 1
                diff += px[x + dx, y + dy][:3] != px[x, y][:3]
    noise = diff / max(1, pairs)
    contrast = hi - lo
    # le sujet doit remplir la boite cible (a 2 px pres sur un des deux cotes), jamais la depasser
    size_ok = (th - 2 <= h or (tw and tw - 2 <= w)) and h <= th and (not tw or w <= tw)

    tests = [
        ("taille", f"{w}x{h} (cible h={th}{', l<=' + str(tw) if tw else ''})", size_ok),
        ("hors_palette", f"{off} px", off == 0),
        ("semi_transparents", f"{semi} px", semi == 0),
        ("pixels_isoles", f"{isolated} px", isolated == 0),
        ("orphelins_couleur", f"{orph / n:.1%} des px opaques (max 12 %)", orph / n <= 0.12),
        ("couverture_contour", f"{outline_cov:.0%} du bord est sombre (min 85 %)", outline_cov >= 0.85),
        ("silhouette_un_bloc", f"{len(comps)} morceau(x), {frag} px detaches (max 2)", frag <= 2),
        ("remplissage_silhouette", f"{fill:.0%} de la boite (35-92 %)", 0.35 <= fill <= 0.92),
        ("couleurs_utilisees", f"{len(used)} (5-20)", 5 <= len(used) <= 20),
        ("contraste_valeurs", f"L* {lo:.0f}->{hi:.0f}, ecart {contrast:.0f} (min 45)", contrast >= 45),
        ("bruit", f"{noise:.0%} de voisins de couleur differente (max 55 %)", noise <= 0.55),
    ]
    failed = [t[0] for t in tests if not t[2]]
    return {
        "sprite": path, "size": [w, h], "opaque_px": len(ops), "colors": len(used),
        "tests": [{"test": t[0], "valeur": t[1], "ok": t[2]} for t in tests],
        "echecs": failed, "plafond": 5 if failed else 10,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sprite")
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--palette", default=PALETTE)
    ap.add_argument("--json")
    a = ap.parse_args()
    r = measure(a.sprite, a.height, a.width, a.palette)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(r, f, indent=1, ensure_ascii=False)
    for t in r["tests"]:
        print(("OK   " if t["ok"] else "ECHEC") + f" {t['test']:<24} {t['valeur']}")
    print(f"plafond objectif : {r['plafond']}/10" + (f"  (echecs : {', '.join(r['echecs'])})" if r["echecs"] else ""))


if __name__ == "__main__":
    main()
