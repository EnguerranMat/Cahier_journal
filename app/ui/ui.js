// Éditeur de semaine. L'emploi du temps fournit le squelette ; la semaine ne
// stocke que ce qu'Audrey saisit réellement.

const JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'];
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
  'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const TEINTES = {
  'MS': ['var(--ms)', 'var(--ms-fond)'],
  'GS': ['var(--gs)', 'var(--gs-fond)'],
  'MS + GS': ['var(--mixte)', 'var(--mixte-fond)'],
};

const $ = s => document.querySelector(s);
const el = (t, p = {}, ...enfants) => {
  const n = Object.assign(document.createElement(t), p);
  for (const e of enfants.flat()) if (e != null) n.append(e);
  return n;
};

let CTX = null;      // référentiel, catalogue, emplois du temps, liste des semaines
let EDT = null;
let SEM = null;      // la semaine en cours d'édition
let ID = null;
let JOUR = 'lundi';
let cible = null;    // ligne visée par la palette de compétences

// ------------------------------------------------------------------ dates

const dateDe = (lundi, n) => {
  const d = new Date(lundi + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d;
};
const enClair = d => `${d.getUTCDate()} ${MOIS[d.getUTCMonth()]}`;

// ----------------------------------------------------- accès aux données

/** Renvoie (en la créant au besoin) la ligne saisie pour un créneau donné. */
function saisie(jour, debut, i) {
  SEM.jours ??= {};
  SEM.jours[jour] ??= {};
  SEM.jours[jour].creneaux ??= {};
  SEM.jours[jour].creneaux[debut] ??= { lignes: [] };
  const c = SEM.jours[jour].creneaux[debut];
  c.lignes ??= [];
  while (c.lignes.length <= i) c.lignes.push({});
  return c.lignes[i];
}
const saisieLue = (jour, debut, i) =>
  SEM.jours?.[jour]?.creneaux?.[debut]?.lignes?.[i] ?? {};

function libelleCompetence(code) {
  const [c, n] = [code.slice(0, code.lastIndexOf('-')), code.slice(code.lastIndexOf('-') + 1)];
  const comp = CTX.referentiel.competences.find(x => x.code === c);
  if (!comp) return { code, texte: code };
  if (comp.sansEtapes) return { code: c, texte: comp.libelle ?? comp.intitule };
  const e = comp.etapes.find(x => String(x.numero) === n);
  return { code: `${c} · étape ${n}`, texte: e?.libelle ?? comp.intitule };
}

function groupeRotation(ligne, jour) {
  const rot = EDT.rotations?.[ligne.rotation];
  if (!rot || !ligne.atelier) return null;
  const semaineISO = () => {
    const d = dateDe(SEM.lundi, 3);
    const p = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil(((d - p) / 86400000 + 1) / 7);
  };
  const dec = rot.cycle === 'semaines' ? semaineISO() : Math.max(0, rot.cycle.indexOf(jour));
  return rot.groupes[(ligne.atelier - 1 + dec) % rot.groupes.length];
}

/** Nombre de lignes à renseigner et nombre déjà renseignées, pour un jour. */
function avancement(jour) {
  const j = EDT.jours.find(x => x.jour === jour);
  let total = 0, faits = 0;
  for (const c of j.creneaux) for (const [i, m] of (c.lignes ?? []).entries()) {
    if (m.saisie === 'aucune') continue;
    total++;
    const s = saisieLue(jour, c.debut, i);
    // repère de progression, pas un contrôle : une ligne compte dès qu'elle
    // porte quelque chose. Certaines activités n'ont pas de compétence.
    if (s.intitule?.trim() || s.competences?.length || s.competencesLibres?.length) faits++;
  }
  return { total, faits };
}

// ----------------------------------------------------------- sauvegarde

let minuteur = null;
function marquer(texte, ok = false) {
  const e = $('#etat');
  e.textContent = texte;
  e.classList.toggle('ok', ok);
}
function enregistrer() {
  clearTimeout(minuteur);
  marquer('Modifié…');
  minuteur = setTimeout(async () => {
    const r = await fetch(`/api/semaine?id=${ID}`, {
      method: 'PUT', headers: { 'content-type': 'application/json' },
      body: JSON.stringify(SEM),
    }).then(r => r.json()).catch(() => null);
    if (!r) return marquer('Enregistrement impossible');
    CTX.catalogue = r.catalogue;
    marquer('Enregistré', true);
    majOnglets();
  }, 700);
}

// --------------------------------------------------------------- rendu

function rendOnglets() {
  const n = $('#onglets');
  n.replaceChildren(...JOURS.map(j => {
    const b = el('button', { type: 'button' });
    b.setAttribute('aria-current', String(j === JOUR));
    b.dataset.jour = j;
    b.append(el('span', { textContent: j[0].toUpperCase() + j.slice(1) }),
             el('span', { className: 'cpt' }));
    b.onclick = () => { JOUR = j; rendOnglets(); rendJour(); };
    return b;
  }));
  majOnglets();
}
function majOnglets() {
  for (const b of $('#onglets').children) {
    const { total, faits } = avancement(b.dataset.jour);
    const c = b.querySelector('.cpt');
    c.textContent = total ? `${faits}/${total}` : '';
    c.classList.toggle('plein', total > 0 && faits === total);
  }
}

function rendRepere() {
  const l = dateDe(SEM.lundi, 0), v = dateDe(SEM.lundi, 4);
  $('#repere').textContent =
    `Période ${SEM.periode} · Semaine ${SEM.semaine} · ${enClair(l)} → ${enClair(v)} ${v.getUTCFullYear()}`;
  $('#contexte').value = SEM.contexte ?? '';
}

function rendLigne(jour, creneau, modele, i) {
  const s = saisieLue(jour, creneau.debut, i);
  const niveau = s.niveau ?? modele.niveau;
  const [bande, teinte] = TEINTES[niveau] ?? TEINTES['MS + GS'];
  const fige = modele.saisie === 'aucune';
  const groupe = s.groupe ?? groupeRotation(modele, jour);
  const org = groupe ? `${modele.organisation} · ${groupe}` : modele.organisation;

  const noeud = el('div', { className: 'ligne' + (fige ? ' fige' : '') });
  noeud.style.setProperty('--bande', bande);
  noeud.style.setProperty('--teinte', teinte);

  const tete = el('div', { className: 'ligne-t' },
    el('span', { className: 'puce', textContent: niveau }),
    el('span', { className: 'meta' },
      el('b', { textContent: modele.domaine ?? '' }),
      document.createTextNode(` · ${modele.priseEnCharge ?? ''} · ${org ?? ''}`)));
  noeud.append(tete);

  if (fige) {
    noeud.append(el('div', { className: 'texte', textContent: modele.intitule ?? '' }));
    return noeud;
  }

  // intitulé, avec suggestions issues du catalogue
  const champ = el('input', { className: 'champ', type: 'text', value: s.intitule ?? '',
    placeholder: modele.intitule ?? "Intitulé de l'activité…" });
  champ.oninput = () => {
    saisie(jour, creneau.debut, i).intitule = champ.value;
    suggerer(champ, jour, creneau.debut, i);
    enregistrer();
  };
  champ.onblur = () => setTimeout(fermerSuggestions, 150);
  noeud.append(champ);

  // compétences
  const comps = el('div', { className: 'comps' });
  const dessineComps = () => {
    const s2 = saisieLue(jour, creneau.debut, i);
    comps.replaceChildren();
    (s2.competences ?? []).forEach((code, k) => {
      const { code: c, texte } = libelleCompetence(code);
      comps.append(el('span', { className: 'comp' },
        el('code', { textContent: c }),
        el('span', { className: 'txt', textContent: texte }),
        el('button', { type: 'button', textContent: '×', title: 'Retirer',
          onclick: () => { saisie(jour, creneau.debut, i).competences.splice(k, 1);
                           dessineComps(); enregistrer(); } })));
    });
    (s2.competencesLibres ?? []).forEach((txt, k) => {
      comps.append(el('span', { className: 'comp libre' },
        el('code', { textContent: 'libre' }),
        el('span', { className: 'txt', textContent: txt }),
        el('button', { type: 'button', textContent: '×', title: 'Retirer',
          onclick: () => { saisie(jour, creneau.debut, i).competencesLibres.splice(k, 1);
                           dessineComps(); enregistrer(); } })));
    });
    comps.append(el('button', { className: 'btn mini', type: 'button',
      textContent: '+ compétence',
      onclick: () => ouvrirPalette(jour, creneau.debut, i, dessineComps) }));
    if (s2.materiel == null) comps.append(el('button', { className: 'btn mini', type: 'button',
      textContent: '+ matériel',
      onclick: () => { saisie(jour, creneau.debut, i).materiel = ''; rendJour(); } }));
  };
  dessineComps();
  noeud.append(comps);

  if (s.materiel != null) {
    const m = el('input', { className: 'champ materiel', type: 'text', value: s.materiel,
      placeholder: 'Matériel…' });
    m.oninput = () => { saisie(jour, creneau.debut, i).materiel = m.value; enregistrer(); };
    noeud.append(m);
  }
  return noeud;
}

function rendJour() {
  const j = EDT.jours.find(x => x.jour === JOUR);
  const zone = $('#jour');

  const actions = el('div', { className: 'jour-actions' },
    el('span', { className: 'pousse' }));
  for (const autre of JOURS.filter(x => x !== JOUR && SEM.jours?.[x]?.creneaux)) {
    actions.append(el('button', { className: 'btn mini', type: 'button',
      textContent: `Recopier ${autre}`,
      onclick: () => { recopier(autre, JOUR); rendJour(); enregistrer(); } }));
  }
  const vide = SEM.jours?.[JOUR]?.supprime;
  actions.append(el('button', { className: 'btn mini', type: 'button',
    textContent: vide ? 'Rétablir la journée' : 'Journée sans classe',
    onclick: () => {
      SEM.jours ??= {}; SEM.jours[JOUR] ??= {};
      SEM.jours[JOUR].supprime = !vide;
      rendJour(); enregistrer();
    } }));

  const corps = el('div');
  if (vide) {
    corps.append(el('p', { style: 'color:var(--encre-3);padding:24px 0',
      textContent: "Journée retirée du cahier-journal : elle ne sera pas imprimée (férié, sortie sur la journée, classe non assurée)." }));
  } else {
    for (const c of j.creneaux) {
      const modeles = c.lignes ?? [{
        niveau: c.niveau, domaine: c.domaine, intitule: c.intitule,
        priseEnCharge: c.priseEnCharge, organisation: c.organisation, saisie: c.saisie }];
      const bloc = el('div', { className: 'creneau' + (c.type === 'pause' || c.type === 'fixe' ? ' fige' : '') },
        el('div', { className: 'heure' },
          document.createTextNode(c.debut.replace(':', 'h')),
          el('small', { textContent: c.fin.replace(':', 'h') })),
        el('div', { className: 'lignes' },
          modeles.map((m, i) => rendLigne(JOUR, c, m, i))));
      corps.append(bloc);
    }
  }
  zone.replaceChildren(actions, corps);
  majOnglets();
}

/** Recopie les intitulés, compétences et matériel d'un jour vers un autre,
 *  créneau par créneau, sans toucher aux groupes (la rotation les recalcule). */
function recopier(de, vers) {
  const src = SEM.jours?.[de]?.creneaux ?? {};
  const jsrc = EDT.jours.find(x => x.jour === de);
  const jdst = EDT.jours.find(x => x.jour === vers);
  SEM.jours[vers] ??= {}; SEM.jours[vers].creneaux ??= {};
  for (const c of jdst.creneaux) {
    const eq = jsrc.creneaux.find(x => x.debut === c.debut);
    if (!eq || !src[c.debut]) continue;
    SEM.jours[vers].creneaux[c.debut] = {
      lignes: (src[c.debut].lignes ?? []).map(l => ({
        intitule: l.intitule, competences: [...(l.competences ?? [])],
        competencesLibres: [...(l.competencesLibres ?? [])],
        ...(l.materiel != null ? { materiel: l.materiel } : {}),
      })),
    };
  }
}

// -------------------------------------------------- suggestions d'activité

let boite = null;
const fermerSuggestions = () => { boite?.remove(); boite = null; };

function suggerer(champ, jour, debut, i) {
  fermerSuggestions();
  const q = champ.value.trim().toLowerCase();
  if (q.length < 2) return;
  const trouves = CTX.catalogue.activites
    .filter(a => a.intitule.toLowerCase().includes(q))
    .slice(0, 8);
  if (!trouves.length) return;

  boite = el('div', { className: 'suggestions' });
  for (const a of trouves) {
    const detail = [a.domaine, a.materiel && `matériel : ${a.materiel}`,
      a.competences?.length && a.competences.join(', ')].filter(Boolean).join(' · ');
    boite.append(el('button', { type: 'button', onmousedown: e => {
      e.preventDefault();
      const s = saisie(jour, debut, i);
      s.intitule = a.intitule;
      if (a.competences?.length) s.competences = [...a.competences];
      if (a.materiel) s.materiel = a.materiel;
      fermerSuggestions(); rendJour(); enregistrer();
    } }, el('div', { className: 's-t', textContent: a.intitule }),
       detail ? el('div', { className: 's-m', textContent: detail }) : null));
  }
  const r = champ.getBoundingClientRect();
  boite.style.left = `${r.left + scrollX}px`;
  boite.style.top = `${r.bottom + scrollY + 3}px`;
  boite.style.width = `${Math.max(r.width, 320)}px`;
  document.body.append(boite);
}

// ---------------------------------------------------- palette compétences

let redessine = null;

function ouvrirPalette(jour, debut, i, apres) {
  cible = { jour, debut, i };
  redessine = apres;
  $('#voile').hidden = false;
  $('#recherche').value = '';
  $('#compLibre').value = '';
  chercher('');
  $('#recherche').focus();
}
const fermerPalette = () => { $('#voile').hidden = true; cible = null; };

function chercher(q) {
  const zone = $('#resultats');
  const mots = q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const lignes = [];
  for (const c of CTX.referentiel.competences) {
    const etapes = c.sansEtapes
      ? [{ numero: null, libelle: c.libelle ?? c.intitule }]
      : c.etapes;
    for (const e of etapes) {
      const foin = `${c.code} ${c.intitule} ${c.famille} ${e.libelle}`.toLowerCase();
      if (mots.every(m => foin.includes(m))) lignes.push({ c, e });
    }
  }
  if (!lignes.length) {
    zone.replaceChildren(el('div', { className: 'vide',
      textContent: 'Aucune compétence ne correspond. Utilise la saisie libre ci-dessous.' }));
    return;
  }
  zone.replaceChildren(...lignes.slice(0, 60).map(({ c, e }) => el('button', {
    type: 'button',
    onclick: () => ajouter(`${c.code}-${e.numero ?? ''}`),
  },
    el('span', { className: 'r-c', textContent: c.code + (e.numero ? ` · étape ${e.numero}` : '') }),
    el('span', { className: 'r-i', textContent: c.intitule }),
    el('span', { className: 'r-l', textContent: e.libelle }))));
}

function ajouter(code) {
  const s = saisie(cible.jour, cible.debut, cible.i);
  s.competences ??= [];
  if (!s.competences.includes(code)) s.competences.push(code);
  redessine?.(); enregistrer(); fermerPalette();
}
function ajouterLibre() {
  const txt = $('#compLibre').value.trim();
  if (!txt) return;
  const s = saisie(cible.jour, cible.debut, cible.i);
  s.competencesLibres ??= [];
  s.competencesLibres.push(txt);
  redessine?.(); enregistrer(); fermerPalette();
}

// ------------------------------------------------------------ démarrage

async function ouvrirSemaine(id) {
  ID = id;
  SEM = await fetch(`/api/semaine?id=${id}`).then(r => r.json());
  EDT = CTX.emploisDuTemps.find(e => e.id === SEM.emploiDuTemps) ?? CTX.emploisDuTemps[0];
  location.hash = id;
  rendRepere(); rendOnglets(); rendJour();
  marquer('');
}

function rendChoix() {
  const s = $('#choixSemaine');
  s.replaceChildren(...CTX.semaines.map(w => el('option', {
    value: w.id, selected: w.id === ID,
    textContent: `P${w.periode} · S${String(w.semaine).padStart(2, '0')} · ${enClair(dateDe(w.lundi, 0))}`,
  })));
  s.onchange = () => ouvrirSemaine(s.value);
}

async function nouvelleSemaine() {
  const derniere = CTX.semaines.at(-1);
  const lundiSuggere = derniere
    ? dateDe(derniere.lundi, 7).toISOString().slice(0, 10)
    : new Date().toISOString().slice(0, 10);
  const lundi = prompt('Date du lundi (AAAA-MM-JJ)', lundiSuggere);
  if (!lundi) return;
  const periode = prompt('Numéro de période', String(derniere?.periode ?? 1));
  if (!periode) return;
  const semaine = prompt('Numéro de semaine dans la période',
    String((derniere?.semaine ?? 0) + 1));
  if (!semaine) return;

  const r = await fetch('/api/semaine', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ lundi, periode, semaine,
      edt: EDT?.id ?? CTX.emploisDuTemps[0].id }),
  }).then(r => r.json());
  if (r.erreur) return alert(r.erreur);
  CTX = await fetch('/api/contexte').then(r => r.json());
  rendChoix();
  await ouvrirSemaine(r.id);
  rendChoix();
}

(async function demarrer() {
  CTX = await fetch('/api/contexte').then(r => r.json());
  const voulu = location.hash.slice(1);
  const id = CTX.semaines.find(w => w.id === voulu)?.id ?? CTX.semaines.at(-1)?.id;
  if (!id) { $('#jour').textContent = 'Aucune semaine. Crée la première.'; }
  else { await ouvrirSemaine(id); }
  rendChoix();

  $('#contexte').oninput = e => { SEM.contexte = e.target.value; enregistrer(); };
  $('#imprimer').onclick = () => window.open(`/imprimer?id=${ID}`, '_blank');
  $('#nouvelleSemaine').onclick = nouvelleSemaine;
  $('#recherche').oninput = e => chercher(e.target.value);
  $('#fermerPalette').onclick = fermerPalette;
  $('#ajouterLibre').onclick = ajouterLibre;
  $('#compLibre').onkeydown = e => { if (e.key === 'Enter') ajouterLibre(); };
  $('#voile').onclick = e => { if (e.target.id === 'voile') fermerPalette(); };
  addEventListener('keydown', e => { if (e.key === 'Escape') fermerPalette(); });
  addEventListener('scroll', fermerSuggestions, true);
})();
