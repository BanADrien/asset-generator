# Grille de notation stricte (sur 10) - v3 : nettete et lisibilite d'abord

But : une note qui ne flatte pas et qui suit le gout REEL de l'utilisateur, appris de ses
notes (`calibration/calibration.md`) : il recompense ce qui est NET et LISIBLE, il punit le
BRUIT. Un 8 doit pouvoir etre montre sans excuse. Ordre : A (script), B (deux juges
separes), C (calcul).

## A. Mesures objectives - `scripts/measure.py --profile petit|detaille`
| Test | Seuil | Pourquoi |
|---|---|---|
| hors_palette | 0 px | coherence de couleur avec le jeu |
| semi_transparents | 0 px | halos sur fond sombre |
| pixels_isoles | 0 px | poussiere |
| **salissure** | <= 25 % (petit) / <= 15 % (detaille) des px en taches de 1-2 px | suit son gout : sprites propres ~10 %, sprites sales 20 % et plus |
| orphelins_couleur | <= 12 % (petit) / <= 18 % (detaille) | bruit d'IA |
| couverture_contour | >= 85 % du bord dans le tiers sombre | silhouette fermee |
| silhouette_un_bloc | <= 2 px detaches (petit) / <= 6 (detaille) | lisibilite |
| remplissage_silhouette | 35-92 % de la boite | ni baton, ni brique |
| contraste_valeurs | ecart L* >= 45 | lecture sur fond nuit |
| bruit | <= 55 % (petit) / <= 65 % (detaille) de voisins differents | aplats et rampes |
| taille | hauteur ou largeur a 2 px de la cible du profil, jamais au-dessus | densite |
| couleurs_utilisees | 5-20 (petit) / 8-48 (detaille) | pixel art, pas peinture |
**Un seul echec => plafond 5/10.**

## B. Jugement visuel (juge separe, voir `judge-prompt.md`)
Chaque critere part de **5**. Chaque point au-dessus de 5 doit etre prouve par une observation
precise et verifiable (zone, couleur, nombre de pixels). Sans preuve, pas de point.

| # | Critere | Poids |
|---|---|---|
| 1 | **Nettete et lisibilite** : formes propres, aucun grain ni tache grumeleuse, parties distinctes d'un coup d'oeil (tete, yeux, bouche, ventre, pattes) | 35 % |
| 2 | **Contour defini** : contour exterieur sombre net et continu + separations interieures franches entre les parties | 15 % |
| 3 | **Volume et lumiere** : ombrage doux et regulier, une direction de lumiere, rampes de 3-4 valeurs, palette coherente | 20 % |
| 4 | **Detail propre et organise** : verrues en points nets, taches aux bords francs, yeux avec pupille, bouche tracee, doigts separes. Le bruit n'est JAMAIS du detail. | 15 % |
| 5 | **Sujet reconnaissable et charme** : on dit « crapaud » a froid ; il est plaisant, prefere ou non au sprite IA actuel | 15 % |

Pose (critere mineur, jamais de plafond) : l'utilisateur prefere « une pose a 4 pattes comme
un crapaud normal » mais la juge « moins redhibitoire ». Pose naturelle de l'animal (crapaud
accroupi sur ses 4 pattes, profil ou 3/4) : **+0,5** sur la note juge. Pose debout de type
« bonhomme » : **-0,5 a -1**, pas plus. De face, 3/4, orientation gauche/droite : neutre.
La nettete passe avant la pose : un crapaud net debout bat un crapaud a 4 pattes bruite.
Un aplat propre vaut mieux qu'une texture sale ; propre mais plat et simpliste reste faible
(critere 3 et 4 bas).

### Ancres (images reelles notees par l'utilisateur)
Ouvrir les images `calibration/*-x8.png` listees dans le prompt du juge, avec leur note
utilisateur, et situer le candidat par rapport a elles. Ce qu'elles enseignent :
- ~1,5-2 : sujet non reconnaissable, OU masse sale (marbrures grumeleuses, faux oeil), OU
  propre mais plat et simpliste.
- ~3-4 : reconnaissable mais brouille (taches en salissure, parties fondues) ou pauvre.
- ~5-5,5 : propre, rond, aplats nets, mais petit (24-30 px) et peu de detail.
- ~6,5 : formes propres, contour net, ombrage doux, parties distinctes, a 60 px (son meilleur).
- 8 : tout cela PLUS du detail propre (yeux dessines, bouche, verrues nettes, doigts), aucun
  pixel parasite au zoom, nettement prefere au sprite IA actuel.
- 9-10 : niveau d'un pixel artiste professionnel. A ne presque jamais donner.

## C. Calcul de la note
1. Note juge = somme ponderee des 5 criteres + ajustement de pose (+0,5 / 0 / -0,5 a -1),
   arrondie a 0,5 pres vers le bas.
2. Sujet non reconnaissable a la lecture a froid : **2 maximum**.
3. Bruit ou salissure dominant (taches grumeleuses sur une grande partie du corps) : **3 maximum**.
4. 8 ou plus exige criteres 1 et 4 >= 8 ; sinon plafond 7,5.
5. Deux juges independants ; **on garde la plus basse** des deux notes.
6. Note finale = min(note retenue, plafond objectif de A).
7. Seuil de livraison : **8/10**. En dessous, on corrige et on recommence.

Historique (sans notes d'images, pour ne rien souffler aux juges) : v1 densite des tuiles,
v2/v2.1 volume et « texture » a 25 % (recompensait une texture sale), v3 nettete d'abord,
bruit plafonne, pose mineure, mesure « salissure » calee sur les notes de l'utilisateur.
Resultats de validation : `calibration/calibration.md`.
