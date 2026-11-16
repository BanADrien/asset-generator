"""Planche comparative : candidat + 3 assets du jeu + 2 references CC0, en jeu / 1x / zoom.

Usage : python -I board.py CANDIDAT.png OUT.png [--game crapaud_actuel agarica_actuel singe_actuel]
        [--refs cc0_froggy_spring cc0_frogs_aroach] [--label "essai 2"]

Bande 1 "en jeu" : tout a l'echelle ecran du jeu (1 px art = 64/24 px, comme les tuiles),
  sur le sol dessine a la main, fond violet nuit ; puis vue x2 pour la lecture.
Bande 2 "1x natif" : candidat, une case de tuile et les references a leur vraie taille.
Bande 3 "zoom x8" : candidat, tuile et references au meme grossissement entier.
"""
import argparse, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import SKILL

EX = os.path.join(SKILL, "style", "examples")
RI = os.path.join(SKILL, "references", "img")
BG = (30, 23, 38, 255)
INK = (238, 239, 237, 255)
SCALE = 64 / 24  # densite de pixels du jeu (tuile de 24 px affichee en 64 px)


def load(p):
    im = Image.open(p).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def nearest(im, s):
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.NEAREST)


def strip(items, gap=14, ground=None, label=""):
    """Aligne des images sur une ligne de sol commune."""
    h = max(i.height for i in items)
    w = sum(i.width for i in items) + gap * (len(items) + 1)
    gh = ground.height if ground else 0
    top = 18
    out = Image.new("RGBA", (w, h + gh + top + 6), BG)
    x = gap
    for i in items:
        out.alpha_composite(i, (x, top + h - i.height))
        x += i.width + gap
    if ground:
        for gx in range(0, w, ground.width):
            out.alpha_composite(ground, (gx, top + h))
    ImageDraw.Draw(out).text((6, 3), label, fill=INK)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cand"); ap.add_argument("out")
    ap.add_argument("--game", nargs="+", default=["crapaud_actuel", "agarica_actuel", "singe_actuel"])
    ap.add_argument("--refs", nargs="+", default=["cc0_froggy_spring", "cc0_frogs_aroach"])
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    cand = load(a.cand)
    game = [load(os.path.join(EX, g + ".png")) for g in a.game]
    refs = [load(os.path.join(RI, r + ".png")) for r in a.refs]
    tile = Image.open(os.path.join(EX, "tuile_A2.png")).convert("RGBA")
    grass = Image.open(os.path.join(EX, "tuile_grass_mid.png")).convert("RGBA")
    ground1x = tile.copy()
    ground1x.alpha_composite(grass.crop((0, 0, 24, 8)), (0, 0))
    ground1x = ground1x.crop((0, 0, 24, 12))

    # bande 1 : en jeu (echelle ecran), puis x2 pour lecture
    b1 = strip([nearest(cand, SCALE)] + game, ground=nearest(ground1x, SCALE),
               label="EN JEU (echelle ecran) : candidat | sprites IA actuels")
    b1 = nearest(b1, 2)
    # bande 2 : 1x natif
    b2 = strip([cand, tile] + refs, label="1x natif (affiche x2) : candidat | tuile du jeu | refs CC0")
    b2 = nearest(b2, 2)
    # bande 3 : zoom x8 (meme grossissement pour tous)
    z = 8
    b3 = strip([nearest(cand, z), nearest(tile, z)] + [nearest(r, min(z, max(2, 260 // r.height))) for r in refs],
               label="ZOOM x8 : candidat | tuile dessinee main | refs CC0 (zoom reduit si grandes)")
    W = max(b.width for b in (b1, b2, b3)) + 20
    H = b1.height + b2.height + b3.height + 60
    sheet = Image.new("RGBA", (W, H), (18, 14, 24, 255))
    d = ImageDraw.Draw(sheet)
    d.text((10, 6), f"pixel-art-forge  {a.label}  candidat {cand.width}x{cand.height}px", fill=INK)
    y = 24
    for b in (b1, b2, b3):
        sheet.alpha_composite(b, (10, y))
        y += b.height + 12
    sheet.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
