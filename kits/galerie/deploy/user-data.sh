#!/bin/bash
# User data : déploie la galerie sans intervention au premier démarrage de l'instance.
# À coller dans « Advanced details › User data » en remplaçant le nom du bucket.
# L'instance doit porter le rôle role-galerie-<prenom> et l'archive doit se trouver
# dans le bucket sous la clé deploy/galerie.tar.gz.
set -euxo pipefail
B="galerie-<prenom>-<suffixe>"
case "$B" in *"<"*) echo "Remplacez le nom du bucket dans le script" >&2; exit 1 ;; esac

dnf install -y nginx python3.12 openssl
aws s3 cp "s3://$B/deploy/galerie.tar.gz" /tmp/galerie.tar.gz

useradd --system --home-dir /opt/galerie --shell /sbin/nologin galerie
mkdir -p /opt/galerie
tar -xzf /tmp/galerie.tar.gz -C /opt/galerie --strip-components=1
python3.12 -m venv /opt/galerie/venv
/opt/galerie/venv/bin/pip install -r /opt/galerie/requirements.txt
chown -R galerie:galerie /opt/galerie
printf 'GALERIE_BUCKET=%s\nGALERIE_REGION=eu-west-3\n' "$B" > /etc/galerie.env

cp /opt/galerie/deploy/galerie.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now galerie

openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj "/CN=galerie" \
  -keyout /etc/nginx/galerie.key -out /etc/nginx/galerie.crt
cp /opt/galerie/deploy/galerie-nginx.conf /etc/nginx/conf.d/galerie.conf
cp /opt/galerie/deploy/galerie-nginx-https.conf /etc/nginx/conf.d/galerie-https.conf
nginx -t
systemctl enable --now nginx
