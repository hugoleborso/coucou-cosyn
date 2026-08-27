# HANDOFF — capture live de la trace Strava & récupération du GPX (agent LOCAL)

> Ce handoff est destiné à un **agent Claude Code qui tourne en local** sur la
> machine de l'utilisateur (ou à l'utilisateur directement). Il fait suite à une
> session **distante** qui, elle, ne pouvait pas aboutir.

## Pourquoi un agent local

L'authentification du front Strava tient entièrement dans le cookie de session
**`_strava4_session`**, présent dans le **navigateur de l'utilisateur**, sur sa
machine. Une session Claude distante s'exécute dans un conteneur isolé : elle
n'a pas ce cookie, et le fait que l'utilisateur se connecte de son côté ne le lui
transmet pas. Vérifié : depuis le conteneur distant, `/activities/{id}` →
`307 → /register/free`, `export_gpx` et `streams` → `301/401`. **Il faut donc
exécuter la capture là où la session existe : en local.**

## Objectif

Pour une activité donnée (id ou URL), produire :
1. `*.gpx` — le fichier GPX de la trace ;
2. `*.streams.json` — le JSON brut de l'endpoint interne `streams` (fallback +
   preuve du « scan du network »).

## Ce qui est déjà établi (ne pas re-chercher)

Détails complets dans [`docs/strava-trace-gpx-extraction.md`](docs/strava-trace-gpx-extraction.md). En bref :

- Le front dessine un **aperçu** depuis une **polyline encodée** (Google Encoded
  Polyline) embarquée dans la page, puis une **carte Mapbox GL** qui charge la
  trace pleine résolution via l'XHR interne :
  `GET /activities/{id}/streams?stream_types[]=latlng&stream_types[]=altitude&stream_types[]=distance&stream_types[]=time`
  → JSON `{ "latlng": [[lat,lng],…], "altitude": […], "distance": […], "time": […] }`
  (`time` = secondes depuis le départ).
- Export direct : `GET /activities/{id}/export_gpx` (aussi `export_tcx`,
  `export_original`). C'est le bouton « … → Export GPX ».
- Auth : cookie `_strava4_session` (pas d'OAuth côté front).

## Prérequis local

```bash
git fetch origin claude/strava-trace-gpx-extraction-rzh2fw
git checkout claude/strava-trace-gpx-extraction-rzh2fw     # récupère docs + scripts
npm i -D playwright && npx playwright install chromium
```

## Méthode A — automatisée (recommandée, = « scan du network »)

Un script prêt à l'emploi : [`scripts/strava-capture-local.mjs`](scripts/strava-capture-local.mjs).
Il ouvre une **fenêtre visible**, laisse l'utilisateur se connecter **une fois**
(profil persistant, donc connexion réutilisée ensuite), écoute l'XHR `streams`,
puis récupère `streams.json` **et** `export_gpx` via le contexte authentifié.

```bash
node scripts/strava-capture-local.mjs <activityIdOuURL> --out sortie
# → sortie.streams.json  et  sortie.gpx
```

- Le cookie de session reste dans le dossier de profil local
  (`~/.strava-capture-profile` par défaut, ou `--profile <dossier>`). **Ne jamais
  committer/loguer/partager ce dossier ni le cookie.**
- Si `export_gpx` renvoie une erreur (activité d'autrui avec carte non
  exportable), utiliser le fallback ci-dessous sur `sortie.streams.json`.

## Méthode B — manuelle, zéro pilotage (fallback le plus simple)

1. Navigateur **déjà connecté** → ouvrir l'activité → DevTools → **Network**.
2. Filtrer `export` puis « … → Export GPX » : la requête `activities/{id}/export_gpx`
   télécharge le fichier. (Ou filtrer `streams`, clic droit sur la requête →
   *Copy response* → coller dans `streams.json`.)
3. Reconstruire depuis les streams si besoin :

```bash
node scripts/strava-streams-to-gpx.mjs streams.json --start "<start_date ISO>" > activite.gpx
```

## Vérification

```bash
xmllint --noout activite.gpx && echo "GPX bien formé"
head -20 activite.gpx    # doit contenir <trkpt lat=... lon=...>
```

## Contraintes

- **Périmètre** : faire ça sur **ses propres activités**, dans **son** navigateur.
  Les activités d'autrui respectent leur visibilité de carte (export refusé/expurgé).
- **CGU / robots.txt** : l'accès automatisé/en masse hors API est interdit par
  Strava ; `robots.txt` bloque même les crawlers IA. Pour tout usage
  programmatique ou en volume → **API v3 officielle** (OAuth, quotas),
  `GET /api/v3/activities/{id}/streams?keys=latlng,altitude,time&key_by_type=true`.
- **Secret** : `_strava4_session` équivaut au mot de passe pour la durée de la
  session — le garder strictement local.
