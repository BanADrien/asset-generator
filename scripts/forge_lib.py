"""Outils communs (Pillow seul, pas de numpy) : palette, Lab, voisinage."""
import math, os

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE = os.path.join(SKILL, "style", "palette.hex")


def load_palette(path=PALETTE):
    cols = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.strip().lstrip("#")
            if len(t) == 6:
                cols.append(tuple(int(t[i:i + 2], 16) for i in (0, 2, 4)))
    return cols


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(rgb):
    r, g, b = (_lin(v) for v in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def de(a, b):
    return math.dist(a, b)


class Snapper:
    def __init__(self, pal):
        self.pal = pal
        self.labs = [lab(c) for c in pal]
        self.cache = {}

    def nearest(self, rgb):
        k = rgb[:3]
        if k not in self.cache:
            l = lab(k)
            i = min(range(len(self.pal)), key=lambda j: de(l, self.labs[j]))
            self.cache[k] = (self.pal[i], de(l, self.labs[i]))
        return self.cache[k]


def lum(rgb):
    return lab(rgb)[0]


N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def opaque(px, w, h, x, y):
    return 0 <= x < w and 0 <= y < h and px[x, y][3] >= 128


def components(px, w, h):
    """Composantes 8-connexes des pixels opaques -> liste de listes de (x, y), triee par taille."""
    seen = set()
    comps = []
    for y in range(h):
        for x in range(w):
            if (x, y) in seen or px[x, y][3] < 128:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            comp = []
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx, dy in N8:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3] >= 128:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps


def unique_path(folder, name):
    """Chemin libre dans folder : name, puis name-2, name-3... (n'ecrase jamais)."""
    base, ext = os.path.splitext(name)
    p = os.path.join(folder, name)
    n = 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{base}-{n}{ext}")
        n += 1
    return p


# Profils de taille. "petit" = densite des tuiles (24-30 px de haut) ; "detaille" = taille des
# personnages actuels du jeu (~64 px), plus de couleurs, reduction moins agressive.
# Le profil par defaut reste "petit" tant que l'utilisateur n'a pas tranche.
PROFILES = {
    "petit": {"height": 24, "width": 32, "colors": (5, 20), "orphans": 0.12, "frag": 2, "noise": 0.55,
              "simplify": 12, "max_colors": 12, "method": "cells", "screen_scale": 64 / 24},
    "detaille": {"height": 60, "width": 80, "colors": (12, 48), "orphans": 0.18, "frag": 6, "noise": 0.65,
                 "simplify": 40, "max_colors": 40, "method": "cells2", "screen_scale": 1.0},
}
DEFAULT_PROFILE = "petit"
