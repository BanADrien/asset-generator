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

## Profil detaille (~64 px) : NET d'abord (grille v3, gout reel de l'utilisateur)
- Prompt (meilleur a ce jour, 6,5/10) : `clean cel-shaded 2d game sprite of a <sujet> <pose
  naturelle, ex. crouching on four legs>, three-quarter side view, bold dark outline, flat
  colors, soft shading, simple readable shapes, <yeux avec pupille>, <bouche>, <peau> with neat
  round warts, <ventre>, white background`.
  Negatif : `noisy, grainy, mottled, dirty, speckled, standing upright, text, watermark,
  scenery, ground, shadow, 3d render, photo` (+ `frog, smooth skin, bright green` pour un crapaud).
- A eviter : « textured / marbled / heavily textured skin » (donne de la salissure, notee 2-3).
- LoRA pixel art SDXL : `--lora 120096:0.8` (Pixel Art XL, gratuit via AI Horde) : sources en
  vrai pixel art, yeux et doigts dessines ; meme note que sans LoRA au premier test.
- Reduction : `--profile detaille` = cellules en 2 passes, palette du jeu des la HD, fusion des
  taches de 1-2 px, contour exterieur. `--method pixel-fixer` garde plus de grain : a eviter
  sauf comparaison.
- Toujours regarder les sprites a grossissement entier (x4, x8).

## Retouche d'image (img2img) : METHODE PAR DEFAUT des qu'il existe une image de base
Principe : « garder le champion, corriger un defaut a la fois ». On part d'une image deja
bonne (l'etalon de style `style/etalon-style.png`, le sprite actuel du jeu, ou le meilleur
essai precedent) et on la retouche au lieu de retirer au hasard (le texte -> image derive :
tortue, grenouille, bonhomme).
- `forge_try.py ... --source <image> --denoise 0.3-0.6` (AI Horde : `source_image` +
  `source_processing: img2img` + `denoising_strength`, accepte avec la cle de compte).
  0,3 garde presque tout (nettoyage, couleurs) ; 0,45-0,5 redessine en gardant l'anatomie ;
  0,55-0,6 change la pose. Si l'essai degrade la base, BAISSER le denoising.
- Prompt = le STYLE voulu (celui de l'etalon : « pale olive, cream belly, soft simple shading,
  few colors, clean shapes, bold dark outline ») + la correction visee (yeux dessines,
  verrues nettes, 4 pattes...). Negatif : bruit, couleurs criardes, autres animaux evoques.
- Essai suivant : prendre comme `--source` l'image HD (`seedX.hd.png` ou `raw/seedX.webp`)
  du meilleur essai et corriger SON defaut principal releve par les juges.
- ControlNet (`--control canny|hed|depth`) : forme imposee par la base, seulement avec un
  modele SD 1.5 (ex. `--model Deliberate`) ; voir learnings.md pour l'essai.
