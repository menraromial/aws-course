#!/bin/bash
# Assemble static/kits/galerie-beanstalk.zip : l'application de kits/galerie
# (app.py, templates, requirements.txt) et les fichiers propres à Elastic
# Beanstalk de kits/galerie-beanstalk (Procfile, .platform, .ebextensions).
# Elastic Beanstalk exige que ces fichiers soient à la racine de l'archive.
set -euo pipefail
cd "$(dirname "$0")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cp -r galerie/app.py galerie/templates galerie/requirements.txt "$TMP"/
cp -r galerie-beanstalk/. "$TMP"/
rm -f ../static/kits/galerie-beanstalk.zip
(cd "$TMP" && zip -qr -X "$OLDPWD/../static/kits/galerie-beanstalk.zip" . -x '*__pycache__*')
unzip -l ../static/kits/galerie-beanstalk.zip
