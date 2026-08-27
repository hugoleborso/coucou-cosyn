#!/usr/bin/env node
/**
 * strava-capture-local
 * ---------------------------------------------------------------------------
 * À EXÉCUTER EN LOCAL (sur ta machine), PAS dans un conteneur distant.
 *
 * Ouvre un navigateur piloté, te laisse te connecter à Strava UNE fois, puis
 * "scanne le network" d'une activité et récupère le GPX :
 *   - capture l'XHR interne  /activities/{id}/streams?stream_types[]=...  → streams.json
 *   - télécharge directement  /activities/{id}/export_gpx                 → activite.gpx
 *
 * Le cookie de session (_strava4_session) reste sur ta machine, dans le
 * dossier de profil du navigateur (--profile). Il n'est jamais affiché,
 * committé ni envoyé ailleurs.
 *
 * Prérequis (en local) :
 *   npm i -D playwright        # ou : npx playwright install chromium
 *
 * Usage :
 *   node scripts/strava-capture-local.mjs <activityIdOuURL> [--profile <dossier>] [--out <prefixe>]
 *
 * Exemple :
 *   node scripts/strava-capture-local.mjs 2865391236
 *   node scripts/strava-capture-local.mjs https://www.strava.com/activities/2865391236 --out sortie
 *
 * Ensuite (fallback si export_gpx est bloqué mais que streams.json est là) :
 *   node scripts/strava-streams-to-gpx.mjs streams.json --start "<start_date ISO>" > activite.gpx
 */

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

function parseArgs(argv) {
  const o = { input: null, profile: null, out: 'activite' };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--profile') o.profile = argv[++i];
    else if (a === '--out') o.out = argv[++i];
    else if (a === '-h' || a === '--help') o.help = true;
    else if (!o.input) o.input = a;
  }
  return o;
}

function activityId(input) {
  if (!input) return null;
  const m = String(input).match(/activities\/(\d+)/) || String(input).match(/^(\d+)$/);
  return m ? m[1] : null;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help || !opts.input) {
    console.error(
      'Usage: node scripts/strava-capture-local.mjs <activityIdOuURL> [--profile <dossier>] [--out <prefixe>]',
    );
    process.exit(opts.help ? 0 : 1);
  }
  const id = activityId(opts.input);
  if (!id) {
    console.error(`Impossible d'extraire un id d'activité de: ${opts.input}`);
    process.exit(1);
  }

  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    console.error(
      "Playwright n'est pas installé. En local :\n" +
        '  npm i -D playwright && npx playwright install chromium',
    );
    process.exit(3);
  }

  const activityUrl = `https://www.strava.com/activities/${id}`;
  const streamsUrl =
    `${activityUrl}/streams?stream_types[]=latlng&stream_types[]=altitude` +
    `&stream_types[]=distance&stream_types[]=time`;
  const exportUrl = `${activityUrl}/export_gpx`;
  const profileDir = opts.profile || join(homedir(), '.strava-capture-profile');

  console.error(`\n▶ Profil navigateur : ${profileDir}`);
  console.error('▶ Ouverture du navigateur (fenêtre visible)…\n');

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 1280, height: 900 },
  });
  const page = context.pages()[0] || (await context.newPage());

  // --- Démonstration "scan du network" : on logue les requêtes de trace ---
  let capturedStreams = null;
  page.on('response', async (res) => {
    const u = res.url();
    if (/\/streams\?/.test(u) && res.status() === 200) {
      try {
        const j = await res.json();
        capturedStreams = j;
        console.error(`  [network] capturé streams XHR (${u.split('?')[0]})`);
      } catch {}
    }
  });

  // --- Attendre la connexion (Strava redirige les anonymes vers /login|/register) ---
  console.error('▶ Connecte-toi à Strava dans la fenêtre ouverte si demandé.');
  console.error('  (j\'attends que la page d\'activité s\'affiche, jusqu\'à 5 min)…');
  let loggedIn = false;
  const deadline = Date.now() + 5 * 60 * 1000;
  while (Date.now() < deadline) {
    try {
      await page.goto(activityUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    } catch {}
    const cur = page.url();
    if (!/\/(login|register|onboarding|challenges)/.test(cur)) {
      loggedIn = true;
      break;
    }
    await sleep(4000);
  }
  if (!loggedIn) {
    console.error('✗ Toujours pas connecté après 5 min. Relance et connecte-toi.');
    await context.close();
    process.exit(2);
  }
  console.error('✓ Session active. Récupération…\n');

  // Laisser la carte/analyse déclencher l'XHR streams
  await page.waitForTimeout(4000);

  // --- Récupération fiable via le contexte authentifié (cookies du profil) ---
  const outStreams = `${opts.out}.streams.json`;
  const outGpx = `${opts.out}.gpx`;

  // 1) streams JSON
  try {
    const r = await context.request.get(streamsUrl, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        Accept: 'application/json, text/plain, */*',
        Referer: activityUrl,
      },
    });
    if (r.ok()) {
      const body = await r.text();
      writeFileSync(outStreams, body);
      console.error(`✓ streams → ${outStreams} (${body.length} octets)`);
    } else {
      console.error(`… streams via request: HTTP ${r.status()} (on tentera le XHR capturé)`);
      if (capturedStreams) {
        writeFileSync(outStreams, JSON.stringify(capturedStreams));
        console.error(`✓ streams (depuis le network capturé) → ${outStreams}`);
      }
    }
  } catch (e) {
    console.error(`… streams: ${e.message}`);
  }

  // 2) export GPX direct
  try {
    const r = await context.request.get(exportUrl, { headers: { Referer: activityUrl } });
    const body = await r.text();
    if (r.ok() && /<gpx[\s>]/i.test(body)) {
      writeFileSync(outGpx, body);
      console.error(`✓ GPX  → ${outGpx} (${body.length} octets)`);
    } else {
      console.error(
        `… export_gpx: HTTP ${r.status()} — probablement une activité non exportable ` +
          `(visibilité de carte). Utilise le fallback streams→GPX.`,
      );
    }
  } catch (e) {
    console.error(`… export_gpx: ${e.message}`);
  }

  console.error(
    `\nSi seul ${outStreams} a été produit :\n` +
      `  node scripts/strava-streams-to-gpx.mjs ${outStreams} --start "<start_date ISO>" > ${outGpx}\n`,
  );
  await context.close();
}

main().catch((e) => {
  console.error('Erreur:', e);
  process.exit(1);
});
