"""Page de test d'eclairage AUTONOME (images integrees en base64, s'ouvre par double-clic).

Usage : python -I viewer.py SPRITE.png|ANIM.anim.json [SPRITE2.png ...] [--regarde gauche] [--noms "crapaud,loup"] [--titre T]
                            [--echelle 6] [--out CHEMIN.html]
Lit a cote de chaque sprite : <nom>.neutre.png, <nom>.normales.png, <nom>.sections.png et
<nom>.cj.png (carte contre-jour, calculee a la volee si absente) (sorties de sections.py). Un seul sprite -> <nom>-lumiere.html a cote de lui ; plusieurs -> une seule page
avec un selecteur d'asset et une case « tous cote a cote » (meme lumiere, meme echelle, tailles
relatives du jeu), ecrite a --out (defaut : assets-lumiere.html a cote du 1er sprite).
Animation (.anim.json de sections.py --animation) : lecture en boucle a la vitesse du jeu,
pause, frame par frame, vitesse, « marcher » (aller-retour devant une lumiere fixe) et « sens »
(miroir + normal.x inverse).
N'ecrase jamais un fichier existant (suffixe -2, -3...).
"""
import argparse, base64, io, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_lib import SKILL, unique_path
from PIL import Image
import sections

TEMPLATE = os.path.join(SKILL, "viewer", "lumiere-template.html")


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def images(sprite):
    stem = os.path.splitext(sprite)[0]
    imgs = {"origine": sprite}
    for k in ("neutre", "normales", "sections"):
        p = f"{stem}.{k}.png"
        if not os.path.exists(p):
            sys.exit(f"manque {p} : lancer d'abord sections.py {sprite}")
        imgs[k] = p
    out = {k: data_uri(p) for k, p in imgs.items()}
    # geometrie pour le contre-jour (bord exterieur reel, epaisseur, distance du halo)
    buf = io.BytesIO()
    sections.geometrie(Image.open(sprite).convert("RGBA")).save(buf, "PNG")
    out["geo"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    # carte contre-jour (v16) : <nom>.cj.png de sections.py (retouchable), sinon calculee ici
    cj = f"{stem}.cj.png"
    if os.path.exists(cj):
        out["cj"] = data_uri(cj)
    else:
        buf = io.BytesIO()
        sections.carte_cj(Image.open(sprite).convert("RGBA"), Image.open(imgs["normales"]),
                          Image.open(imgs["neutre"])).save(buf, "PNG")
        out["cj"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    return out


def asset(sprite, nom, regarde="droite"):
    if sprite.endswith(".anim.json"):   # animation (sections.py --animation)
        with open(sprite, encoding="utf-8") as f:
            man = json.load(f)
        d = os.path.dirname(sprite)
        return {"nom": nom or man["nom"], "fps": man.get("fps", 12), "vitesse": man.get("vitesse", 0),
                "regarde": man.get("regarde", regarde),
                "frames": [{"images": images(os.path.join(d, fr))} for fr in man["frames"]]}
    return {"nom": nom or os.path.basename(os.path.splitext(sprite)[0]), "regarde": regarde,
            "images": images(sprite)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sprites", nargs="+", help="sprites .png ou animations .anim.json (sections.py --animation)")
    ap.add_argument("--regarde", default="", help="sens d'origine des sprites : droite (defaut) ou gauche")
    ap.add_argument("--noms", default="", help="noms affiches, separes par des virgules")
    ap.add_argument("--titre", default="")
    ap.add_argument("--echelle", type=int, default=6, help="agrandissement entier par defaut (x6)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    noms = [n.strip() for n in a.noms.split(",")] if a.noms else []
    assets = [asset(s, noms[i] if i < len(noms) else "", a.regarde or "droite") for i, s in enumerate(a.sprites)]
    titre = a.titre or (assets[0]["nom"] if len(assets) == 1 else "Assets")
    donnees = {"titre": titre, "echelle": max(1, a.echelle), "assets": assets, "geoPad": sections.GEO_PAD}
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("/*__DONNEES__*/null", json.dumps(donnees))
    first = os.path.splitext(a.sprites[0].replace(".anim.json", ".png"))[0]
    out = a.out or (first + "-lumiere.html" if len(assets) == 1
                    else os.path.join(os.path.dirname(first), "assets-lumiere.html"))
    out = unique_path(os.path.dirname(os.path.abspath(out)), os.path.basename(out))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(out)


if __name__ == "__main__":
    main()
