# -*- coding: utf-8 -*-
"""Genere la page de relecture du referentiel a partir du JSON extrait."""
import json, sys, io

ref = json.load(open(sys.argv[1], encoding='utf8'))
out = sys.argv[2]

payload = json.dumps(ref, ensure_ascii=False, separators=(',', ':'))

HTML = """<title>Relecture du livret de suivi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@500;700&display=swap">
<style>
:root{
  --paper:#f2f3ee; --card:#fbfbf8; --ink:#1c2024; --ink-2:#4c545e; --ink-3:#7b838d;
  --rule:#d9dcd3; --rule-2:#e8eae3;
  --stamp:#4a3f8f; --stamp-soft:#ece9f7;
  --flag:#a8402a; --flag-soft:#f7ebe7;
  --ok:#356b52; --ok-soft:#e6efe9;
  --focus:#4a3f8f;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#15181b; --card:#1c2024; --ink:#e9ebe6; --ink-2:#a8b0b8; --ink-3:#7b838d;
  --rule:#2e3439; --rule-2:#252b30;
  --stamp:#a99cf0; --stamp-soft:#252148;
  --flag:#e0917c; --flag-soft:#3a2019;
  --ok:#82c1a2; --ok-soft:#16291f;
  --focus:#a99cf0;
}}
:root[data-theme="dark"]{
  --paper:#15181b; --card:#1c2024; --ink:#e9ebe6; --ink-2:#a8b0b8; --ink-3:#7b838d;
  --rule:#2e3439; --rule-2:#252b30;
  --stamp:#a99cf0; --stamp-soft:#252148;
  --flag:#e0917c; --flag-soft:#3a2019;
  --ok:#82c1a2; --ok-soft:#16291f;
  --focus:#a99cf0;
}

*{box-sizing:border-box}
body{
  background:var(--paper); color:var(--ink);
  font-family:"Source Serif 4",Georgia,serif; font-size:16px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:860px;margin:0 auto;padding:40px 24px 96px;display:flex;flex-direction:column;gap:36px}

h1,h2,h3,.ui{font-family:"Bricolage Grotesque",system-ui,sans-serif}
.mono{font-family:"JetBrains Mono",ui-monospace,monospace}

/* ---------- en-tete ---------- */
.eyebrow{
  font-family:"Bricolage Grotesque",system-ui,sans-serif;
  font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);
}
h1{font-size:clamp(30px,5vw,42px);font-weight:800;line-height:1.05;margin:10px 0 0;letter-spacing:-.02em;text-wrap:balance}
.lede{margin:14px 0 0;max-width:62ch;color:var(--ink-2);font-size:17px}
.lede strong{color:var(--ink);font-weight:600}

.stats{display:flex;flex-wrap:wrap;gap:0;margin-top:24px;border-top:2px solid var(--ink);border-bottom:1px solid var(--rule)}
.stat{flex:1 1 130px;padding:12px 16px 13px;border-right:1px solid var(--rule-2)}
.stat:last-child{border-right:0}
.stat b{display:block;font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:26px;font-weight:700;line-height:1;font-variant-numeric:tabular-nums}
.stat span{display:block;margin-top:5px;font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:11px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
.stat.is-flag b{color:var(--flag)}
.stat.is-ok b{color:var(--ok)}

/* ---------- barre d'outils ---------- */
.tools{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.seg{display:flex;border:1px solid var(--rule);border-radius:2px;overflow:hidden}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}
button:focus-visible,input:focus-visible,textarea:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.seg button{
  font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:13px;font-weight:500;
  padding:6px 13px;border-right:1px solid var(--rule);color:var(--ink-2);
}
.seg button:last-child{border-right:0}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.spacer{flex:1 1 auto}
.savestate{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:12px;color:var(--ink-3)}

/* ---------- blocs ---------- */
.block{display:flex;flex-direction:column;gap:2px}
.block-head{display:flex;align-items:baseline;gap:12px;padding-bottom:9px;border-bottom:2px solid var(--ink)}
.block-head h2{font-size:19px;font-weight:700;margin:0;letter-spacing:-.01em}
.block-head .count{margin-left:auto;font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.block-note{margin:10px 0 6px;color:var(--ink-2);font-size:15px;max-width:62ch}

/* ---------- competence ---------- */
.comp{border-bottom:1px solid var(--rule);padding:16px 0 4px}
.comp:first-of-type{border-top:1px solid var(--rule-2)}
.comp-head{display:flex;align-items:flex-start;gap:12px;margin-bottom:6px}
.chip{
  font-family:"JetBrains Mono",monospace;font-size:12px;font-weight:700;
  padding:3px 7px;border:1px solid var(--rule);border-radius:2px;color:var(--stamp);
  background:var(--stamp-soft);white-space:nowrap;line-height:1.25;
}
.comp-titles .fam{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:10.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3)}
.comp-titles .int{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:17px;font-weight:600;line-height:1.25;margin-top:2px}
.comp-page{margin-left:auto;font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-3);white-space:nowrap;padding-top:3px}

/* ---------- etape ---------- */
.step{display:grid;grid-template-columns:26px 1fr auto;gap:12px;align-items:start;padding:7px 0;border-top:1px solid var(--rule-2)}
.step-n{font-family:"JetBrains Mono",monospace;font-size:12px;font-weight:700;color:var(--ink-3);padding-top:3px;text-align:right;font-variant-numeric:tabular-nums}
.step-lib{font-size:16px;line-height:1.4;text-wrap:pretty}
.step.empty .step-lib{color:var(--flag);font-style:italic}
.step-lib.sansetapes{color:var(--ink-3);font-style:italic;font-size:15px}
.step.fixed{background:var(--ok-soft);margin:0 -10px;padding:7px 10px;border-radius:2px}
.step.todo{background:var(--flag-soft);margin:0 -10px;padding:7px 10px;border-radius:2px}
.old{display:block;color:var(--ink-3);text-decoration:line-through;font-size:14px;margin-bottom:3px}
.note{display:block;margin-top:4px;font-size:14px;color:var(--ink-2);font-style:italic}
.why{display:block;margin-top:3px;font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:11.5px;color:var(--flag)}
.act{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:12.5px;font-weight:500;color:var(--ink-3);padding:3px 8px;border:1px solid var(--rule);border-radius:2px;white-space:nowrap}
.act:hover{color:var(--ink);border-color:var(--ink-2)}

/* ---------- edition ---------- */
.editor{grid-column:1/-1;display:flex;flex-direction:column;gap:8px;padding:12px 0 6px}
label.lab{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
textarea,input[type=text]{
  width:100%;font-family:"Source Serif 4",Georgia,serif;font-size:15.5px;line-height:1.4;
  padding:9px 11px;border:1px solid var(--rule);border-radius:2px;background:var(--card);color:var(--ink);resize:vertical;
}
.editor-row{display:flex;gap:8px;align-items:center}
.btn{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:13px;font-weight:600;padding:7px 15px;border-radius:2px}
.btn.primary{background:var(--ink);color:var(--paper)}
.btn.ghost{border:1px solid var(--rule);color:var(--ink-2)}
.btn.danger{color:var(--flag)}

footer{border-top:1px solid var(--rule);padding-top:16px;color:var(--ink-3);font-size:14px;max-width:62ch}

@media (max-width:600px){
  .wrap{padding:28px 16px 72px}
  .step{grid-template-columns:22px 1fr;gap:9px}
  .act{grid-column:2;justify-self:start;margin-top:4px}
  .comp-page{display:none}
}
@media print{
  body{background:#fff;color:#000}
  .tools,.act,.savestate{display:none}
  .wrap{max-width:none;padding:0;gap:24px}
  .comp{break-inside:avoid}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Cahier-journal MS / GS &middot; étape préparatoire</div>
    <h1>Relecture du livret de suivi</h1>
    <p class="lede">Les <strong>158 étapes</strong> des livrets de français et de mathématiques ont été lues automatiquement dans les deux PDF. L'application n'affichera <strong>que ces formulations</strong>, sans jamais en inventer : il faut donc qu'elles soient exactes. Signale ici tout libellé fautif ou tronqué &mdash; le reste est considéré comme conforme.</p>
    <div class="stats" id="stats"></div>
  </header>

  <div class="tools">
    <div class="seg" role="group" aria-label="Filtrer par domaine">
      <button data-dom="tout" aria-pressed="true">Tout</button>
      <button data-dom="francais" aria-pressed="false">Français</button>
      <button data-dom="maths" aria-pressed="false">Mathématiques</button>
    </div>
    <div class="seg" role="group" aria-label="Filtrer par état">
      <button data-vue="tout" aria-pressed="true">Toutes les étapes</button>
      <button data-vue="attention" aria-pressed="false">À traiter</button>
    </div>
    <div class="spacer"></div>
    <div class="savestate" id="savestate"></div>
  </div>

  <section class="block" id="bloc-attention"></section>
  <section class="block" id="bloc-liste"></section>

  <footer>
    Extraction du <span class="mono">livret français 2026 OK.pdf</span> et du <span class="mono">livret maths 2026 OK V2.pdf</span>.
    Les codes <span class="mono">M9</span> et <span class="mono">M11</span> n'existent pas dans le livret de mathématiques : la numérotation les saute.
    Motricité, activités artistiques et exploration du monde n'ont pas de référentiel &mdash; l'application y proposera une compétence libre.
  </footer>
</div>

<script>
const REF = __PAYLOAD__;
const CORR = new Map();            // "L12-2" -> {libelle, note, par}
let db = null, filtreDom = 'tout', filtreVue = 'tout';

const cle = (c, n) => c + '-' + (n === null ? 'x' : n);
const esc = s => (s || '').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));

function etapesPlates(){
  const out = [];
  for (const c of REF.competences){
    if (!c.etapes.length && !c.sansEtapes) out.push({comp:c, etape:{numero:null, libelle:'', aRelire:true, motif:c.motif}});
    for (const e of c.etapes) out.push({comp:c, etape:e});
  }
  return out;
}
const TOUT = etapesPlates();
const ATTENTION = TOUT.filter(x => x.etape.aRelire || !x.etape.libelle);

function majStats(){
  const traites = ATTENTION.filter(x => CORR.has(cle(x.comp.code, x.etape.numero))).length;
  const autres = [...CORR.keys()].filter(k => !ATTENTION.some(x => cle(x.comp.code, x.etape.numero) === k)).length;
  document.getElementById('stats').innerHTML = [
    ['', REF.competences.length, 'compétences'],
    ['', REF.competences.reduce((a,c)=>a+c.etapes.length,0), 'étapes lues'],
    [traites === ATTENTION.length ? 'is-ok' : 'is-flag', ATTENTION.length - traites, 'à vérifier'],
    [autres ? 'is-ok' : '', autres, 'corrections signalées'],
  ].map(([cl, v, l]) => `<div class="stat ${cl}"><b>${v}</b><span>${l}</span></div>`).join('');
}

function ligneEtape(comp, etape){
  const k = cle(comp.code, etape.numero);
  const corr = CORR.get(k);
  const vide = !etape.libelle;
  const mod = corr ? 'fixed' : vide ? 'empty todo' : etape.aRelire ? 'todo' : '';
  const libelle = corr
    ? (etape.libelle ? `<span class="old">${esc(etape.libelle)}</span>` : '') + esc(corr.libelle)
    : (vide ? 'à saisir à la main' : esc(etape.libelle));
  const why = etape.motif && !corr ? `<span class="why">${esc(etape.motif)}</span>` : '';
  const note = corr && corr.note ? `<span class="note">${esc(corr.note)}</span>` : '';
  return `<div class="step ${mod}" data-k="${k}">
    <div class="step-n">${etape.numero === null ? '—' : etape.numero}</div>
    <div class="step-lib">${libelle}${why}${note}</div>
    <button class="act" data-edit="${k}">${corr ? 'Modifier' : (vide ? 'Compléter' : 'Corriger')}</button>
  </div>`;
}

function blocCompetence(comp, etapes){
  return `<article class="comp" data-dom="${comp.domaine}">
    <div class="comp-head">
      <span class="chip">${comp.code}</span>
      <div class="comp-titles">
        <div class="fam">${esc(comp.famille)}</div>
        <div class="int">${esc(comp.intitule)}</div>
      </div>
      <div class="comp-page">p. ${comp.pageLivret}</div>
    </div>
    ${etapes.length ? etapes.map(e => ligneEtape(comp, e)).join('')
      : `<div class="step"><div class="step-n">&nbsp;</div><div class="step-lib sansetapes">${esc(comp.note || "Pas d'étape détaillée dans le livret : la compétence se travaille telle quelle.")}</div></div>`}
  </article>`;
}

function rendu(){
  // bloc « a completer »
  const reste = ATTENTION.filter(x => !CORR.has(cle(x.comp.code, x.etape.numero)));
  const ba = document.getElementById('bloc-attention');
  if (reste.length && filtreDom === 'tout'){
    ba.hidden = false;
    ba.innerHTML = `<div class="block-head"><h2>À vérifier</h2><span class="count">${reste.length}</span></div>
      <p class="block-note">Ces étapes n'ont pas pu être lues telles quelles dans le PDF : case illustrée, case laissée vide dans le livret, ou libellé redessiné deux fois par le fichier. Chacune indique la raison ; il faut recopier ou confirmer le texte du livret papier.</p>
      ${reste.map(x => blocCompetence(x.comp, [x.etape])).join('')}`;
  } else { ba.hidden = true; ba.innerHTML = ''; }

  // liste complete
  const bl = document.getElementById('bloc-liste');
  const comps = REF.competences.filter(c => filtreDom === 'tout' || c.domaine === filtreDom);
  const corps = comps.map(c => {
    if (c.sansEtapes) return filtreVue === 'attention' ? '' : blocCompetence(c, []);
    let ets = c.etapes.length ? c.etapes : [{numero:null, libelle:'', aRelire:true, motif:c.motif}];
    if (filtreVue === 'attention') ets = ets.filter(e => e.aRelire || !e.libelle || CORR.has(cle(c.code, e.numero)));
    return ets.length ? blocCompetence(c, ets) : '';
  }).join('');
  const titre = filtreDom === 'francais' ? 'Français' : filtreDom === 'maths' ? 'Mathématiques' : 'Toutes les compétences';
  bl.innerHTML = `<div class="block-head"><h2>${titre}</h2><span class="count">${comps.length} comp. · ${comps.reduce((s,c)=>s+c.etapes.length,0)} étapes</span></div>${corps || '<p class="block-note">Rien à traiter dans cette sélection.</p>'}`;
  majStats();
}

function ouvrirEditeur(k){
  const el = document.querySelector(`.step[data-k="${k}"]`);
  if (!el || el.querySelector('.editor')) return;
  const [code, n] = [k.slice(0, k.lastIndexOf('-')), k.slice(k.lastIndexOf('-') + 1)];
  const comp = REF.competences.find(c => c.code === code);
  const etape = (comp.etapes || []).find(e => String(e.numero) === n);
  const corr = CORR.get(k);
  const val = corr ? corr.libelle : (etape ? etape.libelle : '');
  const ed = document.createElement('div');
  ed.className = 'editor';
  ed.innerHTML = `
    <label class="lab" for="t-${k}">Libellé exact du livret</label>
    <textarea id="t-${k}" rows="2">${esc(val)}</textarea>
    <label class="lab" for="n-${k}">Remarque (facultatif)</label>
    <input type="text" id="n-${k}" value="${esc(corr ? corr.note : '')}" placeholder="ex. le livret n'a pas d'étape 4 ici">
    <div class="editor-row">
      <button class="btn primary" data-save="${k}">Enregistrer</button>
      <button class="btn ghost" data-cancel="${k}">Annuler</button>
      ${corr ? `<button class="btn danger" data-del="${k}">Supprimer la correction</button>` : ''}
    </div>`;
  el.appendChild(ed);
  ed.querySelector('textarea').focus();
}

async function ecrire(k, valeur){
  CORR.set(k, valeur);
  rendu();
  if (!db) { etat('Correction gardée sur cet écran seulement'); return; }
  try { await db.doc('relecture/' + k).set(valeur); etat('Enregistré'); }
  catch (e) { etat("Enregistrement impossible — la correction reste affichée ici"); }
}
async function effacer(k){
  CORR.delete(k); rendu();
  if (db) { try { await db.doc('relecture/' + k).delete(); etat('Correction supprimée'); } catch(e){} }
}
function etat(msg){
  const el = document.getElementById('savestate');
  el.textContent = msg;
  clearTimeout(etat._t); etat._t = setTimeout(() => { el.textContent = db ? 'Corrections partagées' : ''; }, 2600);
}

document.addEventListener('click', ev => {
  const t = ev.target.closest('[data-edit],[data-save],[data-cancel],[data-del],[data-dom],[data-vue]');
  if (!t) return;
  if (t.dataset.edit) return ouvrirEditeur(t.dataset.edit);
  if (t.dataset.cancel) return t.closest('.editor').remove();
  if (t.dataset.del) return effacer(t.dataset.del);
  if (t.dataset.save){
    const k = t.dataset.save;
    const libelle = document.getElementById('t-' + k).value.trim();
    const note = document.getElementById('n-' + k).value.trim();
    if (!libelle && !note) return t.closest('.editor').remove();
    return ecrire(k, {libelle, note, date: new Date().toISOString()});
  }
  if (t.dataset.dom){
    filtreDom = t.dataset.dom;
    t.parentElement.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === t)));
    return rendu();
  }
  if (t.dataset.vue){
    filtreVue = t.dataset.vue;
    t.parentElement.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === t)));
    return rendu();
  }
});

rendu();

(async () => {
  db = await window.claude?.use?.('db');
  if (!db) return;
  document.getElementById('savestate').textContent = 'Corrections partagées';
  db.collection('relecture').onSnapshot(
    snap => {
      CORR.clear();
      for (const d of snap.docs) if (d.exists) CORR.set(d.id, d.data() || {});
      rendu();
    },
    () => etat('Synchronisation interrompue — recharge la page')
  );
})();
</script>
"""

open(out, 'w', encoding='utf8').write(HTML.replace('__PAYLOAD__', payload))
print('ecrit', out, len(HTML) + len(payload), 'octets')
