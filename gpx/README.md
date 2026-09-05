# Traces GPX — L'Étape du Tour au départ de Briançon

Deux éditions de L'Étape du Tour sont parties de Briançon : **2017** et **2022**.
Les fichiers ci-dessous reprennent les parcours officiels de ces deux étapes
(l'Étape du Tour emprunte le tracé de l'étape du Tour de France du même millésime).

| Fichier | Parcours | Distance | D+ | Cols |
|---|---|---|---|---|
| `etape-du-tour-2017-briancon-col-izoard.gpx` | Briançon → Col d'Izoard (16/07/2017, 25ᵉ édition — 18ᵉ étape du TdF 2017) | 179,8 km | ~3 600 m | Lac de Serre-Ponçon, Col de Vars (2 109 m), Guillestre, Col d'Izoard (2 360 m) |
| `etape-du-tour-2017-briancon-izoard-briancon-boucle.gpx` | Briançon → Izoard → Briançon (boucle fermée) | 201,5 km | ~3 700 m | idem + descente nord de l'Izoard par Cervières |
| `etape-du-tour-2022-briancon-alpe-d-huez.gpx` | Briançon → L'Alpe d'Huez (10/07/2022, 30ᵉ édition — 12ᵉ étape du TdF 2022) | 165,1 km | ~4 600 m | Col du Lautaret (2 058 m), Col du Galibier (2 642 m), Col de la Croix de Fer (2 067 m), L'Alpe d'Huez (1 850 m) |

## Note sur le « Briançon – Briançon »

Aucune édition de L'Étape du Tour n'a jamais fait Briançon → Briançon en boucle
officielle. L'édition la plus proche est celle de **2017** : départ de Briançon,
grande boucle par Serre-Ponçon et le Col de Vars, puis arrivée au sommet du
Col d'Izoard, qui redescend directement sur Briançon.

Le fichier `...-briancon-izoard-briancon-boucle.gpx` est donc le parcours 2017
**prolongé** par la descente nord de l'Izoard (D902 par Cervières) jusqu'au point
de départ, pour obtenir une vraie boucle Briançon – Briançon de 201 km. Ce
prolongement de 21,8 km n'est pas un tracé officiel : il a été calculé par
routage OpenStreetMap.

## Sources et méthode

- **2022 (Briançon → Alpe d'Huez)** : tracé officiel ASO de la 12ᵉ étape du Tour de
  France 2022, récupéré sur [cyclingstage.com](https://www.cyclingstage.com/tour-de-france-2022-gpx/)
  (`stage-12-parcours.gpx`). Altitudes d'origine conservées.
- **2017 (Briançon → Izoard)** : tracé officiel ASO de la 18ᵉ étape du Tour de
  France 2017, récupéré au format KML sur
  [cyclingstage.com](https://www.cyclingstage.com/tour-de-france-2017-route/stage-18-tdf-2017/)
  (`stage-18-route.kml`). Le KML ne contient pas d'altitude : elle a été
  reconstituée point par point sur le MNT **EU-DEM 25 m** via
  [OpenTopoData](https://www.opentopodata.org/), puis lissée par moyenne glissante
  (± 8 points, ~250 m) pour supprimer le bruit du modèle d'élévation.
- **Retour Izoard → Briançon** : calculé via [BRouter](https://brouter.de/) (profil
  `trekking`, données OpenStreetMap), altitudes SRTM fournies par BRouter.

Format : GPX 1.1, un seul `<trk>` / `<trkseg>` par fichier, altitudes en mètres.
Les fichiers s'importent directement dans Garmin Connect, Wahoo, Strava,
Komoot, RideWithGPS ou VisuGPX.

## Précisions

- Le départ des tracés 2017 correspond au **km 0** de l'étape (sortie sud-ouest de
  Briançon, N94), pas au départ fictif dans le centre-ville.
- Les distances officielles annoncées par ASO étaient de 179,5 km (2017, étape pro ;
  181 km pour la cyclosportive, qui partait du centre de Briançon) et 165,1 km (2022).
- Le dénivelé varie de quelques centaines de mètres selon l'outil de calcul et le
  modèle d'altitude utilisés ; les chiffres du tableau sont ceux mesurés sur ces
  fichiers avec un seuil de 3 m.

## Le week-end (5–6 septembre) — logement à La Salle-les-Alpes

On loge à **La Salle-les-Alpes** (Serre Chevalier, 1 437 m), 12 km au-dessus de Briançon
dans la vallée de la Guisane. Guillaume fait ses deux journées **en entier depuis le
logement** ; moi je descends en voiture à Briançon le samedi matin.

| Fichier | Parcours | Distance | D+ | Selle |
|---|---|---|---|---|
| `moi-samedi-briancon-guillestre-izoard.gpx` | Briançon → Guillestre par la rive gauche, combe du Queyras, Izoard, descente sur Briançon | 87,9 km | 1 740 m | ≈ 4 h 47 |
| `moi-dimanche-la-salle-galibier-la-salle.gpx` | La Salle → Lautaret → Galibier, demi-tour et retour | 55,0 km | 1 300 m | ≈ 3 h 08 |
| `guillaume-samedi-la-salle-izoard-la-salle.gpx` | Descente de la Guisane, boucle de L'Étape 2017, remontée sur La Salle | 226,5 km | 3 760 m | — |
| `guillaume-dimanche-la-salle-alpe-d-huez.gpx` | Parcours de L'Étape 2022 pris à La Salle (le tracé passe devant la porte) | 159,4 km | 4 400 m | — |

Le logement coûte **+25 km et +280 m** à Guillaume le samedi, et lui **fait gagner 6 km**
le dimanche puisque le parcours 2022 remonte la Guisane.

### Les deux trajets Briançon ⇄ La Salle

| Sens | Distance | D+ | Vélo |
|---|---|---|---|
| La Salle → Briançon (descente) | 11,9 km | +9 m | 21 min |
| Briançon → La Salle (remontée) | 13,1 km | +269 m | 48 min |

Asymétrique : la descente du matin est gratuite, la remontée du soir après l'Izoard ne
l'est pas. D'où la voiture.

### Les approches du samedi

| Fichier | Itinéraire | Distance | D+ | N94 |
|---|---|---|---|---|
| `approche-briancon-guillestre.gpx` | Rive gauche de [La Durance à Vélo](https://laduranceavelo.fr/) : Saint-Blaise, D4 des Traverses au-dessus de Prelles, Saint-Martin-de-Queyrières, D994E, L'Argentière, D138A, puis la N94 jusqu'à Mont-Dauphin et la D902A sur Guillestre — entièrement bitumé | 35,5 km | 290 m | 13,8 km |
| `approche-briancon-guillestre-balcon.gpx` | Variante panoramique par le balcon de Champcella (1 496 m) | 49,4 km | 1 088 m | 2 km |

Le verrou de la Durance impose 3,6 km à 2,8 % (+98 m) au km 3,8 à toutes les variantes ;
la montée finale sur Guillestre fait 4,3 km à 2,5 % (+108 m).

### Note sur les dénivelés

Les D+ de ce tableau sont mesurés sur un **profil lissé à 150 m avec un seuil de 8 m**,
pas sur les points bruts. Sur une trace GPS le seuil brut sur-compte lourdement : la
boucle de l'Izoard de vélo-maurienne donne 3 351 m en brut contre 2 251 m annoncés par
sa source, et 2 290 m avec la méthode lissée. Les chiffres ci-dessus sont donc 200 à
300 m plus bas que ceux publiés dans les versions précédentes de ce fichier.

## Visualisation
`roadbook-briancon.html` (à la racine) est une page autonome : le plan du week-end
Paris – Grenoble – Briançon – Oisans sur un fond OpenStreetMap embarqué (tuiles
standard zoom 12, de Grenoble au Queyras). Quatre couches : les deux étapes
intégrales, mon approche en solo, ce qu'on roule ensemble, et les trajets voiture et train. Chaque journée a un
bouton « cadrer sur la carte » qui isole ses couches et recadre la carte dessus.
Chaque jour de vélo a son profil altimétrique avec deux bandes indiquant qui est
sur le vélo ; survoler un profil place le point correspondant sur la carte.

Trajets calculés par routage OpenStreetMap (BRouter) :

| Trajet | Distance | Durée |
|---|---|---|
| Grenoble → La Salle-les-Alpes (Bourg-d'Oisans, Lautaret) | 109 km | 2 h 05 – 2 h 20 |
| La Salle-les-Alpes → L'Alpe d'Huez | 72 km | ≈ 1 h 50 |
| L'Alpe d'Huez → Grenoble | 63 km | ≈ 1 h 25 |
