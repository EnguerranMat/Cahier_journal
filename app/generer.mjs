// Rend une semaine en HTML prêt à imprimer.
//   node app/generer.mjs data/semaines/2026-P1-S03.json [sortie.html]
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve, basename } from 'node:path';
import { rendSemaine } from './rendu.mjs';

const racine = resolve(dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1')), '..');
const lis = p => JSON.parse(readFileSync(resolve(racine, p), 'utf8'));

const cheminSemaine = process.argv[2];
if (!cheminSemaine) {
  console.error('usage : node app/generer.mjs <semaine.json> [sortie.html]');
  process.exit(1);
}

const semaine = lis(cheminSemaine);
const edt = lis(`data/${semaine.emploiDuTemps.replace('edt-', 'emploi-du-temps-')}.json`);
const ref = lis('data/referentiel-competences.json');

const sortie = resolve(racine,
  process.argv[3] ?? `build/${basename(cheminSemaine, '.json')}.html`);
mkdirSync(dirname(sortie), { recursive: true });
writeFileSync(sortie, rendSemaine(edt, semaine, ref), 'utf8');
console.log(sortie);
