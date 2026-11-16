# Calibration sur le gout de l'utilisateur

Les juges ouvrent ces images (version `-x8`) comme ancres : ce sont des notes REELLES de
l'utilisateur. A completer apres chaque livraison (demander sa note, ajouter une ligne).

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

Classement : detaille2 (6,5) > essai4 = essai6 (5,5) > essai1 = essai3 = essai5 (4) >
detaille3 (3) > code32 = detaille1 (2) > essai2 (1,5). Son echelle est severe : 8 reste loin.

## Paroles de l'utilisateur
- « detaille, realiste ».
- « on reste loin du 10 : les contours sont pas definis, y a peu de texture, on distingue
  mal les elements, mais mon prefere reste le 6e » (dit apres le premier lot).
- Le crapaud 32 px dessine en code est « nul ».
- « la pose est moins redhibitoire, meme si je prefererais une pose a 4 pattes comme un
  crapaud normal » (dit apres le lot detaille).

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
