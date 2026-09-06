# -*- coding: utf-8 -*-
"""Extrait un livret de suivi des apprentissages (PDF) vers un JSON structure.

Mise en page exploitee : code de competence a gauche (x~55), grande competence
en majuscules juste au-dessus, sous-titre juste en dessous, numeros d'etape dans
la colonne de gauche, libelles dans la colonne de texte (x>=160). Les vignettes
illustratives se situent entre les deux colonnes et sont ecartees.

Chaque etape sort avec une liste `alertes` : tout ce qui demande une relecture.
"""
import json, re, sys
import pdfplumber

CODE_RE   = re.compile(r'^([LM])(\d{1,2})$')
NUM_RE    = re.compile(r'^(\d)\1?$')          # le PDF double parfois le chiffre : "11" = 1
DEBUT_RE  = re.compile(r"^(Je |J'|J’)")
CAPS_RE   = re.compile(r'^[A-ZÉÈÀÂÎÔÛÇ\s·’\'-]{6,}$')
TEXT_X    = 160.0     # debut de la colonne de texte
NUM_X     = 100.0     # fin de la colonne des numeros
LINE_TOL  = 3.0
BLOCK_GAP = 16.0


def group_lines(words, tol=LINE_TOL):
    out = []
    for w in sorted(words, key=lambda w: (round(w['top'], 1), w['x0'])):
        if out and abs(w['top'] - out[-1]['top']) <= tol:
            out[-1]['words'].append(w)
            out[-1]['bottom'] = max(out[-1]['bottom'], w['bottom'])
        else:
            out.append({'top': w['top'], 'bottom': w['bottom'], 'words': [w]})
    for l in out:
        l['words'].sort(key=lambda w: w['x0'])
        l['text'] = ' '.join(w['text'] for w in l['words'])
        l['x0'] = min(w['x0'] for w in l['words'])
    return out


def dedup(text):
    """Supprime les repetitions dues au PDF, qui redessine un fragment de texte.

    Le fragment repete n'est pas toujours en fin de libelle :
      "... les nasales. nasales."                  (fin)
      "... je parle assez parle assez fort ..."    (milieu)
    On cherche donc, a chaque position, un groupe de mots immediatement suivi
    du meme groupe, et on garde la premiere occurrence. Toute suppression est
    signalee : la decision revient a la relecture humaine.
    """
    mots = text.split()
    retire = []
    i = 0
    while i < len(mots):
        for n in range(min(10, (len(mots) - i) // 2), 0, -1):
            if mots[i:i + n] == mots[i + n:i + 2 * n]:
                retire.append(' '.join(mots[i:i + n]))
                del mots[i + n:i + 2 * n]
                break
        else:
            i += 1
    return ' '.join(mots), retire


def extract(path):
    comps = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = [w for w in page.extract_words(x_tolerance=1.2)
                     if 45 < w['top'] < page.height - 35 and w['text'] != 'img']

            codes = [{'code': w['text'], 'top': w['top']}
                     for w in words if CODE_RE.match(w['text']) and w['x0'] < 90]
            if not codes:
                continue
            codes.sort(key=lambda c: c['top'])

            entetes = group_lines([w for w in words if 85 <= w['x0'] < 400])
            for c in codes:
                dessus = [l for l in entetes
                          if -16 < (l['top'] - c['top']) < -3 and CAPS_RE.match(l['text'])]
                dessous = [l for l in entetes if 3 < (l['top'] - c['top']) < 18]
                c['titre'] = dessus[-1]['text'] if dessus else ''
                c['soustitre'] = dessous[0]['text'] if dessous else ''
                c['etapes'] = []

            nums = []
            for w in words:
                m = NUM_RE.match(w['text'])
                if m and w['x0'] < NUM_X:
                    nums.append({'n': int(m.group(1)), 'top': w['top']})

            corps = [l for l in group_lines([w for w in words if w['x0'] >= TEXT_X])
                     if not l['text'].startswith('Valid')
                     and not CAPS_RE.match(l['text'])
                     and not any(abs(l['top'] - c['top']) < 18
                                 and l['text'] in (c['titre'], c['soustitre'])
                                 for c in codes)]

            blocs = []
            for l in corps:
                if blocs and (l['top'] - blocs[-1]['bottom']) < BLOCK_GAP:
                    blocs[-1]['lines'].append(l)
                    blocs[-1]['bottom'] = l['bottom']
                else:
                    blocs.append({'top': l['top'], 'bottom': l['bottom'], 'lines': [l]})

            pris = set()
            for b in blocs:
                texte = re.sub(r'\s+', ' ', ' '.join(l['text'] for l in b['lines'])).strip()
                texte, retire = dedup(texte)
                if not DEBUT_RE.match(texte):
                    continue
                proches = [n for n in nums
                           if b['top'] - 8 <= n['top'] <= b['bottom'] + 8 and id(n) not in pris]
                if not proches:
                    mid = (b['top'] + b['bottom']) / 2
                    cand = sorted((n for n in nums if id(n) not in pris),
                                  key=lambda n: abs(n['top'] - mid))[:1]
                    proches = [n for n in cand if abs(n['top'] - mid) <= 16]
                num = None
                if proches:
                    num = proches[0]['n']
                    pris.add(id(proches[0]))

                proprio = [c for c in codes if c['top'] < b['top']]
                if not proprio:
                    continue
                alertes = []
                for r in retire:
                    alertes.append(f'repetition supprimee automatiquement : "{r}"')
                if num is None:
                    alertes.append('numero d etape introuvable')
                if not texte.rstrip().endswith(('.', '…', ')')):
                    alertes.append('libelle possiblement tronque')
                proprio[-1]['etapes'].append(
                    {'numero': num, 'libelle': texte, 'alertes': alertes})

            # numeros restes sans libelle = cases vides ou etapes illustrees
            bornes = {c['code']: (c['top'],
                                  min([x['top'] for x in codes if x['top'] > c['top']],
                                      default=1e9))
                      for c in codes}
            for c in codes:
                vus = {e['numero'] for e in c['etapes']}
                debut, fin = bornes[c['code']]
                for n in nums:
                    if debut < n['top'] < fin and n['n'] not in vus and id(n) not in pris:
                        c['etapes'].append({
                            'numero': n['n'], 'libelle': '',
                            'alertes': ['libelle absent du PDF (etape illustree ou case vide) '
                                        '- a saisir a la main']})
                c['etapes'].sort(key=lambda e: (e['numero'] is None, e['numero'] or 0))
                c.pop('top')
                c['page'] = pno
                if not c['etapes']:
                    c['alertes'] = ['aucune etape extraite - competence a saisir a la main']
                comps.append(c)
    return comps


if __name__ == '__main__':
    src, dom, out = sys.argv[1], sys.argv[2], sys.argv[3]
    comps = extract(src)
    for c in comps:
        c['domaine'] = dom
    json.dump(comps, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    n = sum(len(c['etapes']) for c in comps)
    a = (sum(1 for c in comps for e in c['etapes'] if e['alertes'])
         + sum(1 for c in comps if c.get('alertes')))
    print(f'{out}: {len(comps)} competences, {n} etapes, {a} a relire')
