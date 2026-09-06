# Cahier-journal MS / GS

Outil de préparation hebdomadaire pour une classe de maternelle à double niveau
moyenne / grande section. On saisit la semaine, on imprime cinq pages A4 — une
par jour — au format de la maquette validée.

## Principe

L'**emploi du temps** fournit le squelette : horaires, niveaux, domaines, prise
en charge et type de groupe sont déjà là. Il ne reste qu'à renseigner l'intitulé
de l'activité, la ou les compétences travaillées, et le matériel s'il doit être
précisé. Les rotations de groupes se calculent toutes seules.

Les données sont des fichiers JSON lisibles. **C'est la source de vérité** :
l'application n'est qu'un éditeur par-dessus. Si elle disparaît, les fichiers
restent, et les PDF déjà imprimés aussi.

## Installation sur un Mac

1. Installer **Node.js** — version LTS, sur <https://nodejs.org>. Un installeur
   signé par Apple, double-clic, deux minutes. À faire une fois par machine.
2. Placer le dossier du projet dans iCloud Drive.
3. Double-cliquer sur `demarrer.command`.

Le navigateur s'ouvre sur l'application. La fenêtre du terminal doit rester
ouverte pendant l'utilisation.

Les données sont écrites dans
`~/Library/Mobile Documents/com~apple~CloudDocs/Cahier-journal/`, donc
synchronisées entre le MacBook et l'iMac sans rien faire.

## Utilisation en développement (Windows, Linux)

```bash
node app/serveur.mjs
```

Les données sont alors lues dans `data/`. Pour pointer ailleurs :

```bash
CJ_DONNEES=/chemin/vers/les/donnees node app/serveur.mjs
```

## Imprimer

Le bouton **Imprimer** ouvre les cinq pages mises en forme. Ensuite
`Cmd` + `P`, puis *PDF → Enregistrer au format PDF*, ou impression directe.

La taille du texte s'ajuste page par page : chaque journée prend la plus grande
taille qui tient encore sur une page. Une journée chargée rétrécit un peu, une
journée légère grossit — mais jamais de sixième page.

## Organisation des fichiers

```
app/
  serveur.mjs       serveur local, API fichiers — zéro dépendance
  rendu.mjs         mise en page imprimable
  generer.mjs       rendu en ligne de commande
  ui/               interface de saisie
data/
  emploi-du-temps-2026-2027-P1.json   le squelette de la semaine, éditable
  referentiel-competences.json        les 156 étapes des livrets
  referentiel-corrections.json        les décisions humaines sur le référentiel
  catalogue-activites.json            s'enrichit tout seul à chaque saisie
  semaines/                           une semaine = un fichier
tools/                extraction des livrets PDF, amorce de l'emploi du temps
docs/                 sources : livrets, emploi du temps, programmations
```

**Aucune dépendance npm**, volontairement : pas de `node_modules` à
synchroniser dans iCloud, et rien qui casse à la prochaine mise à jour d'un
paquet tiers.

## Le référentiel de compétences

Les 156 étapes viennent des deux livrets d'évaluation, extraites des PDF puis
relues et validées. Motricité, activités artistiques et exploration du monde
n'ont pas de référentiel : l'application y propose une **compétence libre**,
plutôt que d'inventer des codes.

Pour ré-extraire les livrets après une mise à jour des PDF :

```bash
python tools/extract_livret.py "docs/livret maths 2026 OK V2.pdf" maths /tmp/ma.json
python tools/extract_livret.py "docs/livret français 2026 OK.pdf" francais /tmp/fr.json
python tools/build_referentiel.py /tmp/ma.json /tmp/fr.json \
    data/referentiel-competences.json data/referentiel-corrections.json
```

Les corrections humaines sont réappliquées automatiquement : elles survivent à
la ré-extraction.
