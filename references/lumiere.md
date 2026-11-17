# Sprites en sections : eclairage dynamique (mode « sections »)

But : un sprite du jeu reagit a la lumiere sans filtre par-dessus. Pour chaque sprite :
- `<nom>.neutre.png` : couleurs de base en aplats (une couleur par matiere, prise dans la palette
  du sprite), sans ombre ni reflet dessines ; contour, traits sombres et oeil gardes tels quels ;
- `<nom>.normales.png` : carte de normales par zones (peu de directions, bords nets) ;
- `<nom>.sections.png` : les memes zones en couleurs franches, a retoucher a la main.
La lumiere s'applique par PALIERS (3-4 teintes), pas en degrade lisse : ca reste du pixel art.

## Commandes
    $py = "$env:LOCALAPPDATA\Programs\pgAdmin 4\python\python.exe"
    & $py -I scripts/sections.py W/crapaud.png --apercu           # neutre + sections + normales
    & $py -I scripts/sections.py W/crapaud.png --depuis-sections W/crapaud.sections.png  # apres retouche
    & $py -I scripts/viewer.py W/crapaud.png --echelle 6           # page autonome crapaud-lumiere.html
    # sprites HD du jeu (images peintes reduites par setScale) : ramener d'abord a la taille ecran
    & $py -I scripts/sections.py agarica/assets/sprites/loup_frames/loup_row0_0.png --echelle-jeu 0.4 --sortie W/loup
    # plusieurs assets dans UNE page (selecteur + « tous cote a cote ») :
    & $py -I scripts/viewer.py W/crapaud.png W/loup.png W/grizzly.png W/agarica.png --noms "Crapaud,Loup,Grizzly,Agarica" --out W/assets-lumiere.html
Options : `--garder dea019,fdfdfd` (couleurs a garder telles quelles), `--rampes "hex,hex;hex,hex"`
(forcer le regroupement des couleurs en matieres), `--gauche` (versions retournees pour un sprite
qui regarde a gauche, voir Phaser), `--apercu` (planche : origine, neutre, sections, eclaire a
gauche, eclaire a droite).

## Sprites HD du jeu (mode « image peinte », `--echelle-jeu`)
Les sprites actuels du jeu (loup, ours, Agarica...) sont des images peintes de 200-700 px, a
milliers de couleurs et bords semi-transparents, affichees reduites (`setScale`, constantes de
`src/entities/Player.js` : WOLF_SCALE 0,4, OURS_SCALE 0,34, HUMAN_SCALE 0,24). Methode retenue :
on travaille A LA TAILLE VUE EN JEU (rendu fidele, pixels nets ensuite a l'echelle 1) :
recadrage, reduction Lanczos (alpha premultiplie), alpha net, palette propre de 32 couleurs en
Lab (k-moyennes ; les couleurs rares tres differentes, comme un oeil vert, gardent leur teinte),
puis la meme chaine que le pixel art. `<sortie>.png` = ce sprite reduit (a charger dans le jeu
a l'echelle 1 a la place du HD, avec ses normales). Reglages propres a ce mode : ombrage
d'origine moins suivi, nettoyage des zones plus fort. Une rampe ne couvre pas plus de 48 de
luminosite (L*) : peau claire, tunique beige et pantalon restent des matieres separees.
Travailler sur l'image HD d'origine donnerait des zones trop fines, perdues a la reduction.

## Comment le decoupage est fait
1. Matieres : les couleurs voisines dans l'image, de meme teinte et meme saturation relative,
   forment une rampe (corps olive, gorge creme, taches brun-rouge). Neutre = couleur de la
   palette la plus proche de la moyenne de la rampe ; grains isoles de 1-2 px absorbes.
2. Parties : les traits sombres interieurs (epaissis d'1 px pour fermer les fuites) et les
   changements de matiere de surface coupent la silhouette (cuisse, gorge, patte, tete-dos...).
   Les taches sont un motif : elles ne coupent pas.
3. Orientation de chaque pixel = volume d'ensemble (silhouette floutee : le dos regarde en haut,
   le ventre en bas) + bombe de sa partie (la partie floutee seule) + ombrage d'origine (clair =
   tourne vers la lumiere d'origine en haut a gauche). Puis quantification sur 17 sections,
   filtre majoritaire dans chaque partie, zones de moins de 6 px fondues : bords nets.
4. Contour exterieur : rasant, tourne vers l'exterieur. Traits interieurs et oeil : section voisine.

## Table sections -> normales
Normales : R = x (droite), G = y (HAUT, convention OpenGL, celle du Light2D de Phaser 3),
B = z (vers le spectateur) ; decodage n = rgb / 255 * 2 - 1. Incline = 40 degres, rasant = 68.
Pour retoucher `sections.png`, peindre avec ces couleurs exactes (la couleur la plus proche est
prise de toute facon), sans antialiasing, puis `--depuis-sections`.

| Section | Couleur dans sections.png | Normale (R, G, B) |
|---|---|---|
| face | #c8c8c8 | (128, 128, 255) |
| droite incline | #fa7070 | (209, 128, 225) |
| haut-droite incline | #fad870 | (185, 185, 225) |
| haut incline | #b5fa70 | (128, 209, 225) |
| haut-gauche incline | #70fa93 | (70, 185, 225) |
| gauche incline | #70fafa | (46, 128, 225) |
| bas-gauche incline | #7093fa | (70, 70, 225) |
| bas incline | #b570fa | (127, 46, 225) |
| bas-droite incline | #fa70d8 | (185, 70, 225) |
| droite rasant | #9e0808 | (246, 128, 175) |
| haut-droite rasant | #9e7908 | (211, 211, 175) |
| haut rasant | #539e08 | (128, 246, 175) |
| haut-gauche rasant | #089e2d | (44, 211, 175) |
| gauche rasant | #089e9e | (9, 128, 175) |
| bas-gauche rasant | #082d9e | (44, 44, 175) |
| bas rasant | #53089e | (127, 9, 175) |
| bas-droite rasant | #9e0879 | (211, 44, 175) |

Meme famille de teinte = meme direction (clair = incline, fonce = rasant).

## Si le neutre automatique est mauvais
1. Forcer les matieres (`--rampes`) ou garder des couleurs (`--garder`).
2. Secours : UNE generation Codex au plus (methode de `prompting.md` : binaire de l'extension,
   dossier vide, bac a sable), image jointe = le sprite, demande « le meme sprite, memes pixels et
   meme silhouette, couleurs de base en aplats, sans ombres ni reflets », puis `grid_reduce.py`.
   Ne l'utiliser que si la silhouette est identique au pixel pres (comparer les alphas).
3. Alternative manuelle gratuite : Laigter (generateur de cartes de normales pour sprites 2D,
   reglages a la main, apercu de lumiere) ; garder alors nos paliers cote jeu.

## Page de test
`<nom>-lumiere.html` ou, pour plusieurs assets, `assets-lumiere.html` (selecteur d'asset et case
« tous cote a cote » : meme echelle, meme lumiere, poses sur le meme sol, tailles relatives du
jeu). Autonome, double-clic, Chrome : le sprite au centre a echelle entiere,
lumiere a glisser (souris ou doigt), WebGL sans bibliotheque. Reglages : hauteur, intensite,
portee, ambiante, couleur (torche, lune, blanc), paliers 2-5 ou lisse, 2e lumiere, affichage du
sprite d'origine / des sections / des normales a la place. Adresse : `#l=0.1,0.3` (lumiere au
depart, fraction de la boite affichee), `&a=2` (asset), `&tous`, `&m=2` (affichage).

## Dans le jeu (Phaser 3.80.1, charge par CDN dans index.html d'agarica)
Light2D existe en 3.80 : carte de normales jointe a la texture, lumieres de scene.

    // preload : [image, carte de normales]
    this.load.image('crapaud', ['assets/sprites/crapaud.neutre.png', 'assets/sprites/crapaud.normales.png']);
    // planche d'animation : this.load.spritesheet({ key, url, normalMap, frameConfig })

    // create
    this.textures.get('crapaud').setFilter(Phaser.Textures.FilterMode.NEAREST); // aussi la carte de normales
    const crapaud = this.add.sprite(x, y, 'crapaud').setPipeline('Light2D');     // echelle 1 (ou x2, x3 entiers)
    this.lights.enable().setAmbientColor(0x55506a);
    const torche = this.lights.addLight(px, py, 180, 0xffb35c, 1.2); // x, y, rayon, couleur, intensite
    // deplacer : torche.setPosition(x, y) a chaque update

Points a savoir en 3.80 :
- Le jeu filtre en lineaire par defaut : forcer NEAREST sur ces textures (setFilter ci-dessus).
- La hauteur de lumiere est fixe dans le shader Light2D (z = 0,1) ; pas de reglage par lampe.
- `flipX` ne retourne pas les normales (le rouge n'est pas inverse) : pour un sprite tourne a
  gauche, charger aussi `--gauche` (`crapaud.neutre-gauche.png` + `crapaud.normales-gauche.png`)
  sous une autre cle et changer de texture au lieu de flipX.
- Nombre de lumieres : 10 par defaut (`render: { maxLights }` dans la config du jeu).
- Tout objet qui doit etre eclaire doit avoir le pipeline Light2D (sinon il reste plein jour).

### Paliers (pixel art) : pipeline derive de Light2D
Light2D eclaire en degrade lisse. Pour des paliers, copier le shader de la 3.80.1
(`src/renderer/webgl/shaders/Light-frag.js`, sur cdn.jsdelivr.net/npm/phaser@3.80.1/) dans le
jeu (le build ne l'expose pas), et dans la boucle des lumieres remplacer l'ajout a `finalColor`
par une version arrondie :

    float e = attenuation * diffuseFactor;                 // 0..1
    e = min(floor(e * 4.0), 3.0) / 3.0;                    // 4 paliers
    finalColor += light.color * e * light.intensity;

puis :

    class PaliersPipeline extends Phaser.Renderer.WebGL.Pipelines.LightPipeline {
      constructor(game) { super({ game, fragShader: PALIERS_FRAG }); } // %LIGHT_COUNT% remplace par Phaser
    }
    // config du jeu : pipeline: { Paliers: PaliersPipeline }
    crapaud.setPipeline('Paliers');

C'est la meme formule que la page de test (paliers = floor(e x N) / (N - 1)).
