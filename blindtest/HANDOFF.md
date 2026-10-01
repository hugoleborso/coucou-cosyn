# Handoff : blind test par équipe dans la PWA offsite

Document écrit le 2026-10-01 vers 20h. Le jeu a lieu le 2026-10-02 vers 22h, à la soirée bisca.

## Ce qui est demandé

Hugo veut ajouter un blind test à la PWA du voyage Theodo. Le blind test est proposé par Camille et se joue sur ses sons custom. Hugo a fixé les règles suivantes :

- le jeu n'est visible qu'une fois activé par un admin ;
- une liste de sons donne les bonnes réponses ;
- seule la première bonne réponse de chaque équipe compte ;
- les points sont donnés par équipe, dans l'ordre d'arrivée des réponses ;
- l'accès simultané de tous les joueurs est le gros risque technique.

Le but est d'engager le plus de Theodoers possible, parce que le blind test au buzzer frustre tout le monde sauf le plus rapide. La spec complète est dans [`spec.md`](./spec.md).

## Ce que ce dossier n'est pas

Ce dépôt (`coucou-cosyn`) ne contient pas le code de la PWA. Il sert seulement de support à ce handoff. Le code de la PWA est dans `github.com/marek-e/v0-offsite-pwa`. Hugo n'y a pas encore accès : Marek Elmayan doit l'ajouter ce soir. Vincent Duarte a envoyé le dépôt en zip à Hugo sur Slack (DM du 2026-10-01 à 19h11, fichier `v0-offsite-pwa-main.zip`), ainsi qu'une copie du Sheet de prod (`bdd.xlsx`). Ces fichiers ne sont pas recopiés ici : le code appartient à un autre dépôt, et le Sheet contient des données personnelles.

## Ce qui a été fait

1. Lecture des échanges Slack : le DM avec Vincent Duarte et le canal #blindtest-soiree-bisca.
2. Analyse du code de la PWA. C'est du Next.js 16 sur Vercel, avec une connexion Google (NextAuth). Toutes les données sont dans un Google Sheet, lu et écrit par un seul compte de service. Il existe déjà un jeu par équipe (`lib/game-sheets.ts`), une page admin réservée à `ADMIN_EMAILS`, une page de scores qui lit le bloc `teams | Score` de l'onglet `game_config`, et des notifications push.
3. Comptage dans le Sheet de prod : 18 équipes de 12 membres, soit environ 216 joueurs.
4. Inventaire du dossier Drive des musiques et brouillon de l'onglet `blindtest_tracks`.
5. Rédaction de la spec avec Hugo, en suivant à peu près le skill `specification` du dépôt `borso.fr`.

Aucun code n'a été écrit. Une copie locale du zip existait dans la session avec une branche `feat/blindtest`, mais elle n'a été poussée nulle part et disparaît avec le conteneur.

## Décisions prises avec Hugo

| Sujet | Décision |
| --- | --- |
| Format | Réponse libre dans la PWA, sur le téléphone de chaque joueur. Des ardoises papier servent de plan B si le réseau du bar lâche. |
| Ce qui compte | Le titre ou l'artiste. Ce sont deux courses séparées, et chacune vaut la moitié des points. |
| Comparaison | Tolérante aux fautes, avec normalisation et distance de Levenshtein. Hugo a écrit « Jev », qu'on a compris comme une comparaison floue. C'est à confirmer. |
| Barème | Rang 1 = 10, rang 2 = 9, … minimum 1, divisé par 2 pour chaque partie. |
| Stockage en direct | Upstash Redis, ajouté depuis le marketplace Vercel. `SET NX` garantit une seule réponse retenue par équipe, et `RPUSH` donne le rang. |
| Diffusion de l'état | Les téléphones interrogent le serveur toutes les 2 s pendant un son, avec un cache de 1 s par instance. |
| Son | Joué par l'animateur sur la sono du bar, pas dans l'application. |

## Pourquoi le Google Sheet ne suffit pas

L'API Google Sheets limite chaque utilisateur à 60 écritures par minute et par projet ([doc](https://developers.google.com/workspace/sheets/api/limits)). La PWA écrit avec un seul compte de service, donc 216 joueurs qui répondent dans la même demi-minute provoqueraient des erreurs 429. De plus, `upsertGamePhoto` vide l'onglet puis le réécrit en entier : deux écritures simultanées s'écraseraient. Enfin, le cache serveur (`lib/server-cache.ts`) est propre à chaque instance Vercel, donc il ne peut pas servir de verrou.

## Points encore ouverts

- **Camille** doit valider l'ordre des sons et les réponses acceptées. Le [dossier Drive](https://drive.google.com/drive/folders/1k27pnIFj2KEXNcm1gnbVTEvS3mnk6cuZ) contient 21 reprises custom, chacune étant un tube rejoué dans un autre style (par exemple *Lose Yourself* d'Eminem en country), plus les 21 originaux. La réponse est donc le titre et l'artiste de l'original. Un brouillon des 21 lignes est dans [`blindtest_tracks.csv`](./blindtest_tracks.csv), prêt à coller dans l'onglet `blindtest_tracks`. L'ordre est une proposition : *Ce matin va être une pure soirée* est placé en dernier, puisque la dernière musique lance la soirée.
- **Rythme :** 21 sons en environ 20 minutes laissent moins d'une minute par son. Ouvrir et fermer un son doit donc se faire en un tap chacun. Après chaque son, l'animateur peut passer quelques secondes de l'original.
- **Écran :** on ne sait pas s'il y a un projecteur au bar. La page `/blindtest/screen` est prévue quand même, et elle s'ouvre aussi sur un téléphone.
- **Admins :** Hugo et Camille doivent figurer dans `ADMIN_EMAILS` sur Vercel. Changer cette variable demande un redéploiement.
- **Maquettes :** il n'y en a pas. Les écrans sont décrits en mots dans la spec.

## Prochaines étapes, dans l'ordre

1. Marek ajoute Hugo au dépôt et ajoute Upstash Redis au projet Vercel. Les variables d'environnement sont injectées automatiquement.
2. Coder la logique pure (`lib/blindtest-match.ts`, `lib/blindtest-scoring.ts`) avec des tests vitest.
3. Coder le stockage Redis et les trois routes d'API (`/api/blindtest`, `/api/blindtest/guess`, `/api/blindtest/admin`).
4. Coder l'écran joueur `/blindtest` et la carte sur la page d'accueil.
5. Coder la section admin, puis le bouton « Publier les scores » qui écrit une seule fois dans `teams | Score`.
6. Coder l'écran `/blindtest/screen`.
7. Écrire le script de charge `scripts/blindtest-load.mjs`. Il envoie 216 réponses simultanées et vérifie une seule réponse retenue par équipe et par partie, et des rangs de 1 à 18 sans trou.
8. Répétition le 2026-10-02 après-midi sur un déploiement de preview, avec 5 vrais téléphones et le script de charge.
9. Avant 22h : imprimer les ardoises du plan B et préparer la notification push d'annonce.
