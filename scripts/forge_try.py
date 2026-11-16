"""Un essai complet : generation (plusieurs graines) -> pixelisation -> mesures -> planches.

Usage :
  python -I forge_try.py --work DIR --essai 1 --profile petit|detaille --prompt "..." \
      --negative "..." --seeds 11 22 33 [--height H --width L] [--engine horde|pollinations] \
      [--model "..."] [--method cells|cells2|pixel-fixer] [--orient auto|keep] [--reuse DIR_RAW]

Le profil fixe les valeurs par defaut (taille, couleurs, methode, echelle ecran de la planche) :
voir PROFILES dans forge_lib.py. Profil par defaut : "petit" (l'utilisateur n'a pas tranche).
Ecrit DIR/essai-<n>/ : raw/ (images HD), seed<k>.png (sprite), seed<k>.x8.png, seed<k>.board.png,
seed<k>.measure.json, et essai.json (parametres + tableau des mesures). Affiche le tableau.
--reuse : repixeliser les images HD d'un essai precedent sans regenerer.
"""
import argparse, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from measure import measure
from forge_lib import PALETTE, PROFILES, DEFAULT_PROFILE


def run(args):
    r = subprocess.run([sys.executable, "-I"] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--essai", type=int, required=True)
    ap.add_argument("--profile", default=DEFAULT_PROFILE, choices=sorted(PROFILES))
    ap.add_argument("--prompt", default="")
    ap.add_argument("--negative", default="")
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    ap.add_argument("--engine", default="horde")
    ap.add_argument("--model", default="AlbedoBase XL (SDXL)")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--height", type=int, default=0, help="defaut : profil")
    ap.add_argument("--width", type=int, default=-1, help="defaut : profil")
    ap.add_argument("--detail", type=int, default=3)
    ap.add_argument("--outline", default="outside")
    ap.add_argument("--orient", default="auto", choices=["auto", "keep"],
                    help="auto = retourne le sprite s'il semble regarder a gauche (heuristique)")
    ap.add_argument("--flip-seeds", nargs="*", default=[], help="forcer le miroir de ces graines (ex. seed201)")
    ap.add_argument("--method", default="", choices=["", "cells", "cells2", "pixel-fixer"])
    ap.add_argument("--simplify", type=int, default=0)
    ap.add_argument("--max-colors", type=int, default=0)
    ap.add_argument("--bg-tol", type=int, default=40)
    ap.add_argument("--lora", default="", help="LoRA AI Horde, ex. 120096:0.8 (Pixel Art XL)")
    ap.add_argument("--source", default="", help="image de base a retoucher (img2img) : methode par defaut des qu'on a un champion")
    ap.add_argument("--denoise", type=float, default=0.45, help="force de retouche (0,3 garde la base, 0,6 la change)")
    ap.add_argument("--control", default="", help="ControlNet (SD 1.5 seulement)")
    ap.add_argument("--reuse", default="")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    P = PROFILES[a.profile]
    height = a.height or P["height"]
    width = P["width"] if a.width < 0 else a.width
    method = a.method or P["method"]
    simplify = a.simplify or P["simplify"]
    max_colors = a.max_colors or P["max_colors"]

    d = os.path.join(a.work, f"essai-{a.essai}")
    raw = a.reuse or os.path.join(d, "raw")
    os.makedirs(d, exist_ok=True)
    gen_out = ""
    if not a.reuse:
        code, gen_out = run([os.path.join(HERE, "generate.py"), "--prompt", a.prompt, "--negative", a.negative,
                             "--out", raw, "--engine", a.engine, "--model", a.model, "--size", str(a.size),
                             "--seeds"] + [str(s) for s in a.seeds] + (["--lora", a.lora] if a.lora else [])
                            + (["--source", a.source, "--denoise", str(a.denoise)] if a.source else [])
                            + (["--control", a.control] if a.control else []))
    files = sorted(f for f in glob.glob(os.path.join(raw, "seed*.*")) if not f.endswith(".json"))
    rows = []
    for f in files:
        seed = os.path.splitext(os.path.basename(f))[0]
        sprite = os.path.join(d, seed + ".png")
        args = [os.path.join(HERE, "pixelize.py"), f, sprite, "--height", str(height), "--detail", str(a.detail),
                "--outline", a.outline, "--bg-tol", str(a.bg_tol), "--method", method,
                "--simplify", str(simplify), "--max-colors", str(max_colors),
                "--orient", "flip" if seed in a.flip_seeds else a.orient]
        if width:
            args += ["--width", str(width)]
        if P.get("palette_first"):
            args.append("--palette-first")
        if P.get("despeckle"):
            args += ["--despeckle", str(P["despeckle"])]
        if f.endswith(".jpg"):
            args.append("--mask-logo")
        code, out = run(args)
        if code != 0 or not os.path.exists(sprite):
            rows.append({"seed": seed, "erreur": out[-300:]})
            continue
        m = measure(sprite, height, width, PALETTE, a.profile)
        with open(os.path.join(d, seed + ".measure.json"), "w", encoding="utf-8") as fh:
            json.dump(m, fh, indent=1, ensure_ascii=False)
        run([os.path.join(HERE, "board.py"), sprite, os.path.join(d, seed + ".board.png"),
             "--label", f"essai {a.essai} {seed} {a.label}", "--screen-scale", str(P["screen_scale"])])
        from PIL import Image
        im = Image.open(sprite)
        z = 8 if max(im.size) <= 40 else 4
        im.resize((im.width * z, im.height * z), Image.NEAREST).save(os.path.join(d, seed + ".x8.png"))
        rows.append({"seed": seed, "sprite": sprite, "taille": m["size"], "couleurs": m["colors"],
                     "plafond": m["plafond"], "echecs": m["echecs"]})
    info = {"essai": a.essai, "profil": a.profile, "params": vars(a), "generation": gen_out[-1500:], "resultats": rows}
    with open(os.path.join(d, "essai.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, ensure_ascii=False)
    print(f"essai {a.essai} ({a.profile}) -> {d}")
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
