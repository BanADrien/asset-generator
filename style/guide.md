# Guide de style - Legend of Agarica

Base « apprise » par analyse des assets du depot `BanADrien/agarica` (16/11/2026) : mesures
(tailles, couleurs, transparence, echelles du code) + lecture des images. Ce n'est PAS un
entrainement de modele : le generateur ne connait pas le jeu ; c'est ce guide, la palette et la
notation qui ramenent chaque image vers le style du jeu. Planche : `planche-exemples.png`.

## Constat sur les assets actuels
- Tuiles de sol `decors/tuiles.png` : seul vrai pixel art du jeu, dessine a la main. Cases de
  24 px, affichees en 64 px (GROUND_TILE_SIZE) -> **1 px art = 64/24 = 2,67 px ecran**.
  Pierres brun-rouge sombre (542715, 3c1b0f, 2e150b), joints presque noirs, herbe en 4 verts
  (173104 -> 48871d), 0 pixel semi-transparent.
- Sprites (personnages, animaux) : images IA peintes en haute definition (200 a 700 px par
  frame), 10 000 a 70 000 couleurs, 20 a 60 % de pixels semi-transparents, reduites a l'ecran
  par `setScale` (0,24 a 0,4). Faux pixel art : flous a 1x, densite de pixels differente des
  tuiles. C'est ce que le skill doit depasser.
- Direction artistique (CLAUDE.md / GDD du jeu) : silhouettes sombres facon Hollow Knight,
  violet nuit / vert lunaire / touches de rose, silhouette + contour lumineux, fonds degrades.
- Moteur : Phaser 3, canvas 960x540, vue de profil (plateformer), sprites tournes vers la
  droite (le jeu retourne l'image pour la gauche).

## CURSEUR DE REALISME (reglage central, 16/11/2026)
Sa zone est AU MILIEU. Trop stylise (totem 1, mascotte et cartoon 3) et trop realiste ou peint
(illustration naturaliste 4-5, bestiaire « too much ») sont tous deux penalises.
Zone cible : entre l'anguleux modele (n°7 de l'essai 3, note contestee) et le pixel art propre realiste (7) : anatomie vraie
et couleurs naturelles, MAIS formes simplifiees en plans nets (2-3 valeurs par plan), peu de
couleurs (12-16), contour sombre franc, pas de rendu peint ni de texture grenue.
La PETITE TAILLE fait partie du style : plus le sprite est grand, plus Codex y met de detail
et plus ca fait « trop realiste ». Viser ~64-80 px de large pour un crapaud.
Chaque prompt doit placer l'image sur ce curseur (et ne pas resservir une image deja vue).

## CRITERE « ERGONOMIQUE » (parole de l'utilisateur, 16/11/2026)
« ergonomique c'est une forme globale plus propre et definie, avec un style propre » :
FORME GLOBALE PROPRE ET DEFINIE + DESIGN COHERENT d'un bout a l'autre du personnage. C'est le
critere n°1 au-dela de la technique. Image cible : `references/cible/crapaud-cible-n7.png`
(defauts cites : bouche ouverte, pas assez realiste). Quand un design plait, le CONSERVER
(silhouette, pose, proportions, taille de grille) et ne retoucher que les defauts cites.

## ACQUIS VALIDES PAR L'UTILISATEUR (crapaud, 16/11/2026)
« un niveau de realisme intermediaire est parfait, la forme avec la grosse gorge est bien, il
est bien proportionne ». Realisme : 3 a 4 crans au-dessus de l'anguleux (5 crans = haut du
curseur, deja moins bien). Forme : grosse gorge, bien proportionne, gueule fermee. Cible
principale : `references/cible/crapaud-cible-principale-1.png` et `-2.png` (~98x64).

## REFERENCE DE STYLE (etalon) - `etalon-style.png` (+ `etalon-style-x8.png`)
Parole de l'utilisateur : « je prefere quand meme le design de la version debout dans le
style ». Cette image (crapaud debout du profil detaille, note 6,5) est le STYLE voulu pour
ses assets : formes propres et simples, couleurs pales et sobres (olive clair, creme), ombrage
doux en peu de valeurs, contour sombre net, aucun grain. A utiliser comme image source
(`--source`) ou comme reference de prompt pour les futurs assets, et comme comparaison
directe par les juges (critere « appartenance au style »).
Le crapaud orange actuel du jeu reste l'ancre de QUALITE (6,75) : la barre a depasser.

## Integration dans le jeu (profil natif, par defaut)
- Le sprite natif (sortie de `grid_reduce.py`) s'affiche a l'**echelle 1** avec `pixelArt: true`
  dans Phaser ; jamais d'echelle non entiere (elle deforme les pixels). Si un agrandissement
  est necessaire, x2 ou x3 entier seulement.
- Taille : la hauteur de grille demandee a Codex ~ la hauteur a l'ecran du sprite actuel du
  sujet (+10 % au plus). Repere crapaud : natif 84 x 62 integre ; crapaud actuel 71 x 56 a l'ecran.
- Palette : celle de l'image (couleurs sobres demandees au prompt) ; la palette du jeu n'est
  plus imposee (elle ternissait les couleurs).

## Anciens profils de taille (hors chemin par defaut) (l'utilisateur n'a pas encore tranche ; defaut : petit)
- **petit** : densite des tuiles (1 px art = 2,67 px ecran), tableau ci-dessous. Lisible mais
  pauvre : meilleur resultat 5,5/10 selon l'utilisateur.
- **detaille** : ~60-64 px de haut, affiche a l'echelle ~1 comme les personnages actuels
  (crapaud : boite 80 x 60), 12-48 couleurs, texture et lignes interieures gardees. Repond a
  son « detaille, realiste », au prix d'une densite differente de celle des tuiles.

## Tailles cibles du profil petit (px art = taille ecran actuelle / 2,67)
| Sujet | Taille ecran actuelle | Cible pixel art (l x h) |
|---|---|---|
| Agarica (humaine) | 45 x 84 | ~17 x 31 |
| Crapaud (corps, langue rentree) | 71 x 56 | ~28-32 x 21-24 |
| Aigle / oiseau (ailes ouvertes) | 78 x 92 | ~29 x 34 |
| Loup | 107 x 68 | ~40 x 26 |
| Ours | 178 x 104 | ~64 x 39 |
| Singe (roule en boule) | ~43 x 46 (echelle a confirmer) | ~16 x 17 |
| Chat, ours-hibou, autres | regle : meme densite, taille relative a Agarica (31 px) |
Dans le jeu : afficher le PNG avec `pixelArt: true` et une echelle 64/24 (ou 3 si on veut
un entier). Ne jamais lisser.

## Regles de style
1. **Densite unique** : un pixel du sprite = un pixel des tuiles. Pas de sprite « HD » a cote.
2. **Profil strict**, oriente a droite, pose lisible (pattes, oeil, bouche visibles).
3. **Contour 1 px ferme**, selectif : teinte tres sombre de la matiere (brun-noir, vert-noir,
   violet-noir), noir pur seulement au plus profond. Pas de contour double, pas de trou.
4. **Lumiere** venant du haut-gauche (lune). 3 a 4 valeurs par matiere : ombre, base, clair,
   eclat. Ombres decalees vers le violet/brun (5e5371, 432b59, 30273d), eclats vers le chaud
   (f5b87f, f8d2a1). Pas de « pillow shading » (bord sombre + centre clair sans direction).
5. **Palette** : uniquement `palette.hex` (45 couleurs : 30 extraites du jeu, verts de l herbe, vert lunaire, rose, rampe olive et jaune d oeil ajoutes pendant le test du crapaud). Un sprite utilise 6 a 20 couleurs.
6. **Silhouette d'abord** : reconnaissable en aplat noir a 1x ; formes trapues et franches,
   details (oeil, verrues, griffes) en groupes de 2 px et plus, pas de poussiere de pixels.
7. **Contraste** : le sujet doit se detacher du fond violet nuit (1e1726) ; garder un clair
   franc (yeux, ventre, eclat) et un sombre franc (contour).
8. **Personnalite** : un detail signature par animal (oeil jaune du crapaud, plumes violettes
   de l'aigle, yeux verts lunaires des formes d'Agarica).

## Animaux du jeu (double saut de chaque forme)
- Oiseau/aigle : plane (ailes ouvertes, plumes violet nuit, nervures vertes).
- Singe : liane (brun roux, visage clair, yeux verts).
- Crapaud : grappin-langue (corps trapu brun-olive ou vert mousse, ventre creme, oeil jaune,
  langue rose 8-12 px quand elle sort).
- Ours-hibou : ecrasement (masse sombre, bec, plumes sur la tete).
- Chat : wall jump (silhouette fine, queue haute).
