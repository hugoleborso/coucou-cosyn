# 05 — Montage, fiabilité, plan d'essais

## 1. Procédure de montage

Objectif : moins de 3 minutes, sans outil, cinq verrouillages contrôlables.

### Roues (≈ 25 s chacune)

1. **Dérouler le chapelet d'arcs.** Les 8 arcs sont enfilés sur le cordon
   aramide : ils ne peuvent ni se perdre ni s'inverser.
2. **Fermer l'anneau.** Les tenons coniques 6° sont autocentrants ; le dernier
   joint se ferme à la main.
3. **Engager le moyeu**, puis 1/16<sup>e</sup> de tour : les 8 secteurs
   baïonnette capturent les 8 groupes de rayons simultanément.
4. **Rabattre le levier de came.** Les brides s'écartent de 2,55 mm et les
   32 rayons montent à 700 N d'un seul geste.
5. **Contrôle** : le témoin de tension passe au vert quand le levier est
   sur-centré.

### Vélo (≈ 90 s)

6. Déployer la poutre principale jusqu'à l'index de butée usiné, rabattre
   l'expandeur (E1 puis E2).
7. Déployer la colonne de direction, rabattre l'expandeur (E3), déplier les
   deux demi-cintres.
8. Déployer la tige de selle à la hauteur indexée, rabattre les expandeurs
   (E4, E5).
9. Basculer le mât de selle en position et verrouiller le cône.
10. Poser les manivelles (vis auto-extractibles, 1/4 de tour chacune).
11. Enfiler les roues sur leur tourillon, serrer l'écrou central.

**Contrôle avant départ, 4 points** : les 5 témoins d'expandeur sont verts, les
2 leviers de came de roue sont sur-centrés, les 2 écrous centraux sont serrés,
les 2 leviers de frein ont une course inférieure à la moitié.

## 2. Ce qui ne peut pas être perdu

| Élément | Captivité |
|---|---|
| 8 arcs de jante × 2 | cordon aramide traversant |
| 32 rayons × 2 | sertis dans les arcs et dans les secteurs de moyeu |
| Tubes télescopiques | butée d'extraction usinée dans chaque étage |
| Expandeurs, leviers de came | imperdables (vis captive) |
| Manivelles | seuls organes réellement démontés — logement dédié dans la mousse |

Les manivelles sont le seul point faible de cette liste. Alternative si le
risque est jugé inacceptable : manivelles repliables à charnière, environ
+ 90 g et un maillon supplémentaire dans le chemin d'effort de pédalage.

## 3. Tenue en fatigue sur spectre

Cumul de Miner sur un spectre de service ramené à 8 000 km (pédalage régulier
et en côte, rotation de roue sur chaussée lisse et dégradée, joints de chaussée
et pavés, trottoirs, nids-de-poule).

| Sous-ensemble | Élément | Dommage à 8 000 km | Durée de vie estimée |
|---|---|---|---|
| Cadre | tige de selle étage 1 | 0,607 | **13 200 km** |
| Jante | siège de rayon | 0,615 | **13 000 km** |
| Rayons | coude / filetage, K<sub>f</sub> = 2,2 | ≈ 0 | > 10⁹ cycles |

Coefficient sur l'objectif : **1,6**. Le dommage du cadre est dominé à 99 % par
le bloc « pédalage en côte / démarrage » (8 % du kilométrage, facteur 2,1) et
celui de la jante se répartit entre chaussée dégradée, trottoirs et
nids-de-poule — donc entre événements rares et sévères, ce qui rend l'estimation
sensible au profil d'usage réel.

## 4. Cycles de montage / démontage (3 000 visés)

| Organe | Mode de dégradation | Statut |
|---|---|---|
| Tenon conique de jante | matage Al/Al anodisé dur | à qualifier par essai — critère : jeu < 0,05 mm après 3 000 cycles |
| Expandeur conique | traction du tirant M6 en 42CrMo4, σ<sub>a</sub> = 92 MPa | illimité |
| Came de tension de moyeu | contact hertzien came/poussoir, acier cémenté 58 HRC, p<sub>max</sub> = 1 100 MPa | ≈ 10⁶ cycles |
| Cordon captif aramide | flexion alternée sur rayon 25 mm | **pièce d'usure déclarée**, remplacement tous les 2 000 cycles |

## 5. Analyse des modes de défaillance

| # | Défaillance | Effet | Cotation | Parade retenue |
|---|---|---|---|---|
| 1 | Levier de came non sur-centré | perte de tension des rayons, voile puis effondrement | **critique** | témoin de tension visible + butée sur-centrée + contrôle au point 5 |
| 2 | Joint de jante mal emboîté | désaffleurement, choc à chaque tour, ouverture progressive | **critique** | tenon 6° autocentrant ; le vélo ne peut pas rouler droit si un joint est ouvert (défaut immédiatement perceptible) |
| 3 | Expandeur non serré | flou de direction de 1,1 mm, puis glissement en longueur | **majeur** | index de butée mécanique : le tube ne peut pas rentrer sous charge, il ne peut que flotter |
| 4 | Écrou central de roue desserré | perte de roue | **critique** | écrou à créneaux + goupille bêta captive |
| 5 | Manivelle oubliée dans le sac | vélo inutilisable | mineur | logement mousse à silhouette + liste de contrôle sérigraphiée |
| 6 | Rupture du cordon captif | les arcs deviennent 8 pièces libres | majeur | pièce d'usure à remplacement périodique ; le vélo reste roulable, seul le pliage devient risqué |
| 7 | Fatigue de la poutre principale (CS 1,43) | rupture au boîtier | **critique** | contrôle visuel périodique ; à surveiller en priorité au prototype |

## 6. Plan d'essais du premier prototype

**Priorité 1 — invalider ou valider le concept de roue**

- E1. Essai radial statique sur roue seule : montée jusqu'à 3 000 N, mesure de
  la flèche, comparaison au 3 720 N/mm calculé.
- E2. Essai de tension : mesure de la tension des 32 rayons au tensiomètre
  après 20 cycles de montage — dispersion attendue ≤ ± 8 %.
- E3. Endurance en roulement : 200 000 tours sous 650 N sur tambour à
  obstacles, contrôle du désaffleurement aux joints toutes les 20 000 tours.
- E4. Essai de matage des tenons : 3 000 cycles d'emboîtement, mesure du jeu.

**Priorité 2 — cadre**

- E5. ISO 4210-2 essai de fatigue en pédalage (100 000 cycles à 1 100 N).
- E6. ISO 4210-2 essai de choc (masse tombante, 22,5 kg à 180 mm).
- E7. ISO 4210-5 essai statique et de fatigue guidon/potence.
- E8. Mesure de la raideur de direction : la valeur calculée (39 N·m/deg) est
  basse, il faut savoir si c'est perceptible.

**Priorité 3 — usage**

- E9. Chronométrage du montage par 10 utilisateurs non entraînés, à froid, sans
  notice. Critère : 90 % sous 4 min au troisième essai.
- E10. Mesure de la résistance au roulement du bandage alvéolaire sur tambour.
  La valeur retenue (C<sub>rr</sub> = 0,020) est une estimation et pilote
  directement l'acceptabilité du vélo.
