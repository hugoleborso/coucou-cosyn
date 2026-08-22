# 04 — Masse et encombrement

## 1. Bilan de masse

Chaque ligne est marquée **[C]** si elle est calculée à partir de la géométrie
et de la masse volumique, **[E]** si elle est estimée d'après des composants
existants. L'incertitude est propagée en quadrature.

| Groupe | Masse | Part |
|---|---|---|
| Cadre | 3 186 g | 37,8 % |
| Roues | 2 724 g | 32,3 % |
| Transmission | 944 g | 11,2 % |
| Poste de pilotage | 525 g | 6,2 % |
| Selle | 357 g | 4,2 % |
| Freinage | 320 g | 3,8 % |
| Suspension | 220 g | 2,6 % |
| Divers | 150 g | 1,8 % |
| **TOTAL** | **8 426 g ± 195 g** | |
| Objectif | 8 000 g | |
| **Écart** | **+ 426 g (+ 5,3 %)** | |

Probabilité de tenir 8,00 kg en construction aluminium, compte tenu des
incertitudes : **1 %**. Autrement dit : **l'objectif de 8 kg n'est pas
atteignable en aluminium**. Il est atteignable en composite.

### Détail des deux postes lourds

**Roues (2 724 g)** — jante 8 arcs 1 036 g, moyeux à brides écartables 580 g,
bande de roulement 340 g, rayons + écrous 298 g, disques 180 g, tenons 144 g,
inserts 77 g, cordon captif 70 g.

**Cadre (3 186 g)** — bras arrière + hauban + mât 755 g, poutre principale
3 étages 633 g, fourche monobras 479 g, expandeurs et leviers 275 g, raccords
collés-goupillés 270 g, tube de direction + jeu 234 g, tourillons 210 g,
boîtier de pédalier 180 g, charnières 150 g.

## 2. Leviers d'allègement chiffrés

| Levier | Gain | Remarque |
|---|---|---|
| Fourche et poutre en carbone stratifié | **− 250 g** | net, après surdimensionnement des zones d'appui |
| Jante 7075 → jante carbone enroulée | **− 240 g** | impose de repenser le tenon (insert titane collé) |
| Bandage alvéolaire → boyau pneumatique | − 90 g | gagne aussi 64 W, perd l'increvabilité |
| Chaîne → courroie crantée | + 50 g | plus lourd, mais supprime le graissage |
| Suppression de la suspension | − 220 g | **déconseillé** : × 2,4 sur les efforts de choc |

**Configuration « carbone » : 8 426 − 250 − 240 = 7 936 g**, objectif tenu avec
64 g de marge. C'est la configuration à retenir si les 8 kg sont une contrainte
ferme ; elle coûte cher et complique l'industrialisation.

## 3. Encombrement replié

### Volume utile retenu

490 × 280 × 195 mm = **26,8 L**, ce qui correspond au volume utile d'un sac à
dos 30 L à dos rigide (dimensions extérieures ≈ 530 × 310 × 220 mm).

### Organes repliés

| Organe | Encombrement | Volume solide | Remplissage |
|---|---|---|---|
| Demi-fagot de jante AV-a (4 arcs) | 198 × 120 × 54 | 0,85 L | 66 % |
| Demi-fagot de jante AV-b (4 arcs) | 198 × 120 × 54 | 0,85 L | 66 % |
| Demi-fagot de jante AR-a (4 arcs) | 198 × 120 × 54 | 0,85 L | 66 % |
| Demi-fagot de jante AR-b (4 arcs) | 198 × 120 × 54 | 0,85 L | 66 % |
| Moyeu à secteurs + disque AV | 144 × 144 × 102 | 0,29 L | 14 % |
| Moyeu à secteurs + disque AR | 144 × 144 × 102 | 0,29 L | 14 % |
| Module arrière (BdP, bras, mât rabattu) | 474 × 138 × 150 | 1,26 L | 13 % |
| Module avant (fourche monobras + direction) | 246 × 96 × 474 | 0,88 L | 8 % |
| Ensemble cintre | 288 × 150 × 72 | 0,68 L | 22 % |
| Poutre principale rétractée | 234 × 48 × 48 | 0,44 L | 81 % |
| Tige de selle + selle rabattue | 252 × 144 × 90 | 1,96 L | 60 % |
| Manivelles + pédales pliantes | 180 × 96 × 30 | 0,23 L | 45 % |
| Trousse (outils, pompe, sangles) | 192 × 78 × 48 | 0,72 L | 100 % |
| **TOTAL matière** | | **10,1 L** | |

### Vérification du rangement

La vérification n'est pas une somme de volumes — elle ne prouverait rien. Chaque
organe est décrit par une union de primitives (boîtes et cylindres à bouts
plats), **voxelisé au pas de 6 mm**, puis placé dans le volume utile par un
algorithme « meilleur ajustement » testant les 24 orientations axiales plus des
poses obliques, avec quatre ordres de rangement différents
(`calc/c06_encombrement.py`).

**Résultat : les 13 organes sont rangés.** Volume réellement occupé
**486 × 282 × 174 mm**, soit 23,8 L de l'enveloppe pour 10,1 L de matière
(38 % de remplissage solide, 37 % de voxels occupés).

Le plan de rangement obtenu (`plans/04-plan-de-rangement.svg`) sert directement
de définition pour la mousse de calage du sac.

## 4. Ce qui a rendu le rangement possible

Trois décisions, toutes issues du calcul d'encombrement :

1. **Fagots en deux paquets de 4 arcs** plutôt qu'un bloc de 8. Le cordon
   captif le permet. Une rangée de 8 arcs fait 240 mm de large et ne pave pas
   la section ; deux paquets de 4 font 120 mm et se placent partout.
2. **Manivelles démontables**. Elles imposaient 174 mm de section au module
   arrière (Q-factor 150 + Ø24) contre 120 mm sans elles.
3. **Monobras avant et arrière** (voir `docs/01`).

Sans ces trois points, le vélo demande environ 31 à 33 L et ne tient pas dans
un 30 L. C'est le résultat le plus fragile du dossier : il n'y a pas de marge
généreuse, il y a exactement ce qu'il faut.
