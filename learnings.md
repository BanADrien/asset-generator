# Lecons apprises (relire au debut de chaque utilisation, ajouter a la fin de chaque essai)

Format : date - sujet - ce qui a fait monter (+) ou baisser (-) la note - regle a retenir.

- 2026-11-16 - mise en place - (-) `AIO Pixel Art` (SD1.5) donne un vrai rendu pixel mais
  ignore le sujet (crapaud -> personnage debout). (+) `AlbedoBase XL (SDXL)` suit « side view,
  profile facing right, white background ». Regle : generer propre en SDXL, pixeliser ensuite.
- 2026-11-16 - mise en place - SDXL tourne parfois le sujet vers la gauche malgre le prompt :
  regarder la graine, utiliser `--flip` plutot que regenerer.
- 2026-11-16 - crapaud essai 1 (3,5/10) - (-) prompt « cel shading » seul : SDXL rend une
  figurine 3D pale ; pixel-fixer + palette a 24 px perd l'oeil et la bouche, grain de
  peinture (bruit 60 %), ombre portee grise gardee. Regle : detourer l'ombre grise, aplats HD
  (filtre median + 12 couleurs) avant reduction.
- 2026-11-16 - crapaud essai 2 (3/10) - (+) « 2d side-scrolling / pixel art sprite, flat
  cartoon » donne des illustrations plates. (-) le modele tourne le sujet de face malgre
  « side view » ; olive pale -> jaune-ocre a la palette. Les mesures passent (plafond 10) mais
  les juges voient une brique : la lisibilite se juge a l'oeil, pas au script.
  Regle : choisir la graine dont la tete pointe vraiment de cote ; reduction `--method cells`
  (majorite par cellule + priorite aux sombres) garde oeil, bouche et contour bien mieux que
  pixel-fixer a cette taille ; palette completee par une rampe olive (4a4a1c, 6e6b2c, 9a9645,
  c4bf5c, e0dc8a) et un jaune d'oeil (d9a521, f5d24a).
- 2026-11-16 - crapaud essai 3 (4/10) - (+) reduction par cellules : silhouette et ventre
  lisibles. (-) prompt long (> 77 jetons CLIP) : la fin est ignoree, pose de 3/4, fond sombre.
- 2026-11-16 - crapaud essai 4 (4,5/10, meilleur) - (+) prompt COURT, sujet + vue en tete :
  sources propres, gros oeil jaune, fond blanc. (-) le sujet regardait a gauche (3/4) ; l'oeil
  de 4 px devient un paquet noir. Regle : prompt de 30-45 mots ; verifier le sens sur `raw/`.
- 2026-11-16 - crapaud essais 5-6 (4 puis 3) - (-) pousser la saturation fait virer l'olive au
  jaune ; « huge eye » ne change rien, SDXL garde le 3/4 ; l'oeil reste illisible a 24 px.
  Limite actuelle : la reduction automatique ne fabrique pas un oeil, une bouche, une patte
  lisibles a 24 px. Piste suivante : cible plus haute (30-32 px) validee par l'utilisateur,
  ou image source en silhouette tres simple (« flat icon, 3 colors »), ou retouche manuelle.
- 2026-11-16 - mise en place - Pollinations anonyme : 1 image/min, 402 au-dela, logo en bas
  a droite ; AI Horde anonyme : 2 travaux en parallele max (429 sinon).
