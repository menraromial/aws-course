---
title: "TP 4 : Un bucket et un rôle"
sidebar_label: "Le TP"
description: "Bucket S3 privé, téléversement depuis la console, URL présignée, accès depuis une instance EC2 grâce à un rôle IAM."
hide_table_of_contents: true
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import tp4Architecture from '@site/src/figures/tp4-architecture.svg';
import Chemin from '@site/src/components/Chemin';
import Verrou from '@site/src/components/Verrou';

<Seance items={['Module 4', 'Travaux pratiques']} />

<Verrou id="tp4">


:::note[Votre nom dans les énoncés]
Partout où l'énoncé écrit `<prenom>`, mettez votre prénom, en minuscules et sans accent, sur un compte personnel ; sur le compte de l'enseignant, mettez votre nom d'utilisateur AWS, par exemple `student12`. Exemple : `cle-<prenom>` devient `cle-camille` ou `cle-student12`.
:::

Ce TP assemble les trois modules précédents. Vous allez créer un bucket privé, y déposer un fichier, le partager sans ouvrir le bucket, puis donner à une instance EC2 le droit d'y lire et d'y écrire, sans lui confier la moindre clé.

<Schema svg={tp4Architecture} num="TP4" alt="Dans la région du compte, l'instance web-<prenom>, qui endosse le rôle role-galerie-<prenom>, lit et écrit dans le bucket galerie-<prenom>-<suffixe> (aws s3 cp, ls). Depuis l'extérieur, vous téléversez des fichiers depuis la console, un navigateur accède au bucket avec une URL présignée, et un anonyme reçoit une erreur 403.">
  Ce que vous allez construire. Le bucket, le rôle et sa stratégie resserviront tels quels au projet final.
</Schema>

Vous aurez besoin de la paire de clés `cle-<prenom>`, du Security Group `pare-feu-web-<prenom>` et du numéro du compte (12 chiffres, visible dans le menu du compte). Préparez aussi une petite image sur votre ordinateur, une photo quelconque de quelques centaines de kilo-octets.

## 1. Créer le bucket

1. Ouvrez <Chemin>S3 › Buckets › Create bucket</Chemin>. Vérifiez que la région affichée est la vôtre : **Europe (Stockholm) eu-north-1** sur la plupart des comptes personnels, **Europe (Paris) eu-west-3** sur le compte de l'enseignant.
2. Nom : `galerie-<prenom>-<suffixe>`, où `<suffixe>` est un nombre de quatre chiffres tiré au hasard. Le nom doit être en minuscules, sans espace ni accent. Si la console répond qu'il existe déjà, changez de suffixe : quelqu'un, quelque part dans le monde, l'a déjà pris.
3. Parcourez les autres réglages sans les modifier, en les reconnaissant au passage. **Object Ownership** est sur *ACLs disabled*. **Block all public access** est coché. **Default encryption** indique un chiffrement côté serveur par des clés gérées par S3. C'est exactement ce que dit le cours : un bucket neuf est privé et chiffré.
4. Ajoutez un tag `Proprietaire` avec pour valeur votre `<prenom>` (obligatoire sur le compte de l'enseignant), puis cliquez sur **Create bucket**.

## 2. Déposer un fichier et essayer de le lire

1. Ouvrez votre bucket, puis <Chemin>Upload › Add files</Chemin>. Choisissez votre image et cliquez sur **Upload**.
2. Une fois le téléversement terminé, cliquez sur le nom de l'objet. La page de détails affiche sa clé, sa taille, son type (`image/jpeg` ou `image/png`), et une **Object URL** de la forme `https://galerie-<prenom>-<suffixe>.s3.<région>.amazonaws.com/<nom-du-fichier>`.
3. Copiez cette adresse et ouvrez-la dans une **fenêtre de navigation privée**.

Vous obtenez un court document XML avec le code `AccessDenied`. C'est la requête d'un anonyme : elle n'est signée par personne, et le bucket est privé.

Revenez dans votre fenêtre normale et cliquez sur le bouton **Open** en haut de la page de l'objet. Cette fois, l'image s'affiche. Regardez l'adresse dans la barre du navigateur : elle est beaucoup plus longue, avec des paramètres `X-Amz-Credential`, `X-Amz-Expires` et `X-Amz-Signature`. La console a fabriqué pour vous une URL présignée, avec votre propre identité.

## 3. Partager le fichier pour cinq minutes

1. Sur la page de l'objet, choisissez <Chemin>Object actions › Share with a presigned URL</Chemin>.
2. Indiquez une durée de **5 minutes** et validez. La console copie l'URL dans le presse-papiers.
3. Collez-la dans la fenêtre de navigation privée : l'image s'affiche, alors que cette fenêtre n'est connectée à aucun compte.
4. Revenez essayer la même URL dans six minutes. Vous obtiendrez une erreur `AccessDenied` accompagnée du message `Request has expired`.

Vous venez de partager un fichier précis, pour une durée précise, sans rendre public ni le bucket ni l'objet. C'est ce que fera l'application du projet final pour chaque téléchargement.

## 4. Une instance qui n'a le droit de rien

Vérifiez d'abord qu'aucune instance du TP 3 ne tourne encore à votre nom : sur le compte de l'enseignant, vous n'avez droit qu'à une instance en marche, et sur un compte personnel, une instance oubliée consomme vos crédits. Lancez ensuite une instance comme au TP 3 : nom `web-<prenom>`, tag `Proprietaire`, Amazon Linux 2023, `t3.micro`, paire de clés `cle-<prenom>`, Security Group `pare-feu-web-<prenom>`, crédits *Standard*. Pas de user data cette fois, et surtout, dans **Advanced details**, laissez le champ **IAM instance profile** vide.

Connectez-vous en SSH, puis demandez à AWS qui vous êtes :

```bash title="Sur l'instance"
aws sts get-caller-identity
aws s3 ls s3://galerie-<prenom>-<suffixe>/
```

Les deux commandes échouent avec `Unable to locate credentials`. L'outil `aws` est bien installé, mais l'instance n'a aucune identité : elle ne peut signer aucune requête. La tentation serait maintenant de lancer `aws configure` et d'y coller une clé d'accès. C'est précisément ce qu'on ne fait pas.

## 5. Donner un rôle à l'instance

Vous allez d'abord écrire la stratégie, puis créer le rôle qui la porte, puis l'associer à l'instance.

**La stratégie.** Ouvrez <Chemin>IAM › Policies › Create policy</Chemin>, passez en mode JSON et collez la stratégie suivante, en remplaçant le nom du bucket aux deux endroits :

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListerLeBucket",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::galerie-<prenom>-<suffixe>"
    },
    {
      "Sid": "LireEtEcrire",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::galerie-<prenom>-<suffixe>/*"
    }
  ]
}
```

Nommez-la `galerie-s3-<prenom>` et créez-la. Vous reconnaissez la stratégie étudiée en cours (module 2).

**Le rôle.** Ouvrez <Chemin>IAM › Roles › Create role</Chemin>.

1. **Trusted entity type** : *AWS service*. **Use case** : *EC2*. Cliquez sur **Next**.
2. Cherchez et cochez `galerie-s3-<prenom>`. Sur un compte personnel, passez directement à l'étape suivante. Sur le compte de l'enseignant, dépliez plus bas **Set permissions boundary**, choisissez d'utiliser une limite de permissions et sélectionnez `aws-cours-limite-role`, comme pour le stagiaire du TP 2. Cette limite plafonne le rôle à la lecture et à l'écriture dans des buckets `galerie-...` et à l'usage de files `file-...` : quoi que contienne un jour sa stratégie, une instance qui endosse ce rôle ne pourra rien faire d'autre. Sans elle, la création du rôle est refusée. Cliquez sur **Next**.
3. Nommez le rôle `role-galerie-<prenom>`. Avant de valider, regardez le bloc **Trust policy** affiché par la console : c'est la stratégie de confiance du cours, qui autorise `ec2.amazonaws.com` à endosser le rôle. Créez le rôle.

**L'association.** Dans la liste des instances, sélectionnez `web-<prenom>`, puis <Chemin>Actions › Security › Modify IAM role</Chemin>. Choisissez `role-galerie-<prenom>` et cliquez sur **Update IAM role**. Il n'est pas nécessaire de redémarrer l'instance.

## 6. Ce que le rôle permet, et ce qu'il ne permet pas

Revenez dans votre session SSH et recommencez :

```bash title="Sur l'instance"
aws sts get-caller-identity
```

L'ARN renvoyé a changé de forme : `arn:aws:sts::<compte>:assumed-role/role-galerie-<prenom>/i-0...`. L'instance a endossé le rôle, et la session porte son propre identifiant. Si la commande échoue encore, attendez une dizaine de secondes et réessayez.

Vérifiez maintenant, une par une, ce que le rôle autorise :

```bash title="Sur l'instance"
B=galerie-<prenom>-<suffixe>
aws s3 ls s3://$B/
echo "Bonjour depuis $(hostname)" > bonjour.txt
aws s3 cp bonjour.txt s3://$B/depuis-ec2/bonjour.txt
aws s3 cp s3://$B/<nom-de-votre-image> .
ls -l
```

Lister, écrire, lire : tout fonctionne. Rafraîchissez le bucket dans la console : un « dossier » `depuis-ec2/` est apparu, qui n'est rien d'autre que le préfixe de la clé que vous venez d'écrire.

Essayez maintenant ce que le rôle n'autorise pas :

```bash title="Sur l'instance"
aws s3 rm s3://$B/depuis-ec2/bonjour.txt
aws s3 ls
aws s3 ls s3://galerie-<prenom-d-un-voisin>-<son-suffixe>/
```

Les trois commandes échouent avec `AccessDenied`. La suppression, parce que la stratégie n'accorde pas `s3:DeleteObject`. La liste de tous les buckets du compte, parce qu'il faudrait `s3:ListAllMyBuckets`. Le bucket du voisin, parce que la stratégie ne cite que le vôtre. Si cette instance était un jour compromise, l'attaquant n'aurait accès qu'à votre bucket, sans pouvoir rien y effacer.

Fabriquez enfin une URL présignée depuis l'instance, et ouvrez-la dans votre navigateur :

```bash title="Sur l'instance"
aws s3 presign s3://$B/<nom-de-votre-image> --expires-in 300
```

## 7. Voir les identifiants temporaires

D'où viennent les identifiants que la commande `aws` utilise depuis l'étape 6 ? Du service de métadonnées. Regardez-les :

```bash title="Sur l'instance"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/role-galerie-<prenom>
```

La réponse contient une clé d'accès, une clé secrète, un jeton de session et une date d'expiration, quelques heures plus tard. Remarquez le début de la clé d'accès : `ASIA`. Les clés temporaires commencent par `ASIA`, les clés permanentes d'un utilisateur IAM par `AKIA`. Si vous tombez un jour sur une clé `AKIA` dans du code, vous savez ce qu'il faut faire.

## 8. Ranger

Cette fois, une partie de ce que vous avez créé resservira au projet final.

À **supprimer** : l'instance `web-<prenom>` (<Chemin>Instance state › Terminate (delete) instance</Chemin>).

À **garder** : le bucket et son contenu (quelques kilo-octets, pour un coût négligeable), la stratégie `galerie-s3-<prenom>`, le rôle `role-galerie-<prenom>`, la paire de clés et le Security Group.

## Questions

1. Pourquoi l'**Object URL** d'un objet renvoie-t-elle `AccessDenied`, alors que le bouton **Open** affiche l'image ?
2. Une URL présignée fabriquée par l'instance avec les identifiants de son rôle est valable 5 minutes. Pourrait-on la rendre valable une semaine ? Qu'est-ce qui limite sa durée ?
3. Pourquoi `aws s3 ls` (sans nom de bucket) est-il refusé alors que `aws s3 ls s3://galerie-<prenom>-<suffixe>/` fonctionne ?

</Verrou>
