# Enseignements du projet (apprentissages flaggés)

Notes techniques accumulées pendant la réalisation — utiles pour réutiliser les
API PRIM, reproduire l'analyse, ou affronter le même WAF.

## 1. API PRIM Île-de-France Mobilités — ce sont bien 2 API différentes

- **Vélo = Geovelo**, **Transports = Navitia** : URLs, verbes HTTP et formats de
  requête **distincts**. Il faut lire les deux docs séparément.
- **Navitia (transports)** — `GET /marketplace/v2/navitia/journeys`
  - Coordonnées au format **`lon;lat`** (longitude d'abord !), paramètres `from` / `to`.
  - Auth par header **`apikey`** (pas `Authorization`).
  - La réponse contient plusieurs `journeys` ; on prend `min(duration)` (secondes).
- **Geovelo (vélo)** — `POST /marketplace/computedroutes`
  - **Header `Source: prim` obligatoire** (sinon rejet) + `apikey` + `Content-Type: application/json`.
  - Corps JSON : `waypoints` (objets `latitude`/`longitude`), `transportModes:["BIKE"]`,
    `bikeDetails` (profil, vitesse…). Query `single_result=true` pour une seule route.
  - Durée dans `route.duration` (secondes).
- **Limite fonctionnelle** : pour 5 lycées de Seine-et-Marne à 46–59 km, Navitia
  renvoie **HTTP 404 `no_solution`** — pas de trajet TC calculable depuis Paris.
  Ce n'est pas un bug : c'est une vraie absence de solution. À gérer comme un `NaN`,
  pas comme une erreur réseau (le `min` retombe alors sur le vélo).
- Les **pages de doc** du portail PRIM renvoient 403 aux fetchers, mais les
  **endpoints d'API eux-mêmes répondent** en `curl` : tester directement l'endpoint
  est souvent plus rapide que de batailler avec la doc.

## 2. Le WAF de aladdin.ac-creteil.fr bloque tout accès automatisé

La page des zones (`liste_zones.php`) est protégée par un WAF qui **refuse l'accès
depuis un datacenter / IP cloud**. Tentatives et résultats :

| Méthode | Résultat |
|---------|----------|
| `curl` / `Chromium` (Playwright) via l'egress | Connexion **réinitialisée** (TLS reset) |
| WebFetch | **HTTP 503** systématique |
| Proxys serveur (allorigins, codetabs) | **522** (leur backend non plus n'atteint l'origine) |
| r.jina.ai | **401** (bad IP reputation) |
| Google Translate proxy | challenge anti-bot (PerimeterX) |
| Wayback Machine / archive.today | **bloqués par la politique egress** |

**Enseignement** : quand une source est derrière un WAF qui filtre les IP cloud,
aucun proxy hébergé en datacenter ne passe. La seule issue fiable est un **navigateur
réel sur IP résidentielle** — donc **demander le contenu à l'utilisateur** plutôt que
s'acharner. Ne jamais inventer les données manquantes.

**Résolution retenue** : contenu collé par l'utilisateur → `data/zones_source.txt`,
parsé par `parse_zones.py`. Reproductible et traçable.

## 3. Rapprochement des noms de communes

Les libellés diffèrent entre sources (casse, accents, tirets, `SAINT`/`ST`,
`-sur-Seine`…). `aggregate.py` **normalise** (NFKD sans accents, majuscules,
tirets/apostrophes → espaces) avant le join, et **signale les communes non
appariées** au lieu de les laisser filer silencieusement.

3 communes avec lycée absentes de la liste ALADDIN (Chailly-en-Brie, La Rochette,
Saint-Mammès) ont été rattachées **objectivement** : zone du lycée classé le plus
proche (1,6–4,4 km, vérifié par distance haversine), cohérent avec la carte des zones.

## 4. Outliers : la moyenne ment, la médiane et les moustaches sauvent

La consigne demandait `count` + **moyenne** du `min` par zone. Mais en grande
couronne, la **moyenne est tirée par des outliers** (lycées lointains sans TC,
chiffrés en vélo, 240–352 min). On a donc ajouté **médiane / min / max** et surtout
des **boîtes à moustaches par zone** qui exposent la dispersion et flaguent les
outliers. **Toujours accompagner une moyenne d'une mesure de dispersion** quand la
distribution peut être asymétrique.

## 5. Dataviz : la couleur se valide, elle ne se devine pas

- Palette catégorielle **validée CVD** (daltonisme) avant usage : `blue/green/orange`
  échoue (green↔orange indistinguables en protanopie, ΔE 3.2) ; **`blue/orange/violet`**
  passe tous les tests. → toujours faire tourner le validateur.
- Encodage **redondant** : couleur (petite/grande couronne) **+** tri **+** étiquettes
  directes, pour ne jamais dépendre de la seule couleur.
- Moyenne (losange) **et** médiane (trait) sur le même graphe = l'écart entre les
  deux **est** l'information sur les outliers.

## 6. Environnement d'exécution

- Repo cloné éphémère : tout livrable doit être **commité et poussé**.
- Chromium pré-installé (`/opt/pw-browsers`) — utile, mais inutile ici car l'egress
  re-termine le TLS : un vrai navigateur ne change pas l'IP vue par l'origine.
