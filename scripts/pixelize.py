"""Image HD -> sprite pixel art propre a la taille du jeu.

Etapes : 1) detourage (fond uni par remplissage depuis les bords, logo Pollinations masque,
petits morceaux retires, recadrage) ; 2) pixelisation par pixel-fixer (outil de l'utilisateur,
node) avec la palette du jeu, sinon repli interne Pillow ; 3) nettoyage : alpha 0/255,
palette exacte, pixels isoles retires, trous de 1 px bouches, contour sombre ferme.

Usage :
  python -I pixelize.py IN.png OUT.png --height 24 [--width 32] [--detail 3]
      [--outline selective|darkest|none] [--bg-tol 40] [--mask-logo] [--palette P.hex]
      [--method cells|pixel-fixer] [--pixel-fixer CHEMIN/cli.js] [--no-pixel-fixer] [--flip]
Ecrit OUT.png et OUT.hd.png (detourage HD), et affiche un resume JSON.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import load_palette, Snapper, lum, lab, de, components, N4, N8, PALETTE

def _pf_default():
    """Chemin de pixel-fixer (cli.js) : variable PIXEL_FIXER_CLI, sinon config.local.json
    a la racine du skill (non versionne), sinon rien (repli interne)."""
    if os.environ.get("PIXEL_FIXER_CLI"):
        return os.environ["PIXEL_FIXER_CLI"]
    cfg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.local.json")
    if os.path.exists(cfg):
        with open(cfg, encoding="utf-8") as f:
            return json.load(f).get("pixel_fixer_cli", "")
    return ""


DEFAULT_PF = _pf_default()
SENT = (1, 254, 3)


def cutout(src, tol, mask_logo):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if mask_logo:  # logo "pollinations.ai" en bas a droite
        ImageDraw.Draw(im).rectangle([int(w * 0.66), int(h * 0.90), w, h], fill=im.getpixel((w - 1, int(h * 0.85))))
    work = im.copy()
    step = max(1, min(w, h) // 64)
    seeds = [(x, 0) for x in range(0, w, step)] + [(x, h - 1) for x in range(0, w, step)] + \
            [(0, y) for y in range(0, h, step)] + [(w - 1, y) for y in range(0, h, step)]
    for sd in seeds:
        if work.getpixel(sd) != SENT:
            ImageDraw.floodfill(work, sd, SENT, thresh=tol)
    out = im.convert("RGBA")
    po, pw = out.load(), work.load()
    for y in range(h):
        for x in range(w):
            if pw[x, y] == SENT:
                po[x, y] = (0, 0, 0, 0)
    # ombre portee grise collee au sujet : gris peu sature et clair, relie au fond -> retire
    pi = im.load()
    def shadowish(c):
        return max(c) - min(c) < 24 and 70 < sum(c) / 3 < 250
    stack = [(x, y) for y in range(h) for x in range(w) if po[x, y][3] == 0]
    while stack:
        x, y = stack.pop()
        for dx, dy in N4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and po[nx, ny][3] and shadowish(pi[nx, ny]):
                po[nx, ny] = (0, 0, 0, 0)
                stack.append((nx, ny))
    # garder le sujet : plus grande composante + morceaux >= 3 % de sa taille
    small = out.resize((w // 4, h // 4), Image.NEAREST)
    sp = small.load()
    comps = components(sp, small.width, small.height)
    if comps:
        keep = set()
        for c in comps:
            if len(c) >= 0.03 * len(comps[0]):
                keep.update(c)
        for y in range(h):
            for x in range(w):
                if po[x, y][3] and (x // 4, y // 4) not in keep:
                    po[x, y] = (0, 0, 0, 0)
    bb = out.getchannel("A").getbbox()
    if not bb:
        raise SystemExit("detourage vide : fond non uni ou tolerance trop forte")
    out = out.crop(bb)
    pad = max(2, max(out.size) // 40)
    canvas = Image.new("RGBA", (out.width + 2 * pad, out.height + 2 * pad), (0, 0, 0, 0))
    canvas.paste(out, (pad, pad))
    return canvas


def simplify(hd, colors):
    """Aplats en HD avant la reduction : filtre median + N couleurs sans tramage.
    Evite le grain (« peinture reduite ») qui fait echouer le test de bruit."""
    if colors <= 0:
        return hd
    from PIL import ImageFilter, ImageEnhance
    a = hd.getchannel("A")
    rgb = hd.convert("RGB").filter(ImageFilter.MedianFilter(5))
    # leger contraste (la saturation poussee faisait virer l'olive au jaune a la palette)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.1)
    q = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    out = q.convert("RGBA")
    out.putalpha(a)
    return out


def run_pixel_fixer(cli, hd_path, height, width, palette, outline, detail):
    tmp = tempfile.mkdtemp(prefix="pf_")
    cmd = ["node", cli, hd_path, "--out", tmp, "--height", str(height), "--palette", palette,
           "--detail", str(detail), "--outline", outline, "--pixel-perfect", "--background", "auto", "--json"]
    if width:
        cmd += ["--width", str(width)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp, timeout=300)
    res = os.path.join(tmp, os.path.splitext(os.path.basename(hd_path))[0] + ".png")
    if r.returncode != 0 or not os.path.exists(res):
        return None, (r.stdout + r.stderr)[-400:]
    return Image.open(res).convert("RGBA"), "pixel-fixer"


def fallback(hd, height, width):
    s = height / hd.height
    if width and hd.width * s > width:
        s = width / hd.width
    tw, th = max(1, round(hd.width * s)), max(1, round(hd.height * s))
    # couleur + alpha moyens par cellule (BOX), sur image premultipliee pour eviter les halos
    a = hd.getchannel("A")
    rgb = Image.composite(hd.convert("RGB"), Image.new("RGB", hd.size, (0, 0, 0)), a)
    small_rgb = rgb.resize((tw, th), Image.BOX)
    small_a = a.resize((tw, th), Image.BOX)
    out = Image.new("RGBA", (tw, th))
    po, pr, pa = out.load(), small_rgb.load(), small_a.load()
    for y in range(th):
        for x in range(tw):
            al = pa[x, y]
            if al < 110:
                po[x, y] = (0, 0, 0, 0)
            else:
                c = pr[x, y]
                k = 255 / al
                po[x, y] = (min(255, int(c[0] * k)), min(255, int(c[1] * k)), min(255, int(c[2] * k)), 255)
    return out


def cells(hd, height, width, dark_share=0.28):
    """Reduction par cellules sur l'image HD en aplats : couleur majoritaire de la cellule,
    sauf si un sombre (contour, pupille, bouche) y occupe >= dark_share : il gagne.
    Garde les traits fins qui font lire un petit sprite (oeil, bouche, contour)."""
    s = height / hd.height
    if width and hd.width * s > width:
        s = width / hd.width
    tw, th = max(1, round(hd.width * s)), max(1, round(hd.height * s))
    src = hd.load()
    out = Image.new("RGBA", (tw, th))
    po = out.load()
    lcache = {}
    for ty in range(th):
        y0, y1 = int(ty * hd.height / th), max(int(ty * hd.height / th) + 1, int((ty + 1) * hd.height / th))
        for tx in range(tw):
            x0, x1 = int(tx * hd.width / tw), max(int(tx * hd.width / tw) + 1, int((tx + 1) * hd.width / tw))
            counts = {}
            tot = op = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    tot += 1
                    c = src[x, y]
                    if c[3] >= 128:
                        op += 1
                        counts[c[:3]] = counts.get(c[:3], 0) + 1
            if op * 2 < tot or not counts:
                po[tx, ty] = (0, 0, 0, 0)
                continue
            for c in counts:
                if c not in lcache:
                    lcache[c] = lum(c)
            major = max(counts, key=counts.get)
            # trait saillant : couleur tres contrastee (pupille, oeil jaune, bouche, eclat,
            # contour) qui couvre une bonne part de la cellule -> elle gagne sur la majorite
            lm = lab(major)
            salient = [c for c in counts if c != major and counts[c] >= dark_share * op and de(lab(c), lm) >= 30]
            best = max(salient, key=lambda c: counts[c]) if salient else major
            po[tx, ty] = (*best, 255)
    return out


def outer_ring(im, pal):
    """Contour exterieur 1 px : chaque pixel transparent touchant le sujet devient la teinte
    tres sombre de son voisin (contour selectif ferme, comme les references CC0)."""
    sn = Snapper(pal)
    w, h = im.width + 2, im.height + 2
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (1, 1))
    src = out.copy().load()
    po = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            ns = [src[x + dx, y + dy] for dx, dy in N4 if 0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3]]
            if ns:
                # teinte de la matiere tres assombrie et tiree vers le violet nuit (pas de noir pur)
                r, g, b = min(ns, key=lum)[:3]
                po[x, y] = (*sn.nearest((int(r * 0.3 + 12), int(g * 0.3 + 8), int(b * 0.3 + 16)))[0], 255)
    return out


def limit_colors(im, n):
    """Fusionne les couleurs les moins utilisees dans la plus proche jusqu'a n couleurs."""
    px = im.load()
    w, h = im.size
    while True:
        cnt = {}
        for y in range(h):
            for x in range(w):
                if px[x, y][3]:
                    cnt[px[x, y][:3]] = cnt.get(px[x, y][:3], 0) + 1
        if len(cnt) <= n:
            return im
        rare = min(cnt, key=cnt.get)
        lr = lab(rare)
        tgt = min((c for c in cnt if c != rare), key=lambda c: de(lr, lab(c)))
        for y in range(h):
            for x in range(w):
                if px[x, y][3] and px[x, y][:3] == rare:
                    px[x, y] = (*tgt, 255)


def cleanup(im, pal, outline, max_colors=12):
    sn = Snapper(pal)
    w, h = im.size
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (*sn.nearest((r, g, b))[0], 255) if a >= 128 else (0, 0, 0, 0)
    if max_colors:
        limit_colors(im, max_colors)
    # pixels isoles (aucun voisin opaque en 8-connexite)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and not any(0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] for dx, dy in N8):
                px[x, y] = (0, 0, 0, 0)
    # damier : pixel entoure sur 4 cotes d'une meme autre couleur, avec 2+ diagonales de sa
    # couleur -> motif en echiquier (oeil, taches) : on le fond dans ses voisins.
    # Une vraie pupille (diagonales de la couleur de l'oeil) est gardee.
    snap = im.copy().load()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = snap[x, y]
            if not c[3]:
                continue
            ns = [snap[x + dx, y + dy] for dx, dy in N4]
            if ns[0][3] and all(n == ns[0] for n in ns) and ns[0] != c:
                diag = sum(snap[x + dx, y + dy] == c for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)))
                if diag >= 2:
                    px[x, y] = ns[0]
    # trous d'un pixel entoures sur 4 cotes
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not px[x, y][3] and all(px[x + dx, y + dy][3] for dx, dy in N4):
                ns = [px[x + dx, y + dy] for dx, dy in N4]
                px[x, y] = max(set(ns), key=ns.count)
    if outline != "none":
        used = {px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3]}
        dark_pal = sorted(pal, key=lum)
        darkest = dark_pal[0] if outline == "darkest" else None
        for y in range(h):
            for x in range(w):
                if not px[x, y][3]:
                    continue
                edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or not px[x + dx, y + dy][3] for dx, dy in N4)
                if edge and lum(px[x, y]) > 28:
                    if darkest:
                        px[x, y] = (*darkest, 255)
                    else:  # contour selectif : teinte de la matiere, tres assombrie
                        r, g, b = px[x, y][:3]
                        px[x, y] = (*sn.nearest((int(r * 0.3), int(g * 0.3), int(b * 0.3)))[0], 255)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--detail", type=int, default=3)
    ap.add_argument("--outline", default="outside", choices=["outside", "selective", "darkest", "none"],
                    help="outside = contour 1 px ajoute autour du sujet (ferme, net) ; selective = bord du sujet assombri")
    ap.add_argument("--max-colors", type=int, default=12)
    ap.add_argument("--bg-tol", type=int, default=40)
    ap.add_argument("--mask-logo", action="store_true")
    ap.add_argument("--palette", default=PALETTE)
    ap.add_argument("--pixel-fixer", default=DEFAULT_PF)
    ap.add_argument("--no-pixel-fixer", action="store_true")
    ap.add_argument("--flip", action="store_true", help="miroir horizontal (sujet tourne du mauvais cote)")
    ap.add_argument("--simplify", type=int, default=12, help="couleurs des aplats HD avant reduction (0 = non)")
    ap.add_argument("--method", default="cells", choices=["pixel-fixer", "cells", "cells2"],
                    help="cells = reduction par cellules avec priorite aux sombres (oeil, bouche, contour)")
    a = ap.parse_args()

    hd = simplify(cutout(a.src, a.bg_tol, a.mask_logo), a.simplify)
    if a.flip:
        hd = hd.transpose(Image.FLIP_LEFT_RIGHT)
    hd_path = os.path.splitext(a.out)[0] + ".hd.png"
    hd.save(hd_path)
    pal = load_palette(a.palette)
    engine, note = "interne", ""
    small = None
    outside = a.outline == "outside"
    th, tw = (a.height - 2, a.width - 2 if a.width else 0) if outside else (a.height, a.width)
    inner_outline = "none" if outside else a.outline
    if a.method == "cells":
        small, engine = cells(hd, th, tw), "cellules"
    elif a.method == "cells2":  # passe intermediaire a 2x puis 2x2 -> 1 (moins de damier)
        mid = cells(hd, th * 2, tw * 2 if tw else 0)
        small, engine = cells(mid, th, tw, dark_share=0.5), "cellules 2 passes"
    elif not a.no_pixel_fixer and shutil.which("node") and os.path.exists(a.pixel_fixer):
        small, note = run_pixel_fixer(a.pixel_fixer, os.path.abspath(hd_path), th, tw, os.path.abspath(a.palette),
                                      "selective" if outside else a.outline, a.detail)
        if small is not None:
            engine = "pixel-fixer"
    if small is None:
        small = fallback(hd, th, tw)
    small = cleanup(small, pal, inner_outline, a.max_colors)
    bb = small.getchannel("A").getbbox()
    if bb:
        small = small.crop(bb)
    if outside:
        small = outer_ring(small, pal)
    small.save(a.out)
    print(json.dumps({"out": a.out, "hd": hd_path, "size": small.size, "engine": engine, "note": note if engine == "interne" else ""}, ensure_ascii=False))


if __name__ == "__main__":
    main()
