# Lecons apprises (relire au debut de chaque utilisation, ajouter a la fin de chaque essai)

## BILAN (16/11/2026, apres ~45 images) - a lire en premier
La chaine technique donne de facon fiable un 7 (Codex + reduction native, realiste propre).
Aucune exploration a l'aveugle n'a depasse 7,25. Les hypotheses de gout deduites des notes
ont ete refutees une fois sur deux. REGLE : au-dela de 7, ne plus explorer sans IMAGES DE
REFERENCE fournies par l'utilisateur (sprites qu'il trouve a 9-10, dans `references/cible/`).
Sans elles, les lui demander avant de generer.

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
- 2026-11-16 - REGLE PERMANENTE - apres chaque livraison, demander sa note a l'utilisateur
  (et son prefere) et l'ajouter a `calibration/calibration.md` avec l'image : c'est ce qui
  cale les juges sur son gout (v1 : ecart moyen 0,92 ; v2 avec ancres : 0,58).
- 2026-11-16 - calibration - l'utilisateur veut du « detaille, realiste » ; ses reproches :
  contours pas definis, peu de texture, elements mal distingues ; prefere l'essai 6 (masse
  ronde, peau marbree). Le crapaud propre mais plat dessine en code est « nul ».
- 2026-11-16 - crapaud profil detaille (3 essais : 5 / 4,5 / 4,5) - (+) a 60 px l'oeil, le
  ventre et la texture marbree passent enfin ; juges : texture reussie. (-) SDXL dessine le
  crapaud de face ou debout (« bonhomme ») ; oeil/bouche/patte avant restent fondus ;
  « 2d creature illustration, bold ink » donne des encres fines qui deviennent des tirets.
  Regle : comparer `--method cells` et `pixel-fixer` sur les memes images (`--reuse`) ;
  pixel-fixer garde plus de texture a cette taille, cells est plus net mais plus plat.
  Correction pendant la boucle : minimum de couleurs du profil detaille passe de 12 a 8
  (la palette du jeu donne 10-11 couleurs sur un sprite propre).
- 2026-11-16 - AI Horde - la cle de compte (sans kudos) n'accelere pas beaucoup : ~10 min
  par essai de 3 images dans les deux cas aux heures chargees.
- 2026-11-16 - REVIRAGE DE GOUT (notes du lot detaille : 2 / 6,5 / 3) - l'utilisateur
  recompense la NETTETE (formes propres, contour net, parties distinctes, ombrage doux) et
  punit le BRUIT ; la v2.1 avait recompense une texture sale. Grille v3 : nettete 35 %,
  plafond 3 si bruit dominant, mesure « salissure » (taches de 1-2 px) calee sur ses notes.
  La pose compte peu (+0,5 a 4 pattes, -0,5 a -1 « bonhomme »).
- 2026-11-16 - crapaud-net essai 1 (6,5) - (+) prompt « clean cel-shaded ... bold dark
  outline, flat colors, soft shading, simple readable shapes » + negatif « noisy, grainy,
  mottled, dirty, speckled » : sources propres a 4 pattes, reduction propre (salissure 10 %).
  (-) lu comme une grenouille (vert vif, peau lisse, pas de verrues).
- 2026-11-16 - LoRA AI Horde « Pixel Art XL » (CivitAI 120096, `--lora 120096:0.8`), essai 2
  (6,5, meme prompt) - (+) sources en vrai pixel art, yeux et doigts dessines, plus crapaud
  (dos brun). (-) jaune sature, petit grain sur le dos ; pas mieux note que sans LoRA.
  Disponible et gratuit avec la cle ; a reessayer avec un prompt plus brun-olive.
- 2026-11-16 - outil - regarder les sprites a un grossissement ENTIER (x4, x8) : un
  agrandissement non entier fabrique de faux pointilles et fait croire a du bruit.
- 2026-11-16 - pixelisation - palette appliquee des la HD (`--palette-first`) + fusion des
  taches de 1-2 px (`--despeckle 2`) : salissure 10 % -> 5 % sans perdre oeil ni reflet ;
  actives par defaut en profil detaille. Tolerance du test « taille » : 7 % (le recadrage
  mangeait 4-6 px sur 80).
- 2026-11-16 - notes du lot « net » (5,5 / 4,5 / 1,5, juges 6,5 / 6,5 / 5,5) - juges trop
  genereux ; un sujet lu « tortue/champignon » doit valoir 2 max ; jaune sature = penalite.
  Grille v3.1 puis v3.2 (plafonds calcules par `scripts/score.py`, champ `animal_lu`,
  `autre_lecture_dominante`, harmonie des couleurs, style etalon, ancre orange 6,75).
  Validation v3.2 : ecart moyen 1,29 (0,94 sans le cas tortue) ; les juges ECRIVENT
  « evoque une carapace » sans cocher « dominante » : a surveiller.
- 2026-11-16 - etalon de STYLE = crapaud debout pale (`style/etalon-style.png`) ; ancre de
  QUALITE = crapaud orange actuel (6,75). Un 8 doit le surpasser nettement.
- 2026-11-16 - RETOUCHE (img2img AI Horde) : fonctionne avec la cle de compte (768 px,
  `--source --denoise`). Base orange a 0,5 : garde anatomie et pose a 4 pattes, sprite net
  (6,5, juges : « plus propre que l'ancre », oeil petit, pas de bouche, orange encore
  sature). Base etalon a 0,55 : la pose debout NE change PAS (5) -> pour changer la pose,
  partir d'une base deja dans la bonne pose. ControlNet (SD 1.5) refuse : HTTP 403, demande
  des kudos que le compte neuf n'a pas.
- 2026-11-16 - AI Horde abandonne le 2026-11-16 : plafonne a 6,5 selon les juges, juge
  « horrible » par l'utilisateur (« les 3 sont horribles, oublie l'outil gratuit »).
  Pollinations abandonne le meme jour. Generateur unique : Codex (`codex exec`), dont une image
  brute a ete notee 7,25 (sa meilleure note).
- 2026-11-16 - reduction : `grid_reduce.py` (fidele a la grille Codex, resolution native,
  palette propre) devient la reduction par defaut ; l'ancienne (64 px + palette du jeu)
  coutait ~3 points. Mesure `fidelite_brut` : natif 10, ancienne reduction 21 (notee 4).
- 2026-11-16 - quota Codex : 6 images par essai (« fais-les par 6 »), 4 essais max ; des
  l'essai 2, 3 retouches du champion + 3 nouvelles. Tri des 6 (lecteur aveugle + mesures),
  2 juges sur les 3 meilleures.
- 2026-11-16 - juges v4 (lecteur aveugle + placement par comparaison) testes et NON adoptes :
  ecart moyen 1,66 sur 19 images ; le lecteur aveugle dit « crapaud » a tout (meme brique,
  tortue). Il reste utile pour verifier oeil et bouche au tri.
- 2026-11-16 - premier vrai essai Codex x6 (crapaud) : 6 images en ~4 min, toutes propres
  aux mesures et lues « crapaud » ; tri sur les defauts du lecteur (patte arriere fondue,
  spirale lue coquille). Juges : 7 / 8 / 7,5 sur les 3 retenues. Defaut commun : verrues
  trop denses et regulieres, une seule narine. Codex ne respecte pas toujours la grille
  demandee (une image a 142x90 au lieu de ~84x62).
- 2026-11-16 - l'utilisateur note les 6 crapauds Codex x6 a 7 chacun : technique acquise, mais
  « j'aime pas le style actuel, j'aime pas la forme » et « 6 propositions quasi identiques,
  ce qui revient a ne m'en faire aucune ». De 7 a 10 = direction artistique, pas details.
  Regles : essai 1 = 6 directions vraiment differentes (style, forme, palette), une generation
  par direction sans reference commune ; juges limites a la technique, plafond 7.
- 2026-11-16 - « le mieux des 6 reste le 4e » : son prefere etait une image ECARTEE au tri
  (patte fondue dans le flanc). Ce qui le distinguait (a confirmer) : verrues discretes
  (« ton sur ton » refute ensuite : 4/10). Ne rien deduire d'un trait commun a toutes les propositions (la
  forme trapue). Tri assoupli : n'ecarter que mauvais animal, oeil/bouche absents, bruit.
- 2026-11-16 - essai des 6 directions (une generation Codex par direction, ~2 min en tout,
  3 en parallele) : 6 dessins vraiment differents. `grid_reduce` rendait transparents les
  grands blancs d'yeux et reflets enfermes (yeux cartoon) : corrige (un blanc qui entoure une
  pupille ou loin du bord de la silhouette reste blanc ; sorties Codex x6 inchangees).
  Mesure `fidelite_brut` en echec sur 5/6 alors que la reduction est fidele a l'oeil : artefact
  d'alignement sur les dessins a aplats tres contrastes, a recaler. Le totem a grosse grille
  sort a 123x80 (Codex n'a pas tenu ~84x62).
- 2026-11-16 - notes des 6 directions : naturaliste 7 >> stylises 1-5 (anguleux 5, totem 1).
  Rester dans le realisme et les couleurs naturelles ; faire varier la forme, la pose et le
  traitement (essai 3 : 6 formes naturalistes opposees).
- 2026-11-16 - essai des formes naturalistes (6 + 3 anguleuses, ~3 min) : formes bien
  distinctes, mais Codex depasse encore la taille (jusqu'a 136x81 malgre « never more than
  90 x 66 ») ; les rendus peints echouent salissure/contour sans etre sales a l'oeil. Avec
  l'image de reference jointe, « Anguleux pose » l'a presque recopiee (orange compris) : une
  reference de style tire vers la copie, preciser ce qui doit changer. Petits trous blancs
  (< 9 cases) entre les pattes gardes blancs par la reduction (crapaud doux) : a traiter.
- 2026-11-16 - notes essai 3 : elance assis 7, anguleux modele 6 (note contestee ensuite), naturalistes peints 4-5,
  bestiaire « too much », poses dynamiques 3-4. Reglage central = CURSEUR DE REALISME, zone au
  milieu (plans nets, 12-16 couleurs, contour franc, petite taille ~64-80 px de large).
- 2026-11-16 - essai 4 « anguleux realiste » (4 images, ~1 min, 4 en parallele) : la consigne
  « only about 64 big pixels wide, each pixel a big visible square » donne 57-100 px ; 2 sprites
  a 100 px regeneres avec « AT MOST 64 x 50, ~16 image px par pixel » -> 88 et 70 px. Petits
  trous blancs (< 9 cases) entre les pattes : non corriges, toute regle simple (bord proche +
  contour sombre, taille 4-8 cases) effacait aussi les reflets d'une peau sombre luisante.
- 2026-11-16 - essai 5 : 3 retouches du n°7 (image jointe agrandie x10 « this is an EDIT, keep
  strictly identical ... change ONLY ») : silhouette, pose et palette conservees sur les 3, en
  ~1 min. La retouche garde le design la ou un nouveau dessin le perd (essai 4).
- 2026-11-16 - essai 6 : 3 retouches de la retouche n°3 (3, 4, 5 crans de realisme + bouche et
  gorge corrigees), design conserve sur les 3, ~1 min. Notes 4 -> 5 -> 6 a l'essai 5 : sur un
  design qui plait, monter le realisme par crans jusqu'a ce que la note redescende.
- 2026-11-16 - « j'ai jamais dit qu'il etait a 6 » : une note de sa liste affichee sur la
  planche suivante comme etiquette de reference l'a trompe. Ses notes sont RELATIVES a la
  planche : remettre la reference SANS note et la lui faire renoter.
- 2026-11-16 - essai 7 : meme crapaud (retouche 2 de l'essai 6 jointe) en 6 styles de dessin
  generes separement, ~2 min : 6 styles distincts, forme conservee sur les 6. Le tramage
  retro a fait detecter une grille plus fine (122x80) ; « clair de lune » vire au bleu malgre
  « must stay brown-olive ».
- 2026-11-16 - essai 7 : styles retenus = contour colore lumineux et clair de lune, les deux ou
  la lumiere est la plus travaillee. L'utilisateur n'a aucune gestion de la lumiere pour ses
  assets. PISTE (non implementee) : produire un sprite a eclairage neutre + une carte de
  normales ou des calques de lumiere, pour que le jeu eclaire lui-meme (Phaser Light2D).
- 2026-11-17 - mode sections, contre-jour : « je veux pas de liseré [...] pas mettre une vieille
  bande ». PAS de lisere ni de bande ajoutee par-dessus (ni couleur de lampe plaquee sur le
  contour, ni couronne, ni halo). Le contre-jour passe par les SECTIONS existantes : matiere x
  lumiere avec les memes paliers ; il choisit seulement quelles sections rasantes s'allument
  (sens par rapport a la lampe) et jusqu'ou (portee). Le contour prend l'eclairage de la section
  voisine, un palier plus bas. Lampe placee trop loin devant le plan : le sommet des formes
  s'assombrit (profondeur 8 px par defaut).
- 2026-11-17 - contre-jour, suite : « ca eclaire trop la face visible centrale [...] on dirait pas
  une lumiere qui vient de derriere ». Lampe derriere : seules les sections RASANTES qui donnent
  sur le vide s'allument ; jamais les inclinees ni la face, meme a grande portee (la portee ne
  regle que la distance 2D). Controle chiffre : < ~20 % de la silhouette eclairee, lampe au centre.
- 2026-11-17 - contre-jour v9 « pas naturel, comme si la logique etait forcee » : des conditions
  tout-ou-rien empilees sur des normales quantifiees donnent des taches eparses. Faire UN modele
  de lumiere continu (normale lissee, fonctions douces) et quantifier une seule fois a la fin.
