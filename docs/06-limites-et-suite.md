# 06 — Limites, risques et suite du projet

## 1. Ce qui n'est pas tenu

**La masse.** 8 426 g ± 195 g en aluminium contre 8 000 g visés. Il n'y a pas
d'astuce : les deux tiers de la masse sont dans le cadre et les roues, tous
deux déjà dimensionnés au plus juste (CS mini 1,43 en fatigue sur la poutre).
Trois options, par ordre de préférence :

1. **Passer la fourche, la poutre et la jante en composite** → 7 936 g. Coût
   pièce nettement supérieur, tenon conique de jante à repenser en insert
   titane collé.
2. **Réduire la roue à 440 mm** → environ − 280 g, mais la résistance au
   roulement du bandage plein augmente d'environ 13 % et le confort baisse.
3. **Accepter 8,4 kg** et le dire. Un Brompton pèse 11 à 12,5 kg ; 8,4 kg dans
   un sac à dos reste remarquable.

## 2. Ce qui est fragile dans le dossier

| Point | Nature du risque | Comment le lever |
|---|---|---|
| **Résistance au roulement du bandage** | C<sub>rr</sub> = 0,020 est une estimation de littérature. Si la valeur réelle est 0,028, la puissance de roulement passe de 107 à 150 W et le vélo devient pénible | essai E10, prioritaire |
| **Raideur de direction 39 N·m/deg** | en dessous des références (60–110). Le ressenti n'est pas prédictible par le calcul | essai E8 |
| **Durabilité des tenons coniques** | matage Al/Al sur 3 000 cycles, aucune donnée | essai E4 |
| **Marge d'encombrement quasi nulle** | 486 × 282 × 174 mm dans 490 × 280 × 195. Toute pièce oubliée dans la nomenclature fait sauter le rangement | maquette volumique imprimée en 3D avant tout usinage |
| **Fatigue de la poutre, CS 1,43** | 3 % au-dessus du critère | essai E5, et ne rien retirer à ce tube |
| **Moyeu supposé indéformable** | la raideur latérale réelle de la roue sera inférieure au calcul | essai E1 étendu au latéral |

## 3. Variante « performance » à documenter

Si le rendement prime sur l'increvabilité :

- boyau pneumatique repliable collé par secteurs (libre au droit des joints,
  ce qui lui permet de plier en accordéon) ;
- gonflage à 4 bar au montage, pompe intégrée dans la poutre principale creuse ;
- gain : **64 W à 20 km/h** (43 W au lieu de 107 W de résistance au roulement),
  − 90 g, confort nettement meilleur ;
- coût : deux dégonflages et deux gonflages par pliage, et une crevaison en
  déplacement devient un incident bloquant.

C'est un vélo différent, pas une option de finition. La décision appartient au
demandeur ; le dossier actuel a tranché en faveur de la fiabilité parce que
c'était l'exigence énoncée.

## 4. Ce que le calcul ne couvre pas

- **Dynamique.** Aucune analyse modale. Une jante en 8 arcs a des modes propres
  qui peuvent être excités par les impacts de joint (4 par tour à 3,5 tr/s,
  soit 14 Hz et harmoniques). À traiter avant industrialisation.
- **Stabilité en conduite.** Chasse 41,7 mm et empattement 980 mm sont dans les
  usages des vélos pliants compacts, mais le comportement à basse vitesse avec
  des roues de 500 mm et un centre de gravité haut n'est pas simulé.
- **Freinage.** La décélération de basculement calculée est 0,63 g, ce qui est
  normal ; mais le freinage avant seul sur roue de 500 mm avec bandage plein
  (adhérence réduite) n'a pas été étudié en dynamique.
- **Corrosion galvanique.** Rayons inox dans des inserts aluminium, tenons
  aluminium anodisé, cordon aramide : à traiter (isolation, revêtement).
- **Coût.** Aucune estimation. Le nombre de pièces usinées (16 tenons,
  16 secteurs de moyeu, 5 expandeurs) est élevé.

## 5. Prochaines étapes recommandées

1. **Maquette volumique** imprimée en 3D à l'échelle 1, sans fonction
   mécanique, pour valider le rangement et le geste de montage (2 semaines).
   C'est l'essai le moins cher et celui qui peut tuer le projet le plus tôt.
2. **Prototype de roue seule**, monté sur un bâti d'essai. Essais E1 à E4.
   C'est le cœur du concept ; si la roue ne tient pas, le reste ne sert à rien.
3. **Prototype complet** seulement ensuite, pour les essais E5 à E10.

## 6. Reproduire les calculs

```bash
cd calc
python3 test_fem.py      # validation du solveur (7 cas analytiques)
python3 run_all.py       # chaîne complète -> out/rapport-calculs.txt + plans
```

Toute la géométrie est dans `calc/params.py`. Modifier une cote y régénère
l'ensemble : vérifications structurelles, bilan de masse, rangement et plans
cotés.
