"""Calcul de la note finale (grille v3.2) a partir des JSON des juges et des mesures.

Les plafonds durs sont appliques ici, par le calcul, pas par l'appreciation du juge :
  - animal lu a froid faux (ni le sujet ni un cousin)  -> 2 maximum
  - autre animal/objet qui saute aux yeux (autre_lecture_dominante) -> 2 maximum
  - cousin proche (grenouille pour crapaud)             -> -1
  - teinte criarde dominante                            -> -1,5 (avec le cousin : -1,5 au total)
  - bruit / salissure dominant                          -> 3 maximum
  - oeil reduit a un tiret / carre plat, ou bouche absente -> 4,5 maximum
  - plus de 6,5 sans « depasse_ancre » justifie         -> 6,5 maximum
  - plus de 7 sans « depasse_orange » justifie          -> 7 maximum
  - 8 ou plus sans criteres 1 et 4 >= 8                 -> 7,5 maximum
  - mesures objectives en echec                         -> 5 maximum
Deux juges : on garde la plus basse.

Usage : python -I score.py --judge J1.json [--judge J2.json] [--measure M.json]
        [--animal crapaud] [--synonyms crapaud,toad] [--cousins grenouille,frog,batracien,amphibien]
Un fichier juge peut contenir du texte autour du JSON : le premier objet {...} est lu.
Affiche le detail et ecrit la note finale sur la derniere ligne.
"""
import argparse, json, math, re, sys

WEIGHTS = {1: 0.25, 2: 0.10, 3: 0.15, 4: 0.15, 5: 0.10, 6: 0.15, 7: 0.10}  # 6 = appartenance au style (etalon), 7 = sujet + charme


def load_json(path):
    t = open(path, encoding="utf-8").read()
    i, depth = t.find("{"), 0
    for j in range(i, len(t)):
        depth += {"{": 1, "}": -1}.get(t[j], 0)
        if depth == 0:
            return json.loads(t[i:j + 1])
    raise SystemExit(f"pas de JSON dans {path}")


def norm(s):
    s = s.lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ô", "o"), ("î", "i")):
        s = s.replace(a, b)
    return s


def judge_score(j, syn, cousins):
    notes = {int(c["id"]): float(c["note"]) for c in j["criteres"]}
    s = sum(WEIGHTS[k] * notes.get(k, 5) for k in WEIGHTS) + float(j.get("pose", 0) or 0)
    lu = norm(str(j.get("animal_lu", "")))
    log = [f"ponderee+pose {s:.2f}"]
    words = set(re.findall(r"[a-z]+", lu))
    pen = 0.0
    if words & syn:
        lecture = "bon"
    elif words & cousins:
        lecture = "cousin"; pen += 1; log.append("cousin -1")
    else:
        lecture = "faux"
    if j.get("autre_lecture_dominante"):
        lecture = "faux"; log.append(f"autre lecture dominante « {j.get('autre_lecture', '')} »")
    if j.get("teinte_criarde"):
        pen += 1.5; log.append("teinte criarde -1,5")
    s -= min(pen, 1.5)  # penalites non cumulables au-dela de 1,5
    s = math.floor(s * 2) / 2
    caps = []
    if lecture == "faux":
        caps.append((2, f"animal lu « {j.get('animal_lu', '')} » : 2 max"))
    if j.get("bruit_dominant"):
        caps.append((3, "bruit dominant : 3 max"))
    if j.get("oeil_plat") or j.get("bouche_absente"):
        caps.append((4.5, "oeil en tiret/carre plat ou bouche absente : 4,5 max"))
    if s > 6.5 and not str(j.get("depasse_ancre", "")).strip():
        caps.append((6.5, "au-dessus de l'ancre 6,5 sans preuve : 6,5 max"))
    if s > 7 and not str(j.get("depasse_orange", "")).strip():
        caps.append((7, "pas nettement meilleur que le crapaud orange (6,75) : 7 max"))
    if s >= 8 and (notes.get(1, 0) < 8 or notes.get(4, 0) < 8):
        caps.append((7.5, "criteres 1 et 4 < 8 : 7,5 max"))
    for c, why in caps:
        if s > c:
            s = c
        log.append(why)
    return max(0.0, s), lecture, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="append", required=True)
    ap.add_argument("--measure")
    ap.add_argument("--animal", default="crapaud")
    ap.add_argument("--synonyms", default="crapaud,crapauds,toad")
    ap.add_argument("--cousins", default="grenouille,frog,batracien,amphibien,rainette")
    a = ap.parse_args()
    syn = {norm(x) for x in a.synonyms.split(",")} | {norm(a.animal)}
    cousins = {norm(x) for x in a.cousins.split(",")}
    scores = []
    for p in a.judge:
        s, lecture, log = judge_score(load_json(p), syn, cousins)
        scores.append(s)
        print(f"{p}: {s} (lecture {lecture} ; {', '.join(log)})")
    final = min(scores)
    if a.measure:
        cap = json.load(open(a.measure, encoding="utf-8")).get("plafond", 10)
        if final > cap:
            print(f"plafond objectif {cap}")
        final = min(final, cap)
    print(f"juges {' / '.join(str(x) for x in scores)} -> note finale {final}")


if __name__ == "__main__":
    main()
