"""Livraison dans Telechargements sans jamais ecraser (suffixe -2, -3... commun a tous les fichiers).

Usage : python -I deliver.py --name crapaud-retouche --sprite S.png --history H.png --notes N.md
        [--board B.png] [--dest DIR]
Par defaut (souhait de l'utilisateur) : <name>.png (sprite 1x transparent), <name>-historique.png
(tous les essais notes) et <name>-notes.md. La planche comparative reste dans le dossier de
travail pour les juges ; --board ne l'ajoute que si on la demande.
"""
import argparse, os, shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--sprite", required=True)
    ap.add_argument("--history", required=True)
    ap.add_argument("--notes", required=True)
    ap.add_argument("--board", default="", help="planche comparative (seulement si demandee)")
    ap.add_argument("--dest", default=os.path.join(os.path.expanduser("~"), "Downloads"))
    a = ap.parse_args()
    os.makedirs(a.dest, exist_ok=True)
    items = [("", ".png", a.sprite), ("-historique", ".png", a.history), ("-notes", ".md", a.notes)]
    if a.board:
        items.append(("-planche", ".png", a.board))
    n = 1
    while True:
        tag = a.name if n == 1 else f"{a.name}-{n}"
        paths = [os.path.join(a.dest, tag + s + e) for s, e, _ in items]
        if not any(os.path.exists(p) for p in paths):
            break
        n += 1
    for p, (_, _, src) in zip(paths, items):
        shutil.copyfile(src, p)
        print(p)


if __name__ == "__main__":
    main()
