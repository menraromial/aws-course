---
title: "TP 3 : Un serveur web sur EC2"
sidebar_label: "Le TP"
description: "Paire de clés, lancement d'une instance Amazon Linux 2023, connexion SSH, installation de Nginx, métadonnées, arrêt et redémarrage, relance par user data."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import tp3Architecture from '@site/src/figures/tp3-architecture.svg';
import Chemin from '@site/src/components/Chemin';

<Seance items={['Module 3', 'Travaux pratiques']} />

Vous allez lancer votre première instance, vous y connecter, y installer un serveur web et l'ouvrir dans votre navigateur. Puis vous la détruirez, et vous en relancerez une identique sans taper une seule commande dessus.

<Schema svg={tp3Architecture} num="TP3" alt="Votre navigateur atteint en HTTP 80, et votre terminal en SSH 22 depuis votre adresse, la passerelle Internet du VPC par défaut (172.31.0.0/16) en région eu-west-3. Dans la zone eu-west-3a, le sous-réseau public contient l'instance web-<prenom> qui fait tourner Nginx, protégée par le Security Group sg-web-<prenom> et munie d'un volume EBS de 8 Gio.">
  Ce que vous allez construire. Le VPC par défaut fournit déjà le réseau, la passerelle Internet et des sous-réseaux publics : vous n'avez qu'à y poser l'instance.
</Schema>

Vous avez besoin du Security Group `sg-web-<prenom>` créé au TP 2. S'il n'existe plus, recréez-le d'abord (TP 2, étape 6). Vérifiez aussi que votre adresse IP n'a pas changé depuis : ouvrez [checkip.amazonaws.com](https://checkip.amazonaws.com/) et comparez avec la source de la règle SSH.

:::cout
À partir de maintenant, vous créez des ressources qui coûtent tant qu'elles existent. La dernière étape de ce TP consiste à tout résilier. Ne partez pas sans l'avoir faite.
:::

## 1. Créer votre paire de clés

1. Ouvrez <Chemin>EC2 › Key Pairs › Create key pair</Chemin>.
2. Nom : `cle-<prenom>`. Type : **ED25519**. Format : **.pem** (choisissez **.ppk** seulement si vous comptez utiliser PuTTY sous Windows).
3. Cliquez sur **Create key pair**. Le navigateur télécharge aussitôt le fichier `cle-<prenom>.pem`. C'est la seule fois que vous pourrez l'obtenir.

Rangez le fichier dans un dossier à vous, par exemple `~/.ssh/`, puis restreignez ses permissions. Sans cela, le client SSH refusera de s'en servir.

```bash title="Linux ou macOS"
mv ~/Téléchargements/cle-<prenom>.pem ~/.ssh/
chmod 400 ~/.ssh/cle-<prenom>.pem
```

```powershell title="Windows (PowerShell)"
icacls .\cle-<prenom>.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

## 2. Lancer l'instance

Ouvrez <Chemin>EC2 › Instances › Launch instances</Chemin> et remplissez l'assistant de haut en bas.

1. **Name and tags** : nommez l'instance `web-<prenom>`. Cliquez sur **Add additional tags** et ajoutez le tag `Proprietaire` avec votre prénom.
2. **Application and OS Images** : dans *Quick Start*, choisissez **Amazon Linux**, puis l'AMI **Amazon Linux 2023** en architecture **64-bit (x86)**. Notez son identifiant `ami-...`.
3. **Instance type** : `t3.micro`.
4. **Key pair** : `cle-<prenom>`.
5. **Network settings** : cliquez sur **Edit**. Laissez le VPC par défaut et le sous-réseau proposé, vérifiez que **Auto-assign public IP** est sur *Enable*, puis choisissez **Select existing security group** et sélectionnez `sg-web-<prenom>`.
6. **Configure storage** : laissez le volume proposé, 8 Gio en `gp3`.
7. **Advanced details** : dépliez la rubrique. Vous y trouverez deux réglages dont on a parlé en cours.
    - **Credit specification** : choisissez **Standard**. En cas de charge anormale, l'instance ralentira au lieu de coûter plus cher.
    - **Metadata version** : vérifiez qu'il est indiqué **V2 only (token required)**.
8. Dans le résumé à droite, relisez tout, puis cliquez sur **Launch instance**.

Revenez à la liste des instances. La vôtre passe de `Pending` à `Running` en quelques dizaines de secondes. Attendez que la colonne **Status check** affiche `2/2 checks passed` : cela signifie que la machine virtuelle et son système d'exploitation répondent.

Cliquez sur l'instance et relevez dans l'onglet **Details** son adresse IPv4 publique, son adresse IPv4 privée et sa zone de disponibilité.

## 3. Se connecter en SSH

```bash title="Votre terminal"
ssh -i ~/.ssh/cle-<prenom>.pem ec2-user@<IP-publique>
```

À la première connexion, SSH affiche l'empreinte de la clé du serveur et demande confirmation : répondez `yes`. Vous devez arriver sur une invite de la forme `[ec2-user@ip-172-31-... ~]$`.

Faites connaissance avec la machine :

```bash title="Sur l'instance"
cat /etc/os-release | head -3
nproc && free -h
df -h /
ip -brief address
```

Vous retrouvez les deux processeurs et le gigaoctet de mémoire d'une `t3.micro`, et le disque de 8 Gio. La dernière commande réserve une surprise : l'interface réseau n'affiche que l'adresse **privée**, en `172.31.x.x`. L'adresse publique n'existe pas sur la machine. C'est la passerelle Internet du VPC qui traduit, à l'entrée et à la sortie, l'adresse publique en adresse privée.

## 4. Installer Nginx

```bash title="Sur l'instance"
sudo dnf install -y nginx
sudo systemctl enable --now nginx
systemctl status nginx --no-pager
curl -sI http://localhost | head -1
```

La dernière commande doit répondre `HTTP/1.1 200 OK`. Ouvrez maintenant, dans votre navigateur, l'adresse `http://<IP-publique>`. Tapez bien `http://` : certains navigateurs essaient d'abord `https://`, qui n'est pas encore configuré. La page de test de Nginx doit s'afficher.

Si c'est le cas, faites le point : la requête de votre navigateur a traversé Internet, la passerelle du VPC, le Security Group (règle HTTP), et atteint Nginx sur l'instance.

## 5. Une page qui dit où elle tourne

Remplaçons la page de test par une page qui affiche les informations de l'instance, lues dans le service de métadonnées. Essayez d'abord l'ancienne méthode, sans jeton :

```bash title="Sur l'instance"
curl -s -o /dev/null -w "%{http_code}\n" http://169.254.169.254/latest/meta-data/instance-id
```

La réponse est `401` : IMDSv2 est exigé, la requête sans jeton est refusée. Faites-le correctement :

```bash title="Sur l'instance"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
md() { curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/$1"; }
md instance-id; echo; md placement/availability-zone; echo
```

Générez ensuite la page :

```bash title="Sur l'instance"
sudo tee /usr/share/nginx/html/index.html > /dev/null <<EOF
<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>web-<prenom></title></head>
<body>
  <h1>Bonjour depuis EC2</h1>
  <ul>
    <li>Instance : $(md instance-id)</li>
    <li>Type : $(md instance-type)</li>
    <li>Zone : $(md placement/availability-zone)</li>
    <li>IP publique au moment de la génération : $(md public-ipv4)</li>
  </ul>
</body></html>
EOF
```

Rechargez la page dans votre navigateur.

## 6. Vérifier le pare-feu depuis l'extérieur

CloudShell tourne sur une machine d'AWS, avec une adresse IP qui n'est pas la vôtre. C'est l'endroit idéal pour vérifier ce que voit « le reste d'Internet ». Ouvrez CloudShell et essayez :

```bash title="CloudShell"
curl -s http://<IP-publique> | head -5
timeout 10 bash -c "</dev/tcp/<IP-publique>/22" && echo "port 22 ouvert" || echo "port 22 fermé"
```

La page web s'affiche, puisque le port 80 est ouvert à tous. Le port 22, lui, ne répond pas : la règle SSH n'autorise que votre adresse, et le Security Group ignore silencieusement tout le reste.

## 7. Arrêter et redémarrer

Dans la console, sélectionnez l'instance et choisissez <Chemin>Instance state › Stop instance</Chemin>. Attendez l'état `Stopped`, puis <Chemin>Instance state › Start instance</Chemin>.

Pendant que l'instance est arrêtée, ouvrez <Chemin>EC2 › Volumes</Chemin> : son volume est toujours là, dans l'état `In-use`. C'est lui que vous continuez de payer, quelques centimes par mois pour 8 Gio. Les heures de calcul, elles, ne sont plus facturées, et l'adresse IPv4 publique a été rendue à AWS, donc ne coûte plus rien non plus.

Une fois l'instance revenue à l'état `Running`, relevez de nouveau les adresses. L'adresse privée n'a pas bougé ; l'adresse publique a changé. Votre ancienne connexion SSH est morte, et l'ancienne adresse dans le navigateur ne répond plus. Ouvrez la nouvelle : la page s'affiche, puisque Nginx a été activé au démarrage (`enable`) et que le disque a gardé son contenu. Regardez pourtant la ligne « IP publique » : elle affiche toujours l'ancienne adresse. La page est un fichier généré une fois pour toutes, qui ne sait pas que le monde a changé autour d'elle.

Comparez avec un simple redémarrage. Reconnectez-vous en SSH avec la nouvelle adresse et tapez `sudo reboot`, puis, une minute plus tard, `uptime` après vous être reconnecté. Cette fois l'adresse publique n'a pas changé : un redémarrage relance le système d'exploitation sans libérer la machine physique ni l'adresse, alors qu'un arrêt rend tout à AWS, à l'exception du volume. Après un nouveau démarrage, l'instance a d'ailleurs pu atterrir sur un autre serveur physique.

## 8. Tout recommencer, sans les mains

Vous allez maintenant détruire cette instance et en lancer une nouvelle qui se configure seule au démarrage.

1. Sélectionnez `web-<prenom>` et choisissez <Chemin>Instance state › Terminate (delete) instance</Chemin>. Confirmez.
2. Relancez l'assistant <Chemin>Instances › Launch instances</Chemin> avec exactement les mêmes réglages qu'à l'étape 2, en nommant l'instance `web2-<prenom>`.
3. Dans **Advanced details**, tout en bas, collez ce script dans le champ **User data** :

    ```bash title="User data"
    #!/bin/bash
    dnf install -y nginx
    TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
      -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
    md() { curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
      "http://169.254.169.254/latest/meta-data/$1"; }
    cat > /usr/share/nginx/html/index.html <<EOF
    <!doctype html>
    <html lang="fr"><head><meta charset="utf-8"><title>web2</title></head>
    <body>
      <h1>Cette instance s'est configurée toute seule</h1>
      <p>Instance $(md instance-id), zone $(md placement/availability-zone),
         générée le $(date '+%d/%m/%Y à %H:%M').</p>
    </body></html>
    EOF
    systemctl enable --now nginx
    ```

4. Lancez l'instance. Dès qu'elle est `Running`, attendez encore une minute : le script s'exécute pendant ce temps. Ouvrez `http://<nouvelle-IP-publique>`.

Vous n'avez tapé aucune commande sur cette machine, et elle sert déjà votre page. Si rien ne s'affiche au bout de deux minutes, connectez-vous en SSH et lisez le journal d'exécution du script : `sudo cat /var/log/cloud-init-output.log`.

## 9. Ranger

Résiliez `web2-<prenom>` (<Chemin>Instance state › Terminate (delete) instance</Chemin>). Vérifiez dans la liste qu'aucune instance à votre nom n'est dans l'état `Running` ou `Stopped`.

Gardez la paire de clés `cle-<prenom>` et le Security Group `sg-web-<prenom>`, qui ne coûtent rien et resserviront aux modules 4 et 5. Gardez aussi le script de l'étape 8 : il servira de point de départ la prochaine fois.

## Si ça ne marche pas

La connexion SSH reste bloquée puis se termine par `Connection timed out` : c'est presque toujours le Security Group. Votre adresse a peut-être changé depuis la création de la règle ; comparez avec [checkip.amazonaws.com](https://checkip.amazonaws.com/) et corrigez la source de la règle SSH. Certains réseaux d'établissement bloquent aussi les connexions SSH sortantes ; le partage de connexion de votre téléphone permet de le vérifier (pensez alors à mettre à jour la règle).

SSH répond `Permission denied (publickey)` : le Security Group laisse passer, mais la clé ne convient pas. Vérifiez que vous utilisez bien `cle-<prenom>.pem`, l'utilisateur `ec2-user` et non `root`, et que l'instance a été lancée avec cette paire de clés.

SSH répond `UNPROTECTED PRIVATE KEY FILE` : les permissions du fichier `.pem` sont trop ouvertes. Reprenez le `chmod 400` ou la commande `icacls` de l'étape 1.

Le navigateur tourne sans fin sur `http://<IP>` : vérifiez l'adresse (elle change à chaque redémarrage), la règle HTTP du Security Group, et que Nginx tourne (`systemctl status nginx`).

## Questions

1. Pourquoi la commande `ip -brief address` n'affiche-t-elle pas l'adresse publique de l'instance ?
2. Après l'arrêt et le redémarrage, qu'est-ce qui a été conservé, qu'est-ce qui a changé, et pourquoi ?
3. Que se serait-il passé si vous aviez perdu le fichier `cle-<prenom>.pem` avant l'étape 3 ?
4. Quel avantage voyez-vous à l'instance `web2` par rapport à `web` ? Et quel inconvénient ?
