# Grille de notation stricte (sur 10)

But : une note qui ne flatte pas. Un 8 doit pouvoir etre montre a l'utilisateur sans excuse.
Ordre : A (script) puis B (deux juges separes) puis C (regles de calcul).

## A. Mesures objectives - `scripts/measure.py`
| Test | Seuil | Pourquoi |
|---|---|---|
| taille | hauteur ou largeur a 2 px de la cible, jamais au-dessus | densite des tuiles |
| hors_palette | 0 px | coherence de couleur avec le jeu |
| semi_transparents | 0 px | halos sur fond sombre |
| pixels_isoles | 0 px | poussiere |
| orphelins_couleur | <= 12 % des px opaques | bruit d'IA, detail illisible |
| couverture_contour | >= 85 % du bord dans le tiers sombre | silhouette fermee |
| silhouette_un_bloc | <= 2 px detaches | lisibilite a 1x |
| remplissage_silhouette | 35-92 % de la boite | ni baton, ni brique |
| couleurs_utilisees | 5-20 | pixel art, pas peinture |
| contraste_valeurs | ecart L* >= 45 | lecture sur fond nuit |
| bruit | <= 55 % de voisins differents | aplats et rampes, pas de grain |
**Un seul echec => plafond 5/10**, quel que soit l'avis des juges.

## B. Jugement visuel (juge separe, voir `judge-prompt.md`)
Chaque critere part de **5**. Chaque point au-dessus de 5 doit etre prouve par une observation
precise et verifiable sur la planche (zone, couleur, nombre de pixels). Sans preuve, le point
n'est pas accorde. Les defauts font descendre sous 5.

| # | Critere | Poids |
|---|---|---|
| 1 | Silhouette lisible a 1x (aplat reconnaissable, pose claire) | 20 % |
| 2 | Fidelite au sujet et a la pose demandee (anatomie juste, comptes justes) | 15 % |
| 3 | Appartenance au jeu (densite des tuiles, palette, contour, lumiere, a sa place sur la bande « en jeu ») | 25 % |
| 4 | Proprete pixel (lignes regulieres, pas de doubles/jaggies, groupes >= 2 px) | 15 % |
| 5 | Volume et lumiere (une direction, 3-4 valeurs par matiere, ombres teintees) | 15 % |
| 6 | Charme et superiorite sur le sprite IA actuel du meme sujet | 10 % |

### Ancres (pour tout le sprite et pour chaque critere)
- **3/10** : on ne reconnait pas le sujet a 1x, ou anatomie fausse (patte en trop, oeil
  absent), bouillie de pixels, contour ouvert, couleurs qui jurent avec les tuiles. A cote du
  sprite IA actuel, il fait regression.
- **6/10** : le sujet se reconnait, proprete correcte, palette respectee, mais quelque chose
  trahit l'outil : rampes plates ou bruitees, details en poussiere, volume confus, pose
  generique ; sur la bande « en jeu » il se remarque comme rapporte d'ailleurs. Equivalent ou
  a peine meilleur que le sprite IA actuel.
- **8/10** : sur la bande « en jeu », il semble dessine par la meme main que les tuiles ;
  silhouette immediate a 1x ; lumiere claire en 3-4 valeurs ; aucun pixel parasite visible au
  zoom x8 ; detail signature lisible (oeil, langue...). Nettement meilleur que le sprite IA
  actuel (on le choisirait sans hesiter). Les references CC0 ne le font pas paraitre amateur.
- 9-10 : niveau d'un pixel artiste professionnel. A ne presque jamais donner.

## C. Calcul de la note
1. Note juge = somme ponderee des 6 criteres, arrondie a 0,5 pres vers le bas.
2. Si un critere <= 3 : note juge plafonnee a 5.
3. 8 ou plus exige critere 3 >= 8 ET critere 6 >= 8 ; sinon plafond 7,5.
4. Deux juges independants ; **on garde la plus basse** des deux notes.
5. Note finale = min(note retenue, plafond objectif de A).
6. Seuil de livraison : **8/10**. En dessous, on corrige et on recommence (max 6 essais).
