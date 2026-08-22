# 03 — Roue déployable : définition et vérification

## 1. Définition

| Caractéristique | Valeur |
|---|---|
| Diamètre hors-tout | 500 mm |
| Jante | 8 arcs de 45°, caisson extrudé 7075-T6 24 × 22 × 1,4 mm |
| Rayon fibre neutre | 227,5 mm |
| Jonctions | tenons coniques 6°, autocentrants |
| Captivité | cordon aramide Ø4 traversant les 8 arcs (principe de l'arceau de tente) |
| Rayons | 32, inox 18/8 Ø1,8/1,6, croisés 2, précontrainte 700 N |
| Sièges de rayon | inserts rapportés rayon 3 mm (K<sub>t</sub> = 1,8) |
| Moyeu | corps à 8 secteurs baïonnette + 2 brides écartables |
| Mise en tension | came à levier, course 5,1 mm, effort ≈ 103 N crête |
| Bande de roulement | PU alvéolaire 11,5 × 28 mm, densité relative 0,32 |
| Frein | disque Ø140 solidaire du moyeu |
| Masse | 1 362 g par roue |

## 2. Comportement mécanique

### 2.1 Principe

La précontrainte des rayons crée une **compression circonférentielle de
3 510 N** dans la jante. Cette compression est ce qui ferme les huit joints.
Les tenons coniques ne travaillent donc jamais en traction — c'est le point
qui rend le concept viable.

### 2.2 Enveloppe de phase

Un piège identifié en cours d'étude : selon la position angulaire de la roue,
le point de contact au sol tombe ou non sur un joint. Une position figée donne
un résultat trop favorable (66 MPa au lieu de 199 MPa dans les premiers
calculs). **La roue tourne : chaque joint passe sous la charge.** Tous les
résultats ci-dessous sont donc des enveloppes sur un balayage de la phase de
roue en 8 à 12 positions.

### 2.3 Résultats

| Cas | P radial | T max | T min | Rayons détendus | Flèche radiale | k radial | σ locale |
|---|---|---|---|---|---|---|---|
| W1 statique AR | 643 N | 736 N | 555 N | 0 | 0,17 mm | 3 720 N/mm | 93 MPa |
| W2 choc vertical AV | 1 020 N | 757 N | 470 N | 0 | 0,22 mm | 4 608 N/mm | 124 MPa |
| W3 choc vertical AR | 1 606 N | 790 N | 337 N | 0 | 0,30 mm | 5 410 N/mm | 172 MPa |
| W4 virage appuyé AR | 1 028 N + 385 lat. | 901 N | 142 N | 0 | 0,22 mm | 4 629 N/mm | **208 MPa** |
| W5 freinage AV 0,45 g | 574 N + 120 N·m | 897 N | 423 N | 0 | 0,18 mm | 3 252 N/mm | 92 MPa |
| W6 nid-de-poule oblique | 829 N + 383 lat. | 910 N | 188 N | 0 | 0,20 mm | 4 220 N/mm | 191 MPa |

- **Aucun rayon ne se détend**, dans aucun cas. La tension mini descend à
  142 N sur les 700 N de précontrainte : la marge est réelle mais pas énorme,
  c'est ce qui a fixé le nombre de rayons à 32.
- Cas extrême : 208 MPa pour R<sub>e</sub> = 503 MPa → **CS 2,42**.
- Cas courant : 93 MPa pour une limite d'endurance de 159 MPa → **CS 1,71**.

### 2.4 État des joints (cas dimensionnant W4)

| θ | N (compression) | M | V | e = M/N | Noyau | σ max | σ mini |
|---|---|---|---|---|---|---|---|
| 45° | 3 722 N | 3,12 N·m | 74 N | 0,84 mm | 7,59 mm | 34,2 MPa | 27,4 MPa |
| 225° | 3 735 N | 8,43 N·m | 155 N | 2,26 mm | 7,59 mm | 40,1 MPa | 21,7 MPa |
| **270°** (contact sol) | 3 595 N | 15,39 N·m | 133 N | **4,28 mm** | 7,59 mm | 46,5 MPa | **12,9 MPa** |
| 315° | 3 752 N | 7,92 N·m | 47 N | 2,11 mm | 7,59 mm | 39,6 MPa | 22,4 MPa |

σ mini reste **strictement positive sur les huit joints** : la portée est
intégralement comprimée, le joint ne s'entrouvre jamais.

> Note de calcul : le noyau central d'une section creuse vaut Z/A, soit
> 7,59 mm ici, et non h/6 = 3,67 mm (valeur du rectangle plein). La première
> version du script utilisait h/6 et concluait à tort à l'ouverture d'un joint.

### 2.5 Flambement de l'anneau

Charge radiale répartie appliquée par les rayons : 15 428 N/m.
Charge critique de l'anneau (inertie pénalisée de 55 % pour tenir compte des
joints) : 83 021 N/m. **Marge 5,4** pour 3,0 exigés.

## 3. Mécanisme de mise en tension

Les deux brides du moyeu s'écartent axialement de 2,55 mm sous l'action d'une
came à levier logée dans l'axe creux. Chaque rayon s'allonge de 0,365 mm, ce
qui développe exactement 700 N (raideur de rayon 1,92 MN/m, longueur 209,5 mm).

| Grandeur | Valeur |
|---|---|
| Course de came | 5,10 mm |
| Poussée axiale par bride | 1 604 N |
| Effort au levier (90 mm), moyen / crête | 47 N / **103 N** |
| Sensibilité du réglage | 27 N de tension par 0,1 mm |

L'effort crête est comparable à celui d'un blocage rapide de roue classique.
La sensibilité de 27 N/0,1 mm impose un écrou de réglage fin à l'opposé de la
came, réglé une fois en atelier — exactement la logique d'un blocage rapide.

## 4. Étude de sensibilité

### Nombre de rayons (jante 24 × 22 × 1,4, 6 arcs)

| Rayons | Masse | σ extrême | CS/R<sub>e</sub> | T min | σ fatigue | CS 10⁶ |
|---|---|---|---|---|---|---|
| 18 | 89 g | 127 MPa | 3,96 | 71 N | 84 MPa | 2,07 |
| 24 | 115 g | 115 MPa | 4,39 | 96 N | 83 MPa | 2,09 |
| 30 | 140 g | 121 MPa | 4,15 | 151 N | 92 MPa | 1,87 |
| 36 | 166 g | 120 MPa | 4,19 | 244 N | 95 MPa | 1,82 |

Le nombre de rayons ne pilote pratiquement pas la contrainte : il pilote la
**marge de détension**. C'est le critère de choix.

### Concentration de contrainte au siège de rayon

Sur l'ensemble des configurations testées, passer de K<sub>t</sub> = 2,5
(perçage brut) à K<sub>t</sub> = 1,8 (insert rapporté) réduit la contrainte
locale de 28 % pour une masse quasi nulle — davantage que d'ajouter 8 rayons ou
4 mm de hauteur de jante. **C'est le meilleur levier de la roue.**

## 5. Limites du modèle

- Le moyeu est supposé indéformable : la raideur latérale réelle sera
  inférieure aux 1,22 mm sous 385 N calculés ici.
- La rigidification géométrique due à la précontrainte n'est pas prise en
  compte (effet du second ordre, favorable).
- La bande de roulement n'est pas modélisée : elle répartit la charge de
  contact sur un arc plus grand que les trois nœuds retenus. Hypothèse
  conservative.
- Le comportement dynamique (résonance de jante, 4 impacts de joint par tour
  en cas de désaffleurement) n'est pas traité et doit l'être par l'essai.
