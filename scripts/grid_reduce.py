"""REDUCTION PAR DEFAUT du skill. Reduction « fidele a la grille » d'une image pixel art agrandie (generee par IA, grille un peu irreguliere).

Pillow seul, pas de numpy. 1 cellule de la grille detectee = 1 pixel du sprite.
Etapes :
  1. Profil de bords par colonne / par ligne (nombre de transitions de couleur nettes).
  2. Pas estime par autocorrelation du profil, puis lignes de grille choisies par programmation
     dynamique (espacement autorise 0,7-1,35 x le pas) : suit une grille qui derive localement.
  3. Couleur de cellule = mode (couleurs regroupees) du coeur de la cellule.
  4. Palette propre de l'image : fusion des quasi-doublons (Lab), plafond --max-colors.
  5. Fond blanc relie au bord -> transparent (alpha net), recadrage.

Garde la resolution native (1 case = 1 pixel) et la palette propre de l image : pas de palette
du jeu, pas de taille imposee (l ancienne reduction 64 px + palette coutait ~3 points).

Usage : python -I grid_reduce.py SRC.png OUT.png [--max-colors 32] [--merge 7] [--step P] [--debug DBG.png]
"""
import argparse, math, os, sys
from collections import Counter
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import lab


def cdiff(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def edge_profiles(im, thr=45):
    w, h = im.size
    px = im.load()
    col = [0.0] * (w + 1)
    row = [0.0] * (h + 1)
    for y in range(0, h, 2):
        for x in range(2, w - 1):
            # transition entre x-1 et x (on regarde x-2 / x+1 pour encaisser le flou de 1 px)
            if cdiff(px[x - 1, y], px[x, y]) > thr and cdiff(px[x - 2, y], px[x + 1, y]) > thr:
                col[x] += 1
    for x in range(0, w, 2):
        for y in range(2, h - 1):
            if cdiff(px[x, y - 1], px[x, y]) > thr and cdiff(px[x, y - 2], px[x, y + 1]) > thr:
                row[y] += 1
    return col, row


def autocorr(prof, lo, hi):
    n = len(prof)
    m = sum(prof) / n
    d = [v - m for v in prof]
    var = sum(v * v for v in d) / n or 1
    return {lag: sum(d[i] * d[i + lag] for i in range(n - lag)) / (n - lag) / var for lag in range(lo, hi + 1)}


def est_step(profs, lo=10, hi=16):
    # plage 10-16 px : images Codex de 1024-1536 px pour ~80-120 cases ; au-dela on attrape un
    # multiple du pas (ex. 17,5 = 3 x 5,85 sur une image dessinee en blocs de 2 cases)
    """Pas commun aux deux axes (pixels carres) : somme des autocorrelations normalisees."""
    scores = {}
    for p in profs:
        for lag, s in autocorr(p, lo, hi).items():
            scores[lag] = scores.get(lag, 0) + s
    # pic local le plus haut ; on prefere le plus petit lag dont le score vaut >= 85 % du max
    mx = max(scores.values())
    peaks = [l for l in scores if scores[l] >= 0.85 * mx and scores[l] >= scores.get(l - 1, -1e18) and scores[l] >= scores.get(l + 1, -1e18)]
    lag = min(peaks) if peaks else max(scores, key=scores.get)
    # affinage sous-entier : moyenne ponderee autour du pic
    a, b, c = scores.get(lag - 1, 0), scores[lag], scores.get(lag + 1, 0)
    den = a - 2 * b + c
    off = 0.5 * (a - c) / den if den != 0 else 0
    return lag + max(-0.5, min(0.5, off))


def grid_lines(prof, step):
    """DP : positions de coupe 0..n maximisant le profil, espacement dans [0,7p ; 1,35p]."""
    n = len(prof) - 1
    # profil lisse a 3 px pour tolerer le flou
    sm = [max(prof[max(0, i - 1):i + 2]) * 0.5 + prof[i] * 0.5 for i in range(len(prof))]
    mean = sum(sm) / len(sm)
    lo, hi = max(2, int(round(step * 0.7))), int(round(step * 1.35))
    NEG = -1e18
    best = [NEG] * (n + 1)
    prev = [-1] * (n + 1)
    # premiere coupe libre dans [0, hi]
    for i in range(0, min(hi, n) + 1):
        best[i] = sm[i] - mean
    for i in range(1, n + 1):
        for d in range(lo, hi + 1):
            j = i - d
            if j < 0 or best[j] == NEG:
                continue
            v = best[j] + sm[i] - mean - 0.15 * abs(d - step) * mean
            if v > best[i]:
                best[i], prev[i] = v, j
    # derniere coupe dans [n-hi, n]
    end = max(range(max(0, n - hi), n + 1), key=lambda i: best[i])
    cuts = []
    i = end
    while i != -1:
        cuts.append(i)
        i = prev[i]
    cuts.reverse()
    if cuts[0] > 0:
        cuts.insert(0, 0)
    if cuts[-1] < n:
        cuts.append(n)
    return cuts


DARK = 210        # somme R+G+B sous laquelle une couleur compte comme trait sombre
DARK_SHARE = 0.3  # part minimale de sombre dans la cellule pour la peindre sombre


def cell_color(px, x0, x1, y0, y1):
    mx = max(1, (x1 - x0) // 6)
    my = max(1, (y1 - y0) // 6)
    xs = range(x0 + mx, max(x0 + mx + 1, x1 - mx))
    ys = range(y0 + my, max(y0 + my + 1, y1 - my))
    cnt = Counter()
    vals = {}
    for y in ys:
        for x in xs:
            c = px[x, y]
            k = (c[0] // 12, c[1] // 12, c[2] // 12)
            cnt[k] += 1
            vals.setdefault(k, []).append(c)
    total = sum(cnt.values())
    # priorite aux sombres (contour, pupille, bouche) : un trait d'une cellule decale de
    # moitie sur la grille doit rester un trait
    dark = [k for k in cnt if sum(k) * 12 < DARK]
    dn = sum(cnt[k] for k in dark)
    if dark and dn >= DARK_SHARE * total:
        k = max(dark, key=lambda q: cnt[q])
    else:
        k, _ = cnt.most_common(1)[0]
    v = vals[k]
    return tuple(sorted(p[i] for p in v)[len(v) // 2] for i in range(3))


def build_palette(colors, merge, max_colors):
    """Regroupe les couleurs de cellules (ponderees) : fusion des quasi-doublons puis plafond."""
    cnt = Counter(colors)
    clusters = []  # [sum_r, sum_g, sum_b, n]
    for c, n in cnt.most_common():
        L = lab(c)
        for cl in clusters:
            if math.dist(L, cl[4]) < merge:
                cl[0] += c[0] * n; cl[1] += c[1] * n; cl[2] += c[2] * n; cl[3] += n
                break
        else:
            clusters.append([c[0] * n, c[1] * n, c[2] * n, n, L])
    def center(cl):
        return (round(cl[0] / cl[3]), round(cl[1] / cl[3]), round(cl[2] / cl[3]))
    while len(clusters) > max_colors:
        best = None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = math.dist(clusters[i][4], clusters[j][4]) * min(clusters[i][3], clusters[j][3]) ** 0.25
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        a, b = clusters[i], clusters[j]
        m = [a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3], None]
        m[4] = lab(center(m))
        clusters[i] = m
        del clusters[j]
    # representant = couleur reelle de cellule la plus frequente du groupe (pas la moyenne,
    # qui ternit les couleurs) : garde les teintes de l'image brute
    return [center(cl) for cl in clusters]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--max-colors", type=int, default=32)
    ap.add_argument("--merge", type=float, default=7.0, help="distance Lab de fusion des quasi-doublons")
    ap.add_argument("--step", type=float, default=0)
    ap.add_argument("--white", type=int, default=232, help="seuil du fond blanc (min des canaux)")
    ap.add_argument("--debug", default="")
    a = ap.parse_args()
    im = Image.open(a.src).convert("RGB")
    w, h = im.size
    px = im.load()
    col, row = edge_profiles(im)
    sx = sy = a.step or est_step([col, row])
    xs = grid_lines(col, sx)
    ys = grid_lines(row, sy)
    gw, gh = len(xs) - 1, len(ys) - 1
    cells = [[cell_color(px, xs[i], xs[i + 1], ys[j], ys[j + 1]) for i in range(gw)] for j in range(gh)]
    # fond : cellules quasi blanches reliees au bord
    def white(c):
        return min(c) >= a.white
    bg = [[False] * gw for _ in range(gh)]
    stack = [(i, j) for i in range(gw) for j in (0, gh - 1)] + [(i, j) for j in range(gh) for i in (0, gw - 1)]
    while stack:
        i, j = stack.pop()
        if 0 <= i < gw and 0 <= j < gh and not bg[j][i] and white(cells[j][i]):
            bg[j][i] = True
            stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    # trous de fond enfermes (entre une patte et le ventre) : composantes blanches de >= 4 cases ;
    # le reflet de l'oeil (1-3 cases) reste blanc
    seen = [[False] * gw for _ in range(gh)]
    for j0 in range(gh):
        for i0 in range(gw):
            if seen[j0][i0] or bg[j0][i0] or not white(cells[j0][i0]):
                continue
            comp, st = [], [(i0, j0)]
            seen[j0][i0] = True
            while st:
                i, j = st.pop()
                comp.append((i, j))
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < gw and 0 <= nj < gh and not seen[nj][ni] and not bg[nj][ni] and white(cells[nj][ni]):
                        seen[nj][ni] = True
                        st.append((ni, nj))
            if len(comp) >= 9:
                for i, j in comp:
                    bg[j][i] = True
    fg = [cells[j][i] for j in range(gh) for i in range(gw) if not bg[j][i]]
    pal = build_palette(fg, a.merge, a.max_colors)
    pl = [lab(p) for p in pal]
    out = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    op = out.load()
    cache = {}
    for j in range(gh):
        for i in range(gw):
            if bg[j][i]:
                continue
            c = cells[j][i]
            if c not in cache:
                L = lab(c)
                cache[c] = pal[min(range(len(pal)), key=lambda k: math.dist(L, pl[k]))]
            op[i, j] = cache[c] + (255,)
    bbox = out.getbbox()
    out = out.crop(bbox)
    out.save(a.out)
    used = len([c for _, c in out.getcolors(1 << 16) if c[3]])
    print(f"{os.path.basename(a.src)}: pas {sx:.2f} x {sy:.2f}, grille {gw}x{gh}, sprite {out.width}x{out.height}, {used} couleurs")
    if a.debug:
        dbg = im.convert("RGB").copy()
        d = ImageDraw.Draw(dbg)
        for x in xs:
            d.line([(x, 0), (x, h)], fill=(255, 0, 255))
        for y in ys:
            d.line([(0, y), (w, y)], fill=(255, 0, 255))
        dbg.save(a.debug)


if __name__ == "__main__":
    main()
