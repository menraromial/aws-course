---
title: "Introduction à AWS"
sidebar_label: "Organisation"
slug: /
description: "Déployer une application web publique sur AWS, avec EC2, S3, IAM et les Security Groups."
---

import Schema from '@site/src/components/Schema';
import architectureFinale from '@site/src/figures/architecture-finale.svg';
import Chemin from '@site/src/components/Chemin';
import Telechargement from '@site/src/components/Telechargement';
import Comptes from '@site/src/components/Comptes';
import TabItem from '@theme/TabItem';

Dans ce cours, vous allez mettre en ligne une petite application web sur AWS. Rien de spectaculaire : une page où l'on dépose un fichier, qui le range dans un espace de stockage et permet de le retélécharger. Ce qui est intéressant, c'est tout ce qu'il faut comprendre pour qu'elle fonctionne proprement. Elle tournera sur une machine virtuelle que vous aurez configurée vous-même, elle sera joignable par n'importe qui sur Internet, et pourtant personne d'autre que vous ne pourra se connecter à la machine. Elle écrira dans un bucket S3 sans qu'aucun mot de passe ni aucune clé ne soit écrit dans son code.

<Schema svg={architectureFinale} num="0" alt="Architecture du projet final. Des utilisateurs sur Internet atteignent en HTTP, ports 80 et 443, une instance EC2 qui fait tourner Nginx et l'application. L'instance se trouve dans un Security Group, dans le sous-réseau public du VPC par défaut, dans la région du compte. Seule votre adresse peut s'y connecter en SSH. L'instance endosse un rôle IAM qui lui permet de lire et d'écrire des fichiers dans un bucket S3 privé. Des pastilles numérotées de 1 à 5 indiquent le module qui construit chaque élément.">
  L'application que vous aurez déployée à la fin du cours. Les pastilles indiquent le module où chaque élément est construit.
</Schema>

Chaque module ajoute une pièce à ce schéma. Le premier vous apprend à vous repérer dans AWS : ce qu'on y loue, qui est responsable de quoi, où se trouvent les centres de données et comment on paie. Le deuxième traite de la sécurité : qui a le droit de faire quoi dans le compte, et quel trafic peut atteindre une machine. Le troisième vous fait lancer votre première machine virtuelle et y installer un serveur web. Le quatrième est consacré au stockage et, plus brièvement, aux bases de données et aux files de messages. Le dernier assemble le tout.

## Organisation

| Module | Cours | Travaux pratiques |
|---|---|---|
| 1 | [Introduction à AWS](module-1/cours.md) | [Prendre ses marques](module-1/tp.md) |
| 2 | [Sécurité et gestion des accès : IAM, VPC, Security Groups](module-2/cours.md) | [Un stagiaire, des droits, un pare-feu](module-2/tp.md) |
| 3 | [Calcul : Amazon EC2](module-3/cours.md) | [Un serveur web sur EC2](module-3/tp.md) |
| 4 | [Stockage, bases de données et messages : S3, EBS, RDS, DynamoDB, SQS](module-4/cours.md) | [Un bucket, un rôle, une file](module-4/tp.md) |
| 5 | [Projet final : la galerie](module-5/projet.md) | [Déployer la galerie](module-5/tp.md), puis [deux serveurs derrière un répartiteur](module-5/repartition.md) |

Chaque module commence par la théorie, présentée avec les diapositives du cours, puis passe à la pratique. Les pages de cours de ce site reprennent ces diapositives en les développant : vous pouvez les lire avant le cours pour le préparer, ou après pour revenir sur un point. Les TP se font dans l'ordre, chacun réutilisant parfois ce que le précédent a construit.

<Telechargement fichier="diapositives/introduction-aws.pdf">Télécharger les diapositives (PDF)</Telechargement>

## Ce qu'il vous faut

Il vous faut un accès à AWS, et il y en a deux sortes dans ce cours. Selon les groupes, chaque étudiant crée son propre compte AWS, ou bien l'enseignant remet à chacun un accès à un compte partagé. Les énoncés sont presque partout les mêmes ; là où la marche à suivre diffère, la page affiche deux onglets. Choisissez le vôtre une fois : le site s'en souvient et ouvre le même onglet sur toutes les pages.

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Vous créez vous-même votre compte, au début du TP 1, avec la nouvelle inscription d'AWS : on s'y connecte avec un AWS Builder ID, ou avec un compte Google, GitHub ou Apple, et la plupart des nouveaux inscrits n'ont pas à donner de carte bancaire[^inscription]. Le compte reçoit 100 $ de crédits, et jusqu'à 100 $ de plus si vous faites quelques activités guidées. Tant qu'il reste dans le plan gratuit, rien ne vous est facturé ; il se ferme seul au bout de six mois, ou plus tôt si les crédits sont épuisés[^plan-gratuit].

AWS place toutes vos ressources dans une région choisie d'après le pays de votre adresse, et vous ne pouvez pas en changer : Europe (Stockholm), `eu-north-1`, pour une adresse au Cameroun comme dans la plupart des pays d'Afrique et d'Europe[^region-projet]. Vous travaillerez dans cette région pendant tout le cours.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Les accès au compte AWS du cours vous sont remis au début du cours : une adresse de connexion, un nom d'utilisateur et un mot de passe provisoire. Ce compte est partagé par tous les étudiants, et il est réglé pour la région Europe (Paris), `eu-west-3`.

</TabItem>
</Comptes>

Pour le reste, un ordinateur portable suffit, avec un navigateur récent et un client SSH. Linux et macOS en ont un par défaut ; sous Windows 10 ou 11, la commande `ssh` est disponible dans PowerShell. Tout ce qui concerne AWS en ligne de commande se fera dans CloudShell, le terminal intégré à la console, sans rien installer.

## Comment lire les énoncés

Le titre de chaque bloc de commandes indique où le taper : **CloudShell**, **Votre terminal** (celui de votre ordinateur) ou **Sur l'instance**, c'est-à-dire sur la machine virtuelle une fois connecté en SSH. Le bouton de copie, en haut à droite du bloc, copie les commandes telles quelles.

Les chemins dans la console sont écrits comme ceci : <Chemin>EC2 › Instances › Launch instances</Chemin>. Ils reprennent les libellés anglais, langue par défaut de la console et de la documentation. AWS modifie régulièrement l'interface ; si un bouton a changé de place, la barre de recherche (<kbd>Alt</kbd>+<kbd>S</kbd>) retrouve n'importe quel service par son nom.

Dans les noms de ressources, les énoncés écrivent `<prenom>`.

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Remplacez `<prenom>` par votre prénom, en minuscules et sans accent : `galerie-camille-4821`, `cle-camille`. Le compte n'appartient qu'à vous, rien ne vous y oblige, mais ces noms vous aideront à reconnaître vos ressources et à suivre les corrigés.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Remplacez `<prenom>` par votre **nom d'utilisateur AWS**, celui qui vous a été remis avec votre mot de passe, de la forme `student12`. Malgré le nom du repère, ce n'est donc pas votre prénom : si votre identifiant est `student12`, votre bucket s'appellera `galerie-student12-4821` et votre paire de clés `cle-student12`. Ce n'est pas qu'une convention : les droits de votre compte ne vous autorisent à créer et à modifier que des ressources qui portent ce nom.

</TabItem>
</Comptes>

Les énoncés écrivent aussi « votre région ». C'est Stockholm (`eu-north-1`) pour la plupart des comptes personnels et Paris (`eu-west-3`) sur le compte de l'enseignant. Les commandes la lisent elles-mêmes quand c'est possible, et les noms de zones s'écrivent `<région>a`, `<région>b` : `eu-north-1a` à Stockholm, `eu-west-3a` à Paris.

[^inscription]: AWS, « New AWS experience helps builders get started and ship faster », annonce du 16 septembre 2026, [aws.amazon.com/about-aws/whats-new/2026/09/New-AWS-Builder-Experience](https://aws.amazon.com/about-aws/whats-new/2026/09/New-AWS-Builder-Experience/).
[^plan-gratuit]: AWS, « Choosing a plan », *AWS Billing User Guide*, [docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).
[^region-projet]: AWS, « AWS Regions for your projects », *AWS Account Management Reference Guide*, avec la liste des pays et de leur région, [docs.aws.amazon.com/accounts/latest/reference/project-regions.html](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html).
