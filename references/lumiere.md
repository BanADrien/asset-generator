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

## Sprites du jeu passes en pixel art par pixel-fixer (`--facteur f`) : CAS GENERAL
Depuis la branche `feature/demo-histoire` (11/2026), les sprites du jeu sont refaits en pixel art
par `tools/pixelfix.js` : l'image garde sa taille HD mais chaque pixel dessine est un bloc de `f` px,
`f` etant note dans `src/data/pixel_fixed.js` (ex. marche d'Agarica 3,76 ; loup 2,5 / 2,17 ;
grizzly 3,65-6,02 selon la frame ; crapaud 2,5). Les originaux IA sont dans
`assets/_pixelfix_originals/`. Le jeu les affiche sans lissage (NEAREST) a leur `setScale`.
`--facteur f` revient a la resolution NATIVE exacte : la grille est calee automatiquement (decalage
qui rend chaque case la plus uniforme), 1 case = 1 pixel (couleur du centre), couleurs de l'image
gardees telles quelles (pas de nouvelle palette). En animation, une seule grille pour toutes les
frames. Lire les fichiers du jeu avec git (`git show`, `git cat-file blob`) si le checkout est
incomplet ; ne rien modifier dans le depot du jeu.

    & $py -I scripts/sections.py frames_marche/ --animation --facteur 3.76 --fps 12 --vitesse 190 --sortie W/agarica-marche

Meme rampe, deux matieres : pixel-fixer donne une palette commune ou la peau et la tunique beige
partagent les memes couleurs. Les parties de chaque rampe (fermees par des traits) sont alors
classees en deux groupes par luminosite moyenne (2-moyennes, sur toutes les frames a la fois) ;
deux groupes a plus de 12 L* d'ecart et chacun >= 15 % de la rampe prennent chacun leur couleur
neutre (visage clair, tunique plus sombre), identique d'une frame a l'autre.

## Sprites HD non convertis (mode « image peinte », `--echelle-jeu`)
Pour une image encore peinte (absente de pixel_fixed.js). Ces images de 200-700 px, a
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

## Animation (`--animation`) : toutes les frames ensemble
    & $py -I scripts/sections.py agarica/assets/sprites/agarica_walk_frames --animation --echelle-jeu 0.24 --fps 12 --vitesse 190 --sortie W/agarica-marche
    & $py -I scripts/viewer.py W/agarica-marche.anim.json --regarde gauche --out W/agarica-marche-lumiere.html
Frames, ordre et vitesse : dans le code du jeu (`anims.create` : marche d'Agarica = agarica-walk-0..3,
frameRate 12, `AGARICA_WALK_FRAME_INDICES` de Player.js ; vitesse de marche moveMaxSpeed 190 px/s).
Pour que l'eclairage ne clignote pas :
- meme toile pour toutes les frames, calee en bas au centre (origine (0.5, 1) du jeu : pieds au
  meme niveau), meme cadrage (union des boites), meme reduction ;
- UNE palette calculee sur toutes les frames, et les matieres/sections calculees en une seule
  analyse sur une mosaique des frames (memes rampes, memes regles, memes seuils) ;
- lissage dans le temps : apres recalage global de la frame voisine (le corps monte et descend),
  un pixel qui garde la meme matiere prend la direction majoritaire sur sa frame et ses deux
  voisines (4 passes) ; une partie qui bouge vraiment change de matiere sous le pixel et garde
  sa propre orientation. Le script affiche le taux de changement avant/apres (marche
  d'Agarica : 38 % -> 15 %, le reste = cape et jambes qui bougent).
Sorties : `<nom>_N.png` (+ `.neutre`, `.normales`, `.sections`), `<nom>.planche.png` (une colonne
par frame : origine, neutre, sections, eclaire a gauche, a droite), `<nom>.anim.json` (frames, fps,
vitesse) que `viewer.py` lit : lecture/pause, frame par frame, vitesse, « marcher » (aller-retour
devant une lumiere fixe), « sens ».

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
portee, ambiante, profondeur de la lumiere (-60 derriere a +60 devant, 8 par defaut ; trop
grande devant, le sommet des formes s'assombrit quand la lampe est proche ; derriere : contre-jour,
point lumineux cache par la silhouette ; reglage « Contre-jour » : les sections du bord
s'allument, de plus en plus loin avec la portee), couleur
(torche, lune, blanc), paliers 2-5 ou lisse, 2e lumiere, affichage du
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
- PROFONDEUR de la lumiere : Light2D la fixe a z = 0,1 x petit cote de l'ecran, soit ~54 px du
  jeu en 960x540 : la lampe est loin DEVANT le plan du sprite. Alors une lampe placee juste
  au-dessus d'une tete eclaire mieux la face (normales vers le spectateur) que le sommet (normales
  rasantes vers le haut) : le haut des cheveux tombe dans un palier sombre (bug constate sur la
  page de test avec l'ancienne valeur 40 px : sommet 0,51 contre 0,59 au milieu des cheveux ;
  avec 8 px : 0,67 contre 0,41). Pour des torches DANS la scene, prendre une profondeur faible :
  dans la copie du shader, remplacer le 0,1 de la ligne
  `vec3 lightDir = vec3((light.position.xy / res) - (gl_FragCoord.xy / res), 0.1);`
  par ~0,015 (~8 px a 540 px de haut). La page de test regle la meme chose (« Profondeur »,
  8 px par defaut).
- Convention verifiee : normale G = y vers le HAUT ; Light2D retourne y de la lumiere
  (hauteur - y) et travaille en gl_FragCoord (y vers le haut) : les cartes livrees sont dans le
  bon sens. Controle : demi-sphere synthetique, bord du haut decode (x, y, z) = (-0,08, +0,75, +0,45).
- `flipX` ne retourne pas les normales (le rouge n'est pas inverse) : un sprite retourne est
  eclaire du mauvais cote. Deux solutions : textures `--gauche` (`*.neutre-gauche.png` +
  `*.normales-gauche.png`, autre cle, on change de texture au lieu de flipX), ou mieux le
  pipeline ci-dessous qui inverse normal.x quand le sprite est retourne (c'est ce que fait la
  case « sens » de la page de test).
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

### Lumiere derriere le sprite (contre-jour) dans le meme pipeline
Light2D n'a pas de z negatif (0,1 fixe pour toutes les lampes). Dans la copie du shader :
`uniform float uLightZ[kMaxLights];` et `vec3 lightDir = vec3(... , uLightZ[index]);` ; dans la
classe, apres `super.onRender(scene, camera)` :

    scene.sys.lights.getLights(camera).forEach((l, i) =>
      this.set1f(`uLightZ[${i}]`, l.profondeur ?? 0.015));   // negatif = derriere ; meme ordre que Phaser

Lumiere derriere : PAS de lisere, de bande, de halo ni de couleur de lampe plaquee, PAS de regles
tout-ou-rien, et PAS deux formules devant / derriere (v10 : bascule sensible quand la lampe passe
z = 0 ou entre dans la silhouette). Modele v11 : UNE formule pour toutes les positions de la lampe,
sans branche sur z ni sur « lampe cachee » ; seuls les paliers font des marches.

    wb    = smoothstep(+15, -15, z)                  // poids « derriere », progressif autour de z = 0
    ne    = normalize(mix(n_section, n_lissee_5x5, wb))
    L     = direction 3D vraie vers la lampe (z negatif compris)
    diff  = max((ne . L + w) / (1 + w), 0) x att3D,  w = 0,5 wb      // « wrap » doux
    occ   = smoothstep(-8, 6, distance signee lampe/silhouette)       // lampe cachee, en douceur
            (dedans : profondeur ; dehors : -distance ; texture de geometrie, marge 10 px)
    cj    = 0,67 contre x wb x smoothstep(0,2 ; 0,6 ; 1 - n_section.z)     // plans rasants des SECTIONS
            x (0,5 + 0,5 mix(n2.u, -n2.u, occ))^3                          // n2 : normale lissee
            x sc^2, sc = |z| / sqrt(d2^2 + z^2)                             // diffusion vers l'avant
            x (1 - d2^2 / (0,3 portee)^2)^2
    contour sombre (luminance de base < 0,16) : pas de cj, e = min(diff, 1 palier)
    lumiere = ambiance + couleur x intensite x palier(min(diff + cj, 1))   // un plafond, un palier
    Tout est MULTIPLIE par la couleur de base du neutre : aucune part additive de la lampe.

v12 (crapaud « effet bande sur les cotes ») : en v11 le terme « proximite du bord » (1 - smoothstep(1;5;
profondeur)) x rasance de la normale LISSEE faisait un anneau de 3-5 px d'epaisseur constante,
egal tout autour quand la lampe est cachee (contre-jour moyen 0,44-0,50 sur l'anneau de 3 px contre
0,01 a l'interieur, 79-82 % de l'anneau allume) ; et le contour du crapaud (#212121, luminance 0,13)
n'etait pas reconnu comme sombre (seuil 0,12) : sombre x lampe verte = vert fonce visible. v12 :
rasance prise sur la section, decroissance sc^2 avec la distance 2D, seuil 0,16 -> anneau 9-12 %
allume, palier moyen 0,04, l'interieur garde ses plans (8-9 %).
Lampe devant (z >= 15) : wb = 0, c'est exactement N.L x attenuation, comme avant. Continuite
(variation moyenne avant paliers d'un pas au suivant, « pic isole » = ecart au voisinage),
v10 -> v11 : Agarica, balayage de profondeur lampe a gauche 0,031 -> 0,001, lampe traversant la
silhouette a z = -20 0,109 -> 0,021 ; crapaud 0,020 -> 0,002 et 0,054 -> 0,010. La page garde
temporairement une case « Ancienne version (v10) ».

Dans Phaser (pipeline personnalise) : meme fonction par lampe ; uniforms par lampe : position,
profondeur (uLightZ), occultation precalculee cote JS (lecture de la texture de geometrie a la
position de la lampe) ; textures : normales + geometrie. Pas de `if` sur z dans le shader.

Contour : aucun traitement special du bord dans le shader. Dans sections.py, chaque pixel qui
touche le vide HERITE de la section des pixels interieurs voisins (heriter_bord) : le contour fait
partie de la section qu'il borde ; un contour noir reste sa couleur sombre x l'eclairage de cette
section, donc toujours plus sombre qu'elle. Les cartes de sections ne
changent pas. Dans Phaser : meme calcul dans le pipeline personnalise (profondeur par lampe via
uLightZ ci-dessus ; la texture de geometrie en 3e texture pour savoir si la lampe est cachee).

### Sprite retourne (flipX) : inverser normal.x dans le meme pipeline
Dans la copie du shader, remplacer la ligne du calcul de `normal` par :

    uniform float uFlipX;                                  // 1.0 normal, -1.0 retourne
    vec3 nm = normalMap * 2.0 - 1.0;
    nm.x *= uFlipX;
    vec3 normal = normalize(uInverseRotationMatrix * nm);

et dans la classe, avant chaque sprite (on vide le lot quand le sens change, comme Phaser le fait
deja pour la rotation) :

    batchSprite(gameObject, camera, parentMatrix) {
      const f = gameObject.flipX ? -1 : 1;
      if (f !== this.flipCourant) { this.flush(); this.set1f('uFlipX', f); this.flipCourant = f; }
      super.batchSprite(gameObject, camera, parentMatrix);
    }
    onRender(scene, camera) { super.onRender(scene, camera); this.flipCourant = null; }

Le joueur garde `setFlipX` comme aujourd'hui ; la lumiere eclaire alors le bon cote. A verifier
en jeu (3.80.1 : `batchSprite` et `onRender` existent sur LightPipeline, `set1f` vient de
WebGLPipeline).
