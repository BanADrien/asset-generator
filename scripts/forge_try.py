"""Un essai complet : generation (plusieurs graines) -> pixelisation -> mesures -> planches.

Usage :
  python -I forge_try.py --work DIR --essai 1 --prompt "..." --negative "..." \
      --seeds 11 22 33 --height 24 --width 32 [--engine horde|pollinations] [--model "..."] \
      [--detail 3] [--outline selective] [--flip] [--bg-tol 40] [--reuse DIR_RAW]

Ecrit DIR/essai-<n>/ : raw/ (images HD), seed<k>.png (sprite), seed<k>.board.png (planche),
seed<k>.measure.json, et essai.json (parametres + tableau des mesures). Affiche le tableau.
--reuse : repixeliser les images HD d'un essai precedent sans regenerer (changer detail, contour...).
"""
import argparse, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from measure import measure
from forge_lib import PALETTE


def run(args):
    r = subprocess.run([sys.executable, "-I"] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--essai", type=int, required=True)
    ap.add_argument("--prompt", default="")
    ap.add_argument("--negative", default="")
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    ap.add_argument("--engine", default="horde")
    ap.add_argument("--model", default="AlbedoBase XL (SDXL)")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--detail", type=int, default=3)
    ap.add_argument("--outline", default="outside")
    ap.add_argument("--flip", action="store_true", help="retourner toutes les graines")
    ap.add_argument("--flip-seeds", nargs="*", default=[], help="retourner seulement ces graines (ex. seed201)")
    ap.add_argument("--method", default="cells", choices=["cells", "cells2", "pixel-fixer"])
    ap.add_argument("--simplify", type=int, default=12)
    ap.add_argument("--bg-tol", type=int, default=40)
    ap.add_argument("--reuse", default="")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    d = os.path.join(a.work, f"essai-{a.essai}")
    raw = a.reuse or os.path.join(d, "raw")
    os.makedirs(d, exist_ok=True)
    gen_out = ""
    if not a.reuse:
        code, gen_out = run([os.path.join(HERE, "generate.py"), "--prompt", a.prompt, "--negative", a.negative,
                             "--out", raw, "--engine", a.engine, "--model", a.model, "--size", str(a.size),
                             "--seeds"] + [str(s) for s in a.seeds])
    files = sorted(f for f in glob.glob(os.path.join(raw, "seed*.*")) if not f.endswith(".json"))
    rows = []
    for f in files:
        seed = os.path.splitext(os.path.basename(f))[0]
        sprite = os.path.join(d, seed + ".png")
        args = [os.path.join(HERE, "pixelize.py"), f, sprite, "--height", str(a.height), "--detail", str(a.detail),
                "--outline", a.outline, "--bg-tol", str(a.bg_tol), "--method", a.method, "--simplify", str(a.simplify)]
        if a.width:
            args += ["--width", str(a.width)]
        if a.flip or seed in a.flip_seeds:
            args.append("--flip")
        if f.endswith(".jpg"):
            args.append("--mask-logo")
        code, out = run(args)
        if code != 0 or not os.path.exists(sprite):
            rows.append({"seed": seed, "erreur": out[-300:]})
            continue
        m = measure(sprite, a.height, a.width, PALETTE)
        with open(os.path.join(d, seed + ".measure.json"), "w", encoding="utf-8") as fh:
            json.dump(m, fh, indent=1, ensure_ascii=False)
        run([os.path.join(HERE, "board.py"), sprite, os.path.join(d, seed + ".board.png"),
             "--label", f"essai {a.essai} {seed} {a.label}"])
        from PIL import Image
        im = Image.open(sprite)
        im.resize((im.width * 8, im.height * 8), Image.NEAREST).save(os.path.join(d, seed + ".x8.png"))
        rows.append({"seed": seed, "sprite": sprite, "taille": m["size"], "couleurs": m["colors"],
                     "plafond": m["plafond"], "echecs": m["echecs"]})
    info = {"essai": a.essai, "params": vars(a), "generation": gen_out[-1500:], "resultats": rows}
    with open(os.path.join(d, "essai.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, ensure_ascii=False)
    print(f"essai {a.essai} -> {d}")
    for r in rows:
        if "erreur" in r:
            print(f"  {r['seed']}: ERREUR {r['erreur']}")
        else:
            print(f"  {r['seed']}: {r['taille'][0]}x{r['taille'][1]} px, {r['couleurs']} coul., plafond {r['plafond']}"
                  + (f" (echecs : {', '.join(r['echecs'])})" if r["echecs"] else ""))
    if not rows:
        print("  aucune image : voir essai.json (generation)")
        print(gen_out[-800:])


if __name__ == "__main__":
    main()
