---
title: "TP 2 : Un stagiaire, des droits, un pare-feu"
sidebar_label: "Le TP"
description: "Stratégie sur mesure, groupe et utilisateur au moindre privilège, simulateur de stratégies, refus explicite, Security Group du serveur web."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import Chemin from '@site/src/components/Chemin';

<Seance items={['Module 2', 'Travaux pratiques']} />

:::note[Votre nom dans les énoncés]
Partout où l'énoncé écrit `<prenom>`, mettez votre nom d'utilisateur AWS, tel qu'il figure dans l'e-mail qui vous a transmis vos identifiants. C'est en général votre prénom en minuscules et sans accent, parfois un autre de vos prénoms ou votre prénom suivi d'un chiffre. Exemple : `cle-<prenom>` devient `cle-camille`, ou `cle-camille2`.
:::

Un stagiaire arrive dans l'équipe. Sa mission : faire l'inventaire des machines virtuelles et des pare-feu du compte. Il ne doit rien pouvoir créer, rien modifier, rien supprimer, et il n'a aucune raison de voir les fichiers stockés dans S3. Vous allez lui préparer un accès qui corresponde exactement à cette mission, puis vérifier, en vous mettant à sa place, qu'il ne peut rien faire de plus.

Dans la seconde partie, vous préparerez le Security Group qui protégera votre serveur web au module 3.

Le compte du cours est partagé : tout ce que vous créez porte votre nom d'utilisateur, pour que chacun retrouve ses ressources et ne touche pas à celles des autres. IAM et les Security Groups sont gratuits ; ce TP ne coûte rien.

## 1. Écrire la stratégie du stagiaire

Première idée : lui donner la stratégie gérée par AWS `ReadOnlyAccess`. Ouvrez-la pour voir (<Chemin>IAM › Policies</Chemin>, puis cherchez `ReadOnlyAccess`) et parcourez la liste des services qu'elle couvre. Elle permet de lire à peu près tout le compte, y compris le contenu de tous les buckets S3. C'est beaucoup trop pour un inventaire des machines. Vous allez écrire une stratégie sur mesure.

1. Ouvrez <Chemin>IAM › Policies › Create policy</Chemin>.
2. Passez en mode **JSON** et remplacez tout le contenu par :

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "InventaireEC2",
          "Effect": "Allow",
          "Action": "ec2:Describe*",
          "Resource": "*"
        }
      ]
    }
    ```

3. Cliquez sur **Next**. Nommez la stratégie `lecture-ec2-<prenom>` et donnez-lui une description, par exemple « Inventaire EC2 en lecture seule ».
4. Avant de valider, lisez le résumé que la console a tiré de votre JSON : un seul service, EC2, avec des niveaux d'accès *List* et *Read*, et aucune écriture. Cliquez sur **Create policy**.

Pourquoi `"Resource": "*"` ? Parce que la plupart des actions `Describe` d'EC2 ne peuvent pas être restreintes à une ressource particulière : on liste toutes les instances ou aucune. La documentation précise, pour chaque action, ce qu'on peut mettre dans `Resource`[^actions-ec2].

## 2. Créer le groupe et l'utilisateur

1. Ouvrez <Chemin>IAM › User groups › Create group</Chemin>. Nommez le groupe `stagiaires-<prenom>`.
2. Dans la liste des stratégies, attachez-en deux : la vôtre, `lecture-ec2-<prenom>` (le filtre **Customer managed** aide à la retrouver), et `AWSCloudShellFullAccess`, gérée par AWS. Sans cette seconde stratégie, le stagiaire ne pourrait même pas ouvrir CloudShell : chaque outil demande sa propre permission.
3. Créez le groupe.
4. Ouvrez <Chemin>IAM › Users › Create user</Chemin>. Nommez l'utilisateur `stagiaire-<prenom>` et cochez **Provide user access to the AWS Management Console**. Si la console vous propose IAM Identity Center, choisissez **I want to create an IAM user**.
5. Choisissez un mot de passe personnalisé et notez-le. Décochez l'obligation de le changer à la première connexion, puisque c'est vous qui allez l'utiliser.
6. À l'étape des permissions, choisissez **Add user to group** et cochez `stagiaires-<prenom>`.
7. Toujours sur cette page, dépliez **Set permissions boundary**, choisissez d'utiliser une limite de permissions et sélectionnez `aws-cours-limite-stagiaire`. Terminez la création.

    Une **limite de permissions** (*permissions boundary*) fixe le maximum de ce qu'un utilisateur pourra jamais faire, quelles que soient les stratégies qu'on lui attache par la suite : ses droits réels sont l'intersection de ses stratégies et de sa limite. Le compte du cours vous oblige à en poser une, préparée par votre enseignant, sur tout utilisateur que vous créez. Sans elle, n'importe quel étudiant pourrait écrire une stratégie `"Action": "*"`, l'attacher à son stagiaire, se connecter sous ce nom et devenir administrateur du compte. Si vous oubliez cette étape, la création de l'utilisateur est refusée.
8. Sur la page de confirmation, notez l'**adresse de connexion à la console** affichée pour cet utilisateur.

## 3. Se mettre à la place du stagiaire

Ouvrez une **fenêtre de navigation privée**, ou un autre navigateur, pour garder votre propre session ouverte à côté. Connectez-vous avec l'adresse notée, l'utilisateur `stagiaire-<prenom>` et son mot de passe. Placez-vous sur la région de Paris.

Commencez par ce qui doit fonctionner. Ouvrez <Chemin>EC2 › Security Groups</Chemin> : la liste des groupes du compte s'affiche. Ouvrez <Chemin>EC2 › Instances</Chemin> : même chose. Le tableau de bord d'EC2, lui, affiche peut-être quelques erreurs en rouge. C'est normal : il interroge au passage d'autres services, comme CloudWatch, auxquels le stagiaire n'a pas accès.

Essayez maintenant ce qui ne doit pas fonctionner. Dans <Chemin>EC2 › Security Groups</Chemin>, cliquez sur **Create security group**, remplissez un nom quelconque et validez. Vous devez obtenir un message d'erreur qui mentionne `ec2:CreateSecurityGroup`. Ouvrez ensuite S3 : la liste des buckets est refusée, elle aussi. Le stagiaire ne sait même pas quels buckets existent.

Refaites la même vérification en ligne de commande. Ouvrez CloudShell dans la fenêtre du stagiaire :

```bash title="CloudShell (stagiaire)"
aws sts get-caller-identity
aws ec2 describe-security-groups --query "SecurityGroups[].GroupName" --output text
aws ec2 create-security-group --group-name essai --description essai
aws s3 ls
```

La première commande doit afficher un ARN qui se termine par `user/stagiaire-<prenom>`, la deuxième la liste des Security Groups. La troisième échoue avec `UnauthorizedOperation`, la quatrième avec `AccessDenied`. Lisez ces messages en entier : ils disent précisément qui a demandé quoi.

Aucune de ces deux erreurs ne vient d'une interdiction. Aucune stratégie ne dit « le stagiaire n'a pas le droit de créer un Security Group » ; simplement, aucune ne l'y autorise. C'est le refus par défaut.

## 4. Tester sans rien exécuter

Essayer chaque action à la main n'est pas très pratique, et certaines sont trop dangereuses pour qu'on les tente « pour voir ». AWS fournit un outil qui évalue des stratégies sans rien exécuter : le **simulateur de stratégies IAM**[^simulateur].

1. Dans **votre** fenêtre (pas celle du stagiaire), ouvrez [policysim.aws.amazon.com](https://policysim.aws.amazon.com/).
2. Dans la colonne de gauche, sélectionnez l'utilisateur `stagiaire-<prenom>`.
3. En haut, choisissez le service **Amazon EC2** et cochez les actions `DescribeInstances`, `RunInstances` et `TerminateInstances`.
4. Cliquez sur **Run Simulation**.

Vous devez voir `allowed` pour `DescribeInstances` et `denied` pour les deux autres. Dépliez une ligne : le simulateur indique quelle stratégie a produit la décision, ou l'absence de toute stratégie pour un refus par défaut. Essayez aussi le service **IAM** avec l'action `ListUsers` : le stagiaire peut-il voir la liste des utilisateurs du compte ?

## 5. Provoquer un refus explicite

Vérifions maintenant, sur un cas concret, qu'un `Deny` l'emporte sur les `Allow`.

1. Dans votre fenêtre, ouvrez le groupe `stagiaires-<prenom>` et attachez-lui, en plus, la stratégie gérée `AmazonEC2ReadOnlyAccess`. Elle autorise elle aussi `ec2:Describe*`, parmi d'autres choses.
2. Toujours sur le groupe, onglet **Permissions**, choisissez <Chemin>Add permissions › Create inline policy</Chemin>. En mode JSON, saisissez :

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Deny",
          "Action": "ec2:DescribeVolumes",
          "Resource": "*"
        }
      ]
    }
    ```

    Nommez-la `interdire-volumes` et créez-la.

3. Revenez dans le CloudShell du stagiaire :

    ```bash title="CloudShell (stagiaire)"
    aws ec2 describe-volumes
    aws ec2 describe-instances --query "Reservations[].Instances[].InstanceId"
    ```

La première commande est refusée, alors que **deux** stratégies du groupe l'autorisent. La seconde fonctionne normalement. Un seul `Deny` a suffi.

4. Retirez ensuite du groupe `AmazonEC2ReadOnlyAccess` et la stratégie `interdire-volumes`, pour revenir à la situation de l'étape 2.

## 6. Le Security Group de votre serveur web

Fermez la fenêtre du stagiaire. Vous allez préparer le pare-feu de la machine que vous lancerez au module 3.

Commencez par regarder quelle adresse IP Internet voit pour votre ordinateur : ouvrez [checkip.amazonaws.com](https://checkip.amazonaws.com/). Sur le réseau de l'école, cette adresse est probablement partagée par tous les postes, puisque le réseau sort vers Internet par une seule adresse. Autoriser « votre IP » revient donc à autoriser toute l'école, ce qui reste bien plus étroit que le monde entier. Si vous changez de réseau, en passant sur le partage de connexion de votre téléphone par exemple, votre adresse change et il faudra mettre la règle à jour.

1. Ouvrez <Chemin>EC2 › Security Groups › Create security group</Chemin>.
2. Nom : `pare-feu-web-<prenom>`. Description : `Serveur web public, SSH restreint`. VPC : laissez le VPC par défaut.

    AWS refuse les noms qui commencent par `sg-` : ce préfixe est réservé aux identifiants que la console attribue elle-même à chaque groupe (`sg-0a1b2c...`). Le nom est libre pour le reste, mais il ne peut plus être modifié une fois le groupe créé, et la description non plus : relisez-les avant de valider. Ils n'acceptent que des caractères ASCII, d'où l'absence d'accent dans les descriptions.

3. Ajoutez trois règles entrantes :

    | Type | Source | Description |
    |---|---|---|
    | HTTP | Anywhere-IPv4 | `Site web public` |
    | HTTPS | Anywhere-IPv4 | `Site web public chiffre` |
    | SSH | My IP | `Administration depuis mon poste` |

4. Laissez la règle sortante par défaut, qui autorise tout : votre instance devra télécharger des paquets et joindre S3.
5. Ajoutez un tag `Proprietaire` avec pour valeur votre nom d'utilisateur AWS, puis créez le groupe.

Ouvrez le groupe créé et vérifiez l'onglet **Inbound rules** : trois règles, dont une SSH dont la source se termine par `/32`.

Ouvrez ensuite, pour comparer, le Security Group nommé `default`. Sa règle entrante autorise tout le trafic dont la source est… ce groupe lui-même. Les machines qui en font partie peuvent se parler entre elles, et personne d'autre ne peut les joindre.

:::tip[Et la connexion SSH depuis le navigateur ?]
La console EC2 propose de se connecter à une instance directement dans le navigateur, avec EC2 Instance Connect. Ce service se connecte depuis des adresses d'AWS, pas depuis la vôtre : avec une règle SSH limitée à votre adresse, il ne fonctionnera pas. C'est voulu. Nous utiliserons le client SSH de votre ordinateur.
:::

## 7. Ranger

Gardez le Security Group `pare-feu-web-<prenom>` : il servira au module 3.

Supprimez tout le reste, dans cet ordre :

1. l'utilisateur `stagiaire-<prenom>` (<Chemin>IAM › Users</Chemin>, **Delete**, puis saisissez son nom pour confirmer) ;
2. le groupe `stagiaires-<prenom>` ;
3. la stratégie `lecture-ec2-<prenom>` (<Chemin>IAM › Policies</Chemin>, filtre **Customer managed**).

Un utilisateur dont personne ne se sert est une porte d'entrée que personne ne surveille.

## Pour aller plus loin

Écrivez une stratégie qui autorise le stagiaire à arrêter et démarrer des instances (`ec2:StopInstances`, `ec2:StartInstances`), mais **uniquement** celles qui portent le tag `Projet` avec la valeur `formation`. Il vous faudra un bloc `Condition` utilisant la clé `aws:ResourceTag/Projet`[^tags]. Testez-la dans le simulateur, sur une instance taguée et sur une instance qui ne l'est pas.

## Questions

1. Pourquoi attacher `lecture-ec2-<prenom>` au groupe plutôt qu'à l'utilisateur directement ?
2. À l'étape 3, la création du Security Group a été refusée. Est-ce un refus explicite ou un refus par défaut ? Comment le savez-vous ?
3. Un collègue propose d'ouvrir le port 22 à `0.0.0.0/0`, « puisque de toute façon il faut une clé pour se connecter ». Que lui répondez-vous ?
4. Votre Security Group n'a aucune règle sortante particulière pour les réponses HTTP. Pourquoi le site fonctionnera-t-il quand même ?

[^actions-ec2]: AWS, *Actions, resources, and condition keys for Amazon EC2*, Service Authorization Reference, [docs.aws.amazon.com](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonec2.html).
[^simulateur]: AWS, *Testing IAM policies with the IAM policy simulator*, IAM User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html).
[^tags]: AWS, *Controlling access to AWS resources using tags*, IAM User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_tags.html).
