# Grille de notation stricte (sur 10) - v3.2 : nettete, sujet juste, couleurs sobres, style etalon

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
Le juge NOTE ; les plafonds sont appliques par `scripts/score.py` a partir de ses champs
(`animal_lu`, `teinte_criarde`, `bruit_dominant`, `depasse_ancre`). Chaque critere part de
**5**. Chaque point au-dessus de 5 doit etre prouve par une observation precise (zone,
couleur, nombre de pixels). Sans preuve, pas de point.

| # | Critere | Poids |
|---|---|---|
| 1 | **Nettete et lisibilite** : formes propres, aucun grain ni tache grumeleuse, parties distinctes d'un coup d'oeil (tete, yeux, bouche, ventre, pattes) | 25 % |
| 2 | **Contour defini** : contour exterieur sombre net et continu + separations interieures franches | 10 % |
| 3 | **Volume et lumiere** : ombrage doux et regulier, une direction de lumiere, rampes de 3-4 valeurs | 15 % |
| 4 | **Detail propre et organise** : verrues en points nets, taches aux bords francs, OEIL bien dessine (iris, pupille, reflet, a sa place, pas un anneau vu de face sur un corps de 3/4), bouche tracee, doigts separes. Le bruit n'est JAMAIS du detail. | 15 % |
| 5 | **Harmonie des couleurs** : teintes naturelles, sobres, peu nombreuses, accordees. Jaune ou vert fluo/sature = note basse. | 10 % |
| 6 | **Appartenance au style** : comparaison DIRECTE avec l'image etalon `style/etalon-style.png` (formes propres et simples, couleurs pales et sobres, ombrage doux, contour net) | 15 % |
| 7 | **Sujet reconnaissable et charme** : on dit le bon animal a froid ; plaisant ; prefere ou non au sprite IA actuel | 10 % |

Champs a remplir par le juge (utilises par le calcul) :
- `animal_lu` : UN mot, l'animal qu'on nomme a la lecture a froid, AVANT de lire la demande.
- `autre_lecture` / `autre_lecture_dominante` : autre animal ou objet que le sprite evoque
  (tortue, champignon, pain, rocher...) ; `true` s'il saute aux yeux autant ou plus que le
  sujet (un joueur pourrait le nommer). -> 2 maximum.
- `teinte_criarde` : true si une teinte criarde (jaune/vert fluo, sature) domine le sprite.
- `bruit_dominant` : true si grain, taches grumeleuses ou marbrures sales couvrent une grande
  partie du corps.
- `oeil_plat` : true si l'oeil est reduit a un tiret ou a un carre plat (ni iris, ni pupille
  distincte). `bouche_absente` : true si aucune bouche n'est tracee. -> 4,5 maximum.
- `depasse_ancre` : vide, sauf si le sprite surpasse NETTEMENT l'ancre a 6,5 sur un point
  precis : le citer. Sans cela, la note est bornee a 6,5.
- `depasse_orange` : vide, sauf si le sprite est NETTEMENT meilleur que le crapaud orange
  actuel du jeu (ancre de qualite 6,75) : le justifier par ecrit. Sans cela, 7 maximum ; un 8
  exige de le surpasser nettement.

Pose (mineure, jamais de plafond) : naturelle a 4 pattes **+0,5** ; debout type « bonhomme »
**-0,5 a -1** ; face, 3/4, orientation : neutre. La nettete passe avant la pose.
Un aplat propre vaut mieux qu'une texture sale ; propre mais plat et simpliste reste faible.

### Ancres (images reelles notees par l'utilisateur)
Ouvrir les images `calibration/*-x8.png` listees dans le prompt du juge, avec leur note
utilisateur, et situer le candidat par rapport a elles, en comparant DIRECTEMENT avec l'ancre a
6,5 (son meilleur, encore « loin du compte »). Ce qu'elles enseignent :
- ~1,5-2 : sujet non reconnaissable ou lu comme un autre animal/objet, OU masse sale, OU
  propre mais plat et simpliste.
- ~3-4,5 : reconnaissable mais brouille, grain, ou couleurs criardes.
- ~5-5,5 : propre, aplats nets, couleurs sobres, mais oeil faible ou peu de detail.
- ~6,5 : formes propres, contour net, ombrage doux, couleurs pales et harmonieuses, parties
  distinctes : le meilleur genere, encore loin du compte (c'est aussi l'etalon de STYLE).
- ~6,75 : le crapaud orange actuel du jeu, ancre de QUALITE la plus haute.
- 8 : tout cela PLUS du detail propre (yeux bien dessines, bouche, verrues nettes, doigts),
  aucun pixel parasite au zoom, nettement prefere au sprite IA actuel.
- 9-10 : niveau d'un pixel artiste professionnel. A ne presque jamais donner.

## C. Calcul de la note (`scripts/score.py`)
1. Note juge = somme ponderee des 7 criteres + pose ; cousin proche lu (grenouille pour
   crapaud) -1 ; `teinte_criarde` -1,5 ; les deux ensemble : -1,5 ; arrondi a 0,5 vers le bas.
2. `animal_lu` faux (ni le sujet ni un cousin) ou `autre_lecture_dominante` : **2 maximum**.
3. `bruit_dominant` : **3 maximum** ; `oeil_plat` ou `bouche_absente` : **4,5 maximum**
   (une image propre qui a perdu son oeil a la reduction valait 4 pour l'utilisateur).
4. Au-dessus de 6,5 sans `depasse_ancre` : **6,5 maximum** ; au-dessus de 7 sans
   `depasse_orange` : **7 maximum**.
5. 8 ou plus exige criteres 1 et 4 >= 8 ; sinon 7,5 maximum.
6. Deux juges independants ; **on garde la plus basse**. Puis min avec le plafond objectif (A).
7. Seuil de livraison : **8/10**. En dessous, on corrige et on recommence.

Historique (sans notes d'images, pour ne rien souffler aux juges) : v1 densite des tuiles,
v2/v2.1 volume et « texture », v3 nettete d'abord et mesure « salissure », v3.1 sujet faux
plafonne par le calcul, harmonie des couleurs, borne a 6,5 sans preuve, oeil verifie ;
v3.2 autre lecture dominante, penalites non cumulables, style etalon, ancre orange.
Resultats de validation : `calibration/calibration.md`.
