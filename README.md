# pixel-art-forge

Skill Claude Code qui fabrique des sprites pixel art pour le jeu Legend of Agarica : une
image est generee gratuitement (AI Horde, secours Pollinations, sans compte ni cle), puis
detouree, reduite a la densite des tuiles du jeu, ramenee a la palette du jeu, et notee sur
10 (mesures automatiques + deux juges separes). La boucle recommence jusqu'a 8/10, 6 essais
au plus, et livre le sprite, une planche comparative, l'historique des essais notes et une
fiche de notes. Les lecons de chaque utilisation s'ajoutent a `learnings.md`.

## Installer sur un autre PC
    git clone https://github.com/BanADrien/asset-generator.git ~/.claude/skills/pixel-art-forge
Claude Code le detecte au demarrage suivant (il se declenche sur « sprite », « pixel art »,
« asset du jeu », « agarica »...).

## Ce qu'il faut
- Python 3 avec Pillow (pas de numpy). Sur ce poste : le Python fourni avec pgAdmin, lance
  avec `-I`. Rien a installer.
- Acces Internet pour la generation (AI Horde / Pollinations, gratuits).
- Optionnel : une cle de compte AI Horde (gratuite) pour sortir de la file anonyme, tres lente
  aux heures chargees. La mettre dans `config.local.json` (non versionne), champ
  `horde_api_key`, ou dans la variable `AIHORDE_API_KEY`. Sans cle, le skill utilise la cle
  anonyme publique. La cle n'est jamais affichee ni ecrite dans les sorties.
- Optionnel : pixel-fixer (https://github.com/BanADrien/pixel-fixer, Node 18+ et `npm install`)
  pour `--method pixel-fixer`. Indiquer son chemin dans `config.local.json` (non versionne) :
  `{"pixel_fixer_cli": "C:/chemin/vers/pixel-fixer/cli.js"}` ou dans la variable
  `PIXEL_FIXER_CLI`. Sans lui, la reduction du skill (`--method cells`) suffit.

## Contenu
- `SKILL.md` : la procedure suivie par Claude.
- `style/` : guide de style tire des assets du jeu, palette, planche d'exemples.
- `references/` : grille de notation, prompt des juges, conseils de prompt, sources.
- `scripts/` : generation, pixelisation, mesures, planches, historique, livraison.
- `calibration/` : sprites notes par l'utilisateur, ancres des juges (`calibration.md`).
- Deux profils de taille : `petit` (24-30 px, densite des tuiles, par defaut) et `detaille`
  (~64 px, taille des personnages actuels).

## Licences des references
Les images de `references/img/` sont toutes en CC0 (domaine public) : Spring Spring,
ARoachIFoundOnMyPillow et Clint Bellanger (OpenGameArt), Kenney (kenney.nl). Detail et liens
dans `references/SOURCES.md`. Les exemples de `style/examples/` sont des copies reduites des
assets du jeu Legend of Agarica.
