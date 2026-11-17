"""Page de test d'eclairage AUTONOME (images integrees en base64, s'ouvre par double-clic).

Usage : python -I viewer.py SPRITE.png [--echelle 6] [--out CHEMIN.html]
Lit a cote du sprite : <nom>.neutre.png, <nom>.normales.png, <nom>.sections.png (sorties de
sections.py). Ecrit <nom>-lumiere.html a cote du sprite (ou --out), sans ecraser un fichier
existant (suffixe -2, -3...).
"""
import argparse, base64, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import SKILL, unique_path

TEMPLATE = os.path.join(SKILL, "viewer", "lumiere-template.html")


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sprite")
    ap.add_argument("--echelle", type=int, default=6, help="agrandissement entier par defaut (x6)")
    ap.add_argument("--nom", default="", help="nom affiche (defaut : nom du fichier)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    stem = os.path.splitext(a.sprite)[0]
    imgs = {"origine": a.sprite}
    for k in ("neutre", "normales", "sections"):
        p = f"{stem}.{k}.png"
        if not os.path.exists(p):
            sys.exit(f"manque {p} : lancer d'abord sections.py {a.sprite}")
        imgs[k] = p
    nom = a.nom or os.path.basename(stem)
    donnees = {"nom": nom, "echelle": max(1, a.echelle), "images": {k: data_uri(p) for k, p in imgs.items()}}
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("/*__DONNEES__*/null", json.dumps(donnees))
    out = a.out or stem + "-lumiere.html"
    out = unique_path(os.path.dirname(os.path.abspath(out)), os.path.basename(out))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(out)


if __name__ == "__main__":
    main()
