# Grille de notation stricte (sur 10) - v2.1, calee sur le gout de l'utilisateur

But : une note qui ne flatte pas et qui suit le gout de l'utilisateur (« detaille,
realiste »). Un 8 doit pouvoir etre montre sans excuse. Ordre : A (script), B (deux juges
separes), C (calcul). Calage et ancres : `calibration/calibration.md`.

## A. Mesures objectives - `scripts/measure.py --profile petit|detaille`
Tests de proprete (tous profils) :
| Test | Seuil | Pourquoi |
|---|---|---|
| hors_palette | 0 px | coherence de couleur avec le jeu |
| semi_transparents | 0 px | halos sur fond sombre |
| pixels_isoles | 0 px | poussiere |
| orphelins_couleur | <= 12 % (petit) / <= 18 % (detaille) | bruit d'IA |
| couverture_contour | >= 85 % du bord dans le tiers sombre | silhouette fermee |
| silhouette_un_bloc | <= 2 px detaches (petit) / <= 6 (detaille) | lisibilite |
| remplissage_silhouette | 35-92 % de la boite | ni baton, ni brique |
| contraste_valeurs | ecart L* >= 45 | lecture sur fond nuit |
| bruit | <= 55 % (petit) / <= 65 % (detaille) | aplats et rampes, pas de grain |
Tests qui dependent du profil :
| Test | petit (24-30 px) | detaille (~64 px) |
|---|---|---|
| taille | hauteur ou largeur a 2 px de la cible, jamais au-dessus | idem (cible du profil) |
| couleurs_utilisees | 5-20 | 8-48 (minimum 12 corrige a 8 le 16/11 : la palette du jeu donne 10-11 couleurs sur un crapaud propre) |
**Un seul echec => plafond 5/10.**

## B. Jugement visuel (juge separe, voir `judge-prompt.md`)
Chaque critere part de **5**. Chaque point au-dessus de 5 doit etre prouve par une observation
precise et verifiable (zone, couleur, nombre de pixels). Sans preuve, pas de point.

### Les trois exigences de l'utilisateur (a verifier EN PREMIER, reussi / moyen / echec)
Ses mots : « les contours sont pas definis, y a peu de texture, on distingue mal les elements ».
- **CONTOURS DEFINIS** : contour exterieur net et continu, ET separations interieures entre
  les parties (tete / corps / pattes / ventre) tracees par une ligne ou une rupture de valeur
  franche.
- **TEXTURE** : matiere de peau visible (verrues, taches, marbrures organisees, pas du bruit).
  Un aplat lisse est penalise.
- **ELEMENTS DISTINCTS** : on peut montrer du doigt l'oeil, la bouche, chaque patte, le ventre.
  Des parties fondues en une masse font baisser la note.
Elles nourrissent les criteres 1 (texture), 2 (elements distincts) et 4 (contours).

| # | Critere | Poids |
|---|---|---|
| 1 | Volume, matiere et richesse de detail (rondeur credible, peau, plis, verrues, 3-4 valeurs par matiere, lumiere) | 25 % |
| 2 | Silhouette et lecture du sujet (on reconnait l'animal et sa pose ; tete, corps, pattes distincts) | 20 % |
| 3 | Fidelite au sujet demande (anatomie, comptes, details signature : oeil, bouche...) | 15 % |
| 4 | Proprete pixel (lignes regulieres, pas de damier ni de poussiere, groupes >= 2 px) | 15 % |
| 5 | Charme et superiorite sur le sprite IA actuel du meme sujet | 15 % |
| 6 | Appartenance au jeu : a cote des PERSONNAGES actuels (sprites detailles), meme univers, palette, contour | 10 % |

Ce qui n'est PAS un defaut : l'orientation gauche/droite (le script retourne le sprite) et un
3/4 leger. Ne rien retirer pour cela.

### Ancres (images reelles notees par l'utilisateur)
Ouvrir les images `calibration/*-x8.png` listees dans le prompt du juge, avec leur note
utilisateur, et situer le candidat par rapport a elles. Resume de ce qu'elles enseignent :
- ~1,5-2 : sujet non reconnaissable (brique vue de face), ou propre mais plat et simpliste.
- ~4 : animal reconnaissable mais pauvre en volume, ou masse credible tres brouillee.
- ~5-5,5 : masse ronde et credible, matiere nuancee (olive marbree), meme si l'oeil est
  illisible. C'est le meilleur obtenu a 24-30 px ; l'essai 6 (peau marbree, verrues) est le
  PREFERE de l'utilisateur, devant l'essai 4 a note egale : la texture departage.
- 8 : volume et matiere au moins aussi riches que les personnages actuels du jeu, oeil et
  bouche lisibles, aucun pixel parasite au zoom, nettement prefere au sprite IA actuel.
- 9-10 : niveau d'un pixel artiste professionnel. A ne presque jamais donner.

## C. Calcul de la note
1. Note juge = somme ponderee des 6 criteres, arrondie a 0,5 pres vers le bas.
2. Sujet non reconnaissable a la lecture a froid (on ne dit pas « crapaud/grenouille ») ou
   forme plate de face sans tete ni pattes : **2 maximum**.
3. Oeil ou bouche absents : -1 a -1,5 sur le critere 3 (fidelite), sans plafond global.
4. 8 ou plus exige criteres 1 et 5 >= 8 ET les trois exigences (contours, texture,
   elements) reussies ; sinon plafond 7,5. Echec net sur deux des trois exigences : **6 maximum**.
5. Deux juges independants ; **on garde la plus basse** des deux notes.
6. Note finale = min(note retenue, plafond objectif de A).
7. Seuil de livraison : **8/10**. En dessous, on corrige et on recommence.

Historique : v1 (16/11/2026) jugeait la densite des tuiles a 25 % et plafonnait a 5 tout
critere <= 3 ; elle sous-notait le volume et la matiere (ecart moyen 0,92 avec l utilisateur, 2,5 sur l essai 6).
v2 (meme jour) : volume/matiere 25 %, ancres = images notees ; validation : ecart moyen 0,58,
essai 2 dernier, essai 6 encore sous-note de 1,5. v2.1 : ajout des trois exigences dites par
l utilisateur (contours, texture, elements distincts) et de sa preference pour l essai 6.
