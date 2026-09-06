# -*- coding: utf-8 -*-
"""Genere l'emploi du temps de reference (periode 1, 2026-2027) en JSON.

Amorce a executer une fois : ensuite l'emploi du temps est une donnee editable
dans l'application, et ce script n'est plus la source de verite.

Sources : « EDT 2026 P1 V3.docx » et la maquette validee « Cahier-journal MS-GS
- Semaine type.docx ». Correction apportee par Audrey le 5 septembre 2026 :
jeudi et vendredi, le regroupement est de 10h00 a 10h15 et la recreation de
10h15 a 10h45 (l'EDT d'origine faisait se chevaucher les deux).

Vocabulaire des champs
  type      fixe | ateliers | seance | pause
  saisie    aucune      rien a renseigner, la ligne est deja complete
            competence  l'intitule est fixe, la competence travaillee est a choisir
            complete    intitule, competence et materiel sont a saisir
  rotation  nom d'une rotation declaree en tete de fichier
"""
import json, os, sys

# --------------------------------------------------------------------------
# briques recurrentes


def fixe(debut, fin, domaine, intitule, par, org='Classe entière', niveau='MS + GS',
         pause=False):
    return {'debut': debut, 'fin': fin, 'type': 'pause' if pause else 'fixe',
            'niveau': niveau, 'domaine': domaine, 'intitule': intitule,
            'priseEnCharge': par, 'organisation': org, 'saisie': 'aucune'}


def ligne(niveau, domaine, par, org, intitule=None, saisie='complete',
          rotation=None, atelier=None):
    l = {'niveau': niveau, 'domaine': domaine, 'priseEnCharge': par,
         'organisation': org, 'saisie': saisie}
    if intitule:
        l['intitule'] = intitule
    if rotation:
        l['rotation'] = rotation
    if atelier:
        l['atelier'] = atelier
    return l


def ateliers(debut, fin, lignes):
    return {'debut': debut, 'fin': fin, 'type': 'ateliers', 'lignes': lignes}


def seance(debut, fin, l):
    return {'debut': debut, 'fin': fin, 'type': 'seance', 'lignes': [l]}


ACCUEIL = lambda: fixe('08:50', '09:10', 'Accueil',
    "Affaires, étiquette-prénom, rituel mathématiques, métiers (date, présents / absents, "
    "météo). MS en autonomie dans les espaces ; GS s'inscrivent au plan de travail.",
    'Audrey + Delphine')
ACCUEIL_ENCADRE = lambda: fixe('09:10', '09:30', 'Accueil encadré',
    "Remédiation pour les élèves fragiles, observation, évaluation. Espaces pour les autres.",
    'Audrey', 'Petit groupe')
CANTINE = lambda: fixe('12:00', '13:50', 'Cantine · pause méridienne',
    "Repas 12h–13h. Sieste MS puis lever échelonné ; activité périscolaire GS.",
    'Delphine', 'Périscolaire', pause=True)
CALME = lambda: fixe('13:50', '14:00', 'Accueil calme',
    "Lecture offerte, album de la période.", 'Audrey', niveau='GS')
BILAN = lambda: fixe('16:10', '16:15', 'Bilan',
    "De la journée, préparation à la sortie.", 'Audrey')
RECRE = lambda d, f: fixe(d, f, 'Récréation', "Cour, surveillance partagée.",
                          'Audrey + Delphine', pause=True)
PDT = lambda: ligne('GS', 'Plan de travail', 'Autonomie', 'Individuel',
                    'Plan de travail n° …', saisie='competence')
MOTRICITE = lambda: seance('11:15', '12:00',
    ligne('MS + GS', 'Motricité', 'Audrey', 'Classe entière'))
ECHELONNES = lambda: seance('14:45', '15:15',
    ligne('MS + GS', 'Formes et grandeurs', 'Delphine', 'Petit groupe',
          'Ateliers échelonnés : brevets (puzzle, construction…)', saisie='competence'))
RITUELS_GS = lambda: seance('14:00', '14:15',
    ligne('GS', 'Mathématiques ou langage', 'Audrey', 'Classe entière',
          'Activités ritualisées', saisie='complete'))

# --------------------------------------------------------------------------
# journees

LUNDI_MARDI = lambda: [
    ACCUEIL(), ACCUEIL_ENCADRE(),
    ateliers('09:30', '10:00', [
        ligne('MS', 'Langage oral ou écrit', 'Audrey', 'Petit groupe'),
        ligne('MS', 'Mathématiques', 'Delphine', 'Petit groupe'),
        PDT(),
    ]),
    ateliers('10:00', '10:30', [
        ligne('MS', 'Graphisme', 'Delphine', 'Petit groupe'),
        ligne('GS', 'Phonologie · principe alphabétique', 'Audrey', 'Demi-groupe',
              'Activités ritualisées'),
    ]),
    seance('10:30', '10:45',
           ligne('MS + GS', 'Regroupement', 'Audrey', 'Classe entière',
                 'Chant, langue, réussites du jour.', saisie='competence')),
    RECRE('10:45', '11:15'),
    MOTRICITE(), CANTINE(), CALME(), RITUELS_GS(),
    ateliers('14:15', '14:45', [
        ligne('GS', 'Écriture', 'Audrey', 'Petit groupe',
              "Atelier 1 — J'écris (CLEO) ou préparation à l'écriture",
              rotation='ateliersGS', atelier=1),
        ligne('GS', 'Mathématiques', 'Delphine', 'Petit groupe',
              'Atelier 2 — jeux de logique ou représentation dans l\'espace',
              rotation='ateliersGS', atelier=2),
        ligne('GS', 'Atelier autonome', 'Autonomie', 'Petit groupe',
              'Atelier 3 — atelier autonome', rotation='ateliersGS', atelier=3),
        ligne('MS', 'Motricité fine', 'Autonomie', 'Individuel',
              'Ateliers autonomes'),
    ]),
    ECHELONNES(), RECRE('15:15', '15:35'),
    ateliers('15:40', '16:10', [
        ligne('MS + GS', 'Compréhension', 'Audrey', 'Demi-groupe',
              'Lecture compréhension', rotation='lectureBCD', atelier=1),
        ligne('MS + GS', 'Écrits', 'Delphine', 'Demi-groupe',
              'BCD', rotation='lectureBCD', atelier=2),
    ]),
    BILAN(),
]

MERCREDI = lambda: [
    fixe('08:50', '09:15', 'Accueil',
         "Affaires, étiquette-prénom, rituel mathématiques, métiers (date, présents / "
         "absents, météo). Espaces en autonomie.", 'Audrey + Delphine'),
    fixe('09:15', '09:30', 'Regroupement',
         "Métiers, puis explication des trois ateliers tournants.", 'Audrey'),
    ateliers('09:30', '10:00', [
        ligne('MS + GS', 'Langage écrit', 'Audrey', 'Petit groupe',
              'Atelier 1', rotation='ateliersMercredi', atelier=1),
        ligne('MS + GS', 'Formes et grandeurs', 'Delphine', 'Petit groupe',
              'Atelier 2', rotation='ateliersMercredi', atelier=2),
        ligne('MS + GS', 'Atelier autonome', 'Autonomie', 'Petit groupe',
              'Atelier 3 — atelier autonome', rotation='ateliersMercredi', atelier=3),
    ]),
    seance('10:00', '10:15',
           ligne('MS + GS', 'Empathie · CPS', 'Audrey', 'Classe entière',
                 "Séance d'empathie en appui sur les autres disciplines")),
    RECRE('10:15', '10:45'),
    fixe('10:45', '11:45', 'Suite des ateliers',
         "Les trois ateliers de 9h30 : les enfants tournent.",
         'Audrey · Delphine · autonomie', 'Petit groupe'),
    fixe('11:45', '12:00', 'Regroupement',
         "Bilan de la matinée, préparation à la sortie.", 'Audrey'),
]


def jeudi_vendredi(apresmidi, fin_journee):
    return [
        ACCUEIL(), ACCUEIL_ENCADRE(),
        ateliers('09:30', '10:00', [
            ligne('MS', 'Mathématiques', 'Audrey', 'Petit groupe'),
            ligne('MS', "Principe alphabétique ou préparation à l'écriture",
                  'Delphine', 'Petit groupe'),
            PDT(),
        ]),
        # correction Audrey : regroupement 10h00-10h15, recreation 10h15-10h45
        seance('10:00', '10:15',
               ligne('MS + GS', 'Regroupement', 'Audrey', 'Classe entière',
                     'Chant, langue, réussites du jour.', saisie='competence')),
        RECRE('10:15', '10:45'),
        ateliers('10:45', '11:15', [
            ligne('MS', 'Phonologie · maths · principe alphabétique', 'Audrey',
                  'Demi-groupe', 'Rituels'),
            ligne('GS', 'Lettres, maths ou graphisme', 'Delphine', 'Petit groupe'),
        ]),
        MOTRICITE(), CANTINE(), CALME(), RITUELS_GS(),
        *apresmidi,
        ECHELONNES(), RECRE('15:15', '15:35'), fin_journee, BILAN(),
    ]


JEUDI = lambda: jeudi_vendredi(
    [ateliers('14:15', '14:45', [
        ligne('GS', 'Écriture', 'Audrey', 'Petit groupe',
              "Atelier 1 — J'écris (CLEO) ou préparation à l'écriture",
              rotation='ateliersGS', atelier=1),
        ligne('GS', 'Mathématiques', 'Delphine', 'Petit groupe',
              "Atelier 2 — jeux de logique ou représentation dans l'espace",
              rotation='ateliersGS', atelier=2),
        ligne('GS', 'Atelier autonome', 'Autonomie', 'Petit groupe',
              'Atelier 3 — atelier autonome', rotation='ateliersGS', atelier=3),
        ligne('MS', 'Motricité fine', 'Autonomie', 'Individuel', 'Ateliers autonomes'),
    ])],
    seance('15:40', '16:10',
           ligne('MS + GS', 'Éducation musicale · diversité linguistique', 'Audrey',
                 'Classe entière', saisie='complete')))

VENDREDI = lambda: jeudi_vendredi(
    [ateliers('14:15', '14:45', [
        ligne('GS', 'Mathématiques', 'Audrey', 'Demi-groupe',
              rotation='mathsVendrediGS', atelier=1),
        ligne('MS + GS', 'Jeux de société · motricité fine', 'Delphine', 'Petit groupe'),
    ])],
    seance('15:40', '16:10',
           ligne('MS + GS', 'Bilan de semaine', 'Audrey', 'Classe entière',
                 'Bilan de la semaine puis lecture offerte', saisie='competence')))


EDT = {
    'id': 'edt-2026-2027-P1',
    'anneeScolaire': '2026-2027',
    'periode': 1,
    'libelle': 'Emploi du temps MS / GS — Période 1',
    'sources': ['EDT 2026 P1 V3.docx', 'Cahier-journal MS-GS - Semaine type.docx'],
    'corrections': [
        "Jeudi et vendredi : regroupement 10h00–10h15 puis récréation 10h15–10h45 "
        "(l'EDT d'origine faisait se chevaucher regroupement 10h00–10h30 et "
        "récréation 10h15–10h45). Corrigé par Audrey."
    ],
    'referentiels': {
        'niveaux': ['MS', 'GS', 'MS + GS'],
        'priseEnCharge': ['Audrey', 'Delphine', 'Audrey + Delphine', 'Autonomie'],
        'organisations': ['Classe entière', 'Demi-groupe', 'Petit groupe',
                          'Individuel', 'Périscolaire'],
    },
    'rotations': {
        'ateliersGS': {
            'libelle': 'Ateliers GS de 14h15 — les trois groupes tournent',
            'groupes': ['A', 'B', 'C'],
            'cycle': ['lundi', 'mardi', 'jeudi'],
            'note': "Confirmé par Audrey : chaque groupe fait chacun des trois "
                    "ateliers une fois dans la semaine.",
        },
        'lectureBCD': {
            'libelle': 'Lecture compréhension et BCD de 15h40 — les deux demi-groupes '
                       'permutent',
            'groupes': ['1', '2'],
            'cycle': ['lundi', 'mardi'],
        },
        'mathsVendrediGS': {
            'libelle': "Atelier maths GS du vendredi — demi-groupe, une semaine sur deux",
            'groupes': ['1', '2'],
            'cycle': 'semaines',
            'note': "L'atelier ne prend qu'un demi-groupe : les deux moitiés "
                    "alternent d'une semaine à l'autre. Le groupe est calculé "
                    "d'après la semaine, et reste modifiable à la main.",
        },
        'ateliersMercredi': {
            'libelle': 'Trois ateliers du mercredi — rotation dans la matinée',
            'groupes': ['A', 'B', 'C'],
            'cycle': ['mercredi-1', 'mercredi-2', 'mercredi-3'],
            'note': "Rotation interne à la matinée : les enfants tournent entre 9h30 "
                    "et la suite de 10h45, pas d'un jour à l'autre.",
        },
    },
    'jours': [
        {'jour': 'lundi', 'creneaux': LUNDI_MARDI()},
        {'jour': 'mardi', 'creneaux': LUNDI_MARDI()},
        {'jour': 'mercredi', 'creneaux': MERCREDI(), 'demiJournee': 'matin'},
        {'jour': 'jeudi', 'creneaux': JEUDI()},
        {'jour': 'vendredi', 'creneaux': VENDREDI()},
    ],
}

if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(EDT, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    for j in EDT['jours']:
        n_lig = sum(len(c.get('lignes', [])) or 1 for c in j['creneaux'])
        a_saisir = sum(1 for c in j['creneaux'] for l in c.get('lignes', [])
                       if l['saisie'] != 'aucune')
        print(f"  {j['jour']:10} {len(j['creneaux']):2} créneaux, {n_lig:2} lignes, "
              f"{a_saisir:2} à renseigner")
    print(out)
