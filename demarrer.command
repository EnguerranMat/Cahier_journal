#!/bin/bash
# Lance le cahier-journal sur un Mac. Double-clic depuis le Finder.
# Garder cette fenêtre ouverte pendant l'utilisation ; la fermer arrête l'appli.
#
# Si le double-clic répond « vous n'avez pas les autorisations nécessaires »,
# c'est que le fichier n'est pas marqué exécutable. Une seule fois, dans le
# Terminal :   chmod +x "chemin/vers/demarrer.command"

cd "$(dirname "$0")" || exit 1

echec() {
  echo
  echo "$1"
  echo
  read -r -p "Appuie sur Entrée pour fermer."
  exit 1
}

if ! command -v node >/dev/null 2>&1; then
  echec "Node.js n'est pas installé sur ce Mac.
Télécharge la version LTS sur https://nodejs.org, installe-la,
puis relance ce fichier."
fi

# Les données vivent dans iCloud Drive : elles se synchronisent toutes seules
# entre le MacBook et l'iMac, et restent lisibles sans l'application.
ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
[ -d "$ICLOUD" ] || echec "iCloud Drive est introuvable sur ce Mac.
Active-le dans Réglages Système > identifiant Apple > iCloud > iCloud Drive,
ou modifie la variable CJ_DONNEES dans ce fichier pour choisir un autre dossier."

export CJ_DONNEES="${CJ_DONNEES:-$ICLOUD/Cahier-journal}"
mkdir -p "$CJ_DONNEES/semaines" || echec "Impossible de créer $CJ_DONNEES"

# Premier lancement : déposer le référentiel et l'emploi du temps dans le
# dossier de données. Un fichier déjà présent n'est jamais écrasé.
for f in referentiel-competences.json referentiel-corrections.json \
         emploi-du-temps-2026-2027-P1.json; do
  if [ ! -f "$CJ_DONNEES/$f" ] && [ -f "data/$f" ]; then
    cp "data/$f" "$CJ_DONNEES/$f"
    echo "installé : $f"
  fi
done
[ -f "$CJ_DONNEES/referentiel-competences.json" ] || echec \
  "Le référentiel des compétences est introuvable.
Attendu dans $CJ_DONNEES
ou dans le dossier data/ à côté de ce fichier."

echo "Cahier-journal — démarrage…"
echo "Données : $CJ_DONNEES"
node app/serveur.mjs &
SERVEUR=$!
trap 'kill $SERVEUR 2>/dev/null' EXIT

sleep 1
kill -0 $SERVEUR 2>/dev/null || echec "Le serveur n'a pas démarré. Voir le message ci-dessus."
open "http://127.0.0.1:4173"

echo
echo "L'application est ouverte dans le navigateur."
echo "Laisse cette fenêtre ouverte. Pour arrêter : ferme-la, ou Ctrl+C."
wait $SERVEUR
