"""Historique des essais : fiche par essai + planche de tous les essais cote a cote.

1) Apres le jugement de chaque essai (retenu ou non) :
   python -I history.py record --work W --essai 2 --seed seed22 --note 6 --juge1 6.5 --juge2 6 \
       [--plafond 5] --defauts "contour ouvert sous le ventre" "oeil illisible a 1x" ["..."]
   -> W/essai-2/fiche.json et fiche.md (le sprite reste dans W/essai-2/seed22.png).
2) A la livraison :
   python -I history.py board --work W --out W/historique.png
   -> tous les essais dans l'ordre, sprite agrandi, et sous chacun : numero, note finale,
      notes des deux juges, plafond objectif s'il s'applique, 2-3 defauts principaux.
"""
import argparse, glob, json, os, re, textwrap
from PIL import Image, ImageDraw, ImageFont

BG = (18, 14, 24, 255)
CARD = (30, 23, 38, 255)
INK = (238, 239, 237, 255)
DIM = (170, 160, 190, 255)
OK = (127, 178, 74, 255)
KO = (236, 127, 160, 255)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def record(a):
    d = os.path.join(a.work, f"essai-{a.essai}")
    sprite = os.path.join(d, a.seed + ".png")
    fiche = {"essai": a.essai, "seed": a.seed, "sprite": sprite, "board": os.path.join(d, a.seed + ".board.png"),
             "note_finale": a.note, "juge1": a.juge1, "juge2": a.juge2,
             "plafond_objectif": a.plafond or None, "defauts": a.defauts[:3], "retenu": False}
    with open(os.path.join(d, "fiche.json"), "w", encoding="utf-8") as f:
        json.dump(fiche, f, indent=1, ensure_ascii=False)
    lines = [f"# Essai {a.essai} ({a.seed})", "",
             f"- Note finale : {a.note}/10",
             f"- Juges : {a.juge1} et {a.juge2} (on garde la plus basse)",
             f"- Plafond objectif : {str(a.plafond) + '/10' if a.plafond else 'aucun'}",
             "- Defauts principaux :"] + [f"  - {x}" for x in a.defauts[:3]]
    with open(os.path.join(d, "fiche.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(os.path.join(d, "fiche.json"))


def board(a):
    fiches = []
    for p in glob.glob(os.path.join(a.work, "essai-*", "fiche.json")):
        with open(p, encoding="utf-8") as f:
            fiches.append(json.load(f))
    if not fiches:
        raise SystemExit("aucune fiche : lancer d'abord 'history.py record' pour chaque essai")
    fiches.sort(key=lambda x: x["essai"])
    # meilleur : note finale, puis somme des deux juges, puis le plus ancien
    best = max(fiches, key=lambda x: (x["note_finale"], x["juge1"] + x["juge2"], -x["essai"]))
    sprites = [Image.open(f["sprite"]).convert("RGBA") for f in fiches]
    zoom = max(2, min(8, 200 // max(max(s.size) for s in sprites)))
    cw = max(220, max(s.width for s in sprites) * zoom + 24)
    ih = max(s.height for s in sprites) * zoom
    f_big, f_txt = font(20), font(14)
    wrap = max(18, cw // 8)
    texts = []
    for f in fiches:
        t = [f"juges : {f['juge1']} / {f['juge2']}"]
        if f.get("plafond_objectif"):
            t.append(f"plafond objectif : {f['plafond_objectif']}/10")
        for dft in f["defauts"][:3]:
            t += textwrap.wrap("- " + dft, wrap)
        texts.append(t)
    th = 34 + 18 * max(len(t) for t in texts)
    ch = ih + 24 + th
    W = 16 + len(fiches) * (cw + 16)
    H = ch + 60
    out = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 12), "Historique des essais (ordre chronologique) - note finale = plus basse des 2 juges, plafonnee par les mesures",
           fill=DIM, font=f_txt)
    for i, (f, s, t) in enumerate(zip(fiches, sprites, texts)):
        x0, y0 = 16 + i * (cw + 16), 40
        d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=CARD, outline=OK if f is best else CARD, width=3)
        big = s.resize((s.width * zoom, s.height * zoom), Image.NEAREST)
        out.alpha_composite(big, (x0 + (cw - big.width) // 2, y0 + 12 + ih - big.height))
        ty = y0 + ih + 24
        col = OK if f["note_finale"] >= 8 else KO
        d.text((x0 + 10, ty), f"Essai {f['essai']}  -  {f['note_finale']}/10" + ("  (retenu)" if f is best else ""),
               fill=col, font=f_big)
        for j, line in enumerate(t):
            d.text((x0 + 10, ty + 30 + 18 * j), line, fill=INK, font=f_txt)
    out.save(a.out)
    print(a.out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--work", required=True); r.add_argument("--essai", type=int, required=True)
    r.add_argument("--seed", required=True); r.add_argument("--note", type=float, required=True)
    r.add_argument("--juge1", type=float, required=True); r.add_argument("--juge2", type=float, required=True)
    r.add_argument("--plafond", type=float, default=0); r.add_argument("--defauts", nargs="+", default=[])
    b = sub.add_parser("board")
    b.add_argument("--work", required=True); b.add_argument("--out", required=True)
    a = ap.parse_args()
    record(a) if a.cmd == "record" else board(a)


if __name__ == "__main__":
    main()
