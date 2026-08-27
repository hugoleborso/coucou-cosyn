# Strava — affichage de la trace en front & récupération du GPX

Analyse réalisée par observation directe du réseau (requêtes déconnecté sur
`www.strava.com`, août 2026) et corroborée par la documentation Strava.

## TL;DR

- **Oui, on peut récupérer le GPX en scannant le network** — à condition d'être
  **connecté** (tout passe par le cookie de session `_strava4_session`, pas par
  un token OAuth).
- Le front affiche la trace en deux temps : une **aperçu** dessiné depuis une
  **polyline encodée** (Google Encoded Polyline) embarquée dans la page, puis la
  **carte interactive Mapbox GL** qui charge la trace pleine résolution via un
  **XHR interne** `GET /activities/{id}/streams?stream_types[]=latlng…`.
- Trois façons de sortir la trace, par ordre de qualité :
  1. **`GET /activities/{id}/export_gpx`** → le fichier GPX directement (c'est le
     bouton « Export GPX »).
  2. **Reconstruire** un GPX depuis le JSON de `/streams` (latlng + altitude +
     time). Script fourni : [`scripts/strava-streams-to-gpx.mjs`](../scripts/strava-streams-to-gpx.mjs).
  3. **Décoder la polyline** de la page (dégradé : simplifiée, sans temps ni
     altitude — bon pour la forme du tracé seulement).
- **Réserve importante** : les CGU Strava interdisent le scraping/l'accès
  automatisé hors API officielle, et `robots.txt` bloque explicitement les
  crawlers IA. Le faire **à la main, sur ses propres activités**, dans son
  navigateur, est banal ; l'**automatiser** ou viser les données d'autrui sort
  du cadre. La voie propre est l'**API v3** (OAuth).

---

## 1. Comment le front affiche la trace

### 1.1 Authentification : cookie de session obligatoire

Une requête **déconnecté** sur une page d'activité est renvoyée vers l'inscription :

```
GET https://www.strava.com/activities/{id}
→ HTTP/2 307
  location: /register/free
  set-cookie: _strava4_session=…; Domain=.strava.com; HttpOnly; Secure
```

Toute la suite (page, carte, streams, export) est donc gardée par le cookie
**`_strava4_session`**. Il n'y a **pas** de token OAuth côté front : le navigateur
est déjà authentifié par ce cookie, ce qui rend le « rejeu » d'une requête
trivial une fois connecté.

### 1.2 L'aperçu : une polyline encodée dans la page

La page d'activité embarque l'objet `map` de l'activité, avec deux chaînes
encodées au format **Google Encoded Polyline** :

- `map.summary_polyline` — tracé simplifié/sous-échantillonné (vignette, listes) ;
- `map.polyline` — tracé complet en résolution « carte ».

Ces chaînes servent à dessiner l'**aperçu** immédiatement, sans requête réseau
supplémentaire. Une polyline se décode en une liste de points `[lat, lng]` (pas
d'altitude, pas d'horodatage).

### 1.3 La carte interactive : Mapbox GL + XHR `streams`

La carte détaillée est rendue avec **Mapbox GL JS**. Pour l'analyse (profil
d'altitude, survol, tracé pleine résolution), le front déclenche un **XHR vers un
endpoint interne** — distinct de l'API OAuth publique :

```
GET https://www.strava.com/activities/{id}/streams?stream_types[]=latlng&stream_types[]=altitude&stream_types[]=distance&stream_types[]=time
Cookie: _strava4_session=…
X-Requested-With: XMLHttpRequest
```

Réponse (JSON), un tableau par type demandé, tous alignés sur le même index
temporel :

```json
{
  "latlng":   [[48.8566, 2.3522], [48.8567, 2.3523], …],
  "altitude": [35.2, 35.4, …],
  "distance": [0.0, 4.7, …],
  "time":     [0, 1, 3, …]
}
```

- `latlng` : paires `[lat, lng]` en degrés.
- `altitude` : mètres. `distance` : mètres cumulés. `time` : **secondes depuis le
  départ** (offset, pas un timestamp absolu).

> Selon la variante de requête, l'endpoint peut aussi renvoyer chaque type sous
> la forme `{"type":"latlng","data":[…]}`. Le script fourni gère les deux formes.

C'est **cet appel** qui contient la trace complète et exploitable : c'est le
meilleur candidat au « scan du network ».

---

## 2. Les endpoints observés (preuves)

Sondes **déconnecté** sur une activité réelle. Le code de statut est parlant :
`401` = la route **existe** et exige la session ; `404` = la route n'existe pas
sous cette forme ; `301/307` = redirection vers le login.

| Requête (déconnecté) | Statut | Lecture |
|---|---|---|
| `GET /activities/{id}` | `307 → /register/free` | Mur de connexion, pose `_strava4_session` |
| `GET /activities/{id}/streams?stream_types[]=latlng` | **`401`** | **Endpoint XHR interne réel**, auth par cookie |
| `GET /activities/{id}/streams/latlng,altitude` | `404` | Forme « API v3 » — n'existe pas sur `www` |
| `GET /stream/{id}` | `404` | Ancien endpoint, disparu (et `Disallow` robots) |
| `GET /activities/{id}/export_gpx` | **`401`** | **Export GPX direct**, auth par cookie |
| `GET /activities/{id}/export_tcx` | **`401`** | Export TCX (avec fréquence cardiaque/puissance) |
| `GET /activities/{id}/export_original` | **`401`** | Fichier d'origine (souvent le `.fit`/`.gpx` uploadé) |

Autrement dit : connecté, `export_gpx` et `streams?stream_types[]=…` passent de
`401` à `200`.

---

## 3. Récupérer le GPX — trois méthodes

### Méthode A — `export_gpx` (la plus propre)

```
GET https://www.strava.com/activities/{id}/export_gpx
Cookie: _strava4_session=…
```

Renvoie **le GPX directement**. C'est exactement ce que fait le bouton
« … → Export GPX » de la page. Variantes : `export_tcx` (garde cardio/puissance),
`export_original` (le fichier tel qu'uploadé).

**Contraintes de propriété/visibilité** :
- Ses **propres** activités : toujours exportables (fichier complet).
- Activités **d'autrui** : soumis à leur réglage de visibilité de carte ; l'export
  peut être refusé, et Strava retire certaines données de performance.

### Méthode B — reconstruire depuis `/streams`

Si on ne « voit » dans le network que l'XHR `streams`, on reconstitue un GPX
valide en zippant `latlng` + `altitude` (+ `time` pour les horodatages). C'est le
cas d'usage du script fourni :

```bash
# 1. Dans l'onglet Network, clic droit sur la requête .../streams?... → "Copy → Copy response"
#    et coller dans streams.json  (ou "Save response" / "Copy as cURL" puis rejeu).
# 2. Générer le GPX :
node scripts/strava-streams-to-gpx.mjs streams.json \
     --start "2026-08-27T07:12:30Z" \
     --name "Sortie du matin" > activite.gpx
```

`--start` (le `start_date` de l'activité) est optionnel : sans lui, les
trackpoints sont écrits sans balise `<time>` (le GPX reste géographiquement
correct). Avec lui, chaque `time[i]` (secondes) devient un timestamp absolu.

### Méthode C — décoder la polyline (dégradé)

`map.summary_polyline` / `map.polyline` de la page se décodent en `[lat,lng]`
(algorithme Google). Rapide mais **sans temps ni altitude**, et **simplifié** :
utile pour la forme du parcours, pas pour un GPX fidèle.

---

## 4. Recette « scan du network » reproductible

1. Se connecter sur `strava.com` (le cookie `_strava4_session` est alors présent).
2. Ouvrir une activité → DevTools → onglet **Network**.
3. Filtrer sur `streams` : apparaît `activities/{id}/streams?stream_types[]=…`
   (JSON `latlng`). Filtrer sur `export` puis cliquer « … → Export GPX » : apparaît
   `activities/{id}/export_gpx`.
4. Pour rejouer hors navigateur : **clic droit → Copy → Copy as cURL** (la commande
   embarque le cookie de session), ou ouvrir directement l'URL `…/export_gpx` dans
   l'onglet connecté.

> Le cookie de session est un secret équivalent au mot de passe pour la durée de
> vie de la session : ne pas le committer, le logger ni le partager.

---

## 5. La voie officielle (recommandée pour tout usage programmatique)

**Strava API v3** — `GET https://www.strava.com/api/v3/activities/{id}/streams`
avec `keys=latlng,altitude,time,distance&key_by_type=true` et un token OAuth
(`Authorization: Bearer …`, scope `activity:read` / `activity:read_all`).

- Avantages : contractuel, stable, documenté, pas de fragilité liée au front.
- Limites : enregistrement d'une application, **quotas** (par défaut ~100 req/15 min,
  ~1 000/jour), OAuth à implémenter, accès limité aux activités autorisées par le
  scope.

C'est la seule voie **sanctionnée** pour un traitement automatisé ou en volume.

---

## 6. Cadre légal / ToS / robots.txt

- Les **CGU** et l'**API Agreement** de Strava interdisent le scraping et l'accès
  automatisé/en masse en dehors de l'API officielle.
- `robots.txt` (constaté) : `Disallow: /` pour les crawlers IA nommément
  (`ClaudeBot`, `GPTBot`, `Google-Extended`, `Meta-ExternalAgent`) ; pour `*`,
  `Disallow` sur `/api/`, `/stream/`, et de nombreux `/activities/*/…` d'analyse
  (`/heartrate`, `/segments`, `/route`, `/laps`, …). `export_gpx` et `streams`
  n'y figurent pas explicitement, mais l'esprit des CGU couvre l'automatisation.
- **Confidentialité** : les activités d'autrui respectent leurs réglages de
  visibilité ; l'export peut être bloqué ou expurgé.

**En clair** : usage manuel sur ses propres données dans son navigateur → normal.
Automatisation, volume, ou données de tiers → passer par l'**API v3** et respecter
les quotas et le consentement.
