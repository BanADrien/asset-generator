# Calibration sur le gout de l'utilisateur

Les juges ouvrent ces images (version `-x8`) comme ancres : ce sont des notes REELLES de
l'utilisateur. A completer apres chaque livraison (demander sa note, ajouter une ligne).

## Regle de methode pour les interpretations (a appliquer avant toute lecture de ses choix)
Ne deduire une preference que d'un choix entre des options qui s'opposent sur ce point. Si
toutes les propositions partageaient un trait (ici la forme trapue), son choix ne dit rien sur
ce trait.

## Notes (10 images : 9 essais + le crapaud dessine en code)
| Image | Profil | Note utilisateur | Juges a l'epoque | Lecon |
|---|---|---|---|---|
| crapaud-essai1.png | petit | 4 | v1 : 3,5 | Masse moussue, grain de peinture reduite (40 % de taches 1-2 px). |
| crapaud-essai2.png | petit | 1,5 | v1 : 3 | Brique jaune vue de face, ni tete ni pattes : sujet non reconnaissable. |
| crapaud-essai3.png | petit | 4 | v1 : 4 | Grenouille dressee, lisible mais pauvre en volume. |
| crapaud-essai4.png | petit | 5,5 | v1 : 4,5 | 3/4 tourne a gauche, rond, aplats olive propres. |
| crapaud-essai5.png | petit | 4 | v1 : 4 | Meme crapaud que 4, oeil en damier, plus terne. |
| crapaud-essai6.png | petit | 5,5 | v1 : 3 | Masse ronde marbree ; son prefere du premier lot. |
| crapaud-code32.png | petit | 2 au maximum | - | Dessine en code, propre mais plat et simpliste : « nul ». |
| crapaud-detaille1.png | detaille | **2** | v2.1 : 5 (« texture reussie ») | Marbrures grumeleuses, rond dore au front : SALE. Les juges se sont trompes. |
| crapaud-detaille2.png | detaille | **6,5** | v2.1 : 4,5 | Crapaud debout, formes propres, contour net, ombrage doux, parties distinctes : SA MEILLEURE NOTE. |
| crapaud-detaille3.png | detaille | **3** | v2.1 : 4,5 | Taches brunes en salissure, patte avant fondue : sale. |
| crapaud-net1.png | detaille | **5,5** | v3 : 6,5 | Propre, 4 pattes, mais vert/jaune vif, lu « grenouille », oeil en anneau de face. |
| crapaud-net2.png | detaille | **4,5** | v3 : 6,5 | Jaune sature, dos mouchete, griffures : couleur criarde + grain. |
| crapaud-net3.png | detaille | **1,5** | v3 : 5,5 | Lu comme une tortue ou un champignon (dome a pois) : sujet faux. |
| crapaud-orange-actuel.png | sprite IA actuel du jeu (taille ecran) | **6,75** (« 6,5 voire 7 ») | - | ANCRE DE QUALITE : un 8 doit etre nettement meilleur que lui. |
| crapaud-codex-brut.png | image brute Codex (non reduite, HD) | **7,25** (« 7 voire 7,5 ») | - | SA MEILLEURE NOTE : la meilleure image source vue. |
| crapaud-codex-reduit1.png | la meme famille reduite par le skill (64 px, palette) | **4** | 6,5 | La reduction a fait perdre ~3 points : oeil en tiret, verrues en plaques, couleurs ternies. |
| crapaud-codex-reduit2.png | idem | **4** | 6,5 | Idem : juges trop genereux de 2,5 sur une image propre qui a perdu son oeil. |
| crapaud-retoucheA.png | retouche AI Horde (base orange) | **~2** (valeur approximative, il n'a pas donne de chiffre) | v3.2 : 6,5 | « les 3 sont horribles, oublie l'outil gratuit ». |
| crapaud-retoucheB.png | retouche AI Horde (base etalon) | **~2** (approx.) | v3.2 : 5 | idem |
| crapaud-retoucheC.png | retouche AI Horde (champion A corrige) | **~2** (approx.) | v3.2 : 6,5 | idem |
| crapaud-codex6-1.png a crapaud-codex6-6.png | 6 natifs Codex (essai x6, crapaud realiste trapu a verrues) | **7** chacune ; PREFERE : n°4 | 7 / ecarte / 8 / ecarte / ecarte / 7,5 | Le n°4 (brun-beige) avait ete ECARTE au tri. Technique acquise ; manque la DIRECTION ARTISTIQUE (style, forme). Les 6 jugees « quasi identiques ». |
| crapaud-dir-mascotte.png | direction « Mascotte ronde » (chibi, vert pastel) | **3** | - | Stylise/chibi : rejete. |
| crapaud-dir-anguleux.png | direction « Anguleux stylise » (ocre, langue sortie) | **5** | - | Le mieux note des stylises, le plus « animal reel ». |
| crapaud-dir-cartoon.png | direction « Cartoon a caractere » (rouge vif) | **3** | - | Cartoon, couleurs saturees : rejete. |
| crapaud-dir-aventurier.png | direction « Aventurier » (sauge, echarpe, sacoche) | **4** | - | Personnage semi-debout stylise : moyen. |
| crapaud-dir-marais.png | direction « Creature de marais sombre » (bleu-violet) | **2** | - | Fantaisie, couleurs non naturelles : rejete. |
| crapaud-dir-totem.png | direction « Totem minimal » (turquoise, 4 couleurs) | **1** | - | Plat et simplifie : le pire. |
Reference haute NON notee par l'utilisateur : `crapaud-codex-natif3.png` (natif Codex 84 x 62,
reduit fidelement par `grid_reduce.py` depuis le brut a 7,25 ; juges 7 / 7).

Reference de STYLE (≠ ancre de qualite) : `crapaud-detaille2.png`, copiee en
`style/etalon-style.png`. Parole de l'utilisateur : « je prefere quand meme le design de la
version debout dans le style ». Le style voulu pour ses assets : formes propres et simples,
couleurs pales et sobres, ombrage doux, contour net. Le crapaud orange reste la barre de qualite.

Classement : detaille2 (6,5) > essai4 = essai6 = net1 (5,5) > net2 (4,5) > essai1 = essai3 =
essai5 (4) > detaille3 (3) > code32 = detaille1 (2) > essai2 = net3 (1,5).
Son echelle est severe : 6,5 = « le meilleur vu jusqu'ici, encore loin du compte ». 8 reste loin.

## Paroles de l'utilisateur
- « detaille, realiste ».
- « on reste loin du 10 : les contours sont pas definis, y a peu de texture, on distingue
  mal les elements, mais mon prefere reste le 6e » (dit apres le premier lot).
- Le crapaud 32 px dessine en code est « nul ».
- « la pose est moins redhibitoire, meme si je prefererais une pose a 4 pattes comme un
  crapaud normal » (dit apres le lot detaille).
- Le crapaud orange actuel du jeu vaut « 6,5 voire 7 ».
- « je prefere quand meme le design de la version debout dans le style » (crapaud-detaille2).

## Interpretation de Claude (v3, remplace l'ancienne regle « volume et matiere meme sales »)
1. Il recompense la NETTETE et la LISIBILITE : formes propres, contour sombre net, parties
   qu'on distingue d'un coup d'oeil (tete, yeux, ventre, pattes), volume par un ombrage doux
   et regulier, palette coherente (detaille2 6,5 ; essais 4 et 6 5,5).
2. Il punit le BRUIT : taches sombres grumeleuses, marbrures en salissure, masse confuse
   (detaille1 2, detaille3 3, essai1 4). Quand il dit « peu de texture », il veut du detail
   PROPRE et organise (verrues en points nets, taches aux bords francs), jamais du grain.
   Un aplat propre vaut mieux qu'une texture sale.
3. La pose compte peu : le crapaud « debout comme un bonhomme » a sa meilleure note. Il
   prefere quand meme un crapaud a 4 pattes : petit bonus (+0,5) pour la pose naturelle,
   petit malus (-0,5 a -1) pour la pose « bonhomme », jamais de plafond. La nettete prime.
4. Propre mais plat et simpliste (code32) reste mauvais : il faut AUSSI du volume et du detail.
5. Mesure objective qui suit son gout : part des pixels en taches de 1-2 px (« salissure »).
   Profil detaille : propre 10,5 % (6,5/10) contre 19,6-23,3 % (2-3/10) -> seuil 15 %.
   Profil petit : 15-22 % pour les notes 4-5,5, 40 % pour l'essai 1 -> seuil 25 %.

## Interpretation de Claude (v3.1, apres le lot « net » : juges trop genereux de 1, 2 et 4)
6. SUJET FAUX = 2 MAXIMUM : net3 a ete « lu comme une tortue ou un champignon » par les juges,
   qui ont quand meme mis 5,5 ; l'utilisateur 1,5 (meme faute que la brique jaune, essai2).
   Regle dure appliquee par le calcul (`scripts/score.py`, champ `animal_lu` du juge) : si
   la lecture a froid ne nomme pas le bon animal, 2 maximum ; un cousin proche (grenouille
   pour crapaud) coute 1 point, sans plafond.
7. COULEURS : ses deux pires notes « colorees » sont les deux essais jaunes (essai2 1,5 ;
   net2 4,5). Ses mieux notes ont des couleurs sobres, naturelles, peu nombreuses (crapaud
   pale 6,5 ; olive 5,5). Critere « harmonie des couleurs » ; teinte criarde dominante (jaune
   ou vert fluo) : -1,5.
8. GENEROSITE : les juges v3 donnaient ~+1 en haut d'echelle. Pas plus de 6,5 sans surpasser
   NETTEMENT l'ancre a 6,5 (detaille2) sur un point precis cite (champ `depasse_ancre`).
9. OEIL : un oeil « en anneau » ou vu de face sur un corps de 3/4 lui deplait probablement
   (net1 5,5, sous l'ancre). Les juges verifient iris, pupille, reflet, place de l'oeil.

## Validation de la grille v3.1 (12 images, leave-one-out, 1 juge par image)
| Image | Utilisateur | v3.1 | Ecart | Ce qui a joue |
|---|---|---|---|---|
| essai1 | 4 | 3 | -1 | bruit dominant : 3 max |
| essai2 | 1,5 | 2 | +0,5 | animal lu « aucun » : 2 max |
| essai3 | 4 | 4,5 | +0,5 | |
| essai4 | 5,5 | 6 | +0,5 | |
| essai5 | 4 | 5 | +1 | |
| essai6 | 5,5 | 4 | -1,5 | |
| detaille1 | 2 | 3 | +1 | bruit dominant : 3 max |
| detaille2 | 6,5 | 4,5 | -2 | oeil en anneau, juge severe |
| detaille3 | 3 | 3 | 0 | bruit dominant : 3 max |
| net1 | 5,5 | 2 | -3,5 | lu « grenouille » -1 et teinte criarde -1,5 : trop puni |
| net2 | 4,5 | 6 | +1,5 | jaune non signale comme criard par ce juge |
| net3 | 1,5 | 6,5 | +5 | le juge a ecrit « crapaud » tout en notant « evoque une carapace ou un champignon » |
Ecart moyen 1,50, max 5 : objectifs NON atteints. D'ou l'ajustement unique v3.2 :
champ `autre_lecture_dominante` (un autre animal/objet saute aux yeux -> 2 max), penalites
cousin et couleur non cumulables (-1,5 au total), critere « appartenance au style » (etalon),
ancre orange a 6,75 et borne a 7 sans le surpasser.

## Interpretation de Claude (apres le test Codex, 16/11/2026)
10. LA REDUCTION EST LE PREMIER FACTEUR LIMITANT : une bonne image (Codex brut 7,25) perd
    environ 3 points en passant par la reduction du skill (64 px + palette du jeu) : oeil
    reduit a un tiret, verrues en plaques, couleurs ternies (sprites reduits : 4). Avant le
    generateur, c'est la reduction qu'il faut rendre fidele (travail en cours par un autre
    agent : reduction fidele a la grille ; `pixelize.py` n'est pas modifie en attendant).
11. Les juges restent trop genereux (~2,5 points) sur une image propre qui a perdu son oeil.
    Regle dure (calculee par `score.py`) : oeil reduit a un tiret ou a un carre plat
    (`oeil_plat`), ou bouche absente (`bouche_absente`) -> **4,5 maximum**.

## Validation des juges v4 (lecteur aveugle + placement par comparaison, 19 images, leave-one-out)
Note = interpolation du juge entre deux ancres (1,5 brique / 3 detaille3 / 4 codex reduit /
5,5 essai4 / 6,5 debout / 6,75 orange / 7,25 codex brut), arrondie a 0,5 vers le bas, puis
plafond du lecteur aveugle (bouche ou oeil absents de sa liste -> 4,5) et plafonds objectifs.
| Image | Utilisateur | v4 | Ecart |
|---|---|---|---|
| essai1 | 4 | 3 | -1 |
| essai2 (brique) | 1,5 | 1 | -0,5 |
| essai3 | 4 | 3,5 | -0,5 |
| essai4 | 5,5 | 6 | +0,5 |
| essai5 | 4 | 5 | +1 |
| essai6 | 5,5 | 2,5 | -3 |
| detaille1 | 2 | 3,5 | +1,5 |
| detaille2 (debout) | 6,5 | 3,5 | -3 |
| detaille3 | 3 | 2,5 | -0,5 |
| net1 | 5,5 | 3 | -2,5 |
| net2 | 4,5 | 3,5 | -1 |
| net3 (tortue) | 1,5 | 3,5 | +2 |
| orange actuel | 6,75 | 6,5 | -0,25 |
| codex brut | 7,25 | 7,5 | +0,25 (classe premier) |
| codex reduit1 | 4 | 4,5 | +0,5 |
| codex reduit2 | 4 | 7 | +3 |
| retouche A | ~2 | 6,5 | +4,5 |
| retouche B | ~2 | 4,5 | +2,5 |
| retouche C | ~2 | 5,5 | +3,5 |
Ecart moyen 1,66 sur 19 (1,31 sur les 16 sans A/B/C ; v3.2 : 1,29 sur 13), ecart max 4,5
(v3.2 : 5,5). Objectifs (<= 0,8 ; max <= 2 ; net3 <= 2) NON atteints : **v4 non adoptee**,
la v3.2 reste la methode. Constats : le lecteur aveugle dit « crapaud » pour TOUTES les images
(meme la brique et la tortue) : ses plafonds de sujet ne servent a rien. Le placement par
comparaison classe bien le haut (codex brut premier, orange juste) mais rate le gout de
l'utilisateur sur l'etalon debout (3,5 pour 6,5), les retouches Horde (4,5-6,5 pour ~2) et un
codex reduit (7 pour 4). C'est un ecart de GOUT que ni la grille ni les comparaisons ne
comblent pour l'instant.

## Validation de la grille v3.2 (13 images dont l'orange, leave-one-out, 1 juge par image)
| Image | Utilisateur | v3.2 | Ecart |
|---|---|---|---|
| essai1 | 4 | 3 | -1 |
| essai2 | 1,5 | 1,5 | 0 |
| essai3 | 4 | 4,5 | +0,5 |
| essai4 | 5,5 | 6 | +0,5 |
| essai5 | 4 | 4,5 | +0,5 |
| essai6 | 5,5 | 3 | -2,5 (bruit dominant) |
| detaille1 | 2 | 3 | +1 |
| detaille2 | 6,5 | 4 | -2,5 (oeil en anneau) |
| detaille3 | 3 | 3 | 0 |
| net1 | 5,5 | 3,5 | -2 (grenouille + criard) |
| net2 | 4,5 | 4 | -0,5 |
| net3 | 1,5 | 7 | +5,5 (juge : « evoque une carapace ou un champignon » mais non coche « dominante ») |
| orange actuel | 6,75 | 7 | +0,25 |
Ecart moyen 1,29, max 5,5 : objectifs NON atteints (sans net3 : 0,94). L'ajustement unique
est utilise ; pas d'autre retouche. Le crapaud orange est bien place (7 pour 6,75).
Limites constatees : les juges ne cochent pas « autre lecture dominante » meme quand ils
l'ecrivent ; ils sous-notent l'etalon (anneau d'oeil) et les petits sprites marbres que
l'utilisateur aime. Piste : faire nommer 3 choses a froid par un juge SANS la demande et
compter « tortue/champignon » comme faux si cite en premier.

## Validation de la grille v3 (leave-one-out, 1 juge par image, sans voir la note de son image)
| Image | Utilisateur | Juge v3 | Ecart |
|---|---|---|---|
| essai1 | 4 | 2 | -2 |
| essai2 | 1,5 | 2 | +0,5 |
| essai3 | 4 | 4 | 0 |
| essai4 | 5,5 | 4,5 | -1 |
| essai5 | 4 | 5 | +1 |
| essai6 | 5,5 | 3,5 | -2 |
| detaille1 | 2 | 3 | +1 |
| detaille2 | 6,5 | 5,5 | -1 |
| detaille3 | 3 | 3 | 0 |
Ecart moyen 0,94 (objectif <= 1 atteint, sans ajustement). detaille2 classe premier ; detaille1,
detaille3 et essai2 en bas (avec essai1). Reste : les petits sprites marbres (essais 1 et 6)
sont sous-notes de 2 ; la v3 est severe sur le grain a 24-30 px, que l'utilisateur tolere
davantage a cette taille. Fuite constatee pendant la validation : l'historique de rubric.md
donnait la note de detaille2 (le juge l'a signale) ; retire depuis.

## Parole de l'utilisateur sur l'essai Codex x6 (16/11/2026)
« les 6 sont a 7, mais les 3 points restants ne sont plus sur l'acceptable mais sur le bien ;
j'aime pas le style actuel, j'aime pas la forme ; tu m'as fait 6 propositions quasi identiques,
ce qui revient a ne m'en faire aucune ».

Lecture (interpretation de Claude) :
- La TECHNIQUE est acquise : net, propre, lisible = 7. Les juges avaient mis 8 / 7,5 / 7 et
  ecarte trois images qu'il note 7 aussi : ils ne savent pas voir ce qui manque.
- De 7 a 10, c'est de la DIRECTION ARTISTIQUE : le style de dessin et la forme (le design) du
  personnage. Le crapaud realiste, trapu et couvert de verrues ne lui plait pas ; aucune
  correction de detail (narine, verrues) ne fera monter la note.
- 6 variantes d'une meme idee = 0 proposition. Il avait deja dit preferer le DESIGN du crapaud
  debout pale (formes simples, personnage), malgre sa note technique plus basse.
- Consequence : les juges ne notent plus que la technique, plafonnee a 7 ; au-dela, c'est lui.

Precision : « le mieux des 6 reste le 4e » (`crapaud-codex6-4.png`, brun-beige, que le tri
avait ecarte pour « patte arriere confondue avec le flanc, bouche discrete »).
Lecture (interpretation de Claude, A CONFIRMER) : ce qui distinguait vraiment le n°4 des cinq
autres : des verrues discretes fondues dans la couleur au lieu de « pois » clairs tres marques.
(La « teinte chaude ton sur ton » a ete REFUTEE par l'essai 3 : « Doux ton sur ton » = 4.) Rien a deduire sur
la forme : les 6 etaient trapues (correction de l'utilisateur : « je prefere pas un corps
ramasse, vu que j'ai pas eu de choix contraire »). La « patte fondue dans le flanc » ne le gene
pas : le tri etait trop severe. Encore un cas ou les juges (n°3 a 8) et lui (n°4, ecarte)
divergent : les juges trient la technique, il choisit.

## Notes de l'essai des 6 directions (16/11/2026)
Mascotte ronde 3 ; Anguleux stylise 5 ; Cartoon 3 ; Aventurier 4 ; Marais sombre 2 ; Totem
minimal 1. Rappel : les 6 crapauds realistes de l'essai Codex x6 = 7 chacun, n°4 prefere.

Lecture (interpretation de Claude ; valide au sens de la regle de methode, car ces options
s'opposaient vraiment) :
- Rendu NATURALISTE et detaille (7) >> stylise, cartoon, chibi, minimal (1 a 5). La voie vers
  8 reste dans la famille realiste.
- Couleurs naturelles > couleurs saturees ou fantaisie : turquoise 1, bleu-violet 2, rouge vif
  3, vert pastel 3, contre ocre 5, sauge 4, bruns et olives 7.
- Plus le dessin est plat et simplifie, plus la note baisse (totem 1) : il veut du modele et du
  detail.
- Le mieux note des stylises (anguleux, 5) est aussi le plus « animal reel » : anatomie de
  crapaud, teintes naturelles, pose dynamique langue sortie. Hypothese A TESTER : une pose
  dynamique et du caractere plaisent, a condition de rester realiste.
- « j'aime pas le style actuel, j'aime pas la forme » vise donc la FORME et le TRAITEMENT a
  l'interieur du realisme (meme crapaud trapu de profil, verrues en « pois » reguliers), pas le
  realisme lui-meme.

Ajout de l'utilisateur sur la direction n°2 « Anguleux stylise » (notee 5) : « j'aime bien
anguleux, rajoute plus de tests avec cette vision (pas trop non plus) ». -> 3 essais anguleux
(plus modele, pose, en action) ajoutes a l'essai des formes naturalistes.

## Notes de l'essai des formes (essai 3, 16/11/2026)
1 Elance assis 7 ; 2 Massif a grande gueule 5 ; 3 Feuille morte 4 ; 4 Pret a bondir 4 ; 5 Doux
ton sur ton 4 ; 6 Bestiaire contraste 5 ; 7 Anguleux plus modele 6 ; 8 Anguleux pose 3 ;
9 Anguleux en action 3.
Ses mots : « essaye de faire un anguleux plus realiste, mais la le niveau de realisme global est
trop eleve pour un jeu 2D pixel art, et le 6 j'en parle pas, c'est too much ».

Lecture (interpretation de Claude ; options contrastees, lectures valides ; hypotheses marquees) :
- CURSEUR DE REALISME, zone au milieu : trop stylise (totem 1, mascotte et cartoon 3) et trop
  realiste/peint (naturalistes 4-5, bestiaire « too much ») sont penalises. Cible : entre
  l'anguleux modele (n°7 = 6) et le pixel art propre realiste (essai Codex x6 = 7, elance assis
  = 7) : anatomie vraie, couleurs naturelles, formes simplifiees en plans nets, peu de
  couleurs, contour sombre franc, pas de rendu peint ni de texture grenue.
- Forme (HYPOTHESE a confirmer) : l'elance assis droit (7) bat tous les trapus de cet essai
  (4-5) : premiere vraie indication, il prefererait une silhouette fine et relevee.
- REFUTE : « doux ton sur ton » (n°5 = 4) n'est pas ce qui lui plaisait dans son ancien n°4 ;
  l'hypothese « teinte chaude ton sur ton » est retiree.
- REFUTE : la pose dynamique langue sortie n'apporte rien (n°4 = 4, n°9 = 3) : plus par defaut.
- L'orange sature reste penalise (n°8 = 3). Une quasi-copie d'une image deja vue est notee plus
  bas que l'originale : ne jamais resservir la meme.
- Plus le sprite est grand, plus Codex y met de detail, plus ca fait « trop realiste » : la
  petite taille fait partie du style voulu, pas seulement une contrainte d'integration.
