// Rendu d'une semaine de cahier-journal : emploi du temps + saisie -> HTML A4.
// Zéro dépendance : le module ne fait que produire une chaîne de caractères.
// Le PDF est obtenu en imprimant cette page ; l'ajustement de la taille de
// police se fait dans le navigateur, une page par jour étant garantie.

const JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'];
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
  'août', 'septembre', 'octobre', 'novembre', 'décembre'];

const TEINTES = {
  'MS':      { fond: '#fbe8e4', bande: '#c9351b' },
  'GS':      { fond: '#e4eef7', bande: '#3f6f9e' },
  'MS + GS': { fond: '#eeeceb', bande: '#201e1d' },
};
const PAUSE = { fond: '#ffffff', bande: '#c9c5c2' };

const esc = s => String(s ?? '').replace(/[&<>"]/g, m =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));

const teinte = niveau => TEINTES[niveau] ?? TEINTES['MS + GS'];
const heure = h => h.replace(':', 'h');

// --------------------------------------------------------------- dates

function dateDe(lundiISO, decalage) {
  const d = new Date(lundiISO + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() + decalage);
  return d;
}
const enClair = d => `${d.getUTCDate()} ${MOIS[d.getUTCMonth()]}`;
const enClairAnnee = d => `${enClair(d)} ${d.getUTCFullYear()}`;

/** Numéro de semaine ISO — sert aux rotations qui alternent d'une semaine à l'autre. */
function semaineISO(lundiISO) {
  const d = dateDe(lundiISO, 0);
  const jeudi = new Date(d);
  jeudi.setUTCDate(d.getUTCDate() + 3);
  const premier = new Date(Date.UTC(jeudi.getUTCFullYear(), 0, 1));
  return Math.ceil(((jeudi - premier) / 86400000 + 1) / 7);
}

// --------------------------------------------------- compétences et groupes

function libelleCompetence(ref, code) {
  const [c, n] = [code.slice(0, code.lastIndexOf('-')), code.slice(code.lastIndexOf('-') + 1)];
  const comp = ref.competences.find(x => x.code === c);
  if (!comp) return code;
  if (comp.sansEtapes || !n) return `${c} — ${comp.libelle ?? comp.intitule}`;
  const etape = comp.etapes.find(e => String(e.numero) === n);
  return etape && etape.libelle
    ? `${c} · étape ${n} — ${etape.libelle}`
    : `${c} · étape ${n} — ${comp.intitule}`;
}

/** Groupe attribué à une ligne par la rotation déclarée dans l'emploi du temps. */
function groupeRotation(edt, ligne, jour, lundiISO) {
  const rot = edt.rotations?.[ligne.rotation];
  if (!rot || !ligne.atelier) return null;
  const n = rot.groupes.length;
  const decalage = rot.cycle === 'semaines'
    ? semaineISO(lundiISO)
    : Math.max(0, rot.cycle.indexOf(jour));
  return rot.groupes[(ligne.atelier - 1 + decalage) % n];
}

// ------------------------------------------------------------------ lignes

function fusionne(edt, semaine, ref, jour, creneau) {
  const saisie = semaine.jours?.[jour]?.creneaux?.[creneau.debut] ?? {};
  const modele = creneau.lignes ?? [{
    niveau: creneau.niveau, domaine: creneau.domaine, intitule: creneau.intitule,
    priseEnCharge: creneau.priseEnCharge, organisation: creneau.organisation,
    saisie: creneau.saisie,
  }];

  // La saisie peut ajouter des lignes (atelier supplémentaire un jour donné).
  const nb = Math.max(modele.length, (saisie.lignes ?? []).length);
  const lignes = [];
  for (let i = 0; i < nb; i++) {
    const m = modele[i] ?? modele[modele.length - 1] ?? {};
    const s = (saisie.lignes ?? [])[i] ?? {};
    const l = { ...m, ...s };
    if (l.supprimee) continue;

    const groupe = groupeRotation(edt, m, jour, semaine.lundi) ;
    l.groupe = s.groupe ?? groupe;

    const codes = s.competences ?? [];
    const prefixes = s.prefixesCompetences ?? [];
    l.competencesTexte = [
      ...codes.map((c, k) => (prefixes[k] ?? '') + libelleCompetence(ref, c)),
      ...(s.competencesLibres ?? []),
    ];
    lignes.push(l);
  }
  return lignes;
}

// ------------------------------------------------------------------- rendu

function rendLigne(l, pause) {
  const t = pause ? PAUSE : teinte(l.niveau);
  const droite = [l.domaine, l.priseEnCharge,
    l.groupe ? `${l.organisation} · ${l.groupe}` : l.organisation]
    .filter(Boolean).map(esc);
  const comps = l.competencesTexte.map(c =>
    `<div class="comp">${esc(c)}</div>`).join('');
  const materiel = l.materiel
    ? `<span class="mat"> · Matériel : ${esc(l.materiel)}</span>` : '';
  return `<div class="l" style="--fond:${t.fond};--bande:${t.bande}">
    <div class="lvl">${esc(l.niveau)}</div>
    <div class="corps"><div class="act">${esc(l.intitule || '')}${materiel}</div>${comps}</div>
    <div class="meta">${droite.map(x => `<div>${x}</div>`).join('')}</div>
  </div>`;
}

function rendCreneau(edt, semaine, ref, jour, creneau) {
  const pause = creneau.type === 'pause';
  const lignes = fusionne(edt, semaine, ref, jour, creneau)
    .map(l => rendLigne(l, pause)).join('');
  return `<div class="c">
    <div class="h"><b>${heure(creneau.debut)}</b><span>${heure(creneau.fin)}</span></div>
    <div class="lignes">${lignes}</div>
  </div>`;
}

function rendJour(edt, semaine, ref, jour, index) {
  const j = edt.jours.find(x => x.jour === jour);
  const conf = semaine.jours?.[jour] ?? {};
  if (conf.supprime) return '';
  const date = dateDe(semaine.lundi, index);
  const debut = enClair(dateDe(semaine.lundi, 0));
  const fin = enClairAnnee(dateDe(semaine.lundi, 4));
  const titre = jour[0].toUpperCase() + jour.slice(1)
    + (j.demiJournee === 'matin' ? ' · matinée' : '');

  const annotations = conf.annotations ? `<div class="notes">
    <div class="notes-t">Ajustements et annotations</div>
    <div class="lignes-vides"><i></i><i></i><i></i><i></i></div>
  </div>` : '';

  return `<section class="page">
    <div class="tete">
      <div class="tete-g"><div class="jour">${esc(titre)}</div><div class="date">${esc(enClair(date))}</div></div>
      <div class="tete-d">
        <div class="marque">Cahier-journal · MS / GS</div>
        <div class="sem">Période ${semaine.periode} · Semaine ${semaine.semaine} · ${debut} → ${fin}</div>
      </div>
    </div>
    <div class="filet"></div>
    ${conf.contexte || semaine.contexte
      ? `<div class="contexte">${esc(conf.contexte || semaine.contexte)}</div>` : ''}
    <div class="corps-page">
      ${j.creneaux.map(c => rendCreneau(edt, semaine, ref, jour, c)).join('')}
      ${annotations}
    </div>
    <div class="pied">
      <div class="leg">
        ${Object.entries(TEINTES).map(([k, t]) =>
          `<span><i style="background:${t.fond};border-left-color:${t.bande}"></i>${k}</span>`).join('')}
        <span><i style="background:#fff;border-left-color:#c9c5c2;box-shadow:inset 0 0 0 1px #e2dfdc"></i>Récréation · cantine</span>
      </div>
      <div class="leg-d">Colonne de droite : domaine · prise en charge · type de groupe</div>
    </div>
  </section>`;
}

export function rendSemaine(edt, semaine, ref) {
  const pages = JOURS.map((j, i) => rendJour(edt, semaine, ref, j, i)).join('');
  return GABARIT.replace('<!--PAGES-->', pages)
    .replace('<!--TITRE-->', esc(`Cahier-journal — P${semaine.periode} S${semaine.semaine}`));
}

// ---------------------------------------------------------------- gabarit

const GABARIT = `<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title><!--TITRE--></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&display=swap">
<style>
@page { size: A4 portrait; margin: 0; }
:root{ --e:1; }            /* échelle typographique, ajustée au chargement */
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
html,body{margin:0;padding:0;background:#e7e5e2}
body{font-family:Archivo,"Helvetica Neue",Arial,sans-serif;color:#201e1d}

.page{
  width:210mm; height:297mm; padding:8mm 8.5mm 6mm;
  background:#fff; margin:0 auto 8mm; display:flex; flex-direction:column;
  overflow:hidden;
}
@media print{ html,body{background:#fff} .page{margin:0;break-after:page} .page:last-child{break-after:auto} }

.tete{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;padding-bottom:4px}
.tete-g{display:flex;align-items:baseline;gap:14px}
.jour{font-size:calc(15pt * var(--e));font-weight:700;line-height:1}
.date{font-size:calc(9pt * var(--e));font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#6b6866}
.tete-d{text-align:right}
.marque{font-size:calc(7.5pt * var(--e));font-weight:700;letter-spacing:.14em;text-transform:uppercase}
.sem{font-size:calc(7pt * var(--e));font-weight:500;letter-spacing:.04em;color:#6b6866}
.filet{border-top:2px solid #201e1d}
.contexte{
  margin-top:4px;padding:3px 7px;border-left:3px solid #c9351b;background:#fbf1ef;
  font-size:calc(8pt * var(--e));font-weight:600;line-height:1.3;
}

.corps-page{flex:1 1 auto;min-height:0}
.c{display:grid;grid-template-columns:13mm 1fr;border-top:1px solid #d6d3d0;padding:1px 0}
.h{padding:2px 6px 2px 0}
.h b{display:block;font-size:calc(9.5pt * var(--e));font-weight:700;line-height:1.1}
.h span{display:block;font-size:calc(7pt * var(--e));font-weight:500;line-height:1.15;color:#8a8683}
.lignes{display:grid;gap:2px;min-width:0}

.l{display:grid;grid-template-columns:13mm 1fr 38mm;align-items:stretch;background:var(--fond);border-left:4px solid var(--bande)}
.lvl{white-space:nowrap;padding:3px 0 3px 6px;font-size:calc(8pt * var(--e));font-weight:700;line-height:1.2}
.corps{padding:3px 10px 3px 7px;min-width:0}
.act{font-size:calc(10pt * var(--e));font-weight:600;line-height:1.22;text-wrap:pretty}
.mat{font-weight:400;color:#4a4644}
.comp{font-size:calc(8.5pt * var(--e));font-weight:400;line-height:1.26;color:#3d3a38;text-wrap:pretty}
.meta{padding:3px 4px 3px 0;font-size:calc(7.5pt * var(--e));font-weight:500;line-height:1.2;color:#3d3a38}
.meta div:first-child{font-weight:700;color:#201e1d}

.notes{border-top:1px solid #d6d3d0;margin-top:10px;padding-top:7px}
.notes-t{font-size:calc(6.5pt * var(--e));font-weight:600;letter-spacing:.11em;text-transform:uppercase;color:#8a8683}
.lignes-vides{margin-top:12px;display:grid;gap:22px}
.lignes-vides i{display:block;border-bottom:1px solid #dedbd8}

.pied{border-top:2px solid #201e1d;margin-top:6px;padding-top:4px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.leg{display:flex;align-items:center;gap:12px}
.leg span{display:flex;align-items:center;gap:4px;font-size:calc(7pt * var(--e));font-weight:600}
.leg i{width:14px;height:9px;border-left:4px solid;display:block}
.leg-d{font-size:calc(6.5pt * var(--e));font-weight:400;color:#6b6866}
</style></head><body>
<!--PAGES-->
<script>
// Une page par jour : on prend la plus grande échelle qui tient encore.
(function ajuste(){
  const ECHELLES = [1.18, 1.14, 1.10, 1.06, 1.03, 1.00, 0.97, 0.94];
  for (const page of document.querySelectorAll('.page')){
    const corps = page.querySelector('.corps-page');
    for (const e of ECHELLES){
      page.style.setProperty('--e', e);
      page.dataset.echelle = e;
      if (corps.scrollHeight <= corps.clientHeight + 1) break;
    }
  }
})();
</script>
</body></html>`;
