# 01 — Architecture et justification des choix

## 1. Le problème central : un rapport de compacité de 8:1 sur la roue

Une roue de 500 mm de diamètre a un développement de 1 571 mm. Pour la loger
dans un sac dont la plus grande dimension utile est 490 mm, il faut réduire sa
plus grande dimension d'un facteur ≈ 2,5, et son emprise dans le plan d'un
facteur ≈ 8. Aucune roue rigide n'y arrive : une roue rigide qui rentre dans la
section 280 × 195 mm ferait 195 mm de diamètre, c'est-à-dire une roue de
trottinette — inconduisible sur chaussée dégradée et catastrophique en
résistance au roulement.

L'intuition « roue télescopique » est donc juste sur le fond. Reste à choisir
*comment*.

## 2. Étude comparative des architectures de roue

| Architecture | Principe | Masse (par roue) | Rigidité | Fiabilité | Compacité | Verdict |
|---|---|---|---|---|---|---|
| **A — Rayons télescopiques** | rayons tubulaires à 2 étages, jante en un seul morceau | ≈ 1,6 kg | bonne | 32 glissières chargées en flexion alternée, usure garantie | mauvaise : la jante d'un seul tenant reste un cercle de 500 mm | **rejeté** |
| **B — Jante repliante type parapluie** | 4 arcs articulés sur charnières captives | ≈ 1,4 kg | moyenne | 4 charnières dans le chemin d'effort principal | facteur 2 seulement : on obtient un demi-disque de 500 × 250 mm | **rejeté** |
| **C — Roue à moyeu-araignée en compression** | 16 jambes de force rigides, sans précontrainte | ≈ 1,45 kg | faible latéralement | jeu dans chaque rotule, cliquetis, usure | bonne | **rejeté** |
| **D — Jante segmentée + rayons tendus (retenue)** | 8 arcs assemblés par tenons coniques, 32 rayons acier, mise en tension par came | **1,36 kg** | excellente (3,7 kN/mm radial) | rayons en traction pure, joints en compression pure | 4 arcs × 2 rangées : paquet de 198 × 120 × 54 mm | **retenu** |

### Pourquoi D gagne

Dans une roue à rayons tendus, la jante travaille en **compression
circonférentielle** (3 510 N mesurés au calcul sous 700 N de précontrainte par
rayon). Or une jonction bout à bout par tenon conique reprend parfaitement la
compression et le cisaillement — c'est en traction qu'elle serait mauvaise. Le
calcul par éléments finis confirme que la portée des huit joints reste
**intégralement comprimée** (contrainte mini 12,9 MPa dans le cas le plus
défavorable, virage appuyé). Le concept est donc structurellement sain, pas un
compromis.

Deuxième avantage décisif : les rayons étant souples, **aucune articulation
n'est nécessaire**. Détendus, ils laissent les arcs se séparer ; tendus, ils
plaquent les arcs les uns contre les autres. Le mécanisme de pliage, c'est
l'absence de mécanisme.

### Comment les arcs restent captifs

Un cordon aramide de 4 mm passe dans le caisson de jante et traverse les huit
arcs, à la manière d'un **arceau de tente**. Replié, on obtient un chapelet de
huit arcs qui ne peut ni se perdre ni se mélanger ; déployé, le cordon guide
l'emboîtement et les tenons coniques à 6° font le centrage final.

## 3. Pneumatique ou bandage plein ?

C'est l'arbitrage le plus lourd de conséquences.

| Critère | Bandage alvéolaire PU (retenu) | Boyau pneumatique repliable |
|---|---|---|
| Résistance au roulement à 20 km/h | 107 W | 43 W |
| Crevaison | impossible | possible, et irréparable sur jante segmentée en déplacement |
| Montage | rien à faire | dégonfler pour plier, regonfler au montage (≈ 60 coups de pompe × 2) |
| Masse | 202 g/roue | 157 g/roue |
| Écrasement sous charge statique | 2,0 mm | ≈ 10 mm |

Le bandage plein est retenu **parce que la fiabilité était une exigence
explicite**, mais il coûte 64 W à 20 km/h — soit environ +55 % d'effort. C'est
un choix assumé, pas un détail : voir `docs/06` pour la variante pneumatique.

Conséquence structurelle immédiate : avec un bandage quasi rigide, un choc de
50 mm génère **2 490 N** à l'axe. D'où le point suivant.

## 4. La suspension n'est pas un luxe, c'est une conséquence du bandage plein

| Configuration | Raideur équivalente | Effort de choc (chute 50 mm) | Course |
|---|---|---|---|
| Sans suspension | 184 kN/m | **2 490 N** | 13,5 mm |
| Élastomère 30 mm AV et AR | 33 kN/m | **1 050 N** | 32 mm |

Un facteur 2,4 sur l'effort de choc pour 220 g. Deux blocs élastomère
progressifs de 30 mm de course, un dans le bras arrière, un dans la fourche.
C'est le meilleur rapport gain/masse de tout le projet, et cela conditionne le
dimensionnement du cadre (cas de charge F2).

## 5. Monobras avant et arrière

La fourche est **monobras** (côté droit) et le bras arrière aussi (côté
gauche, à l'opposé pour équilibrer). Trois raisons, dans cet ordre :

1. **Montage.** La roue s'enfile sur un tourillon et se bloque par un écrou
   central unique. Il n'y a plus d'axe traversant à présenter dans deux pattes
   en même temps, geste réputé pénible et qui se fait mal dans le noir ou avec
   des gants. C'est le point qui fait passer le montage d'une roue de ≈ 60 s à
   ≈ 25 s.
2. **Encombrement.** La section du module avant tombe de 234 × 132 mm à
   234 × 96 mm, ce qui débloque le pavage de la section du sac (voir `docs/04`).
3. **Cohérence avec la roue.** Le mécanisme de tension de la roue est déjà
   coaxial : le tourillon et la came partagent le même axe.

Coût : la fourche passe de deux tubes Ø25 × 2,2 à un tube Ø46 × 3,2, soit
+ 130 g environ. La vérification par éléments finis donne 107 MPa dans le
monobras au choc de trottoir, soit un coefficient de 4,7 sur R<sub>e</sub>.

## 6. Architecture du cadre : un module de puissance qui ne se démonte jamais

Le boîtier de pédalier, le bras arrière, le tourillon de roue arrière et le mât
de selle forment un **module rigide unique**. La boucle de chaîne n'est donc
jamais ouverte : pas d'attache rapide à manipuler, pas de chaîne qui traîne.
Tout le reste s'articule autour :

- **poutre principale télescopique 3 étages**, 522 mm déployée → 213 mm repliée ;
- **tige de selle télescopique 3 étages**, 453 → 186 mm ;
- **colonne de direction télescopique 1 étage** (Ø34 sur Ø29), 227 → 142 mm ;
- **cintre repliable** en deux demi-cintres ;
- **manivelles démontables** (vis auto-extractibles).

### Pourquoi la colonne de direction n'a qu'un étage

Le premier dimensionnement prévoyait trois étages télescopiques (Ø30 / Ø25,6 /
Ø21,4). Le calcul a montré une contrainte de **763 MPa** dans l'étage
supérieur sous l'essai statique de cintre à 600 N — soit 1,5 fois la limite
élastique. La raison est structurelle : un télescope place le tube le plus fin
là où le moment du cintre est maximal, ce qui est exactement l'inverse de ce
qu'il faudrait. Le passage à un seul étage à grand diamètre (Ø34 / Ø29) ramène
la contrainte à 171 MPa (CS 2,93) **et** double la rigidité de direction
(19,5 → 39,2 N·m/deg). C'est un cas où le calcul a invalidé une intuition de
conception.

## 7. Suppression du flou : l'expandeur conique

Un emmanchement coulissant a par construction un jeu radial (60 µm retenus).
Sans rattrapage, ce jeu produit un basculement de 0,059° par liaison, soit
**1,12 mm de flou cumulé au cintre** — perceptible et anxiogène. Chaque liaison
comporte donc un **expandeur conique 8°** qui dilate une douille fendue et
annule le jeu, actionné par un levier. Effort de tirant calculé : 1,1 à 2,6 kN
selon la liaison, obtenu à 1,3–3,2 N·m sur une vis M6.
