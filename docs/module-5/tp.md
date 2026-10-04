---
title: "TP 5 : Déployer la galerie"
sidebar_label: "Le pas-à-pas"
description: "Déploiement pas à pas de la galerie : archive dans S3, instance avec rôle, installation, service systemd, Nginx en HTTP et HTTPS, vérifications de sécurité, nettoyage."
---

import Seance from '@site/src/components/Seance';
import Chemin from '@site/src/components/Chemin';
import Telechargement from '@site/src/components/Telechargement';

<Seance items={['Module 5', 'Travaux pratiques']} />

:::note[Votre nom dans les énoncés]
Partout où l'énoncé écrit `<prenom>`, mettez votre nom d'utilisateur AWS, par exemple `student12`, et non votre prénom. Exemple : `cle-<prenom>` devient `cle-student12`.
:::

Ce pas-à-pas vous mène d'une instance vide à la galerie en ligne, puis vous fait vérifier, point par point, que le déploiement tient les promesses du [cahier des charges](projet.md#le-cahier-des-charges). Toutes les commandes ont été rejouées sur Amazon Linux 2023 ; si l'une d'elles ne donne pas le résultat annoncé, arrêtez-vous et comprenez pourquoi avant de continuer.

## 1. Rassembler les pièces

Vous avez besoin de ce que vous avez construit aux modules précédents. Vérifiez chaque pièce dans la console avant de commencer.

| Pièce | Où la vérifier | Ce qu'il faut y voir |
|---|---|---|
| Le bucket `galerie-<prenom>-<suffixe>` | <Chemin>S3 › Buckets</Chemin> | région Paris, *Block all public access* activé |
| La stratégie `galerie-s3-<prenom>` | <Chemin>IAM › Policies</Chemin> | exactement deux déclarations : `s3:ListBucket` sur le bucket, `s3:GetObject` et `s3:PutObject` sur `<bucket>/*` |
| Le rôle `role-galerie-<prenom>` | <Chemin>IAM › Roles</Chemin> | entité de confiance `ec2.amazonaws.com`, stratégie `galerie-s3-<prenom>` attachée |
| Le Security Group `pare-feu-web-<prenom>` | <Chemin>EC2 › Security Groups</Chemin> | HTTP et HTTPS depuis `0.0.0.0/0`, SSH depuis votre adresse actuelle en `/32` |
| La paire de clés `cle-<prenom>` | <Chemin>EC2 › Key Pairs</Chemin> et votre dossier `~/.ssh` | le fichier `.pem` est bien sur votre ordinateur |

Si une pièce manque, reprenez l'étape correspondante : TP 2, étape 6 pour le Security Group ; TP 3, étape 1 pour la clé ; TP 4, étapes 1 et 5 pour le bucket, la stratégie et le rôle. Si la stratégie contient encore la déclaration `UtiliserLaFile` du TP 4, retirez-la : le rôle ne doit avoir que les droits dont l'application a besoin.

## 2. Déposer l'application dans le bucket

L'instance n'a pas accès à votre ordinateur, mais elle a accès à votre bucket. C'est donc par lui que l'application va transiter.

1. Téléchargez l'archive de l'application : <Telechargement fichier="kits/galerie.tar.gz" />
2. Dans la console, ouvrez votre bucket, cliquez sur **Create folder**, nommez le dossier `deploy` et créez-le.
3. Ouvrez `deploy/`, puis <Chemin>Upload › Add files</Chemin>, choisissez `galerie.tar.gz` et téléversez.

Vérifiez que l'objet a bien pour clé `deploy/galerie.tar.gz`. Le rôle de l'instance pourra le lire, puisque la stratégie autorise `s3:GetObject` sur tout le bucket.

## 3. Lancer l'instance

Ouvrez <Chemin>EC2 › Instances › Launch instances</Chemin> et reprenez les réglages du TP 3, avec une différence importante.

- **Name** : `galerie-<prenom>`, et le tag `Proprietaire`.
- **AMI** : Amazon Linux 2023, 64-bit (x86). **Type** : `t3.micro`. **Key pair** : `cle-<prenom>`.
- **Network settings** : VPC par défaut, adresse publique activée, Security Group existant `pare-feu-web-<prenom>`.
- **Advanced details** :
  - **IAM instance profile** : `role-galerie-<prenom>`. C'est la différence avec le TP 3, et c'est elle qui permettra à l'application de parler à S3.
  - **Credit specification** : *Standard*.
  - **Metadata version** : *V2 only (token required)*.

Si l'instance du TP 4 tourne encore, résiliez-la d'abord : vous n'avez droit qu'à une instance en marche. Lancez l'instance, attendez `2/2 checks passed`, notez son adresse IPv4 publique, puis connectez-vous en SSH.

```bash title="Votre terminal"
ssh -i ~/.ssh/cle-<prenom>.pem ec2-user@<IP-publique>
```

Si SSH répond `Too many authentication failures`, ajoutez `-o IdentitiesOnly=yes`, comme au TP 3.

Vérifiez tout de suite que l'instance a bien endossé le rôle et qu'elle voit l'archive :

```bash title="Sur l'instance"
aws sts get-caller-identity --query Arn --output text
B=galerie-<prenom>-<suffixe>
aws s3 ls s3://$B/deploy/
```

La première commande doit afficher `arn:aws:sts::<compte>:assumed-role/role-galerie-<prenom>/i-...`, la seconde la ligne de `galerie.tar.gz`. Si vous obtenez `Unable to locate credentials`, le rôle n'a pas été associé : <Chemin>Actions › Security › Modify IAM role</Chemin>.

## 4. Installer l'application

```bash title="Sur l'instance"
sudo dnf install -y nginx python3.12 openssl
aws s3 cp s3://$B/deploy/galerie.tar.gz /tmp/
sudo useradd --system --home-dir /opt/galerie --shell /sbin/nologin galerie
sudo mkdir -p /opt/galerie
sudo tar -xzf /tmp/galerie.tar.gz -C /opt/galerie --strip-components=1
sudo python3.12 -m venv /opt/galerie/venv
sudo /opt/galerie/venv/bin/pip install -r /opt/galerie/requirements.txt
sudo chown -R galerie:galerie /opt/galerie
printf 'GALERIE_BUCKET=%s\nGALERIE_REGION=eu-west-3\n' "$B" | sudo tee /etc/galerie.env
```

Prenez une minute pour comprendre ce que vous venez de faire. Vous avez installé Nginx et Python 3.12, récupéré l'archive depuis S3 grâce au rôle, créé un utilisateur système `galerie` qui ne peut pas ouvrir de session, décompressé l'application dans `/opt/galerie`, créé un environnement Python isolé dans lequel `pip` a installé Flask, boto3 et Gunicorn, puis donné le dossier à l'utilisateur `galerie`. Le dernier fichier, `/etc/galerie.env`, contient toute la configuration : le nom du bucket et la région. Affichez-le avec `cat /etc/galerie.env` et constatez qu'il ne contient aucun secret.

Parcourez aussi le code : `less /opt/galerie/app.py`. Il fait moins de 200 lignes. Cherchez l'endroit où le client S3 est créé et vérifiez qu'aucune clé ne lui est passée.

## 5. En faire un service

```bash title="Sur l'instance"
cat /opt/galerie/deploy/galerie.service
sudo cp /opt/galerie/deploy/galerie.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now galerie
systemctl status galerie --no-pager
curl -s http://127.0.0.1:8000/sante
```

Le fichier de service dit à systemd sous quel utilisateur lancer l'application (`User=galerie`), où trouver sa configuration (`EnvironmentFile=/etc/galerie.env`), quelle commande exécuter (Gunicorn, deux processus, sur `127.0.0.1:8000`) et quoi faire en cas de plantage (`Restart=on-failure`). `enable --now` le démarre immédiatement et au prochain boot.

La dernière commande interroge le point de contrôle de l'application, qui essaie de joindre le bucket. Elle doit répondre `{"bucket":"galerie-...","instance":{...},"statut":"ok"}`. Si le statut est `erreur`, lisez le champ `detail` : l'application traduit en clair les erreurs d'AWS les plus fréquentes. Les journaux du service se lisent avec `journalctl -u galerie -n 30`.

## 6. Ouvrir la galerie au monde

```bash title="Sur l'instance"
cat /opt/galerie/deploy/galerie-nginx.conf
sudo cp /opt/galerie/deploy/galerie-nginx.conf /etc/nginx/conf.d/galerie.conf
sudo nginx -t
sudo systemctl enable --now nginx
```

`nginx -t` vérifie la configuration avant tout démarrage : il doit répondre `syntax is ok` et `test is successful`. Ouvrez maintenant `http://<IP-publique>` dans votre navigateur. La galerie s'affiche, vide. Déposez une image.

La page se recharge avec le message « Fichier déposé dans S3 » et l'image apparaît. Ouvrez votre bucket dans la console : un préfixe `uploads/` est apparu, avec votre fichier, dont la clé commence par la date et l'heure du dépôt. En bas de la galerie, l'application affiche l'identifiant et la zone de l'instance qui l'a servie, lus dans le service de métadonnées.

Déposez deux ou trois autres fichiers, dont un qui n'est pas une image. Essayez aussi un fichier de plus de 10 Mo : l'application doit le refuser avec un message clair.

## 7. Passer en HTTPS

```bash title="Sur l'instance"
sudo openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj "/CN=galerie-<prenom>" \
  -keyout /etc/nginx/galerie.key -out /etc/nginx/galerie.crt
sudo cp /opt/galerie/deploy/galerie-nginx-https.conf /etc/nginx/conf.d/galerie-https.conf
sudo nginx -t && sudo systemctl reload nginx
```

La première commande fabrique une clé privée et un certificat autosigné valable 30 jours. Ouvrez `https://<IP-publique>`. Le navigateur affiche un avertissement de sécurité : il ne connaît pas l'émetteur de ce certificat, puisque c'est vous. Affichez les détails du certificat et retrouvez le nom `galerie-<prenom>` que vous lui avez donné, puis acceptez de continuer. La galerie s'affiche, cette fois par une connexion chiffrée.

## 8. Vérifier que le déploiement tient ses promesses

Chaque ligne du cahier des charges se vérifie par une commande. Faites-les toutes, et notez les résultats : ce sont eux que vous présenterez.

**Depuis CloudShell**, qui joue le rôle d'un inconnu sur Internet :

```bash title="CloudShell"
IP=<IP-publique>
curl -s -o /dev/null -w "HTTP  : %{http_code}\n" http://$IP/
curl -sk -o /dev/null -w "HTTPS : %{http_code}\n" https://$IP/
for p in 22 8000; do
  timeout 5 bash -c "</dev/tcp/$IP/$p" 2>/dev/null && echo "port $p : OUVERT" || echo "port $p : fermé"
done
```

Attendu : `200` en HTTP et en HTTPS, ports 22 et 8000 fermés. Le port 22 est fermé parce que le Security Group ne l'ouvre qu'à votre adresse. Le port 8000 l'est doublement : le Security Group ne l'ouvre pas, et Gunicorn n'écoute de toute façon que sur `127.0.0.1`, ce que vous pouvez constater sur l'instance avec `ss -ltn`.

**Depuis votre navigateur :**

- dans la console S3, ouvrez l'un de vos fichiers, copiez son **Object URL** et ouvrez-la dans une fenêtre de navigation privée : `AccessDenied` ;
- dans la galerie, cliquez sur le lien du même fichier : il s'ouvre, et son adresse contient `X-Amz-Signature` ;
- copiez ce lien, attendez six minutes, et ouvrez-le de nouveau : `Request has expired`. Rechargez la galerie pour obtenir un lien neuf.

**Sur l'instance :**

```bash title="Sur l'instance"
ls -a ~/.aws 2>&1; sudo ls -a /root/.aws 2>&1
sudo grep -rE "AKIA|aws_secret_access_key" /opt/galerie /etc/galerie.env --exclude-dir=venv \
  || echo "aucune clé d'accès"
F=$(aws s3 ls s3://$B/uploads/ | head -1 | awk '{print $4}')
aws s3 rm "s3://$B/uploads/$F"
```

Attendu : aucun dossier `.aws` (donc aucune configuration de clés), aucune clé dans l'application ni dans sa configuration, et un `AccessDenied` sur la suppression. On exclut `venv/` de la recherche parce que le code de boto3 lui-même contient ces mots.

**La résistance aux pannes :**

```bash title="Sur l'instance"
sudo systemctl kill -s KILL galerie; sleep 3
systemctl show -p NRestarts --value galerie; curl -s http://127.0.0.1:8000/sante
```

Vous venez de tuer brutalement l'application. systemd l'a relancée aussitôt : le compteur de redémarrages est passé à `1`, et le point de contrôle répond de nouveau. Enfin, redémarrez l'instance entière avec `sudo reboot`, attendez une minute, et rechargez la galerie dans votre navigateur : elle revient sans que vous ayez rien fait. Un redémarrage, contrairement à un arrêt suivi d'un démarrage, conserve l'adresse IP publique.

## 9. Ranger, pour de bon

C'est la fin du cours : tout ce que vous avez créé doit disparaître. Dans l'ordre :

1. **L'instance** `galerie-<prenom>` : <Chemin>Instance state › Terminate (delete) instance</Chemin>. Attendez l'état `Terminated`.
2. **Le bucket** : dans <Chemin>S3 › Buckets</Chemin>, sélectionnez-le, cliquez sur **Empty** et confirmez, puis sur **Delete**. Un bucket doit être vide pour être supprimé.
3. **Le rôle** `role-galerie-<prenom>`, puis **la stratégie** `galerie-s3-<prenom>`, dans IAM.
4. **Le Security Group** `pare-feu-web-<prenom>`. Il ne peut être supprimé qu'une fois l'instance résiliée.
5. **La paire de clés** `cle-<prenom>` dans <Chemin>EC2 › Key Pairs</Chemin>, et le fichier `.pem` sur votre ordinateur.

Vérifiez enfin, dans <Chemin>EC2 › Global View</Chemin>, qu'aucune instance ne tourne encore à votre nom dans aucune région.

## Pour aller plus loin

**Tout en une seule étape.** L'archive contient un script, `deploy/user-data.sh`, qui enchaîne toutes les commandes des étapes 4 à 7. Relancez une instance avec le rôle, collez ce script dans le champ **User data** en y remplaçant le nom du bucket, et ouvrez l'adresse de l'instance deux minutes plus tard. En cas de problème, le journal se lit dans `/var/log/cloud-init-output.log`. Vous aurez alors une application qu'on peut détruire et reconstruire à l'identique en quelques clics.

**Supprimer des fichiers.** Ajoutez à l'application un bouton qui supprime un fichier. Que faut-il changer dans la stratégie du rôle ? Comment le limiter aux seuls objets du préfixe `uploads/`, pour que l'application ne puisse jamais effacer son propre code dans `deploy/` ?
