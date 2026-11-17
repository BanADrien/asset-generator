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
  python -I sections.py SPRITE.png --depuis-cj SPRITE.cj-apercu.png        (carte contre-jour retouchee)
  Toujours aussi : <nom>.cj.png (carte CONTRE-JOUR : R,G direction du bord expose, B exposition
  arriere) et <nom>.cj-apercu.png (teinte = direction, luminosite = exposition), voir carte_cj().
  --apercu : <nom>.apercu.png (origine | neutre | sections | eclaire gauche | eclaire droite, x4)
  --gauche : <nom>.neutre-gauche.png + <nom>.normales-gauche.png (sprite retourne pour regarder a
             gauche, rouge des normales inverse ; flipX de Phaser 3.80 ne corrige pas les normales)
  Animation (toutes les frames ensemble, sans clignotement) :
  python -I sections.py FRAME0.png FRAME1.png ... --animation [--echelle-jeu 0.24] --fps 12 --sortie W/marche
  -> W/marche_N.png + .neutre/.normales/.sections de chaque frame, W/marche.planche.png, W/marche.anim.json
  Sprite deja passe en pixel art par pixel-fixer (cas general du jeu, src/data/pixel_fixed.js) :
  python -I sections.py FRAME.png --facteur 3.76 --sortie W/nom   (aussi avec --animation)
  -> resolution native exacte (1 case de f px = 1 pixel), couleurs de l'image gardees.
  Image peinte (sprite HD du jeu, affiche reduit par setScale) :
  python -I sections.py FRAME_HD.png --echelle-jeu 0.4 [--couleurs 24] --sortie W/loup
  -> W/loup.png (taille reelle a l'ecran, alpha net, palette reduite) puis les memes sorties.
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
GBLUR_MIN, GBLUR_REL, GPAD = 4.0, 0.1, 12  # flou de la silhouette (bombe global) = max(4, 0,1 x petit cote) ; marge des parties
RAMP_SPAN = 48.0  # etendue max de luminosite (L*) d'une rampe
PART_DL, PART_MIN, PART_PART = 12.0, 20, 0.15  # 2 groupes de parties a >= 12 L* d'ecart, chacun >= 15 % de la rampe
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
    # etendue de luminosite de chaque rampe : une rampe de pixel art couvre ~3-5 valeurs ; au-dela
    # de RAMP_SPAN on relie deux matieres de meme teinte (peau claire et tunique beige, pantalon)
    span = {c: (labs[c][0], labs[c][0]) for c in colors}
    pairs = sorted(((v / math.sqrt(counts[p[0]] * counts[p[1]]), p) for p, v in adj.items()
                    if p[0] in pool and p[1] in pool), reverse=True)
    for s, (a, b) in pairs:
        if counts[a] < rare or counts[b] < rare:
            continue
        fa, fb = feat[a], feat[b]
        grey = fa[2] < 8 and fb[2] < 8
        if s > 0.06 and (grey or (hue_diff(fa[0], fb[0]) < 15 and abs(fa[1] - fb[1]) < 0.17)):
            ra, rb = find(a), find(b)
            if ra == rb:
                continue
            lo, hi = min(span[ra][0], span[rb][0]), max(span[ra][1], span[rb][1])
            if hi - lo > RAMP_SPAN:
                continue
            parent[ra] = rb
            span[rb] = (lo, hi)
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


# ---------------------------------------------------------------- echelle du sprite
# Reglages en pixels (zones, lissages, contour, carte contre-jour) penses pour les sprites de la demo
# (Agarica 67 x 94, loup, grizzly, crapaud : racine de la surface opaque 49 a 87 px). Un sprite plus
# grand (Kainati, ~250) les multiplie par s = max(1, racine(surface opaque) / 96), mediane sur les
# frames d'une animation, arrondie au centieme ; s = 1 : calcul strictement inchange. Meme calcul
# que tools/lumiere/coeur.js du jeu (echelleSprite, aL, aS ; arrondis de Math.round).
ECHELLE_REF = 96


def js_round(x):
    """Math.round de JavaScript (moitie vers le haut), et non round() de Python (moitie vers le pair)."""
    return math.floor(x + 0.5)


def echelle_sprite(ims):
    r = sorted(math.sqrt(sum(im.convert("RGBA").getchannel("A").histogram()[128:])) for im in ims)
    m = r[len(r) // 2] if r else 0
    return max(1, js_round((m / ECHELLE_REF) * 100) / 100)


def aL(v, s):
    """longueur (px) a l'echelle s ; s = 1 : valeur d'origine telle quelle"""
    return js_round(v * s) if s > 1 else v


def aS(v, s):
    """surface (px2) a l'echelle s"""
    return js_round(v * s * s) if s > 1 else v


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


def heriter_bord(codes, opq):
    """Le bord de la silhouette n'a pas d'orientation propre : chaque pixel qui touche le vide prend
    la section majoritaire des pixels INTERIEURS voisins (rayon 1, sinon 2, sinon 3) : le contour
    fait partie de la section qu'il borde (pas d'anneau rasant tourne vers l'exterieur, qui
    s'allumait en bande en contre-jour). Les parties trop fines (tout en bord) gardent la leur."""
    ring = {p for p in opq if any((p[0] + dx, p[1] + dy) not in opq for dx, dy in N8)}
    new = dict(codes)
    for p in ring:
        for r in (1, 2, 3):
            cnt = Counter(codes[q] for q in ((p[0] + dx, p[1] + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1))
                          if q in opq and q not in ring)
            if cnt:
                new[p] = cnt.most_common(1)[0][0]
                break
    return new


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
def neutre_detaille(neutral, w, h, ech, opq, line_px, protected_px, col, ramp_of, rid_of, ramps, L):
    """Grand sprite (s > 1) : le neutre en aplats effacait le dessin (meches, nuances). On ne retire que
    l'ombrage a GRANDE echelle : couleur de base de la matiere + ecart du pixel a la moyenne locale de
    sa matiere (luminance L*, fenetre de 2 s px de rayon), ramene a la couleur de la rampe la plus
    proche (palette du sprite). Puis chaque matiere claire est assombrie (meme rapport pour toutes ses
    couleurs) pour que sa couleur la plus claire reste sous 188 / 255 : x 1,36 (ambiance 0,36 + lampe 1)
    au palier max = blanc, les paliers en dessous restent distincts. Port exact de neutreDetaille()
    (coeur.js du jeu) : memes tables de sommes, meme ordre des operations."""
    rho = aL(2, ech)
    nR = len(ramps)
    W1 = w + 1

    def propre(p):
        return p not in line_px and p not in protected_px and p in rid_of and ramp_of.get(col[p]) == rid_of[p]

    pr = {p for p in opq if propre(p)}
    sl, sn = [], []
    for r in range(nR):
        tl = [0.0] * (W1 * (h + 1))
        tn = [0.0] * (W1 * (h + 1))
        for y in range(h):
            al = an = 0.0
            for x in range(w):
                p = (x, y)
                if p in pr and rid_of[p] == r:
                    al += L[col[p]]
                    an += 1
                tl[(y + 1) * W1 + x + 1] = tl[y * W1 + x + 1] + al
                tn[(y + 1) * W1 + x + 1] = tn[y * W1 + x + 1] + an
        sl.append(tl)
        sn.append(tn)

    def somme(t, x0, y0, x1, y1):
        return t[y1 * W1 + x1] - t[y0 * W1 + x1] - t[y1 * W1 + x0] + t[y0 * W1 + x0]

    out = dict(neutral)
    for p in pr:
        r = rid_of[p]
        x, y = p
        x0, y0, x1, y1 = max(0, x - rho), max(0, y - rho), min(w, x + rho + 1), min(h, y + rho + 1)
        n = somme(sn[r], x0, y0, x1, y1)
        if not n:
            continue
        cible = L[neutral[p]] + (L[col[p]] - somme(sl[r], x0, y0, x1, y1) / n)
        best, bv = neutral[p], math.inf
        for cc in ramps[r]:
            v = abs(L[cc] - cible)
            if v < bv:
                bv, best = v, cc
        out[p] = best
    PLAFOND = 188
    maxi = {}
    for p in opq:
        if p in line_px or p in protected_px or p not in rid_of:
            continue
        maxi[rid_of[p]] = max(maxi.get(rid_of[p], 0), max(out[p]))
    for p in opq:
        if p in line_px or p in protected_px or p not in rid_of:
            neutral[p] = out[p]
            continue
        k = min(1, PLAFOND / (maxi.get(rid_of[p]) or 255))
        c = out[p]
        neutral[p] = c if k >= 1 else tuple(round(v * k) for v in c)


def analyse(im, garder=(), rampes=(), peint=False, taille_ref=None, echelle=1):
    """taille_ref : taille d'UNE frame quand im est une mosaique de frames (mode animation) ;
    echelle : s du sprite (echelle_sprite), reglages en pixels multiplies (grand sprite)."""
    ech = echelle if echelle > 1 else 1
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
        # petites parties fondues dans leur voisine majoritaire, la plus petite d'abord (a taille
        # egale : la premiere apparue), une a la fois ; tailles et membres tenus a jour (meme resultat
        # que tout recompter apres chaque fusion, sans exploser sur un grand sprite)
        pos, taille, premier, membres = {}, Counter(), {}, {}
        for i, p in enumerate(region):
            pos[p] = i
            r = region[p]
            taille[r] += 1
            if r not in premier:
                premier[r] = i
                membres[r] = []
            membres[r].append(p)
        while True:
            petites = sorted(((r, sz, premier[r]) for r, sz in taille.items() if sz < minsize), key=lambda t: (t[1], t[2]))
            changed = False
            for r, _, _ in petites:
                members = sorted(membres[r], key=pos.get)
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
                    taille[nr] += taille.pop(r)
                    premier[nr] = min(premier[nr], premier.pop(r))
                    membres[nr].extend(membres.pop(r))
                    changed = True
                    break
            if not changed:
                return

    absorb(aS(12, ech))
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
    absorb(aS(12, ech))

    def border(X, Y, p_region):
        q = (X, Y)
        if q not in opq or q in line_px:
            return True
        return q in region and region[q] != p_region

    # vecteurs vers le bord de la partie (bombe) et vers le vide (contour exterieur)
    near = {}
    par_region = {}
    for p in region:
        par_region.setdefault(region[p], []).append(p)
    for r in set(region.values()):
        near.update(nearest_vectors(w, h, lambda X, Y, r=r: border(X, Y, r), par_region[r], R=aL(7, ech)))
    out_vec = nearest_vectors(w, h, lambda X, Y: (X, Y) not in opq, opq, R=aL(6, ech))
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
    rso = aL(2, ech)
    for p in body:
        x, y = p
        vals = [off[q] for q in ((x + dx, y + dy) for dx in range(-rso, rso + 1) for dy in range(-rso, rso + 1))
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
    gblur = max(GBLUR_MIN * ech, GBLUR_REL * min(taille_ref or (w, h)))
    gp = int(2.5 * gblur) + 2
    mask = Image.new("L", (w + 2 * gp, h + 2 * gp), 0)
    for (x, y) in opq:
        mask.putpixel((x + gp, y + gp), 255)
    hill = mask.filter(ImageFilter.GaussianBlur(gblur)).load()
    grad = {}
    for (x, y) in opq:
        X, Y = x + gp, y + gp
        grad[(x, y)] = (-(hill[X + 1, Y] - hill[X - 1, Y]) / 2.0, (hill[X, Y + 1] - hill[X, Y - 1]) / 2.0)
    gmax = sorted(math.hypot(*v) for v in grad.values())[int(len(grad) * 0.97)] or 1.0

    # bombe de chaque partie : la partie (sans ses traits) floutee seule, meme principe a petite echelle
    pgrad = {}
    gpad = aL(GPAD, ech)
    for r in set(region.values()):
        members = par_region[r]
        rad = max(1.2 * ech, min(3.0 * ech, dmax[r] * 0.6))
        # flou de la partie sur un rectangle autour d'elle (meme resultat que sur toute l'image tant
        # que la marge couvre son etalement ; coeur.js fait de meme)
        bx0, by0 = min(x for x, _ in members), min(y for _, y in members)
        bx1, by1 = max(x for x, _ in members), max(y for _, y in members)
        M = gpad + 3 * (math.ceil(rad) + 2)
        PW, PH = w + 2 * gpad, h + 2 * gpad
        CX0, CY0 = max(0, bx0 + gpad - M), max(0, by0 + gpad - M)
        CW, CH = min(PW - 1, bx1 + gpad + M) - CX0 + 1, min(PH - 1, by1 + gpad + M) - CY0 + 1
        pm = Image.new("L", (CW, CH), 0)
        for (x, y) in members:
            pm.putpixel((x + gpad - CX0, y + gpad - CY0), 255)
        ph = pm.filter(ImageFilter.GaussianBlur(rad)).load()
        vals = {}
        for (x, y) in members:
            X, Y = x + gpad - CX0, y + gpad - CY0
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
        sh = 0.6 * soff[p] + 0.5 * reg_off[r] / reg_n[r]
        sh = max(-1.2, min(1.2, sh))
        wp = W_PART * min(1.0, dmax[r] / (3.0 * ech))   # petite partie : bombe propre attenue (moins de bruit)
        ws = W_SHADE * (0.6 if peint else 1.0)  # image peinte : ombrage riche, on le suit moins
        nx = gx / gn * gk + wp * px_ + ws * sh * lx
        ny = gy / gn * gk + wp * py_ + ws * sh * ly
        codes[p] = quantize(nx, ny)
    # contour exterieur : rasant, tourne vers l'exterieur ; traits interieurs : comme leurs voisins
    outline = set()
    for p in line_px:
        d, vx, vy = out_vec[p]
        if d <= 2.3 * ech:
            outline.add(p)
            codes[p] = quantize(vx / (math.hypot(vx, vy) or 1), -vy / (math.hypot(vx, vy) or 1))
    for p in protected_px:
        codes.setdefault(p, None)
    pending = [p for p in opq if codes.get(p) is None]
    for _ in range(aL(6, ech)):
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
    codes = mode_filter(codes, regall, keep, iters=aL(5 if peint else 3, ech))
    codes = merge_small(codes, aS(10 if peint else 6, ech), keep)
    codes = heriter_bord(codes, opq)

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
        if len(comp) <= aS(2, ech):
            cnt = Counter(rid_of[t] for (x, y) in comp for t in ((x + dx, y + dy) for dx, dy in N8)
                          if t in rid_of and t not in comp)
            if cnt and cnt.most_common(1)[0][0] != rid_of[p]:
                for t in comp:
                    rid_of[t] = cnt.most_common(1)[0][0]
    # meme rampe, deux matieres : les couleurs d'une rampe peuvent servir a deux matieres de meme
    # teinte (peau claire et tunique beige d'Agarica). On classe les PARTIES de la rampe (fermees par
    # des traits) en deux groupes par leur luminosite moyenne (2-moyennes, sur toutes les frames
    # d'une animation a la fois : decision identique d'une frame a l'autre) ; si les deux groupes
    # sont nettement distincts et chacun assez gros, chaque groupe prend sa propre couleur neutre.
    part_base = {}
    acc = {}
    for p, r in rid_of.items():
        if ramp_of.get(col[p]) != r:   # grains absorbes d'une autre couleur : hors moyenne
            continue
        k = (region.get(p), r)
        a_ = acc.setdefault(k, [0.0, 0.0, 0.0, 0])
        l_ = lab(col[p])
        a_[0] += l_[0]; a_[1] += l_[1]; a_[2] += l_[2]; a_[3] += 1
    par_rampe = {}
    for (reg_, r), a_ in acc.items():
        par_rampe.setdefault(r, []).append((reg_, a_))
    for r, parts in par_rampe.items():
        big = [(reg_, a_) for reg_, a_ in parts if a_[3] >= aS(PART_MIN, ech)]
        if len(big) < 2:
            continue
        ls = [a_[0] / a_[3] for _, a_ in big]
        ws = [a_[3] for _, a_ in big]
        c1, c2 = min(ls), max(ls)
        for _ in range(20):
            g1 = [i for i, l_ in enumerate(ls) if abs(l_ - c1) <= abs(l_ - c2)]
            g2 = [i for i in range(len(ls)) if i not in g1]
            if not g1 or not g2:
                break
            c1 = sum(ls[i] * ws[i] for i in g1) / sum(ws[i] for i in g1)
            c2 = sum(ls[i] * ws[i] for i in g2) / sum(ws[i] for i in g2)
        tot_w = sum(a_[3] for _, a_ in parts)
        if not g1 or not g2 or abs(c2 - c1) < PART_DL or \
                min(sum(ws[i] for i in g1), sum(ws[i] for i in g2)) < PART_PART * tot_w:
            continue
        for g in (g1, g2):
            sw = sum(big[i][1][3] for i in g)
            m = tuple(sum(big[i][1][k] for i in g) / sw for k in range(3))
            cb = min(ramps[r], key=lambda c: math.dist(lab(c), m))
            for i in g:
                part_base[(big[i][0], r)] = cb
    neutral = {}
    for p in opq:
        c = col[p]
        if p in line_px or p in protected_px:
            neutral[p] = c
        else:
            neutral[p] = part_base.get((region.get(p), rid_of[p]), base[rid_of[p]])
    if ech > 1:
        neutre_detaille(neutral, w, h, ech, opq, line_px, protected_px, col, ramp_of, rid_of, ramps, L)
    info = {"ramps": [(hexc(base[i]), [hexc(c) for c in sorted(r, key=lambda c: L[c])]) for i, r in enumerate(ramps)],
            "lines": sorted(hexc(c) for c in dark), "protected": sorted({hexc(col[p]) for p in protected_px}),
            "parts": len(set(region.values())), "region": region, "line_px": line_px, "outline": outline, "part_base": part_base}
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


def _kmeans(items, k, iters=12):
    """k-moyennes ponderees en Lab. items = [(lab, poids, rgb)] ; init deterministe (k-means++ glouton)."""
    if len(items) <= k:
        return [it[0] for it in items]
    cents = [max(items, key=lambda it: it[1])[0]]
    dist = [math.dist(it[0], cents[0]) ** 2 * it[1] for it in items]
    while len(cents) < k:
        i = max(range(len(items)), key=lambda j: dist[j])
        cents.append(items[i][0])
        dist = [min(d, math.dist(it[0], cents[-1]) ** 2 * it[1]) for d, it in zip(dist, items)]
    for _ in range(iters):
        acc = [[0.0, 0.0, 0.0, 0.0] for _ in cents]
        for l, wgt, _ in items:
            j = min(range(len(cents)), key=lambda c: math.dist(l, cents[c]))
            a = acc[j]
            a[0] += l[0] * wgt; a[1] += l[1] * wgt; a[2] += l[2] * wgt; a[3] += wgt
        cents = [(a[0] / a[3], a[1] / a[3], a[2] / a[3]) if a[3] else c for a, c in zip(acc, cents)]
    return cents


def palette_lab(rgbs, ncol):
    """Palette propre de l'image en Lab (separe mieux peau / tissu clair que le median cut RGB) ;
    les couleurs rares mais tres differentes (oeil vert, reflet) recoivent leurs propres teintes.
    Renvoie {rgb d'origine -> rgb de palette}, la teinte de palette etant la moyenne RGB du groupe."""
    cnt = Counter(rgbs)
    # pre-regroupement par cases de 4 niveaux (accelere les k-moyennes)
    bins = {}
    for c, v in cnt.items():
        key = (c[0] >> 2, c[1] >> 2, c[2] >> 2)
        b = bins.setdefault(key, [0, 0, 0, 0])
        b[0] += c[0] * v; b[1] += c[1] * v; b[2] += c[2] * v; b[3] += v
    items = []
    for b in bins.values():
        rgb = (round(b[0] / b[3]), round(b[1] / b[3]), round(b[2] / b[3]))
        items.append((lab(rgb), b[3], rgb))
    cents = _kmeans(items, ncol)
    near = lambda l: min(cents, key=lambda c: math.dist(l, c))
    out = [it for it in items if math.dist(it[0], near(it[0])) > 16]
    if out:
        cents += _kmeans(out, min(4, len(out)))
    # couleur finale de chaque groupe : moyenne RGB ponderee de ses membres
    groups = {}
    for l, wgt, rgb in items:
        j = min(range(len(cents)), key=lambda c: math.dist(l, cents[c]))
        g = groups.setdefault(j, [0, 0, 0, 0])
        g[0] += rgb[0] * wgt; g[1] += rgb[1] * wgt; g[2] += rgb[2] * wgt; g[3] += wgt
    col = {j: (round(g[0] / g[3]), round(g[1] / g[3]), round(g[2] / g[3])) for j, g in groups.items()}
    remap = {}
    for c in cnt:
        l = lab(c)
        j = min(col, key=lambda k: math.dist(l, cents[k]))
        remap[c] = col[j]
    return remap


def peint_vers_jeu(im, echelle, ncol=32):
    """Mode « image peinte » : sprite HD (milliers de couleurs, bords semi-transparents) ramene a sa
    taille d'affichage dans le jeu (setScale), alpha net, palette reduite sans tramage. Le resultat
    est un sprite natif (1 px = 1 px a l'ecran du jeu) que le reste de la chaine traite comme le
    crapaud pixel art."""
    bb = im.getchannel("A").point(lambda v: 255 if v >= 24 else 0).getbbox()
    if bb:
        im = im.crop(bb)
    w, h = max(1, round(im.width * echelle)), max(1, round(im.height * echelle))
    small = im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")
    px = small.load()
    opq = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] >= 128]
    remap = palette_lab([px[p][:3] for p in opq], ncol)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for p in opq:
        out.putpixel(p, remap[px[p][:3]] + (255,))
    return out.crop(out.getchannel("A").getbbox())


# ---------------------------------------------------------------- geometrie (contre-jour)
GEO_PAD = 10       # marge autour du sprite dans la texture de geometrie (distance de la lampe a la silhouette)
GEO_TROU_MIN = 12  # trou transparent enferme : exterieur seulement a partir de 12 px


def geometrie(im, pad=GEO_PAD, trou_min=GEO_TROU_MIN):
    """Texture de geometrie pour le contre-jour de la page de test, taille (w + 2 pad, h + 2 pad) :
    R = profondeur depuis le bord EXTERIEUR (1 = pixel le plus exterieur), G = epaisseur locale,
    B = distance au sprite pour les pixels du fond (halo) ; valeurs x 16, plafond 15.
    Bord exterieur reel : silhouette fermee d'1 px (les fentes de 1-2 px entre visage et cheveux,
    bras et corps, cape et corps ne sont pas du fond), puis remplissage depuis le bord de l'image ;
    trous enfermes < trou_min px et pixels semi-transparents isoles = interieur."""
    from PIL import ImageFilter
    w, h = im.size
    W, H = w + 2 * pad, h + 2 * pad
    m = Image.new("L", (W, H), 0)
    a = im.getchannel("A")
    m.paste(a.point(lambda v: 255 if v >= 128 else 0), (pad, pad))
    closed = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    cm, om = closed.load(), m.load()
    ext = [[False] * H for _ in range(W)]
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if cm[x, y] == 0 and not ext[x][y]:
                ext[x][y] = True; q.append((x, y))
    for y in range(H):
        for x in (0, W - 1):
            if cm[x, y] == 0 and not ext[x][y]:
                ext[x][y] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in N4:
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and not ext[X][Y] and cm[X, Y] == 0:
                ext[X][Y] = True; q.append((X, Y))
    # grands trous enfermes (vrais espaces) : exterieur aussi
    seen = set()
    for y in range(H):
        for x in range(W):
            if om[x, y] == 0 and not ext[x][y] and (x, y) not in seen and cm[x, y] == 0:
                comp, qq = [(x, y)], deque([(x, y)])
                seen.add((x, y))
                while qq:
                    cx, cy = qq.popleft()
                    for dx, dy in N4:
                        X, Y = cx + dx, cy + dy
                        if 0 <= X < W and 0 <= Y < H and (X, Y) not in seen and cm[X, Y] == 0 and not ext[X][Y]:
                            seen.add((X, Y)); comp.append((X, Y)); qq.append((X, Y))
                if len(comp) >= trou_min:
                    for c in comp:
                        ext[c[0]][c[1]] = True
    # profondeur depuis l'exterieur (8-voisins) pour tout ce qui n'est pas exterieur
    INF = 99
    D = [[0 if ext[x][y] else INF for y in range(H)] for x in range(W)]
    q = deque((x, y) for x in range(W) for y in range(H) if ext[x][y])
    while q:
        x, y = q.popleft()
        for dx, dy in N8:
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and D[X][Y] > D[x][y] + 1:
                D[X][Y] = D[x][y] + 1; q.append((X, Y))
    # distance au sprite pour le fond exterieur (halo)
    O = [[INF if ext[x][y] else 0 for y in range(H)] for x in range(W)]
    q = deque((x, y) for x in range(W) for y in range(H) if not ext[x][y])
    while q:
        x, y = q.popleft()
        for dx, dy in N8:
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and O[X][Y] > O[x][y] + 1:
                O[X][Y] = O[x][y] + 1; q.append((X, Y))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    px = out.load()
    for y in range(H):
        for x in range(W):
            d = D[x][y] if om[x, y] else 0
            th = 0
            if om[x, y]:
                mx = max(D[X][Y] for X in range(max(0, x - 1), min(W, x + 2)) for Y in range(max(0, y - 1), min(H, y + 2))
                         if om[X, Y])
                th = 2 * mx - 1
            px[x, y] = (min(d, 15) * 16, min(th, 15) * 16, min(O[x][y], 15) * 16, 255)
    return out


# ---------------------------------------------------------------- carte contre-jour <nom>.cj.png (v16)
# Les normales de face ne savent pas ce qui est expose par l'arriere : une carte DEDIEE le dit.
# Format (RGBA, taille du sprite) :
#   R, G = direction 2D du bord expose, d'ou la lumiere de derriere peut arriver (x droite, y HAUT,
#          encodage des normales : v = (c / 255) x 2 - 1 ; 128 = pas de direction)
#   B    = exposition arriere 0-255 (0 = jamais atteint par une lampe derriere)
#   A    = 255 sur le sprite, 0 ailleurs
# Apercu retouchable <nom>.cj-apercu.png : teinte = direction (0 deg = droite, 90 = haut, sens
# trigonometrique, comme la roue des sections), luminosite = exposition (noir = rien) ;
# --depuis-cj APERCU.png le relit (HSV inverse) et reecrit <nom>.cj.png.
CJ_PORTEE = 12.0   # px : longueur maximale de la decroissance, mesuree DANS la section
CJ_SOMBRE = 0.16   # luminance du neutre sous laquelle un pixel est un trait sombre (comme le shader)
CJ_CONTOUR = 2     # un trait sombre a <= 2 px du vide est le contour exterieur (laisse passer)
CJ_FRANGE = 2      # adoucissement : 2 px dans la section voisine (x 0,5 par px), jamais a travers un trait
CJ_LISSE = 2       # direction lissee sur (2 x 2 + 1)^2 pixels de la meme zone


def carte_cj(im, normales, neutre, pad=GEO_PAD, echelle=1):
    """Carte contre-jour (format ci-dessus), calculee depuis la silhouette, les sections et les traits.
    Exposition : sources = pixels qui touchent l'exterieur (profondeur 1 de geometrie()) ;
    distance geodesique d (8 voisins, 1 / 1,41) SEULEMENT entre pixels de la meme section ; les
    traits sombres interieurs sont des murs. expo = (1 - smoothstep(0, L, d)) x pente, avec
    L = min(profondeur max de la zone + 1, 12 px) (chaque zone s'estompe sur sa propre largeur : pas
    d'anneau d'epaisseur constante) et pente = |n.xy| / 0,93 de la section (rasante 1, inclinee 0,69,
    face 0 : meme etagement que la lampe de face a +49). Une section qui ne touche jamais l'exterieur
    reste a 0, sauf une frange d'adoucissement de 2 px (x 0,5 par px, face comprise) le long d'une
    zone exposee : le plan au maximum n'a jamais l'ambiance pour voisin direct.
    Direction : normale exterieure de la silhouette au pixel source le plus proche, heritee le long de
    la propagation puis lissee sur 5 x 5 pixels de la meme zone."""
    import heapq
    ech = echelle if echelle > 1 else 1
    # grand sprite : contour 2 s, frange 2 s passes a 0,5^(1/s) (meme attenuation totale), direction
    # lissee 2 s, decroissance jusqu'a 12 s px
    contour, frange, lisse, portee = CJ_CONTOUR * ech, aL(CJ_FRANGE, ech), aL(CJ_LISSE, ech), CJ_PORTEE * ech
    demi = 0.5 ** (1 / ech) if ech > 1 else 0.5
    w, h = im.size
    g = geometrie(im, pad).load()
    nm, ne = normales.convert("RGBA").load(), neutre.convert("RGBA").load()
    opq = [(x, y) for y in range(h) for x in range(w) if nm[x, y][3] >= 128]
    S = set(opq)
    D = {p: g[p[0] + pad, p[1] + pad][0] // 16 for p in opq}
    sec = {p: nm[p][:3] for p in opq}
    pente = {}
    for p in opq:
        v = math.hypot(nm[p][0] / 255 * 2 - 1, nm[p][1] / 255 * 2 - 1) / 0.93
        pente[p] = 0.0 if v < 0.05 else min(1.0, v)
    lum = {p: (0.3 * ne[p][0] + 0.59 * ne[p][1] + 0.11 * ne[p][2]) / 255 for p in opq}
    passe = {p: lum[p] >= CJ_SOMBRE or D[p] <= contour for p in opq}
    # normale exterieure aux sources (somme des directions vers le vide ; y vers le HAUT)
    src = {}
    for p in opq:
        if D[p] == 1 and passe[p]:
            vx = vy = 0.0
            for dx, dy in N8:
                if (p[0] + dx, p[1] + dy) not in S:
                    k = 0.7071 if dx and dy else 1.0
                    vx += dx * k
                    vy -= dy * k
            m = math.hypot(vx, vy)
            src[p] = (vx / m, vy / m) if m > 1e-6 else (0.0, 0.0)
    dist, vdir = {}, {}
    tas = [(0.0, p, p) for p in src]
    heapq.heapify(tas)
    while tas:
        d, p, s0 = heapq.heappop(tas)
        if p in dist:
            continue
        dist[p], vdir[p] = d, src[s0]
        for dx, dy in N8:
            q = (p[0] + dx, p[1] + dy)
            if q in S and q not in dist and passe[q] and sec[q] == sec[p]:
                heapq.heappush(tas, (d + (1.4142 if dx and dy else 1.0), q, s0))
    zone, prof = {}, []
    for p in dist:
        if p in zone:
            continue
        k, pile, dm = len(prof), [p], 0.0
        zone[p] = k
        while pile:
            c = pile.pop()
            dm = max(dm, dist[c])
            for dx, dy in N8:
                q = (c[0] + dx, c[1] + dy)
                if q in dist and q not in zone and sec[q] == sec[c]:
                    zone[q] = k
                    pile.append(q)
        prof.append(dm)
    ex, dl = {}, {}
    for p, d in dist.items():
        L = min(prof[zone[p]] + 1.0, portee)
        t = min(1.0, d / L)
        ex[p] = (1.0 - t * t * (3 - 2 * t)) * pente[p]
        ax = ay = 0.0
        for a in range(-lisse, lisse + 1):
            for b in range(-lisse, lisse + 1):
                q = (p[0] + a, p[1] + b)
                if zone.get(q) == zone[p]:
                    ax += vdir[q][0]
                    ay += vdir[q][1]
        m = math.hypot(ax, ay)
        dl[p] = (ax / m, ay / m) if m > 1e-6 else vdir[p]
    # frange d'adoucissement : chaque pixel recoit au moins la moitie de son voisin le plus expose
    # (2 passes : x 0,5 puis x 0,25), y compris dans une autre section ou une zone exposee ailleurs,
    # jamais a travers un trait
    for _ in range(frange):
        ajout = {}
        for p in opq:
            if not passe[p]:
                continue
            best, bd = 0.0, (0.0, 0.0)
            for dx, dy in N8:
                q = (p[0] + dx, p[1] + dy)
                if q in ex and passe[q] and ex[q] > best:
                    best, bd = ex[q], dl[q]
            if demi * best > ex.get(p, 0.0):
                ajout[p] = (demi * best, bd if p not in dl else dl[p])
        for p, (v, d_) in ajout.items():
            ex[p], dl[p] = v, d_
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = out.load()
    for p in opq:
        e = ex.get(p, 0.0)
        vx, vy = dl[p] if e > 0 else (0.0, 0.0)
        px[p] = (round((vx * 0.5 + 0.5) * 255), round((vy * 0.5 + 0.5) * 255), round(255 * e), 255)
    return out


def cj_apercu(cj):
    """Apercu colore retouchable : teinte = direction, luminosite = exposition, fond transparent."""
    import colorsys
    w, h = cj.size
    s = cj.convert("RGBA").load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = s[x, y]
            if a < 128:
                continue
            ang = math.degrees(math.atan2(g / 255 * 2 - 1, r / 255 * 2 - 1)) % 360
            rr, gg, bb = colorsys.hsv_to_rgb(ang / 360, 1.0, b / 255)
            o[x, y] = (round(rr * 255), round(gg * 255), round(bb * 255), 255)
    return out


def cj_depuis_apercu(ap):
    """Inverse de cj_apercu : apercu retouche a la main -> carte cj (gris ou noir = pas d'exposition)."""
    import colorsys
    w, h = ap.size
    s = ap.convert("RGBA").load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = s[x, y]
            if a < 128:
                continue
            hh, ss_, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if ss_ < 0.2:
                o[x, y] = (128, 128, 0, 255)
                continue
            ang = math.radians(hh * 360)
            o[x, y] = (round((math.cos(ang) * 0.5 + 0.5) * 255), round((math.sin(ang) * 0.5 + 0.5) * 255),
                       round(255 * vv), 255)
    return out


def ecrire_cj(stem, depuis="", im=None, echelle=None):
    """<stem>.cj.png + <stem>.cj-apercu.png, depuis le sprite (im, sinon <stem>.png), .normales.png et
    .neutre.png, ou depuis un apercu retouche (depuis = chemin de l'apercu)."""
    if depuis:
        cj = cj_depuis_apercu(Image.open(depuis))
    else:
        im = (im or Image.open(stem + ".png")).convert("RGBA")
        neu = stem + ".neutre.png"
        cj = carte_cj(im, Image.open(stem + ".normales.png"), Image.open(neu) if os.path.exists(neu) else im,
                      echelle=echelle_sprite([im]) if echelle is None else echelle)
    cj.save(stem + ".cj.png")
    if not depuis:
        cj_apercu(cj).save(stem + ".cj-apercu.png")
    return [stem + ".cj.png"] + ([] if depuis else [stem + ".cj-apercu.png"])


# ---------------------------------------------------------------- facteur pixel-fixer
def phase_grille(im, f, pas=0.5):
    """Calage de la grille de f px (pixel-fixer) : decalage (px, py) pour lequel chaque case est
    la plus uniforme (le centre et les points a +-0,3 f ont la meme couleur)."""
    px = im.load()
    w, h = im.size
    d = max(1, int(0.3 * f))
    best, bv = (0.0, 0.0), -1
    steps = [i * pas for i in range(int(f / pas) + 1) if i * pas < f]
    for ox in steps:
        for oy in steps:
            v = 0
            y = oy + f / 2
            while y < h - d:
                x = ox + f / 2
                while x < w - d:
                    cx, cy = int(x), int(y)
                    c = px[cx, cy]
                    if c[3] >= 128:
                        v += (px[cx - d, cy] == c) + (px[cx + d, cy] == c) + (px[cx, cy - d] == c) + (px[cx, cy + d] == c)
                    x += f
                y += f
            if v > bv:
                best, bv = (ox, oy), v
    return best


def echantillonner(im, f, phase=None):
    """Sprite deja en pixel art agrandi (pixel-fixer, src/data/pixel_fixed.js : 1 pixel dessine =
    f px de l'image) -> resolution NATIVE exacte : 1 case de f px = 1 pixel, couleur du centre de
    la case. Pas de reduction, pas de nouvelle palette : les couleurs de l'image sont gardees."""
    ox, oy = phase if phase is not None else phase_grille(im, f)
    w, h = im.size
    n_w = int((w - ox) // f)
    n_h = int((h - oy) // f)
    src = im.load()
    out = Image.new("RGBA", (n_w, n_h), (0, 0, 0, 0))
    for j in range(n_h):
        for i in range(n_w):
            c = src[min(w - 1, int(ox + (i + 0.5) * f)), min(h - 1, int(oy + (j + 0.5) * f))]
            if c[3] >= 128:
                out.putpixel((i, j), c[:3] + (255,))
    return out


# ---------------------------------------------------------------- animation
def meilleur_decalage(ca, cb, r=3, pas=1):
    """Decalage (dx, dy) qui superpose le mieux la frame b sur la frame a (memes couleurs).
    pas > 1 (grand sprite) : un pixel sur pas compte."""
    best, bv = (0, 0), -1
    items = list(ca.items())
    if pas > 1:
        items = items[::pas]
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            v = sum(1 for (x, y), c in items if cb.get((x + dx, y + dy)) == c)
            if v > bv:
                best, bv = (dx, dy), v
    return best


def lisser_temps(codes, cols, keep, echelle=1):
    """Anti-clignotement : un pixel qui garde la meme matiere d'une frame a l'autre (apres recalage
    du corps entier, qui monte et descend en marchant) ne bouge pas vraiment ; il prend la direction
    majoritaire sur sa frame et ses deux voisines (boucle). Renvoie (codes lisses, taux avant, apres)."""
    n = len(codes)
    shifts = {}
    for i in range(n):
        for j in ((i - 1) % n, (i + 1) % n):
            if (i, j) not in shifts:
                shifts[(i, j)] = meilleur_decalage(cols[i], cols[j], aL(3, echelle), aS(1, echelle))

    def taux(cds):
        diff = tot = 0
        for i in range(n):
            j = (i + 1) % n
            dx, dy = shifts[(i, j)]
            for p, c in cols[i].items():
                q = (p[0] + dx, p[1] + dy)
                if p in keep[i] or cols[j].get(q) != c:
                    continue
                tot += 1
                diff += cds[i][p] != cds[j][q]
        return diff / max(1, tot)

    avant = taux(codes)
    out = []
    for i in range(n):
        new = dict(codes[i])
        for p, c in cols[i].items():
            if p in keep[i]:
                continue
            votes = Counter({codes[i][p]: 1.0})
            for j in ((i - 1) % n, (i + 1) % n):
                dx, dy = shifts[(i, j)]
                # position recalee, et ses 8 voisines a demi-poids (un bord de zone qui tremble d'1 px)
                for ox, oy in ((0, 0),) + N8:
                    q = (p[0] + dx + ox, p[1] + dy + oy)
                    if cols[j].get(q) == c:
                        votes[codes[j][q]] += 1.0 if (ox, oy) == (0, 0) else 0.25
            best, v = votes.most_common(1)[0]
            if v >= 2.0:
                new[p] = best
        out.append(merge_small(new, aS(4, echelle), keep[i]))
    return out, avant, taux(out)


def animation(paths, stem, echelle=0.0, ncol=32, fps=12, vitesse=0, garder=(), rampes=(), facteur=0.0):
    """Toutes les frames d'une animation traitees ENSEMBLE : meme toile calee en bas au centre
    (origine (0.5, 1) de Phaser : pieds au meme niveau), meme cadrage, meme reduction, meme palette,
    memes matieres (analyse d'une mosaique des frames), puis lissage dans le temps."""
    import json
    frames = [Image.open(p).convert("RGBA") for p in paths]
    W, H = max(f.width for f in frames), max(f.height for f in frames)
    canv = []
    for f in frames:
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.paste(f, ((W - f.width) // 2, H - f.height))
        canv.append(c)
    if facteur > 0:
        # une seule grille (calee sur la 1re frame) pour toutes : meme decoupe, frames superposables
        ph = phase_grille(canv[0], facteur)
        canv = [echantillonner(c, facteur, ph) for c in canv]
        echelle = 0.0
    boxes = [c.getchannel("A").point(lambda v: 255 if v >= 24 else 0).getbbox() for c in canv]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    canv = [c.crop(box) for c in canv]
    if echelle > 0:
        w, h = max(1, round(canv[0].width * echelle)), max(1, round(canv[0].height * echelle))
        small = [c.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA") for c in canv]
        allc = []
        for im in small:
            px = im.load()
            allc += [px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3] >= 128]
        remap = palette_lab(allc, ncol)   # UNE palette pour toutes les frames
        canv = []
        for im in small:
            o = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            px = im.load()
            for y in range(h):
                for x in range(w):
                    if px[x, y][3] >= 128:
                        o.putpixel((x, y), remap[px[x, y][:3]] + (255,))
            canv.append(o)
    w, h = canv[0].size
    gap = 24
    mosa = Image.new("RGBA", (len(canv) * (w + gap) - gap, h), (0, 0, 0, 0))
    for i, c in enumerate(canv):
        mosa.paste(c, (i * (w + gap), 0))
    ech = echelle_sprite(canv)   # mediane des frames ; grand sprite : reglages en pixels x ech
    opq, neutral, codes, info = analyse(mosa, garder, rampes, peint=echelle > 0, taille_ref=(w, h), echelle=ech)
    mpx = mosa.load()
    fc, fn, fcol, fkeep = [], [], [], []
    for i in range(len(canv)):
        x0 = i * (w + gap)
        sel = [p for p in opq if x0 <= p[0] < x0 + w]
        fc.append({(x - x0, y): codes[(x, y)] for x, y in sel})
        fn.append({(x - x0, y): neutral[(x, y)] for x, y in sel})
        fcol.append({(x - x0, y): mpx[x, y][:3] for x, y in sel})
        fkeep.append({(x - x0, y) for x, y in sel if (x, y) in info["outline"]})
    # matiere de chaque pixel (rampe ; lignes et details : leur couleur) : on compare les matieres,
    # pas les couleurs exactes, l'ombrage peint variant un peu d'une frame a l'autre
    mat = {parse_hex(c): k for k, (_, cs) in enumerate(info["ramps"]) for c in cs}
    fmat = [{p: mat.get(c, c) for p, c in fr.items()} for fr in fcol]
    fc, avant, apres = lisser_temps(fc, fmat, fkeep, ech)
    for _ in range(3):
        fc, _, apres = lisser_temps(fc, fmat, fkeep, ech)
    fc = [heriter_bord(c, set(c)) for c in fc]
    names = []
    for i, c in enumerate(canv):
        fs = f"{stem}_{i}"
        c.save(fs + ".png")
        save_maps(c, set(fc[i]), fn[i], fc[i], fs)
        ecrire_cj(fs, echelle=ech)
        names.append(os.path.basename(fs) + ".png")
    man = {"nom": os.path.basename(stem), "fps": fps, "vitesse": vitesse, "frames": names}
    if ech > 1:
        man["s"] = ech
    with open(stem + ".anim.json", "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    planche_anim(stem, len(canv))
    return info, avant, apres, (w, h)


def planche_anim(stem, n, z=4):
    """Planche : une colonne par frame ; lignes origine, neutre, sections, eclaire gauche, eclaire droite."""
    rows = []
    for i in range(n):
        fs = f"{stem}_{i}"
        o = Image.open(fs + ".png").convert("RGBA")
        ne = Image.open(fs + ".neutre.png").convert("RGBA")
        no = Image.open(fs + ".normales.png").convert("RGBA")
        se = Image.open(fs + ".sections.png").convert("RGBA")
        rows.append([o, ne, se, light(ne, no, (-1, 0.5, 1.0)), light(ne, no, (1, 0.5, 1.0))])
    w, h = rows[0][0].size
    pad = 4
    b = Image.new("RGBA", (n * (w * z + pad) + pad, 5 * (h * z + pad) + pad), (13, 11, 26, 255))
    for i, col in enumerate(rows):
        for r, t in enumerate(col):
            b.alpha_composite(t.resize((w * z, h * z), Image.NEAREST),
                              (pad + i * (w * z + pad), pad + r * (h * z + pad)))
    b.save(stem + ".planche.png")
    return stem + ".planche.png"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sprite", nargs="+", help="un sprite ; ou, avec --animation, les frames (ou un dossier)")
    ap.add_argument("--animation", action="store_true", help="frames traitees ensemble (voir animation())")
    ap.add_argument("--fps", type=int, default=12, help="animation : frameRate du jeu (anims.create)")
    ap.add_argument("--vitesse", type=int, default=0, help="animation : vitesse de deplacement en jeu (px/s)")
    ap.add_argument("--depuis-sections", default="", help="sections.png retouche -> recalcule les normales")
    ap.add_argument("--depuis-cj", default="", help="cj-apercu.png retouche -> reecrit la carte contre-jour .cj.png")
    ap.add_argument("--garder", default="", help="couleurs hex a garder telles quelles (details), ex. dea019,fdfdfd")
    ap.add_argument("--rampes", default="", help='forcer des rampes : "hex,hex;hex,hex"')
    ap.add_argument("--apercu", action="store_true")
    ap.add_argument("--gauche", action="store_true")
    ap.add_argument("--echelle-jeu", type=float, default=0.0,
                    help="mode image peinte : echelle d'affichage dans le jeu (setScale, ex. 0.4) ; "
                         "le sprite HD est d'abord ramene a cette taille")
    ap.add_argument("--couleurs", type=int, default=32, help="mode image peinte : nombre de couleurs")
    ap.add_argument("--facteur", type=float, default=0.0,
                    help="sprite deja passe en pixel art par pixel-fixer : f de src/data/pixel_fixed.js "
                         "(px de l'image par pixel dessine) ; on revient a la resolution native exacte")
    ap.add_argument("--sortie", default="", help="chemin de base des sorties (defaut : celui du sprite)")
    a = ap.parse_args()
    garder = [g for g in a.garder.split(",") if g.strip()]
    rampes = [r for r in a.rampes.split(";") if r.strip()]
    if a.animation:
        paths = []
        for s_ in a.sprite:
            if os.path.isdir(s_):
                paths += sorted(os.path.join(s_, f) for f in os.listdir(s_) if f.lower().endswith(".png"))
            else:
                paths.append(s_)
        stem = os.path.splitext(a.sortie or paths[0])[0]
        info, avant, apres, taille = animation(paths, stem, a.echelle_jeu, a.couleurs, a.fps, a.vitesse,
                                               garder, rampes, a.facteur)
        print("%d frames %d x %d -> %s_N.png (+ .neutre .normales .sections), %s.planche.png, %s.anim.json"
              % (len(paths), taille[0], taille[1], stem, stem, stem))
        print("rampes communes :", " | ".join("%s <- %s" % (b, " ".join(r)) for b, r in info["ramps"]))
        print("orientation qui change sans que la matiere change (frame suivante) : %.1f %% -> %.1f %% apres lissage"
              % (100 * avant, 100 * apres))
        return
    a.sprite = a.sprite[0]
    stem = os.path.splitext(a.sortie or a.sprite)[0]
    im = Image.open(a.sprite).convert("RGBA")
    if a.facteur > 0:
        im = echantillonner(im, a.facteur)
        im = im.crop(im.getchannel("A").getbbox())
        im.save(stem + ".png")
        print(stem + ".png", "(natif %d x %d, %d couleurs)" % (im.width, im.height, len(im.getcolors(1 << 16))))
    elif a.echelle_jeu > 0:
        im = peint_vers_jeu(im, a.echelle_jeu, a.couleurs)
        im.save(stem + ".png")
        print(stem + ".png", "(%d x %d, %d couleurs)" % (im.width, im.height, len(im.getcolors(1 << 16))))
    if a.depuis_cj:
        for p in ecrire_cj(stem, a.depuis_cj):
            print(p)
        return
    if a.depuis_sections:
        p, used = normals_from_sections(a.depuis_sections, stem)
        print(p)
        print("sections lues :", ", ".join(sorted(used)))
        for p in ecrire_cj(stem, im=im):
            print(p)
    else:
        ech = echelle_sprite([im])
        if ech > 1:
            print("grand sprite : reglages en pixels x %g" % ech)
        opq, neutral, codes, info = analyse(im, garder, rampes, peint=a.echelle_jeu > 0, echelle=ech)
        for p in save_maps(im, opq, neutral, codes, stem).values():
            print(p)
        for p in ecrire_cj(stem, im=im):
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
