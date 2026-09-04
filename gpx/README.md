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

## Mes traces à moi (week-end du 19–20 septembre)

Les deux journées prêtes à importer dans un compteur, avec la jonction à Guillestre
le samedi et l'aller-retour au Galibier le dimanche.

| Fichier | Parcours | Distance | D+ |
|---|---|---|---|
| `moi-samedi-briancon-guillestre-izoard.gpx` | Briançon → Guillestre par le balcon de Champcella, puis combe du Queyras, Izoard et descente sur Briançon | 102,3 km | 2 700 m |
| `moi-dimanche-briancon-galibier-briancon.gpx` | Briançon → Lautaret → Galibier, demi-tour et retour | 66,6 km | 1 344 m |

### Les approches du samedi

| Fichier | Itinéraire | Distance | D+ |
|---|---|---|---|
| `approche-briancon-guillestre.gpx` | Balcon de Champcella, section haute-Durance de la véloroute [La Durance à Vélo](https://laduranceavelo.fr/) : Prelles, L'Argentière, Pallon, Champcella, Saint-Crépin, Mont-Dauphin | 49,4 km | 1 088 m |
| `approche-briancon-guillestre-vallee.gpx` | Rive gauche par Saint-Martin-de-Queyrières puis la vallée — évite la N94 sur la première moitié | 36,7 km | 462 m |

La véloroute est balisée en continu, sur petites routes bitumées partagées avec les
voitures, et donnée « moyen » avec des passages à plus de 6 %. Les approches sont
calculées par routage OpenStreetMap (BRouter, profil `fastbike-lowtraffic`) ; le reste
est découpé dans les parcours officiels ASO.

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
| Grenoble → Briançon (Bourg-d'Oisans, Lautaret) | 117 km | 2 h 15 – 2 h 30 |
| Briançon → L'Alpe d'Huez | 79 km | ≈ 2 h |
| L'Alpe d'Huez → Grenoble | 63 km | ≈ 1 h 25 |
