# Generation : moteur, prompt, corrections

## Moteurs (gratuits, sans compte, rien a installer)
- **AI Horde** (defaut) : `--engine horde`, modele `AlbedoBase XL (SDXL)` en 768 px. Suit bien
  « side view / profile / white background ». Cle anonyme publique, 2 travaux a la fois,
  30 s a 3 min par image selon la file. Autres modeles possibles : `Juggernaut XL`,
  `AIO Pixel Art` (vrai rendu pixel mais suit mal le sujet : a eviter pour un animal precis).
- **Pollinations** (secours) : `--engine pollinations`. Palier anonyme : ~1 image par minute
  (HTTP 402 sinon : le script attend), logo en bas a droite (masque automatiquement : garder
  le sujet centre), modele unique `sana`.
- Ne jamais payer, ne jamais creer de compte, n'envoyer que la description du sprite.

## Recette de prompt (anglais, SDXL)
`2d side-scrolling platformer game sprite, <sujet precis> in perfect side profile, looking
right, <pose>, flat 2d cartoon, <detail signature agrandi : "one big round yellow eye...">,
<2-3 couleurs de palette en mots>, flat colors, three tone shading, thick dark outline,
chunky simple shapes, plain flat white background, centered, no shadow`
(« cel shading » seul donne une figurine 3D pale ; « 2d ... flat cartoon » donne des aplats.)
Negatif : `text, watermark, signature, frame, border, scenery, ground, grass, cast shadow,
multiple animals, cropped, front view, three-quarter view, blurry, photo, realistic fur
texture, gradient background`
- Les couleurs viennent du guide (brun-olive, vert mousse, creme, violet nuit...) : la
  palette du jeu sera imposee a la pixelisation, mais partir de teintes proches evite les
  virages de couleur.
- « pixel art » dans le prompt SDXL donne souvent un faux pixel (grille irreguliere) : on
  prefere une image propre en aplats (cel shading) et c'est pixel-fixer qui pixelise.

## Pixelisation (scripts/pixelize.py -> pixel-fixer)
- Avant reduction : detourage, ombre grise retiree, aplats HD (`--simplify 12` couleurs).
- `--method cells` (defaut) : couleur majoritaire par cellule, un sombre qui couvre >= 28 %
  de la cellule gagne (garde pupille, bouche, contour). `--method pixel-fixer` : outil de
  l'utilisateur, meilleur pour les grands sprites ; a 24 px il perd les petits traits.
- `--height` / `--width` : taille cible du guide (le sujet tient dans la boite).
- `--detail 1..5` (pixel-fixer seulement, defaut 3) : 2 = plus simple, 4 = plus fidele.
- `--outline selective|darkest|none` ; `--flip` si le sujet regarde a gauche ;
  `--bg-tol` 30-60 si le detourage mange le sujet (baisser) ou laisse le fond (monter).

## Table symptome -> correction (une variable a la fois)
| Defaut vu | Correction a essayer |
|---|---|
| Sujet faux / mauvaise vue | prompt : preciser l'anatomie et « strict side view », autre graine |
| Bruit, orphelins, trop de couleurs | `--detail 2`, prompt « flat cel shading, simple shapes » |
| Bouillie a 1x, details perdus | agrandir la cible de 2-4 px (dans la limite du guide) ou simplifier le sujet |
| Contour ouvert / clair | `--outline selective` ou `darkest` |
| Ombre portee collee aux pattes | negatif « cast shadow », `--bg-tol` plus haut |
| Couleurs qui virent (vert -> gris) | nommer les teintes de la palette dans le prompt |
| Volume plat | prompt « strong top-left light, three tone shading » |
| Detourage qui mange le sujet clair | fond « plain pure white » -> essayer « plain light grey background » + `--bg-tol 30` |

## Profil detaille (~64 px) : viser les trois exigences de l'utilisateur
- Prompt : `pixel art sprite, side view of a <sujet>, profile, <pose>, bold inked outlines,
  clearly separated head, belly and legs, textured <matiere> skin, <couleurs>, <oeil>, white
  background` ; negatif + `smooth plastic skin, blurry`.
- Reduction : `--profile detaille` (cellules en 2 passes, 40 couleurs d'aplats, contour
  exterieur). `--method pixel-fixer` garde plus de texture et de lignes interieures a cette
  taille ; comparer les deux sur la meme image (`--reuse`) et garder le meilleur.
- Point de depart de forme : l'essai 6 du crapaud (masse ronde, peau marbree), prefere de
  l'utilisateur.
