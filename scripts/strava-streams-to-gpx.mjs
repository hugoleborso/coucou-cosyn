#!/usr/bin/env node
/**
 * strava-streams-to-gpx
 * ---------------------------------------------------------------------------
 * Convertit la réponse JSON de l'endpoint interne du front Strava
 *   GET /activities/{id}/streams?stream_types[]=latlng&stream_types[]=altitude&stream_types[]=time
 * (celle qu'on récupère dans l'onglet Network) en un fichier GPX 1.1 valide.
 *
 * Le script ne parle à aucun réseau : il transforme un JSON déjà capturé.
 *
 * Usage :
 *   node scripts/strava-streams-to-gpx.mjs streams.json [options] > activite.gpx
 *   cat streams.json | node scripts/strava-streams-to-gpx.mjs -   [options] > activite.gpx
 *
 * Options :
 *   --start <ISO>   Instant de départ de l'activité (activity.start_date), ex.
 *                   "2026-08-27T07:12:30Z". Utilisé pour transformer les offsets
 *                   `time` (secondes) en timestamps <time> absolus. Sans lui, les
 *                   trackpoints sont écrits sans <time> (GPX géographiquement valide).
 *   --name <texte>  Nom de la trace (<trk><name>).
 *   --out <fichier> Écrit dans un fichier plutôt que sur stdout.
 *
 * Formes JSON acceptées (les deux que renvoie Strava selon la variante) :
 *   A) { "latlng": [[lat,lng],…], "altitude": [..], "time": [..] }
 *   B) { "latlng": { "data": [[lat,lng],…] }, "altitude": { "data": [..] }, … }
 *   C) [ { "type":"latlng", "data":[…] }, { "type":"altitude", "data":[…] }, … ]
 */

import { readFileSync, writeFileSync } from 'node:fs';

function parseArgs(argv) {
  const opts = { start: null, name: null, out: null, input: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--start') opts.start = argv[++i];
    else if (a === '--name') opts.name = argv[++i];
    else if (a === '--out') opts.out = argv[++i];
    else if (a === '-h' || a === '--help') opts.help = true;
    else if (!opts.input) opts.input = a;
  }
  return opts;
}

function usage() {
  return `Usage: node scripts/strava-streams-to-gpx.mjs <streams.json|-> [--start ISO] [--name NOM] [--out fichier]`;
}

/** Récupère le tableau d'un type de stream quelle que soit la forme du JSON. */
function pickStream(json, type) {
  if (Array.isArray(json)) {
    const entry = json.find((s) => s && s.type === type);
    return entry ? entry.data : undefined;
  }
  if (json && typeof json === 'object') {
    const v = json[type];
    if (Array.isArray(v)) return v;
    if (v && Array.isArray(v.data)) return v.data;
  }
  return undefined;
}

function xmlEscape(s) {
  return String(s).replace(/[<>&'"]/g, (c) => ({
    '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;',
  }[c]));
}

function buildGpx({ latlng, altitude, time, startMs, name }) {
  const lines = [];
  lines.push('<?xml version="1.0" encoding="UTF-8"?>');
  lines.push(
    '<gpx version="1.1" creator="strava-streams-to-gpx" ' +
      'xmlns="http://www.topografix.com/GPX/1/1" ' +
      'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' +
      'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">',
  );
  lines.push('  <trk>');
  if (name) lines.push(`    <name>${xmlEscape(name)}</name>`);
  lines.push('    <trkseg>');

  for (let i = 0; i < latlng.length; i++) {
    const pt = latlng[i];
    if (!Array.isArray(pt) || pt.length < 2) continue;
    const [lat, lon] = pt;
    if (typeof lat !== 'number' || typeof lon !== 'number') continue;
    lines.push(`      <trkpt lat="${lat}" lon="${lon}">`);
    if (altitude && typeof altitude[i] === 'number') {
      lines.push(`        <ele>${altitude[i]}</ele>`);
    }
    if (startMs != null && time && typeof time[i] === 'number') {
      const iso = new Date(startMs + time[i] * 1000).toISOString();
      lines.push(`        <time>${iso}</time>`);
    }
    lines.push('      </trkpt>');
  }

  lines.push('    </trkseg>');
  lines.push('  </trk>');
  lines.push('</gpx>');
  return lines.join('\n') + '\n';
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help || !opts.input) {
    process.stderr.write(usage() + '\n');
    process.exit(opts.help ? 0 : 1);
  }

  const raw =
    opts.input === '-'
      ? readFileSync(0, 'utf8')
      : readFileSync(opts.input, 'utf8');

  let json;
  try {
    json = JSON.parse(raw);
  } catch (e) {
    process.stderr.write(`Erreur: JSON invalide (${e.message})\n`);
    process.exit(1);
  }

  const latlng = pickStream(json, 'latlng');
  if (!Array.isArray(latlng) || latlng.length === 0) {
    process.stderr.write(
      "Erreur: aucun stream 'latlng' trouvé. Vérifie que la capture contient bien " +
        'stream_types[]=latlng.\n',
    );
    process.exit(1);
  }
  const altitude = pickStream(json, 'altitude');
  const time = pickStream(json, 'time');

  let startMs = null;
  if (opts.start) {
    const t = Date.parse(opts.start);
    if (Number.isNaN(t)) {
      process.stderr.write(`Erreur: --start non parsable en date: ${opts.start}\n`);
      process.exit(1);
    }
    startMs = t;
  }

  const gpx = buildGpx({ latlng, altitude, time, startMs, name: opts.name });

  if (opts.out) {
    writeFileSync(opts.out, gpx);
    process.stderr.write(
      `GPX écrit dans ${opts.out} — ${latlng.length} points` +
        `${startMs != null ? ' (avec horodatage)' : ' (sans <time>)'}\n`,
    );
  } else {
    process.stdout.write(gpx);
  }
}

main();
