# 02 — Étude structurelle

## 1. Méthode

Le calcul repose sur un **solveur éléments finis poutres 3D écrit pour le
projet** (`calc/fem.py`, 12 ddl par élément, relâchements d'extrémité par
condensation statique, barres précontraintes « tension only » pour les rayons).

Le solveur est validé sur sept cas à solution analytique fermée
(`calc/test_fem.py`) : flexion et torsion de console, traction, poutre
bi-appuyée obtenue par relâchement, treillis à deux barres en effort et en
flèche, désactivation d'une barre comprimée. **Écart maximal : 1,9 × 10⁻¹⁴**,
c'est-à-dire la précision machine.

Deux modèles utilisent ce solveur :

- **Cadre** : 26 nœuds, 24 éléments, sections tubulaires réelles. Les
  emmanchements télescopiques sont représentés par des tronçons courts de
  rigidité EI réduite (rendement η = 0,60), avec **récupération de contrainte
  sur la section réelle** — le moment se répartit entre tube extérieur et tube
  intérieur au prorata des inerties, la section fictive ne sert qu'à la
  rigidité.
- **Roue** : 40 nœuds de jante, 32 barres de rayon en tension-only, moyeu
  supposé indéformable, tronçons de joint à inertie réduite. Les tensions de
  montage sont **égalisées par itération**, ce qui reproduit le dévoilage réel
  et supprime la dispersion artificielle due à la raideur variable de la jante.

## 2. Cas de charge du cadre

Dérivés d'ISO 4210-2 (cadre), -5 (guidon/potence) et -6 (pédalage).

| Cas | Description | Critère | CS exigé |
|---|---|---|---|
| F1 | Statique assis, 90 kg répartis 60/15/25 | R<sub>e</sub> | 1,50 |
| F2 | Choc de trottoir avant, 1 050 N à l'axe (filtré par l'élastomère) | R<sub>e</sub> | 1,25 |
| F3 | Choc de trottoir arrière, 1,9 g à la selle | R<sub>e</sub> | 1,25 |
| F4 | Pédalage en danseuse, 1 100 N pédale + 600 N latéral (ISO 4210-6) | R<sub>e</sub> | 1,50 |
| F5 | Freinage avant à la limite de basculement (0,63 g) | R<sub>e</sub> | 1,50 |
| F6 | Cintre 600 N sur une extrémité (ISO 4210-5 statique) | R<sub>e</sub> | 1,50 |
| F6b | Cintre ± 270 N, 10⁵ cycles (ISO 4210-5 fatigue) | Wöhler | 1,40 |
| F7 | Pédalage 550 N, 10⁶ cycles ≈ 5 000 km | Wöhler | 1,40 |

Le cas F2 utilise une **méthode d'inertie-relief** : l'amplitude du chargement
appliqué aux trois points d'appui du cycliste est calée pour que la réaction
verticale à l'axe avant vaille exactement l'effort de choc calculé. Sans cela
l'effort part directement dans l'appui et le cadre n'est pas sollicité — erreur
détectée et corrigée en cours d'étude.

## 3. Résultats — cadre

| Cas | Élément critique | σ<sub>VM</sub> | Limite | CS obtenu | CS exigé | |
|---|---|---|---|---|---|---|
| F1 | tige de selle ét. 1 | 61 MPa | 503 | **8,22** | 1,50 | ✔ |
| F2 | tige de selle ét. 1 | 182 MPa | 503 | **2,76** | 1,25 | ✔ |
| F3 | tige de selle ét. 1 | 194 MPa | 503 | **2,59** | 1,25 | ✔ |
| F4 | hauban arrière | 253 MPa | 503 | **1,99** | 1,50 | ✔ |
| F5 | cintre | 175 MPa | 503 | **2,88** | 1,50 | ✔ |
| F6 | cintre | 171 MPa | 503 | **2,93** | 1,50 | ✔ |
| F6b | colonne de direction | 95 MPa | 185 | **1,95** | 1,40 | ✔ |
| F7 | poutre principale ét. 1 | 95 MPa | 138 | **1,43** | 1,40 | ✔ |

**Le cas dimensionnant est F7**, la fatigue de pédalage sur la poutre
principale, avec une marge de 3 % seulement sur le coefficient exigé. C'est là
qu'il ne faut rien retirer.

Les limites de fatigue proviennent d'une droite de Basquin calée sur
0,9 R<sub>m</sub> à 10³ cycles et sur l'amplitude à 10⁷ cycles du matériau,
corrigée de l'état de surface (0,9), de l'effet d'échelle (0,9), d'un effet
d'entaille aux raccords collés-goupillés (K<sub>f</sub> = 1,25) et de la
contrainte moyenne par la droite de Goodman.

## 4. Raideurs caractéristiques

| Grandeur | COSYN-30 | Référence |
|---|---|---|
| Raideur latérale au boîtier de pédalier | **157 N/mm** | vélo de ville acier : 60–90 N/mm |
| Raideur de direction en torsion | **39 N·m/deg** | VTT alu : 60–110 N·m/deg |
| Déplacement du cintre sous 200 N | 3,3 mm | — |
| Flèche de selle sous 800 N | 2,8 mm | — |

Le cadre est très rigide latéralement. La direction, elle, reste en dessous des
références : c'est le prix des tubes télescopiques, et c'est la caractéristique
à surveiller au premier prototype. La sensibilité au rendement des
emmanchements est faible (36,1 à 43,6 N·m/deg pour η de 0,35 à 1,00), ce qui
signifie que la souplesse vient des **sections**, pas des liaisons : il ne sert
à rien de sur-serrer, il faudrait grossir les tubes.

## 5. Emmanchements télescopiques

| Liaison | M enveloppe | Recouvrement | Mini calculé | Matage | CS matage | Flou si non serré | Tirant | Couple vis |
|---|---|---|---|---|---|---|---|---|
| Poutre 1-2 | 244 N·m | 58 mm | 20 mm | 9,0 MPa | 2,78 | 0,54 mm | 1 117 N | 1,3 N·m |
| Poutre 2-3 | 169 N·m | 58 mm | 16 mm | 6,9 MPa | 3,61 | 0,36 mm | 1 163 N | 1,4 N·m |
| Selle 1-2 | 165 N·m | 52 mm | 21 mm | 10,5 MPa | 2,39 | 0,35 mm | 1 577 N | 1,9 N·m |
| Selle 2-3 | 83 N·m | 52 mm | 13 mm | 6,8 MPa | 3,70 | 0,18 mm | 1 919 N | 2,3 N·m |
| Direction | 140 N·m | 58 mm | 16 mm | 7,2 MPa | 3,46 | 0,22 mm | 2 644 N | 3,2 N·m |

Les recouvrements sont dictés par la **longueur repliée**, pas par la
résistance : le mini calculé est 3 à 4 fois inférieur. Il n'y a donc aucun
risque de matage, et la marge peut servir à tolérer l'usure sur 3 000 cycles.

## 6. Ce que le calcul a fait changer dans la conception

Le dossier n'est pas une justification a posteriori. Quatre décisions viennent
directement du calcul :

1. **Colonne de direction : 3 étages → 1 étage à grand diamètre.** 763 MPa
   relevés sur l'étage supérieur (§ `docs/01`, point 6).
2. **Ajout de la suspension élastomère.** Le calcul d'effort de choc donnait
   2 490 N sans elle, 1 050 N avec.
3. **Siège de rayon avec insert rapporté** plutôt que perçage brut :
   K<sub>t</sub> passe de 2,5 à 1,8, ce qui à lui seul fait passer la jante de
   non conforme à conforme en fatigue — pour une masse quasi nulle. C'est le
   levier le plus efficace de toute l'étude de la roue, devant le nombre de
   rayons et l'épaisseur de jante.
4. **Manivelles démontables et plateau ramené de 38 à 34 dents.** Le module
   arrière passait de 174 × 156 mm à 120 × 147 mm de section, ce qui a débloqué
   le pavage de la section du sac.
