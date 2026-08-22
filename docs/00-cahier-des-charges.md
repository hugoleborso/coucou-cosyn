# 00 — Cahier des charges

## Besoin exprimé

Un vélo pliant qui tient **dans un sac à dos de 30 L compact**, pèse **8 kg au
maximum**, se monte facilement et reste fiable. Hypothèse de départ du
demandeur : les roues ne peuvent pas être des roues classiques, il faut quelque
chose de « télescopique ».

## Exigences retenues

| # | Exigence | Valeur | Vérifiée par |
|---|---|---|---|
| E1 | Volume replié | ≤ volume utile d'un sac 30 L compact, soit **490 × 280 × 195 mm = 26,8 L** | `c06_encombrement.py` |
| E2 | Masse à vide | ≤ 8,00 kg | `c05_masses.py` |
| E3 | Cycliste de dimensionnement | 85 kg + 5 kg de charge | `params.py` |
| E4 | Usage | urbain, dernier kilomètre, ≤ 8 km par trajet, chaussée dégradée admise | spectre de `c07_fatigue.py` |
| E5 | Temps de montage | ≤ 3 min, sans outil | `docs/05` |
| E6 | Aucune pièce libre | tout doit rester captif ou rangé dans un logement dédié | architecture |
| E7 | Durée de vie | 8 000 km et 3 000 cycles de montage | `c07_fatigue.py` |
| E8 | Sécurité structurelle | coefficients ci-dessous, cas de charge dérivés d'ISO 4210-2/-5/-6/-7 | `c02_cadre.py`, `c03_roue.py` |
| E9 | Deux freins indépendants | disques mécaniques Ø140 AV et AR | architecture |

## Coefficients de sécurité imposés

| Situation | Référence | Coefficient exigé |
|---|---|---|
| Charge nominale, domaine élastique | R<sub>e</sub> | 1,50 |
| Charge extrême (choc de trottoir) | R<sub>e</sub> | 1,25 |
| Pièces de sécurité (fourche, direction) | R<sub>m</sub> | 2,50 |
| Fatigue | courbe de Wöhler corrigée | 1,40 |
| Flambement | charge critique | 3,00 |
| Matage des portées d'emmanchement | pression admissible | 1,60 |

## Ce qui est explicitement hors périmètre

- Assistance électrique (change entièrement le bilan de masse).
- Vitesses multiples : le vélo est un mono-vitesse 34 × 12 (développement
  4,45 m/tour, soit 21 km/h à 80 tr/min).
- Homologation formelle EN ISO 4210 : les cas de charge s'en inspirent, mais
  la conformité exige des essais physiques, listés en `docs/05`.

## Résultat de synthèse

| Exigence | Cible | Obtenu | Statut |
|---|---|---|---|
| Volume replié | 26,8 L utiles | **10,1 L de matière, 486 × 282 × 174 mm occupés** | tenu |
| Masse | 8,00 kg | **8,43 kg ± 0,20** (alu) / **7,94 kg** (variante carbone) | non tenu en alu |
| Structure | 8 cas de charge | tous vérifiés, CS mini **1,43** | tenu |
| Roue | 6 cas de charge | CS mini **2,42** vs R<sub>e</sub> | tenu |
| Durée de vie | 8 000 km | **13 000 km** estimés (Miner) | tenu |
| Montage | ≤ 3 min | **2 min 30 estimées**, 5 gestes verrouillés | à confirmer par essai |

Le seul écart est la masse : 426 g au-dessus de l'objectif en construction
aluminium. Les leviers chiffrés pour y revenir sont en `docs/04`.
