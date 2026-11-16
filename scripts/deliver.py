"""Livraison dans Telechargements sans jamais ecraser (suffixe -2, -3... commun a tous les fichiers).

Usage : python -I deliver.py --name crapaud-profil --sprite S.png --board B.png --history H.png --notes N.md [--dest DIR]
Copie : <name>.png (sprite 1x transparent), <name>-x8.png (apercu agrandi), <name>-planche.png,
<name>-historique.png (tous les essais notes), <name>-notes.md. Affiche les chemins finaux.
"""
import argparse, os, shutil
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--sprite", required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument("--history", required=True)
    ap.add_argument("--notes", required=True)
    ap.add_argument("--dest", default=os.path.join(os.path.expanduser("~"), "Downloads"))
    a = ap.parse_args()
    os.makedirs(a.dest, exist_ok=True)
    parts = [("", ".png"), ("-x8", ".png"), ("-planche", ".png"), ("-historique", ".png"), ("-notes", ".md")]
    n = 1
    while True:
        tag = a.name if n == 1 else f"{a.name}-{n}"
        paths = [os.path.join(a.dest, tag + s + e) for s, e in parts]
        if not any(os.path.exists(p) for p in paths):
            break
        n += 1
    shutil.copyfile(a.sprite, paths[0])
    im = Image.open(a.sprite)
    im.resize((im.width * 8, im.height * 8), Image.NEAREST).save(paths[1])
    shutil.copyfile(a.board, paths[2])
    shutil.copyfile(a.history, paths[3])
    shutil.copyfile(a.notes, paths[4])
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
