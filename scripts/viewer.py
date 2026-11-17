"""Page de test d'eclairage AUTONOME (images integrees en base64, s'ouvre par double-clic).

Usage : python -I viewer.py SPRITE.png [SPRITE2.png ...] [--noms "crapaud,loup"] [--titre T]
                            [--echelle 6] [--out CHEMIN.html]
Lit a cote de chaque sprite : <nom>.neutre.png, <nom>.normales.png, <nom>.sections.png (sorties de
sections.py). Un seul sprite -> <nom>-lumiere.html a cote de lui ; plusieurs -> une seule page
avec un selecteur d'asset et une case « tous cote a cote » (meme lumiere, meme echelle, tailles
relatives du jeu), ecrite a --out (defaut : assets-lumiere.html a cote du 1er sprite).
N'ecrase jamais un fichier existant (suffixe -2, -3...).
"""
import argparse, base64, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import SKILL, unique_path

TEMPLATE = os.path.join(SKILL, "viewer", "lumiere-template.html")


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def asset(sprite, nom):
    stem = os.path.splitext(sprite)[0]
    imgs = {"origine": sprite}
    for k in ("neutre", "normales", "sections"):
        p = f"{stem}.{k}.png"
        if not os.path.exists(p):
            sys.exit(f"manque {p} : lancer d'abord sections.py {sprite}")
        imgs[k] = p
    return {"nom": nom or os.path.basename(stem), "images": {k: data_uri(p) for k, p in imgs.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sprites", nargs="+")
    ap.add_argument("--noms", default="", help="noms affiches, separes par des virgules")
    ap.add_argument("--titre", default="")
    ap.add_argument("--echelle", type=int, default=6, help="agrandissement entier par defaut (x6)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    noms = [n.strip() for n in a.noms.split(",")] if a.noms else []
    assets = [asset(s, noms[i] if i < len(noms) else "") for i, s in enumerate(a.sprites)]
    titre = a.titre or (assets[0]["nom"] if len(assets) == 1 else "Assets")
    donnees = {"titre": titre, "echelle": max(1, a.echelle), "assets": assets}
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("/*__DONNEES__*/null", json.dumps(donnees))
    first = os.path.splitext(a.sprites[0])[0]
    out = a.out or (first + "-lumiere.html" if len(assets) == 1
                    else os.path.join(os.path.dirname(first), "assets-lumiere.html"))
    out = unique_path(os.path.dirname(os.path.abspath(out)), os.path.basename(out))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(out)


if __name__ == "__main__":
    main()
