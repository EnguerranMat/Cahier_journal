#!/bin/bash
# Lance le cahier-journal sur un Mac. Double-clic depuis le Finder.
# Garder cette fenêtre ouverte pendant l'utilisation ; la fermer arrête l'appli.

cd "$(dirname "$0")" || exit 1

# Les données vivent dans iCloud Drive : elles se synchronisent toutes seules
# entre le MacBook et l'iMac, et restent lisibles sans l'application.
export CJ_DONNEES="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Cahier-journal"
mkdir -p "$CJ_DONNEES/semaines"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js n'est pas installé sur ce Mac."
  echo "Télécharge-le sur https://nodejs.org (version LTS), puis relance ce fichier."
  read -r -p "Appuie sur Entrée pour fermer."
  exit 1
fi

echo "Cahier-journal — démarrage…"
node app/serveur.mjs &
SERVEUR=$!
sleep 1
open "http://localhost:4173"

echo
echo "L'application est ouverte dans le navigateur."
echo "Laisse cette fenêtre ouverte. Pour arrêter : ferme-la, ou Ctrl+C."
trap 'kill $SERVEUR 2>/dev/null' EXIT
wait $SERVEUR
