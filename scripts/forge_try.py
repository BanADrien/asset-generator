"""Un essai complet : generation Codex -> reduction fidele a la grille -> mesures -> planches.

Usage (essai 1, 6 nouvelles propositions) :
  python -I forge_try.py --work W --essai 1 --prompt-file NEUF.txt --ref style/etalon-style.png --ref SPRITE_ACTUEL.png
Usage (essai 2 et suivants : 3 retouches du champion + 3 nouvelles propositions) :
  python -I forge_try.py --work W --essai 2 --prompt-file NEUF.txt --ref ... \
      --champion W/essai-1/raw-new/seed2.png --fix-prompt-file CORRIGE.txt
Repixeliser sans regenerer : --reuse DOSSIER_BRUTS (un ou plusieurs).

Dans les fichiers de prompt, {N} est remplace par le nombre d'images demandees.
Ecrit W/essai-n/ : raw-new/ et raw-fix/ (bruts Codex), <src>-seedK.png (sprite natif),
<src>-seedK.x8.png (fond blanc, agrandi), .board.png, .measure.json (dont fidelite au brut),
essai.json (tableau). Profil par defaut : natif (grid_reduce, palette propre de l'image).
"""
import argparse, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from measure import measure
from forge_lib import PALETTE, PROFILES, DEFAULT_PROFILE


def run(args):
    r = subprocess.run([sys.executable, "-I"] + args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def gen(prompt_file, out, refs, n, d, tag):
    txt = open(prompt_file, encoding="utf-8").read().replace("{N}", str(n))
    pf = os.path.join(d, f"prompt-{tag}.txt")
    with open(pf, "w", encoding="utf-8") as f:
        f.write(txt)
    args = [os.path.join(HERE, "generate.py"), "--out", out, "--prompt-file", pf, "--n", str(n)]
    for r in refs:
        args += ["--ref", r]
    return run(args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--essai", type=int, required=True)
    ap.add_argument("--profile", default=DEFAULT_PROFILE, choices=sorted(PROFILES))
    ap.add_argument("--prompt-file", default="", help="prompt des nouvelles propositions")
    ap.add_argument("--ref", action="append", default=[], help="etalon de style, sprite actuel du sujet...")
    ap.add_argument("--n", type=int, default=6, help="images par essai (quota : 6)")
    ap.add_argument("--champion", default="", help="meilleure image brute de l'essai precedent")
    ap.add_argument("--fix-prompt-file", default="", help="prompt de correction du champion (UN defaut)")
    ap.add_argument("--reuse", nargs="*", default=[])
    ap.add_argument("--method", default="", choices=["", "grid", "cells", "cells2", "pixel-fixer"],
                    help="grid = defaut (natif) ; cells/pixel-fixer = ancienne reduction (profils petit/detaille)")
    ap.add_argument("--max-colors", type=int, default=0)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    P = PROFILES[a.profile]
    method = a.method or P["method"]
    max_colors = a.max_colors or P.get("max_colors", 32)

    d = os.path.join(a.work, f"essai-{a.essai}")
    os.makedirs(d, exist_ok=True)
    logs = []
    raws = list(a.reuse)
    if not raws:
        if a.champion and a.fix_prompt_file:
            k = a.n // 2
            out = os.path.join(d, "raw-fix")
            logs.append(gen(a.fix_prompt_file, out, [a.champion] + a.ref, k, d, "fix")[1]); raws.append(out)
            out = os.path.join(d, "raw-new")
            logs.append(gen(a.prompt_file, out, a.ref, a.n - k, d, "new")[1]); raws.append(out)
        else:
            out = os.path.join(d, "raw-new")
            logs.append(gen(a.prompt_file, out, a.ref, a.n, d, "new")[1]); raws.append(out)
    rows = []
    from PIL import Image
    for rd in raws:
        tag = os.path.basename(os.path.normpath(rd)).replace("raw-", "") or "raw"
        for f in sorted(glob.glob(os.path.join(rd, "seed*.png")) + glob.glob(os.path.join(rd, "seed*.webp"))):
            name = f"{tag}-{os.path.splitext(os.path.basename(f))[0]}"
            sprite = os.path.join(d, name + ".png")
            if method == "grid":
                args = [os.path.join(HERE, "grid_reduce.py"), f, sprite, "--max-colors", str(max_colors)]
            else:
                args = [os.path.join(HERE, "pixelize.py"), f, sprite, "--height", str(P["height"]),
                        "--width", str(P["width"]), "--method", method, "--max-colors", str(max_colors)]
            code, out = run(args)
            if code != 0 or not os.path.exists(sprite):
                rows.append({"image": name, "brut": f, "erreur": out[-300:]})
                continue
            im = Image.open(sprite).convert("RGBA")
            m = measure(sprite, P["height"] or im.height, P["width"], PALETTE, a.profile,
                        raw=f if method == "grid" else None)
            with open(os.path.join(d, name + ".measure.json"), "w", encoding="utf-8") as fh:
                json.dump(m, fh, indent=1, ensure_ascii=False)
            run([os.path.join(HERE, "board.py"), sprite, os.path.join(d, name + ".board.png"),
                 "--label", f"essai {a.essai} {name} {a.label}", "--screen-scale", str(P["screen_scale"])])
            z = 8 if max(im.size) <= 64 else 6
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
            bg.resize((im.width * z, im.height * z), Image.NEAREST).save(os.path.join(d, name + ".x8.png"))
            rows.append({"image": name, "brut": f, "sprite": sprite, "taille": m["size"], "couleurs": m["colors"],
                         "plafond": m["plafond"], "echecs": m["echecs"]})
    info = {"essai": a.essai, "profil": a.profile, "params": vars(a), "generation": [l[-1500:] for l in logs], "resultats": rows}
    with open(os.path.join(d, "essai.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, ensure_ascii=False)
    print(f"essai {a.essai} ({a.profile}, {method}) -> {d}")
    for r in rows:
        if "erreur" in r:
            print(f"  {r['image']}: ERREUR {r['erreur']}")
        else:
            print(f"  {r['image']}: {r['taille'][0]}x{r['taille'][1]} px, {r['couleurs']} coul., plafond {r['plafond']}"
                  + (f" (echecs : {', '.join(r['echecs'])})" if r["echecs"] else ""))
    if not rows:
        print("  aucune image : voir raw-*/codex-log.txt")


if __name__ == "__main__":
    main()
