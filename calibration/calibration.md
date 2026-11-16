# Calibration sur le gout de l'utilisateur

Les juges ouvrent ces images (version `-x8`) comme ancres : ce sont des notes REELLES de
l'utilisateur. A completer apres chaque livraison (demander sa note, ajouter une ligne).

## Notes
| Image | Note utilisateur | Juges v1 | Ecart v1 | Juge v2 (validation) | Ecart v2 | Lecon |
|---|---|---|---|---|---|---|
| crapaud-essai1.png | 4 | 3,5 | -0,5 | 4 | 0 | Masse moussue credible, tournee a gauche, sans oeil : moyen. |
| crapaud-essai2.png | 1,5 | 3 | +1,5 | 1,5 | 0 | Brique jaune vue de face, ni tete ni pattes : sujet non reconnaissable = quasi nul. |
| crapaud-essai3.png | 4 | 4 | 0 | 3,5 | -0,5 | Grenouille dressee de face, lisible mais pauvre en volume : moyen. |
| crapaud-essai4.png | 5,5 | 4,5 | -1 | 4,5 | -1 | 3/4 tourne a gauche, rond, olive nuance : 2e prefere. |
| crapaud-essai5.png | 4 | 4 | 0 | 4,5 | +0,5 | Meme crapaud que 4, oeil en damier, matiere plus terne : nettement moins bien. |
| crapaud-essai6.png | 5,5 | 3 | -2,5 | 4 | -1,5 | Boule marbree, oeil illisible, mais volume et texture de peau : SON PREFERE. |
| crapaud-code32.png | 2 au maximum | - | - | - | - | Dessine en code, propre et lisible mais plat et simpliste : « nul ». |
Ecart moyen (valeur absolue) : v1 0,92 ; v2 0,58 (objectif <= 1 atteint, essai 2 dernier).
Reste : l'essai 6 (son prefere) est encore sous-note de 1,5 par la v2 ; d'ou la v2.1 ci-dessous.
Validation v2 : 1 juge par image, ancres = toutes les autres images avec leur note, sans voir
la note de l'image jugee (16/11/2026).

Classement de l'utilisateur : 6 > 4 > 1 = 3 = 5 > code32 > 2. Son maximum ici est 5,5 : son
echelle est severe, 8 doit rester difficile.

## Paroles de l'utilisateur
- « detaille, realiste ».
- « on reste loin du 10 : les contours sont pas definis, y a peu de texture, on distingue
  mal les elements, mais mon prefere reste le 6e ».
- Le crapaud 32 px dessine en code est « nul ».
=> Ses trois exigences (verifiees en priorite par les juges, axes de correction de la boucle) :
   CONTOURS DEFINIS, TEXTURE, ELEMENTS DISTINCTS (voir `references/rubric.md`, partie B).

## Regles de gout (interpretation de Claude, a partir des ecarts ci-dessus)
a) Volume, rondeur et matiere (peau marbree, masse credible) comptent beaucoup, meme sans oeil
   lisible : un oeil ou une bouche absents coutent des points sur la fidelite, sans ecraser
   la note (essai 6 : utilisateur 5,5, juges v1 3).
b) Forme plate vue de face, « brique » sans tete ni pattes = sujet non reconnaissable :
   2 au maximum (essai 2 : utilisateur 1,5, juges v1 3).
c) Orientation gauche/droite et 3/4 leger ne sont PAS des defauts (essai 4, tourne a gauche
   et de 3/4 : utilisateur +1 sur les juges ; seul indice, a confirmer). Le script retourne
   le sprite si besoin.
d) Propre mais plat et simpliste (crapaud code32) = 2 au maximum : la proprete seule ne vaut
   rien sans richesse de detail.
