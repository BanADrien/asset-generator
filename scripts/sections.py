"""Sprite EN SECTIONS pour l'eclairage dynamique : version neutre + carte de sections + normales.

Pillow seul, pas de numpy. Entree : un sprite PNG existant (fond transparent, profil tourne a
droite, eclaire d'en haut a gauche comme le style du jeu). Sorties a cote de lui :
  <nom>.neutre.png    couleurs de base en aplats (chaque rampe de matiere -> sa couleur moyenne
                      prise dans la palette du sprite) ; contour, lignes sombres et details
                      gardes (oeil, pupille, reflet, bouche)
  <nom>.sections.png  zones en couleurs franches (1 couleur = 1 direction, table SECTIONS
                      ci-dessous et dans references/lumiere.md), a retoucher a la main
  <nom>.normales.png  carte de normales : R = x (droite), G = y (HAUT, convention OpenGL,
                      celle du Light2D de Phaser 3), B = z (vers le spectateur) ; n = rgb*2-1

Decoupage : les lignes sombres interieures et les changements de matiere ferment des parties
(dos, cuisse, gorge, tete...) ; orientation = volume de la silhouette floutee + bombe de la
partie floutee seule + ombrage d'origine (clair = tourne vers la lumiere en haut a gauche) ;
tout est quantifie sur 17 sections (face, 8 inclinees, 8 rasantes) puis nettoye (bords nets).

Usage :
  python -I sections.py SPRITE.png [--apercu] [--gauche] [--garder hex,hex] [--rampes "hex,hex;hex,hex"]
  python -I sections.py SPRITE.png --depuis-sections SPRITE.sections.png   (recalcule les normales)
  --apercu : <nom>.apercu.png (origine | neutre | sections | eclaire gauche | eclaire droite, x4)
  --gauche : <nom>.neutre-gauche.png + <nom>.normales-gauche.png (sprite retourne pour regarder a
             gauche, rouge des normales inverse ; flipX de Phaser 3.80 ne corrige pas les normales)
"""
import argparse, math, os, sys
from collections import Counter, deque
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import lab, N4, N8

# ---------------------------------------------------------------- table des sections
# code -> (nom, couleur franche, direction dans le plan (x droite, y haut) ou None, inclinaison)
# inclinaison : 0 = face au spectateur, 40 deg = incline, 68 deg = rasant (bord tourne).
DIRS = [("droite", 0), ("haut-droite", 45), ("haut", 90), ("haut-gauche", 135),
        ("gauche", 180), ("bas-gauche", 225), ("bas", 270), ("bas-droite", 315)]
TILT_INC, TILT_RAS = 40.0, 68.0
GBLUR, GPAD = 6.0, 16  # flou de la silhouette pour le bombe global (px)
W_GLOBAL, W_PART, W_SHADE = 0.7, 0.55, 0.3  # poids : volume d'ensemble, bombe des parties, ombrage d'origine


def _hsv(hdeg, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((hdeg % 360) / 360.0, s, v)
    return (round(r * 255), round(g * 255), round(b * 255))


SECTIONS = [("face", (200, 200, 200), None, 0.0)]
for nom, ang in DIRS:
    SECTIONS.append((nom + " incline", _hsv(ang, 0.55, 0.98), ang, TILT_INC))
for nom, ang in DIRS:
    SECTIONS.append((nom + " rasant", _hsv(ang, 0.95, 0.62), ang, TILT_RAS))


def section_normal(code):
    _, _, ang, tilt = SECTIONS[code]
    if ang is None:
        return (0.0, 0.0, 1.0)
    t, a = math.radians(tilt), math.radians(ang)
    return (math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t))


def encode_normal(n):
    return tuple(max(0, min(255, round((c * 0.5 + 0.5) * 255))) for c in n)


def quantize(nx, ny):
    """Vecteur dans le plan (y haut) -> code de section."""
    m = math.hypot(nx, ny)
    if m < 0.30:
        return 0
    k = int(round(math.degrees(math.atan2(ny, nx)) / 45.0)) % 8
    return 1 + k if m < 0.72 else 9 + k


def nearest_code(rgb):
    return min(range(len(SECTIONS)), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, SECTIONS[i][1])))


# ---------------------------------------------------------------- analyse des couleurs
def hexc(c):
    return "%02x%02x%02x" % c[:3]


def parse_hex(s):
    s = s.strip().lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def hue_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def cluster_ramps(colors, counts, adj, dark, protected, forced):
    """Rampes de matiere : union des couleurs voisines dans l'image, de meme teinte et meme
    saturation relative (C/L). Les petites couleurs isolees rejoignent la rampe la plus voisine."""
    labs = {c: lab(c) for c in colors}
    feat = {}
    for c, (L, a, b) in labs.items():
        feat[c] = (math.degrees(math.atan2(b, a)), math.hypot(a, b) / max(L, 8.0), math.hypot(a, b))
    parent = {c: c for c in colors}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    for group in forced:
        g = [c for c in group if c in parent]
        for c in g[1:]:
            parent[find(c)] = find(g[0])
    pool = [c for c in colors if c not in dark and c not in protected]
    total = sum(counts[c] for c in pool) or 1
    rare = max(6, int(0.006 * total))
    pairs = sorted(((v, p) for p, v in adj.items() if p[0] in pool and p[1] in pool), reverse=True)
    for v, (a, b) in pairs:
        if counts[a] < rare or counts[b] < rare:
            continue
        s = v / math.sqrt(counts[a] * counts[b])
        fa, fb = feat[a], feat[b]
        grey = fa[2] < 8 and fb[2] < 8
        if s > 0.06 and (grey or (hue_diff(fa[0], fb[0]) < 15 and abs(fa[1] - fb[1]) < 0.17)):
            parent[find(a)] = find(b)
    # couleurs rares : rejoignent la rampe avec laquelle elles se touchent le plus
    for c in sorted(pool, key=lambda c: counts[c]):
        if counts[c] >= rare:
            continue
        best = Counter()
        for (a, b), v in adj.items():
            o = b if a == c else a if b == c else None
            if o is not None and o in pool and counts[o] >= rare:
                best[find(o)] += v
        if best:
            parent[find(c)] = best.most_common(1)[0][0]
    ramps = {}
    for c in pool:
        ramps.setdefault(find(c), []).append(c)
    return list(ramps.values())


def ramp_base(ramp, counts):
    """Couleur moyenne propre de la rampe, prise dans la palette du sprite (pas de couleur inventee)."""
    n = sum(counts[c] for c in ramp)
    m = [sum(lab(c)[i] * counts[c] for c in ramp) / n for i in range(3)]
    return min(ramp, key=lambda c: math.dist(lab(c), m))


# ---------------------------------------------------------------- geometrie
def nearest_vectors(w, h, is_border, cand, R=8):
    """Pour chaque pixel de cand : (distance, vecteur pixel->bord le plus proche)."""
    offs = sorted(((dx, dy) for dx in range(-R, R + 1) for dy in range(-R, R + 1) if (dx or dy)),
                  key=lambda o: o[0] * o[0] + o[1] * o[1])
    out = {}
    for (x, y) in cand:
        found = None
        for dx, dy in offs:
            X, Y = x + dx, y + dy
            if is_border(X, Y):
                d2 = dx * dx + dy * dy
                if found is None:
                    found = [d2, dx, dy, 1]
                elif d2 == found[0]:  # moyenne des bords a egale distance (directions plus stables)
                    found[1] += dx; found[2] += dy; found[3] += 1
                else:
                    break
        if found is None:
            out[(x, y)] = (R + 1, 0.0, 0.0)
        else:
            out[(x, y)] = (math.sqrt(found[0]), found[1] / found[3], found[2] / found[3])
    return out


def mode_filter(codes, region, keep, iters=2):
    """Filtre majoritaire 3x3 a l'interieur de chaque partie (bords de zones nets, pas de pixels isoles)."""
    for _ in range(iters):
        new = dict(codes)
        for p, c in codes.items():
            if p in keep:
                continue
            x, y = p
            cnt = Counter()
            for dx, dy in N8 + ((0, 0),):
                q = (x + dx, y + dy)
                if q in codes and region.get(q) == region.get(p) and q not in keep:
                    cnt[codes[q]] += 2 if (dx, dy) == (0, 0) else 1
            if cnt:
                best, v = cnt.most_common(1)[0]
                if v >= 5 and best != c:
                    new[p] = best
        codes = new
    return codes


def merge_small(codes, minsize, keep):
    """Zones (pixels connexes de meme code) plus petites que minsize -> code voisin majoritaire."""
    seen = set()
    for p in list(codes):
        if p in seen or p in keep:
            continue
        c = codes[p]
        comp, q = [p], deque([p])
        seen.add(p)
        while q:
            x, y = q.popleft()
            for dx, dy in N4:
                r = (x + dx, y + dy)
                if r in codes and r not in seen and codes[r] == c and r not in keep:
                    seen.add(r); comp.append(r); q.append(r)
        if len(comp) < minsize:
            cnt = Counter()
            cs = set(comp)
            for (x, y) in comp:
                for dx, dy in N4:
                    r = (x + dx, y + dy)
                    if r in codes and r not in cs and r not in keep:
                        cnt[codes[r]] += 1
            if cnt:
                nc = cnt.most_common(1)[0][0]
                for r in comp:
                    codes[r] = nc
    return codes


# ---------------------------------------------------------------- programme principal
def analyse(im, garder=(), rampes=()):
    w, h = im.size
    px = im.load()
    opq = {(x, y) for y in range(h) for x in range(w) if px[x, y][3] >= 128}
    col = {p: px[p][:3] for p in opq}
    counts = Counter(col.values())
    colors = list(counts)
    adj = Counter()
    for (x, y) in opq:
        for dx, dy in ((1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q in opq and col[q] != col[(x, y)]:
                adj[tuple(sorted((col[(x, y)], col[q])))] += 1
    L = {c: lab(c)[0] for c in colors}
    chroma = {c: math.hypot(*lab(c)[1:]) for c in colors}
    n = len(opq)

    # lignes sombres : la ou les couleurs les plus sombres (contour + traits interieurs)
    darkest = min(colors, key=lambda c: L[c])
    line_c = max((c for c in colors if L[c] < 22), key=lambda c: counts[c], default=darkest)
    dark = {c for c in colors if L[c] <= L[line_c] + 3.5}

    # details gardes : couleurs rares et tres saturees (oeil) + couleurs rares collees a elles
    protected_px = set()
    rare = max(4, int(0.01 * n))
    med_c = sorted(chroma[c] for c in col.values())[n // 2]
    seeds = {c for c in colors if counts[c] < rare and chroma[c] > max(45, 1.4 * med_c)}
    seeds |= {parse_hex(g) for g in garder}
    front = {p for p in opq if col[p] in seeds}
    protected_px |= front
    for _ in range(2):
        nxt = set()
        for (x, y) in front:
            for dx, dy in N8:
                q = (x + dx, y + dy)
                if q in opq and q not in protected_px and counts[col[q]] < rare:
                    nxt.add(q)
        protected_px |= nxt
        front = nxt
    # couleurs dont tous les pixels sont des details gardes : hors des rampes
    pc = Counter(col[p] for p in protected_px)
    protected_c = {c for c, v in pc.items() if v == counts[c]}
    forced = [[parse_hex(t) for t in g.split(",") if t.strip()] for g in rampes]
    ramps = cluster_ramps(colors, counts, adj, dark, protected_c, forced)
    ramp_of = {c: i for i, r in enumerate(ramps) for c in r}
    base = [ramp_base(r, counts) for r in ramps]

    line_px = {p for p in opq if col[p] in dark and p not in protected_px}

    # matiere de surface vs motif (taches) : un motif touche surtout une autre matiere, peu les lignes
    contact = [Counter() for _ in ramps]
    for (x, y) in opq:
        if (x, y) in line_px or (x, y) in protected_px:
            continue
        r = ramp_of[col[(x, y)]]
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in opq:
                contact[r]["vide"] += 1
            elif q in line_px:
                contact[r]["ligne"] += 1
            elif q not in protected_px and ramp_of[col[q]] != r:
                contact[r][ramp_of[col[q]]] += 1
    seg = list(range(len(ramps)))
    for r, cnt in enumerate(contact):
        tot = sum(cnt.values()) or 1
        others = [(k, v) for k, v in cnt.items() if isinstance(k, int)]
        if others:
            k, v = max(others, key=lambda kv: kv[1])
            if (cnt["ligne"] + cnt["vide"]) / tot < 0.35 and v / tot > 0.45:
                seg[r] = k
    for _ in range(len(seg)):
        seg = [seg[s] for s in seg]

    # parties : remplissage sur les pixels non-ligne, coupe par les lignes et les matieres de surface
    body = [p for p in opq if p not in line_px]
    segm = {p: (seg[ramp_of[col[p]]] if p not in protected_px else -1) for p in body}
    # les traits interieurs ne sont pas toujours fermes : on les epaissit d'1 px pour couper les
    # parties (fuites de 1-2 px), puis les pixels retires reviennent a la partie voisine
    barrier = set(line_px)
    for (x, y) in line_px:
        for dx, dy in N8:
            q = (x + dx, y + dy)
            if q in segm:
                barrier.add(q)
    region = {}
    rid = 0
    for p in body:
        if p in region or p in barrier:
            continue
        stack = [p]
        region[p] = rid
        while stack:
            x, y = stack.pop()
            for dx, dy in N4:
                q = (x + dx, y + dy)
                if q in segm and q not in region and q not in barrier and                         (segm[q] == segm[p] or segm[q] == -1 or segm[p] == -1):
                    region[q] = rid
                    stack.append(q)
        rid += 1

    def absorb(minsize):
        changed = True
        while changed:
            changed = False
            sizes = Counter(region.values())
            for r, sz in sorted(sizes.items(), key=lambda kv: kv[1]):
                if sz >= minsize:
                    break
                members = [p for p in region if region[p] == r]
                cnt = Counter()
                for (x, y) in members:
                    for dx, dy in N8:
                        q = (x + dx, y + dy)
                        if q in region and region[q] != r:
                            cnt[region[q]] += 1
                if cnt:
                    nr = cnt.most_common(1)[0][0]
                    for p in members:
                        region[p] = nr
                    changed = True
                    break

    absorb(12)
    # pixels de la bordure epaissie : rendus a la partie voisine de meme matiere (sinon la plus proche)
    todo = [p for p in body if p not in region]
    for _ in range(4):
        rest = []
        for p in todo:
            x, y = p
            same, other = Counter(), Counter()
            for dx, dy in N8:
                q = (x + dx, y + dy)
                if q in region:
                    (same if segm.get(q) == segm[p] else other)[region[q]] += 1
            pick = same or other
            if pick:
                region[p] = pick.most_common(1)[0][0]
            else:
                rest.append(p)
        todo = rest
    for p in todo:
        region[p] = rid
        rid += 1
    absorb(12)

    def border(X, Y, p_region):
        q = (X, Y)
        if q not in opq or q in line_px:
            return True
        return q in region and region[q] != p_region

    # vecteurs vers le bord de la partie (bombe) et vers le vide (contour exterieur)
    near = {}
    for r in set(region.values()):
        cand = [p for p in region if region[p] == r]
        near.update(nearest_vectors(w, h, lambda X, Y, r=r: border(X, Y, r), cand, R=7))
    out_vec = nearest_vectors(w, h, lambda X, Y: (X, Y) not in opq, opq, R=6)
    dmax = Counter()
    for p, (d, _, _) in near.items():
        dmax[region[p]] = max(dmax[region[p]], d)

    # indice d'ombrage : ecart de luminance a la moyenne de la rampe, lisse dans la partie
    rmean, rstd = {}, {}
    for i, r in enumerate(ramps):
        tot = sum(counts[c] for c in r)
        m = sum(L[c] * counts[c] for c in r) / tot
        sd = math.sqrt(sum((L[c] - m) ** 2 * counts[c] for c in r) / tot) or 1.0
        rmean[i], rstd[i] = m, max(sd, 6.0)
    off = {p: (L[col[p]] - rmean[ramp_of[col[p]]]) / rstd[ramp_of[col[p]]]
           for p in body if p not in protected_px}
    soff = {}
    for p in body:
        x, y = p
        vals = [off[q] for q in ((x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3))
                if q in off and region.get(q) == region[p]]
        soff[p] = sum(vals) / len(vals) if vals else 0.0
    reg_off = Counter()
    reg_n = Counter()
    for p, v in soff.items():
        reg_off[region[p]] += v
        reg_n[region[p]] += 1
    lx, ly = -math.sqrt(0.5), math.sqrt(0.5)  # lumiere d'origine : haut-gauche (y haut)

    # volume d'ensemble : la silhouette floutee est une colline ; sa pente = bombe global
    # (le dos regarde vers le haut, le ventre vers le bas, le museau vers l'avant)
    mask = Image.new("L", (w + 2 * GPAD, h + 2 * GPAD), 0)
    for (x, y) in opq:
        mask.putpixel((x + GPAD, y + GPAD), 255)
    hill = mask.filter(ImageFilter.GaussianBlur(GBLUR)).load()
    grad = {}
    for (x, y) in opq:
        X, Y = x + GPAD, y + GPAD
        grad[(x, y)] = (-(hill[X + 1, Y] - hill[X - 1, Y]) / 2.0, (hill[X, Y + 1] - hill[X, Y - 1]) / 2.0)
    gmax = sorted(math.hypot(*v) for v in grad.values())[int(len(grad) * 0.97)] or 1.0

    # bombe de chaque partie : la partie (sans ses traits) floutee seule, meme principe a petite echelle
    pgrad = {}
    for r in set(region.values()):
        members = [p for p in region if region[p] == r]
        pm = Image.new("L", (w + 2 * GPAD, h + 2 * GPAD), 0)
        for (x, y) in members:
            pm.putpixel((x + GPAD, y + GPAD), 255)
        rad = max(1.2, min(3.0, dmax[r] * 0.6))
        ph = pm.filter(ImageFilter.GaussianBlur(rad)).load()
        vals = {}
        for (x, y) in members:
            X, Y = x + GPAD, y + GPAD
            vals[(x, y)] = (-(ph[X + 1, Y] - ph[X - 1, Y]) / 2.0, (ph[X, Y + 1] - ph[X, Y - 1]) / 2.0)
        pmx = max((math.hypot(*v) for v in vals.values()), default=1.0) or 1.0
        for q, v in vals.items():
            pgrad[q] = (v[0] / pmx, v[1] / pmx)

    codes = {}
    for p in body:
        r = region[p]
        gx, gy = grad[p]
        gm = min(1.0, math.hypot(gx, gy) / gmax)
        gn = math.hypot(gx, gy) or 1.0
        gk = W_GLOBAL * gm ** 0.8
        px_, py_ = pgrad[p]
        s = 0.6 * soff[p] + 0.5 * reg_off[r] / reg_n[r]
        s = max(-1.2, min(1.2, s))
        nx = gx / gn * gk + W_PART * px_ + W_SHADE * s * lx
        ny = gy / gn * gk + W_PART * py_ + W_SHADE * s * ly
        codes[p] = quantize(nx, ny)
    # contour exterieur : rasant, tourne vers l'exterieur ; traits interieurs : comme leurs voisins
    outline = set()
    for p in line_px:
        d, vx, vy = out_vec[p]
        if d <= 2.3:
            outline.add(p)
            codes[p] = quantize(vx / (math.hypot(vx, vy) or 1), -vy / (math.hypot(vx, vy) or 1))
    for p in protected_px:
        codes.setdefault(p, None)
    pending = [p for p in opq if codes.get(p) is None]
    for _ in range(6):
        if not pending:
            break
        rest = []
        for p in pending:
            x, y = p
            cnt = Counter(codes[q] for q in ((x + dx, y + dy) for dx, dy in N8)
                          if codes.get(q) is not None and q not in outline)
            if cnt:
                codes[p] = cnt.most_common(1)[0][0]
            else:
                rest.append(p)
        pending = [p for p in rest if codes.get(p) is None]
    for p in pending:
        codes[p] = 0
    regall = dict(region)
    for p in opq:
        if p not in regall:
            regall[p] = "o" if p in outline else "l"
    keep = outline
    codes = mode_filter(codes, regall, keep, iters=3)
    codes = merge_small(codes, 6, keep)

    # neutre : chaque pixel prend la couleur de base de sa rampe ; les grains isoles (1-2 px d'une
    # autre matiere, ex. eclat de verrue) prennent la matiere qui les entoure
    rid_of = {p: ramp_of[col[p]] for p in body if p not in protected_px}
    seen = set()
    for p in list(rid_of):
        if p in seen:
            continue
        comp, q = [p], deque([p])
        seen.add(p)
        while q:
            x, y = q.popleft()
            for dx, dy in N4:
                t = (x + dx, y + dy)
                if t in rid_of and t not in seen and rid_of[t] == rid_of[p]:
                    seen.add(t); comp.append(t); q.append(t)
        if len(comp) <= 2:
            cnt = Counter(rid_of[t] for (x, y) in comp for t in ((x + dx, y + dy) for dx, dy in N8)
                          if t in rid_of and t not in comp)
            if cnt and cnt.most_common(1)[0][0] != rid_of[p]:
                for t in comp:
                    rid_of[t] = cnt.most_common(1)[0][0]
    neutral = {}
    for p in opq:
        c = col[p]
        if p in line_px or p in protected_px:
            neutral[p] = c
        else:
            neutral[p] = base[rid_of[p]]
    info = {"ramps": [(hexc(base[i]), [hexc(c) for c in sorted(r, key=lambda c: L[c])]) for i, r in enumerate(ramps)],
            "lines": sorted(hexc(c) for c in dark), "protected": sorted({hexc(col[p]) for p in protected_px}),
            "parts": len(set(region.values())), "region": region, "line_px": line_px}
    return opq, neutral, codes, info


def save_maps(im, opq, neutral, codes, stem):
    w, h = im.size
    neu = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sec = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    nor = Image.new("RGBA", (w, h), (128, 128, 255, 0))
    a = im.load()
    for p in opq:
        neu.putpixel(p, neutral[p] + (255,))
        sec.putpixel(p, SECTIONS[codes[p]][1] + (255,))
        nor.putpixel(p, encode_normal(section_normal(codes[p])) + (255,))
    paths = {"neutre": stem + ".neutre.png", "sections": stem + ".sections.png", "normales": stem + ".normales.png"}
    if neutral:
        neu.save(paths["neutre"])
    else:
        paths.pop("neutre")
    sec.save(paths["sections"])
    nor.save(paths["normales"])
    return paths


def normals_from_sections(sec_path, stem):
    sec = Image.open(sec_path).convert("RGBA")
    w, h = sec.size
    s = sec.load()
    nor = Image.new("RGBA", (w, h), (128, 128, 255, 0))
    cache = {}
    for y in range(h):
        for x in range(w):
            if s[x, y][3] >= 128:
                c = s[x, y][:3]
                if c not in cache:
                    cache[c] = nearest_code(c)
                nor.putpixel((x, y), encode_normal(section_normal(cache[c])) + (255,))
    nor.save(stem + ".normales.png")
    return stem + ".normales.png", {SECTIONS[v][0] for v in cache.values()}


def light(neu, nor, ldir, steps=4, amb=0.45, inten=0.85):
    w, h = neu.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    a, b = neu.load(), nor.load()
    m = math.sqrt(sum(c * c for c in ldir))
    L = [c / m for c in ldir]
    for y in range(h):
        for x in range(w):
            if a[x, y][3] < 128:
                continue
            n = [c / 255 * 2 - 1 for c in b[x, y][:3]]
            d = max(0.0, sum(i * j for i, j in zip(n, L)))
            if steps:
                d = math.floor(d * (steps - 1) + 0.5) / (steps - 1)
            f = amb + inten * d
            out.putpixel((x, y), tuple(min(255, round(c * f)) for c in a[x, y][:3]) + (255,))
    return out


def apercu(stem, orig, z=4):
    neu = Image.open(stem + ".neutre.png").convert("RGBA") if os.path.exists(stem + ".neutre.png") else orig
    nor = Image.open(stem + ".normales.png").convert("RGBA")
    sec = Image.open(stem + ".sections.png").convert("RGBA")
    tiles = [orig, neu, sec, light(neu, nor, (-1, 0.5, 1.0)), light(neu, nor, (1, 0.5, 1.0))]
    w, h = orig.size
    pad = 4
    board = Image.new("RGBA", ((w * z + pad) * len(tiles) + pad, h * z + 2 * pad), (13, 11, 26, 255))
    for i, t in enumerate(tiles):
        big = t.resize((w * z, h * z), Image.NEAREST)
        board.alpha_composite(big, (pad + i * (w * z + pad), pad))
    board.save(stem + ".apercu.png")
    return stem + ".apercu.png"


def mirror(stem):
    out = []
    for name in ("neutre", "normales"):
        p = f"{stem}.{name}.png"
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
        if name == "normales":
            r, g, b, a = im.split()
            im = Image.merge("RGBA", (r.point(lambda v: 255 - v), g, b, a))
        q = f"{stem}.{name}-gauche.png"
        im.save(q)
        out.append(q)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sprite")
    ap.add_argument("--depuis-sections", default="", help="sections.png retouche -> recalcule les normales")
    ap.add_argument("--garder", default="", help="couleurs hex a garder telles quelles (details), ex. dea019,fdfdfd")
    ap.add_argument("--rampes", default="", help='forcer des rampes : "hex,hex;hex,hex"')
    ap.add_argument("--apercu", action="store_true")
    ap.add_argument("--gauche", action="store_true")
    a = ap.parse_args()
    stem = os.path.splitext(a.sprite)[0]
    im = Image.open(a.sprite).convert("RGBA")
    if a.depuis_sections:
        p, used = normals_from_sections(a.depuis_sections, stem)
        print(p)
        print("sections lues :", ", ".join(sorted(used)))
    else:
        opq, neutral, codes, info = analyse(im, [g for g in a.garder.split(",") if g.strip()],
                                            [r for r in a.rampes.split(";") if r.strip()])
        for p in save_maps(im, opq, neutral, codes, stem).values():
            print(p)
        print("rampes (couleur neutre <- couleurs) :")
        for b, r in info["ramps"]:
            print("  %s <- %s" % (b, " ".join(r)))
        print("lignes gardees :", " ".join(info["lines"]))
        print("details gardes :", " ".join(info["protected"]) or "-")
        print("parties :", info["parts"], "| zones :", Counter(SECTIONS[c][0] for c in codes.values()).most_common(6))
    if a.gauche:
        for p in mirror(stem):
            print(p)
    if a.apercu:
        print(apercu(stem, im))


if __name__ == "__main__":
    main()
