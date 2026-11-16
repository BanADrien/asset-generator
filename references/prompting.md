# Generation (Codex) et reduction

## Generateur : Codex (seul generateur du skill)
- Valide par l'utilisateur : une image brute Codex a ete notee 7,25 (sa meilleure note).
- `scripts/generate.py` lance `codex exec` (binaire de l'extension VS Code
  `%USERPROFILE%\.vscode\extensions\openai.chatgpt-*\bin\windows-x86_64\codex.exe`, version la
  plus recente, sinon `codex` du PATH ; variable `CODEX_EXE` pour forcer) dans un dossier VIDE,
  bac a sable `workspace-write` limite a ce dossier, avec pour seule mission de generer des PNG.
  Ne jamais lire `~/.codex/auth.json` ni `config.toml`.
- Images jointes (`--ref`, passees en `-i`) : l'etalon de style `style/etalon-style.png` et,
  s'il existe, le sprite actuel du sujet dans le jeu (reference d'anatomie et de detail a depasser).
- QUOTA de l'utilisateur (« fais-les par 6 ») : **6 images par essai, 4 essais maximum par
  sprite**, arret des 8/10.
- **Essai 1 d'un nouveau sujet = 6 DIRECTIONS ARTISTIQUES** reellement differentes, nommees,
  qui varient style de dessin, forme/proportions ET palette (pas six verts olive). Un prompt et
  une generation Codex par direction (`generate.py --n 1`), sans image de reference commune : une
  reference tire tout vers le meme dessin ; ne la joindre qu'a la direction qui s'en reclame.
  Exemples de directions (crapaud, 16/11/2026) : mascotte ronde chibi ; anguleux stylise ;
  cartoon a caractere ; aventurier semi-debout assorti au heros ; creature de marais sombre ;
  totem minimal 5-6 couleurs.
- Essais suivants : creuser la ou les directions choisies par l'utilisateur.
  **Des l'essai 2 : 3 images partent du champion** (la
  meilleure image brute, jointe en premier, avec UN defaut a corriger) **+ 3 nouvelles
  propositions** (`forge_try.py --champion ... --fix-prompt-file ...`).
- AI Horde et Pollinations ont ete abandonnes le 16/11/2026 (voir learnings.md).

## CURSEUR DE REALISME (reglage central, 16/11/2026)
Sa zone est AU MILIEU. Trop stylise (totem 1, mascotte et cartoon 3) et trop realiste ou peint
(illustration naturaliste 4-5, bestiaire « too much ») sont tous deux penalises.
Zone cible : entre l'anguleux modele (6) et le pixel art propre realiste (7) : anatomie vraie
et couleurs naturelles, MAIS formes simplifiees en plans nets (2-3 valeurs par plan), peu de
couleurs (12-16), contour sombre franc, pas de rendu peint ni de texture grenue.
La PETITE TAILLE fait partie du style : plus le sprite est grand, plus Codex y met de detail
et plus ca fait « trop realiste ». Viser ~64-80 px de large pour un crapaud.
Chaque prompt doit placer l'image sur ce curseur (et ne pas resservir une image deja vue).

Formule de prompt qui marche pour la zone cible : « real toad anatomy and natural colors, but
SIMPLIFIED into clean cut planes with 2-3 values per plane, bold continuous dark outline, only
12 to 16 colors, no painterly rendering, no grainy texture » + « the toad is only about 64 big
pixels wide, each pixel a big clearly visible square ». Pas de langue sortie ni de pose
dynamique par defaut (refute : notes 3-4).

## Modele de prompt « nouvelles propositions » (anglais ; {N} remplace par le script)
```
Your ONLY task: use your built-in image generation tool to create {N} images, and save each one
as a PNG file in the current working directory, named seed1.png ... seed{N}.png. Do not write
code, do not install anything, do not run any other commands except what is strictly needed to
save the generated images. Do not access the network except for the image generation itself.

Subject: a pixel art sprite of a <SUJET> for a 2D side-scrolling platformer game.
Attached: Image 1 = style reference (copy its DRAWING STYLE: clean simple shapes, pale muted
natural colors, soft shading, crisp dark outline). Image 2 = current in-game sprite (anatomy
reference and level of detail to EXCEED).
Requirements:
- Real pixel art: regular square pixel grid, no anti-aliasing, no blur, no gradients, no
  dithering grain. The sprite about <H> pixels tall on its grid (see size rule below), shown
  upscaled with nearest-neighbor so every pixel is a crisp square.
- Plain pure white background, no ground, no shadow, no text, no frame; centered with margin.
- Pose: <POSE NATURELLE, ex. crouching on 4 legs, side or slight three-quarter view facing right>.
- Clean and readable above all: bold continuous dark outline, clearly separated parts.
- Eye well drawn (iris, pupil, small highlight, on the side of the head), mouth line.
- Details as neat organized shapes with crisp edges (not random specks).
- Soft regular shading from the top-left, 3-4 value ramps per color.
- Muted natural colors, no bright yellow, no neon, no saturated colors.
- It must clearly read as a <SUJET>, not <COUSINS ET CONFUSIONS A EVITER>.
(Modele d'un essai qui CREUSE une direction choisie. Pour l'essai 1 : un prompt par
direction, avec un bloc « ART DIRECTION » qui fixe style, forme et palette.)
When done, reply with just the list of saved file names.
```

## Modele « garder le champion » (3 images des l'essai 2)
```
Your ONLY task: ... create {N} images ... named seed1.png ... seed{N}.png (same rules).
Attached: Image 1 = a sprite you made before (the CHAMPION). Keep it: same pose, anatomy,
colors, clean dark outline. Image 2 = style reference. Image 3 = current in-game sprite.
Redraw image 1 correcting ONLY this defect: <UN DEFAUT, formule concretement : ex. the eye is
lost at game size - make it bigger: round golden iris ~1/8 of head height, thick black
horizontal pupil, one white highlight block, dark brow line>.
Keep the same regular pixel grid (about <H> px tall), no blur, no dithering, plain white
background. Muted natural colors. Make the {N} images slight variations of the correction.
When done, reply with just the list of saved file names.
```

## Taille demandee (grille de Codex)
Demander une grille adaptee a la taille EN JEU : le sprite natif s'affiche a l'echelle 1
(`pixelArt: true`). Repere crapaud : le natif de 84 x 62 s'integre ; le crapaud actuel fait
71 x 56 a l'ecran. Regle : hauteur de grille ~ hauteur a l'ecran du sprite actuel du sujet
(+10 % au plus). Voir `style/guide.md`.

## Reduction : `scripts/grid_reduce.py` (PAR DEFAUT)
- Detecte la grille de pixels de l'image Codex (meme irreguliere), 1 case = 1 pixel :
  resolution native, palette PROPRE de l'image (fusion des quasi-doublons, `--max-colors 32`),
  fond blanc relie au bord -> transparent, recadrage.
- Pas de palette du jeu, pas de taille imposee : l'ancienne reduction (64 px + palette du jeu,
  `pixelize.py`) coutait ~3 points (oeil en tiret, verrues en plaques, couleurs ternies). Elle
  reste disponible (`--profile petit|detaille --method cells`) mais hors du chemin par defaut.
- Controle : `measure.py --profile natif --raw BRUT.png` (fidelite au brut, frange blanche).
- Toujours regarder les sprites a grossissement ENTIER (x4, x6, x8).

## Table defaut -> correction a demander au champion (une a la fois)
| Defaut vu | Correction a demander |
|---|---|
| Oeil perdu ou en tiret a la taille du jeu | oeil plus grand et plus simple : iris rond, pupille epaisse, reflet, ligne de sourcil |
| Bouche absente | ligne de bouche sombre du museau jusque sous l'oeil |
| Taches ou verrues en carres plats / grain | moins de verrues, plus grosses, rondes, clair dessus et sombre dessous ; pas de petits points |
| Couleurs criardes | olive, olive-brun, creme ; pas de jaune vif ni de vert fluo |
| Lu comme un autre animal ou objet | renforcer l'anatomie typique du sujet ; supprimer l'element trompeur (ex. dos en dome a pois = tortue) |
| Pose « bonhomme » | pose naturelle de l'animal |
| Contour ronge ou flou | contour sombre continu de 1 case |
