// Serveur local du cahier-journal. Zéro dépendance : uniquement la
// bibliothèque standard de Node, pour qu'aucun node_modules n'atterrisse dans
// iCloud Drive.
//
//   node app/serveur.mjs
//   CJ_DONNEES="/chemin/vers/iCloud/Cahier-journal" node app/serveur.mjs
//
// Les données sont des fichiers JSON lisibles : c'est la source de vérité,
// l'application n'est qu'un éditeur par-dessus.

import { createServer } from 'node:http';
import { readFile, writeFile, readdir, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, extname, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { rendSemaine } from './rendu.mjs';

const ICI = dirname(fileURLToPath(import.meta.url));
const PROJET = resolve(ICI, '..');
const DONNEES = resolve(process.env.CJ_DONNEES || join(PROJET, 'data'));
const PORT = Number(process.env.CJ_PORT || 4173);
// Boucle locale uniquement : l'application ne doit jamais être joignable
// depuis le réseau de la maison ou de l'école.
const HOTE = '127.0.0.1';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
};

const lisJSON = async p => JSON.parse(await readFile(p, 'utf8'));
const ecrisJSON = (p, o) => writeFile(p, JSON.stringify(o, null, 2) + '\n', 'utf8');

/** Les identifiants viennent de l'URL : ils ne doivent jamais pouvoir sortir du
 *  dossier de données. Sans ce filtre, « id=../../../ailleurs » ferait écrire
 *  n'importe où sur le disque. */
const NOM_SUR = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
function verifieNom(nom, quoi = 'identifiant') {
  if (typeof nom !== 'string' || !NOM_SUR.test(nom)) {
    const e = new Error(`${quoi} invalide`);
    e.code = 400;
    throw e;
  }
  return nom;
}
const fichierSemaine = id => join(DONNEES, 'semaines', `${verifieNom(id)}.json`);
const fichierEdt = ref =>
  join(DONNEES, `${verifieNom(ref, 'emploi du temps').replace(/^edt-/, 'emploi-du-temps-')}.json`);

// ------------------------------------------------------------- catalogue

/** Le catalogue s'enrichit tout seul : chaque activité saisie y entre, avec
 *  son matériel et les compétences qui lui ont été associées. */
async function majCatalogue(semaine) {
  const p = join(DONNEES, 'catalogue-activites.json');
  const cat = existsSync(p) ? await lisJSON(p) : { activites: [] };
  const index = new Map(cat.activites.map(a => [a.intitule.toLowerCase(), a]));

  for (const [jour, cfg] of Object.entries(semaine.jours ?? {})) {
    for (const creneau of Object.values(cfg.creneaux ?? {})) {
      for (const l of creneau.lignes ?? []) {
        const titre = (l.intitule ?? '').trim();
        if (titre.length < 3) continue;
        const cle = titre.toLowerCase();
        const a = index.get(cle) ?? { intitule: titre, usages: 0 };
        a.usages++;
        a.derniereUtilisation = semaine.lundi;
        if (l.materiel) a.materiel = l.materiel;
        if (l.domaine) a.domaine = l.domaine;
        const codes = new Set([...(a.competences ?? []), ...(l.competences ?? [])]);
        if (codes.size) a.competences = [...codes];
        if (!index.has(cle)) { index.set(cle, a); cat.activites.push(a); }
      }
    }
  }
  cat.activites.sort((x, y) => y.usages - x.usages || x.intitule.localeCompare(y.intitule));
  await ecrisJSON(p, cat);
  return cat;
}

// ------------------------------------------------------------- semaines

async function listeSemaines() {
  const d = join(DONNEES, 'semaines');
  if (!existsSync(d)) return [];
  const noms = (await readdir(d)).filter(n => n.endsWith('.json'));
  const out = [];
  for (const n of noms) {
    const s = await lisJSON(join(d, n));
    out.push({ id: n.replace(/\.json$/, ''), periode: s.periode,
               semaine: s.semaine, lundi: s.lundi });
  }
  return out.sort((a, b) => a.lundi.localeCompare(b.lundi));
}

function semaineVierge({ periode, semaine, lundi, edt }) {
  return { anneeScolaire: '2026-2027', periode: Number(periode),
           semaine: Number(semaine), lundi, emploiDuTemps: edt,
           contexte: '', jours: {} };
}

const identifiant = s =>
  `${s.lundi.slice(0, 4)}-P${s.periode}-S${String(s.semaine).padStart(2, '0')}`;

// ------------------------------------------------------------- contexte

async function contexte() {
  const edts = (await readdir(DONNEES))
    .filter(n => n.startsWith('emploi-du-temps-') && n.endsWith('.json'));
  const emploisDuTemps = [];
  for (const n of edts) emploisDuTemps.push(await lisJSON(join(DONNEES, n)));
  const catP = join(DONNEES, 'catalogue-activites.json');
  return {
    emploisDuTemps,
    referentiel: await lisJSON(join(DONNEES, 'referentiel-competences.json')),
    catalogue: existsSync(catP) ? await lisJSON(catP) : { activites: [] },
    semaines: await listeSemaines(),
    dossierDonnees: DONNEES,
  };
}

// ---------------------------------------------------------------- routes

const json = (res, o, code = 200) => {
  res.writeHead(code, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(o));
};

async function corps(req) {
  const bouts = [];
  for await (const b of req) bouts.push(b);
  return JSON.parse(Buffer.concat(bouts).toString('utf8') || '{}');
}

async function routes(req, res, url) {
  const id = url.searchParams.get('id');

  if (url.pathname === '/api/contexte') return json(res, await contexte());

  if (url.pathname === '/api/semaine' && req.method === 'GET') {
    const p = fichierSemaine(id);
    if (!existsSync(p)) return json(res, { erreur: 'introuvable' }, 404);
    return json(res, await lisJSON(p));
  }

  if (url.pathname === '/api/semaine' && req.method === 'PUT') {
    const semaine = await corps(req);
    await mkdir(join(DONNEES, 'semaines'), { recursive: true });
    await ecrisJSON(fichierSemaine(id), semaine);
    const catalogue = await majCatalogue(semaine);
    return json(res, { enregistre: true, catalogue });
  }

  if (url.pathname === '/api/semaine' && req.method === 'POST') {
    const params = await corps(req);
    const semaine = semaineVierge(params);
    const nouvelId = identifiant(semaine);
    await mkdir(join(DONNEES, 'semaines'), { recursive: true });
    if (existsSync(fichierSemaine(nouvelId)))
      return json(res, { erreur: 'cette semaine existe déjà', id: nouvelId }, 409);
    await ecrisJSON(fichierSemaine(nouvelId), semaine);
    return json(res, { id: nouvelId, semaine });
  }

  if (url.pathname === '/imprimer') {
    const semaine = await lisJSON(fichierSemaine(id));
    const edt = await lisJSON(fichierEdt(semaine.emploiDuTemps));
    const ref = await lisJSON(join(DONNEES, 'referentiel-competences.json'));
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    return res.end(rendSemaine(edt, semaine, ref));
  }

  // fichiers de l'interface
  const nom = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
  const p = join(ICI, 'ui', nom);
  if (!p.startsWith(join(ICI, 'ui')) || !existsSync(p)) {
    res.writeHead(404); return res.end('introuvable');
  }
  res.writeHead(200, { 'content-type': TYPES[extname(p)] ?? 'application/octet-stream' });
  res.end(await readFile(p));
}

createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  try {
    await routes(req, res, url);
  } catch (e) {
    console.error(e);
    if (!res.headersSent) json(res, { erreur: String(e.message ?? e) }, e.code ?? 500);
    else res.end();
  }
}).listen(PORT, HOTE, () => {
  console.log(`Cahier-journal   http://${HOTE}:${PORT}`);
  console.log(`Données          ${DONNEES}`);
});
