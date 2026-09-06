# -*- coding: utf-8 -*-
"""Fusionne les extractions des deux livrets en un referentiel unique.

Sortie : data/referentiel-competences.json
- `competences` : les codes L1..L21 et M1..M20 issus des livrets d'Audrey.
- `domainesSansReferentiel` : motricite, arts, explorer le monde. Le cahier des
  charges interdit d'y inventer des codes : l'application y utilisera de la
  competence libre tant qu'Audrey n'aura pas fourni de referentiel.
"""
import json, sys, os

SRC = {
    'francais': {
        'libelle': "Français — langage oral et écrit",
        'prefixe': 'L',
        'fichier': "livret français 2026 OK.pdf",
    },
    'maths': {
        'libelle': "Mathématiques — premiers outils mathématiques",
        'prefixe': 'M',
        'fichier': "livret maths 2026 OK V2.pdf",
    },
}

DOMAINES_SANS_REFERENTIEL = [
    {'id': 'motricite',  'libelle': "Agir, s'exprimer, comprendre à travers l'activité physique"},
    {'id': 'arts',       'libelle': "Agir, s'exprimer, comprendre à travers les activités artistiques"},
    {'id': 'monde',      'libelle': "Explorer le monde"},
]


def cle_tri(code):
    return (code[0], int(code[1:]))


def main(maths_json, fr_json, out):
    competences = []
    for dom, chemin in (('maths', maths_json), ('francais', fr_json)):
        for c in json.load(open(chemin, encoding='utf8')):
            etapes = []
            for e in c['etapes']:
                etapes.append({
                    'numero': e['numero'],
                    'libelle': e['libelle'],
                    'aRelire': bool(e['alertes']),
                    'motif': '; '.join(e['alertes']) or None,
                })
            competences.append({
                'code': c['code'],
                'domaine': dom,
                'famille': c['titre'],
                'intitule': c['soustitre'],
                'pageLivret': c['page'],
                'etapes': etapes,
                'aRelire': bool(c.get('alertes')) or any(e['aRelire'] for e in etapes),
                'motif': '; '.join(c.get('alertes', [])) or None,
            })
    competences.sort(key=lambda c: cle_tri(c['code']))

    # Overlay des decisions humaines : il survit a une re-extraction des PDF.
    corr = {}
    if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
        corr = json.load(open(sys.argv[4], encoding='utf8'))
    for c in competences:
        fix = corr.get('competences', {}).get(c['code'])
        if fix:
            c.update({k: v for k, v in fix.items() if not k.startswith('_')})
            if fix.get('sansEtapes'):
                c['aRelire'] = False
                c['motif'] = None
        gardees = []
        for e in c['etapes']:
            fix = corr.get('etapes', {}).get(f"{c['code']}-{e['numero']}")
            if fix:
                if fix.get('supprimee'):
                    continue          # case numerotee du PDF sans etape reelle
                e.update({k: v for k, v in fix.items() if not k.startswith('_')})
                e['aRelire'] = False
                e['motif'] = None
            gardees.append(e)
        c['etapes'] = gardees
        # recalcul complet : une alerte levee a l'extraction peut avoir ete
        # resolue par l'overlay (etape fantome supprimee, competence confirmee)
        c['aRelire'] = bool(c.get('motif')) or any(e['aRelire'] for e in c['etapes'])

    doc = {
        'version': 1,
        'statut': 'extraction automatique — en attente de relecture par Audrey',
        'domaines': [
            {'id': k, 'libelle': v['libelle'], 'prefixeCode': v['prefixe'],
             'source': v['fichier']} for k, v in SRC.items()
        ],
        'domainesSansReferentiel': DOMAINES_SANS_REFERENTIEL,
        'competences': competences,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(doc, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=2)

    n_et = sum(len(c['etapes']) for c in competences)
    n_rel = sum(1 for c in competences for e in c['etapes'] if e['aRelire'])
    n_vide = sum(1 for c in competences if not c['etapes'])
    print(f"{out}\n  {len(competences)} competences, {n_et} etapes")
    print(f"  {n_rel} etape(s) a relire, {n_vide} competence(s) sans aucune etape")


if __name__ == '__main__':
    main(*sys.argv[1:4])
