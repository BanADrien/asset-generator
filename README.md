# pixel-art-forge

Skill Claude Code qui fabrique des sprites pixel art pour le jeu Legend of Agarica : Codex
genere des images brutes en pixel art (6 par essai), `grid_reduce.py` en tire le sprite natif
(1 case = 1 pixel, palette propre de l'image), puis mesures automatiques et deux juges separes
cales sur les notes de l'utilisateur. La boucle recommence jusqu'a 8/10 (4 essais au plus) et
livre le sprite, la planche historique des essais notes et une fiche de notes. Les lecons de
chaque utilisation s'ajoutent a `learnings.md`.

Mode « sections » : pour un sprite existant, `scripts/sections.py` produit une version neutre
(couleurs de base en aplats), une carte de sections (zones en couleurs franches, retouchables a
la main) et une carte de normales quantifiee, pour un eclairage dynamique en paliers dans le jeu
(Phaser 3, Light2D) ; `scripts/viewer.py` en fait une page de test autonome ou l'on deplace une
lumiere. Detail et integration : `references/lumiere.md`. Alternative manuelle gratuite : Laigter.

Tester n'importe quelle image : ouvrir `vos-images-lumiere.html` et glisser l'image. La page se
produit avec `node scripts/js/apercu.js --vide` (Node, rien a installer) ; tout le calcul se fait
dans la page (meme resultat que `sections.py`, au pixel pres), rien n'est envoye sur Internet.
Verification : `node scripts/js/test-page.js` (Chrome ou Edge sans fenetre).

## Installer sur un autre PC
    git clone https://github.com/BanADrien/asset-generator.git ~/.claude/skills/pixel-art-forge
Claude Code le detecte au demarrage suivant (il se declenche sur « sprite », « pixel art »,
« asset du jeu », « agarica »...).

## Ce qu'il faut
- Node 18+ pour la page « vos images » (scripts/js), sans dependance.
- Python 3 avec Pillow (pas de numpy). Sur ce poste : le Python fourni avec pgAdmin, lance
  avec `-I`. Rien a installer.
- Codex (extension VS Code « openai.chatgpt » ou `codex` dans le PATH), connecte au compte de
  l'utilisateur ; le skill ne lit jamais ses fichiers d'identification.
- Optionnel (ancienne reduction, hors chemin par defaut) : pixel-fixer
  (https://github.com/BanADrien/pixel-fixer, Node 18+) pour `--method pixel-fixer`. Indiquer son chemin dans `config.local.json` (non versionne) :
  `{"pixel_fixer_cli": "C:/chemin/vers/pixel-fixer/cli.js"}` ou dans la variable
  `PIXEL_FIXER_CLI`. La reduction par defaut (`grid_reduce.py`) n'en a pas besoin.

## Contenu
- `SKILL.md` : la procedure suivie par Claude.
- `style/` : guide de style tire des assets du jeu, palette, planche d'exemples.
- `references/` : grille de notation, prompt des juges, conseils de prompt, sources.
- `scripts/` : generation, pixelisation, mesures, planches, historique, livraison ;
  `sections.py` et `viewer.py` (mode sections) ; `js/` : page « vos images » (copie du calcul
  `tools/lumiere/coeur.js` du jeu).
- `viewer/` : modele de la page de test d'eclairage.
- `calibration/` : sprites notes par l'utilisateur, ancres des juges (`calibration.md`).
- Profil par defaut `natif` (taille et palette de l'image generee) ; anciens profils `petit`
  et `detaille` (reduction 64 px + palette du jeu) gardes pour memoire.

## Licences des references
Les images de `references/img/` sont toutes en CC0 (domaine public) : Spring Spring,
ARoachIFoundOnMyPillow et Clint Bellanger (OpenGameArt), Kenney (kenney.nl). Detail et liens
dans `references/SOURCES.md`. Les exemples de `style/examples/` sont des copies reduites des
assets du jeu Legend of Agarica.
