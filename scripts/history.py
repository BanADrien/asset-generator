"""Historique des essais : une fiche par IMAGE (6 par essai) + planche de tous les essais.

1) Pour chaque image de chaque essai (retenue ou non) :
   - jugee :  python -I history.py record --work W --essai 2 --seed fix-seed1 --note 6 --juge1 6.5 --juge2 6 \
                  [--plafond 5] --defauts "contour ouvert sous le ventre" "oeil illisible" ["..."]
   - ecartee au tri (lecteur aveugle + mesures, pas de juges) :
              python -I history.py record --work W --essai 2 --seed new-seed3 --ecarte "bouche absente (lecteur)"
   -> W/essai-2/fiche-<seed>.json et .md (le sprite reste W/essai-2/<seed>.png).
   - essai de DIRECTIONS (pas de juges) :
              python -I history.py record --work W --essai 2 --seed seed1 --titre "Mascotte ronde" --technique "technique OK"
2) A la livraison :
   python -I history.py board --work W --out W/historique.png
   [--zoom 5 --cols 3] (planche a montrer a l'utilisateur : grande, numerotee 1-6)
   -> une ligne par essai, les images numerotees dans l'ordre ; sous chacune : note finale et notes des
      deux juges (ou « ecarte : motif »), plafond objectif s'il s'applique, 2-3 defauts.
Compatible avec les anciennes fiches (fiche.json, une image par essai).
"""
import argparse, glob, json, os, textwrap
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
             "note_finale": a.note, "juge1": a.juge1, "juge2": a.juge2, "ecarte": a.ecarte or "",
             "plafond_objectif": a.plafond or None, "defauts": a.defauts[:3],
             "titre": a.titre, "technique": a.technique}
    with open(os.path.join(d, f"fiche-{a.seed}.json"), "w", encoding="utf-8") as f:
        json.dump(fiche, f, indent=1, ensure_ascii=False)
    lines = [f"# Essai {a.essai} ({a.seed})", ""]
    if a.titre:
        lines.append(f"- Direction : {a.titre} ; technique : {a.technique or '?'}")
    elif a.ecarte:
        lines.append(f"- Ecarte au tri : {a.ecarte}")
    else:
        lines += [f"- Note finale : {a.note}/10", f"- Juges : {a.juge1} et {a.juge2} (on garde la plus basse)",
                  f"- Plafond objectif : {str(a.plafond) + '/10' if a.plafond else 'aucun'}"]
    lines += ["- Defauts principaux :"] + [f"  - {x}" for x in a.defauts[:3]]
    with open(os.path.join(d, f"fiche-{a.seed}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(os.path.join(d, f"fiche-{a.seed}.json"))


def load_fiches(work):
    fiches = []
    for p in glob.glob(os.path.join(work, "essai-*", "fiche*.json")):
        with open(p, encoding="utf-8") as f:
            x = json.load(f)
        x.setdefault("ecarte", ""); x.setdefault("titre", ""); x.setdefault("technique", "")
        fiches.append(x)
    return fiches


def board(a):
    fiches = load_fiches(a.work)
    if not fiches:
        raise SystemExit("aucune fiche : lancer d'abord 'history.py record'")
    jug = [f for f in fiches if not f["ecarte"] and f.get("note_finale") is not None]
    best = max(jug, key=lambda x: (x["note_finale"], (x["juge1"] or 0) + (x["juge2"] or 0), -x["essai"])) if jug else None
    essais = sorted({f["essai"] for f in fiches})
    rows = [sorted([f for f in fiches if f["essai"] == e], key=lambda x: x["seed"]) for e in essais]
    sprites = {id(f): Image.open(f["sprite"]).convert("RGBA") for f in fiches}
    zoom = a.zoom or max(2, min(8, 180 // max(max(s.size) for s in sprites.values())))
    cw = max(210, max(s.width for s in sprites.values()) * zoom + 20)
    ih = max(s.height for s in sprites.values()) * zoom
    big_ui = zoom >= 4
    f_num, f_big, f_txt = font(40 if big_ui else 22), font(24 if big_ui else 18), font(18 if big_ui else 13)
    lh = 23 if big_ui else 17
    top = 54 if big_ui else 10  # place du numero au-dessus du sprite
    wrap = max(18, cw // (10 if big_ui else 8))
    if a.cols:  # coupe chaque essai en lignes de a.cols images
        rows = [r[i:i + a.cols] for r in rows for i in range(0, len(r), a.cols)]

    def text(f):
        if f["titre"]:
            return textwrap.wrap("technique : " + (f["technique"] or "?"), wrap)
        if f["ecarte"]:
            return textwrap.wrap("ecarte au tri : " + f["ecarte"], wrap)
        t = [f"juges : {f['juge1']} / {f['juge2']}"]
        if f.get("plafond_objectif"):
            t.append(f"plafond objectif : {f['plafond_objectif']}/10")
        for dft in f["defauts"][:3]:
            t += textwrap.wrap("- " + dft, wrap)
        return t
    th = 34 + lh * max(len(text(f)) for f in fiches)
    ch = ih + top + 10 + th
    ncol = max(len(r) for r in rows)
    W = 16 + ncol * (cw + 12)
    H = 40 + len(rows) * (ch + 34)
    rows_num, k = {}, {}
    for r in rows:
        for f in r:
            k[f["essai"]] = k.get(f["essai"], 0) + 1
            rows_num[id(f)] = k[f["essai"]]
    out = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(out)
    if all(f["titre"] for f in fiches):
        d.text((16, 12), "Directions artistiques - sous chaque image : nom de la direction et etat technique (pas de note des juges)",
               fill=DIM, font=f_txt)
    else:
      d.text((16, 12), "Historique (une ligne par essai) - note finale = plus basse des 2 juges, plafonnee par les mesures ;"
           " images ecartees au tri : motif", fill=DIM, font=f_txt)
    y = 40
    for r in rows:
        d.text((16, y), f"Essai {r[0]['essai']}", fill=INK, font=f_big)
        y0 = y + 26
        for i, f in enumerate(r):
            x0 = 16 + i * (cw + 12)
            d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=CARD, outline=OK if f is best else CARD, width=3)
            s = sprites[id(f)]
            big = s.resize((s.width * zoom, s.height * zoom), Image.NEAREST)
            out.alpha_composite(big, (x0 + (cw - big.width) // 2, y0 + top + ih - big.height))
            d.text((x0 + 10, y0 + 6), str(rows_num[id(f)]), fill=INK, font=f_num)
            ty = y0 + ih + top + 6
            if f["titre"]:
                d.text((x0 + 8, ty), f["titre"], fill=INK, font=f_big)
            elif f["ecarte"]:
                d.text((x0 + 8, ty), f"{f['seed']}  -  ecarte", fill=DIM, font=f_big)
            else:
                col = OK if f["note_finale"] >= 8 else KO
                d.text((x0 + 8, ty), f"{f['seed']}  -  {f['note_finale']}/10" + ("  (retenu)" if f is best else ""),
                       fill=col, font=f_big)
            for j, line in enumerate(text(f)):
                d.text((x0 + 8, ty + (32 if big_ui else 26) + lh * j), line, fill=INK, font=f_txt)
        y += ch + 34
    out.save(a.out)
    print(a.out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--work", required=True); r.add_argument("--essai", type=int, required=True)
    r.add_argument("--seed", required=True); r.add_argument("--note", type=float, default=None)
    r.add_argument("--juge1", type=float, default=None); r.add_argument("--juge2", type=float, default=None)
    r.add_argument("--plafond", type=float, default=0); r.add_argument("--defauts", nargs="+", default=[])
    r.add_argument("--ecarte", default="", help="motif du tri (image non jugee)")
    r.add_argument("--titre", default="", help="essai de directions : nom de la direction (pas de juges)")
    r.add_argument("--technique", default="", help="essai de directions : 'technique OK' ou le defaut")
    b = sub.add_parser("board")
    b.add_argument("--work", required=True); b.add_argument("--out", required=True)
    b.add_argument("--zoom", type=int, default=0, help="grossissement entier (defaut auto, ~5 pour une planche lisible)")
    b.add_argument("--cols", type=int, default=0, help="images par ligne (defaut : tout l'essai sur une ligne)")
    a = ap.parse_args()
    if a.cmd == "record" and not a.ecarte and not a.titre and (a.note is None or a.juge1 is None or a.juge2 is None):
        raise SystemExit("image jugee : --note, --juge1 et --juge2 sont obligatoires (sinon --ecarte)")
    record(a) if a.cmd == "record" else board(a)


if __name__ == "__main__":
    main()
