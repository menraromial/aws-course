---
title: "TP 1 : Prendre ses marques"
sidebar_label: "Le TP"
description: "Connexion au compte, réglages de la console, premiers appels depuis CloudShell, prix et caractéristiques des instances, vue globale du compte."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import consoleBarre from '@site/src/figures/console-barre.svg';
import Chemin from '@site/src/components/Chemin';
import Comptes from '@site/src/components/Comptes';
import TabItem from '@theme/TabItem';

<Seance items={['Module 1', 'Travaux pratiques']} />

Ce premier TP sert à se sentir chez soi dans la console : se connecter, régler deux ou trois choses qui vous feront gagner du temps pendant tout le cours, envoyer vos premières requêtes depuis un terminal et regarder combien coûte une machine avant d'en lancer une. Ce TP ne crée aucune ressource.

## 1. Se connecter

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Ouvrez la page d'inscription d'AWS, [signin.aws.amazon.com/signup](https://signin.aws.amazon.com/signup?request_type=builderId), et choisissez de vous inscrire avec un AWS Builder ID ou avec un compte que vous possédez déjà (Google, GitHub, Apple)[^inscription]. Donnez votre véritable adresse postale : AWS en déduit le pays, et du pays la région où seront rangées toutes vos ressources, sans possibilité d'en changer ensuite.

Créez votre compte au moins deux jours avant la première séance : AWS vérifie chaque nouveau compte, et certains services, dont CloudShell, ne s'ouvrent qu'une fois cette vérification terminée.

Si l'inscription vous réclame malgré tout une carte bancaire, arrêtez-vous et prévenez votre enseignant. AWS déploie cette nouvelle inscription progressivement, et certaines personnes tombent encore sur l'ancienne, qui en demande une[^deploiement-progressif].

AWS crée alors pour vous un **projet** : un compte AWS dont vous êtes l'administrateur, sans utilisateur *root* ni mot de passe propre au compte. Vous vous y connectez par [console.aws.amazon.com](https://console.aws.amazon.com/), avec l'identité choisie à l'inscription. Activez tout de suite l'authentification à deux facteurs de cette identité dans **AWS Settings** ([settings.aws.com](https://settings.aws.com)) : c'est elle qui protège tout votre compte.

Toujours dans AWS Settings, ouvrez <Chemin>Project › Overview › Additional Info</Chemin>. Vous y lisez le numéro du compte, sur douze chiffres, et la région de votre projet. Notez les deux[^region-projet].

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Pour commencer, vous avez besoin de ce qui vous a été remis : l'adresse de connexion du compte AWS du cours, votre nom d'utilisateur et un mot de passe provisoire.

Ouvrez l'adresse de connexion. Elle ressemble à `https://<compte>.signin.aws.amazon.com/console`, et la page demande directement un nom d'utilisateur et un mot de passe. Si vous arrivez sur une page qui vous propose de choisir entre *Root user* et *IAM user*, choisissez **IAM user** et saisissez l'identifiant du compte qui vous a été donné.

Au premier passage, AWS vous demande sans doute de remplacer le mot de passe provisoire. Choisissez-en un vrai, que vous ne réutilisez nulle part ailleurs, et rangez-le dans votre gestionnaire de mots de passe.

Une fois connecté, regardez en haut à droite. Vous devez y lire votre nom d'utilisateur, suivi du nom ou du numéro du compte. Si c'est le cas, vous êtes au bon endroit.

</TabItem>
</Comptes>

## 2. Faire le tour de la console

La console change régulièrement d'apparence, mais sa barre supérieure reste organisée de la même façon depuis des années. C'est elle que vous utiliserez le plus.

<Schema svg={consoleBarre} num="TP1" alt="Barre supérieure de la console AWS, avec cinq zones numérotées : 1 le menu des services, 2 la barre de recherche (raccourci Alt+S), 3 l'icône de CloudShell, 4 le sélecteur de région affichant Europe (Paris), 5 le menu du compte affichant l'utilisateur et le numéro du compte.">
  La barre supérieure de la console. En pratique, vous passerez surtout par la recherche (2) et vous garderez un œil sur la région (4).
</Schema>

Commencez par la région.

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Votre console n'a pas de sélecteur de région (4) : elle travaille toujours dans la région de votre projet, celle que vous avez notée dans AWS Settings. Il n'y a rien à régler, et aucune ressource ne peut atterrir par erreur dans une autre région.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Cliquez sur le sélecteur (4) et choisissez **Europe (Paris) eu-west-3**. Pour ne plus avoir à le refaire à chaque connexion, ouvrez le menu du compte (5), puis <Chemin>Settings › Localization and default Region › Edit</Chemin>, et fixez **Default Region** sur Paris.

</TabItem>
</Comptes>

Ensuite, ouvrez un service par la recherche : tapez <kbd>Alt</kbd>+<kbd>S</kbd>, puis `ec2`, et validez. Vous arrivez sur le tableau de bord d'EC2. Survolez son nom dans les résultats de recherche : une petite étoile permet de l'ajouter aux favoris, qui s'affichent ensuite dans la barre. Faites-le pour **EC2**, **S3**, **IAM** et **CloudShell**, les quatre services que vous ouvrirez le plus souvent.

Pour finir, ouvrez IAM, puis EC2, et comparez leurs adresses dans la barre du navigateur. Celle d'EC2 contient le nom de votre région (`eu-north-1.console.aws.amazon.com` ou `eu-west-3.console.aws.amazon.com`) ; celle d'IAM n'en contient aucune. Sur le compte de l'enseignant, le sélecteur de région affiche aussi « Global » dans IAM. C'est la différence entre service global et service régional dont on a parlé en cours.

## 3. Vos premières requêtes depuis CloudShell

Cliquez sur l'icône de CloudShell (3). Un terminal Linux s'ouvre en bas de la fenêtre après quelques secondes. Il est déjà authentifié avec votre identité : pas de clé à configurer, pas d'installation.

:::tip[Si CloudShell refuse de s'ouvrir]
Sur un compte personnel tout neuf, CloudShell répond parfois « Impossible de créer l'environnement. La vérification de votre compte est en cours », et AWS prévient que cette vérification peut prendre jusqu'à deux jours. En attendant, utilisez la CLI sur votre ordinateur : elle envoie les mêmes requêtes, et la commande `aws login` l'authentifie par votre navigateur, sans clé d'accès[^aws-login].

1. Installez la CLI AWS en version 2.32.0 ou plus, en suivant [la page d'installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) pour votre système. Vérifiez avec `aws --version`. Sous Linux, passez par le script `sudo ./aws/install` de l'archive : copier seul le fichier `aws` dans `/usr/local/bin` donne une erreur `Failed to load Python shared library`.
2. Connectez-vous avec `aws login --profile cours`. À la question de la région, donnez celle de votre projet (`eu-north-1` pour la plupart d'entre vous). Le navigateur s'ouvre : choisissez votre projet, puis revenez au terminal.
3. Pour que les commandes suivantes utilisent ce profil sans le répéter, tapez `export AWS_PROFILE=cours` sous Linux et macOS, ou `$env:AWS_PROFILE="cours"` dans PowerShell, à chaque nouveau terminal.

Tapez ensuite dans votre terminal les commandes que les énoncés présentent sous le titre **CloudShell**. Deux différences : la variable `$AWS_REGION` y est vide, et `aws configure get region` affiche la région du profil ; la session dure 12 heures, après quoi on relance `aws login --profile cours`. En fin de séance, `aws logout --profile cours` efface les identifiants temporaires de votre poste. Dès que la vérification du compte est terminée, revenez à CloudShell.
:::

Première question à poser à AWS : qui suis-je ?

```bash title="CloudShell"
aws sts get-caller-identity
```

La réponse est un petit document JSON. `Account` est le numéro du compte, sur douze chiffres. `Arn` est l'identifiant complet de l'identité qui a fait la requête.

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Il commence par `arn:aws:sts::` et contient `assumed-role`. Vous n'êtes pas un utilisateur IAM : AWS a authentifié votre identité (Builder ID, Google, GitHub), puis vous a donné une session sur un rôle d'administrateur du projet[^acces-projet]. Le numéro de compte est celui que vous avez noté dans AWS Settings.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Il a la forme `arn:aws:iam::123456789012:user/student12`. Comparez avec ce qu'affiche le menu du compte (5) : c'est la même identité, vue de deux façons.

</TabItem>
</Comptes>

Demandez maintenant la liste des zones de disponibilité :

```bash title="CloudShell"
aws ec2 describe-availability-zones --query "AvailabilityZones[].ZoneName" --output text
```

Vous devez obtenir trois zones dont le nom prolonge celui de votre région : `eu-north-1a`, `eu-north-1b` et `eu-north-1c` à Stockholm, `eu-west-3a`, `eu-west-3b` et `eu-west-3c` à Paris. Vous n'avez pourtant pas précisé de région. Tapez `echo $AWS_REGION` pour comprendre comment CloudShell l'a devinée.

Posez la même question pour une autre région, en le précisant cette fois :

```bash title="CloudShell"
aws ec2 describe-availability-zones --region us-east-1 --query "AvailabilityZones[].ZoneName" --output text
```

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

La commande est refusée. Lisez le message en entier : il parle d'un refus explicite par une *service control policy*. Ce n'est pas une stratégie IAM de votre compte, mais une règle posée par AWS au-dessus de lui, sur l'organisation qui contient votre projet, et qui interdit les autres régions[^scp-projets]. Nous verrons au module 2 qu'un refus explicite l'emporte sur toutes les autorisations, même celles d'un administrateur.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

La Virginie du Nord en compte davantage. Combien ?

</TabItem>
</Comptes>

Dernière commande, pour compter les régions activées dans le compte :

```bash title="CloudShell"
aws ec2 describe-regions --query "Regions[].RegionName" --output text | wc -w
```

Une question encore : comment CloudShell signe-t-il vos requêtes, puisque vous n'avez saisi aucune clé ? Demandez-le à la CLI elle-même :

```bash title="CloudShell"
aws configure list
```

La colonne `Type` indique d'où viennent la région et les identifiants. Pour ces derniers, vous lisez `container-role` : CloudShell a obtenu pour vous des identifiants temporaires, liés à votre session dans la console, et les a placés dans le conteneur qui fait tourner votre terminal. Aucune clé permanente n'a été créée. Nous retrouverons ce mécanisme, sous une autre forme, avec les rôles des instances.

:::note
Si l'une de ces commandes répond `AccessDenied` ou `UnauthorizedOperation`, ne cherchez pas l'erreur de frappe : vos droits sur le compte ne couvrent pas cette action. Notez le message et signalez-le. C'est exactement le mécanisme que nous étudierons au module 2.
:::

## 4. Combien coûte une machine ?

Vous allez maintenant ouvrir l'assistant de création d'instance, **sans créer d'instance**, simplement pour y lire des prix.

1. Dans EC2, ouvrez <Chemin>Instances › Launch instances</Chemin>.
2. Descendez jusqu'à la rubrique **Instance type**. Ouvrez la liste déroulante et cherchez `t3.micro`. Sous son nom, la console affiche ses caractéristiques (nombre de processeurs virtuels, mémoire) et son prix à la demande pour Linux, par heure. Notez-le.
3. Faites de même pour `t3.large` et `m7i.4xlarge`, deux machines plus grosses.
4. Cliquez sur **Cancel** en bas de la page. Ne cliquez surtout pas sur *Launch instance*.

Le prix dépend de la région. Pour comparer avec la Virginie du Nord, la région la moins chère pour la plupart des services :

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Ouvrez le calculateur de prix d'AWS, [calculator.aws](https://calculator.aws/), qui se consulte sans compte. Ajoutez un service **Amazon EC2**, choisissez la région **US East (N. Virginia)** et le type `t3.micro`, et relevez le prix horaire à la demande. Recommencez avec votre région pour vérifier que vous retrouvez le prix lu dans l'assistant.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Rouvrez l'assistant, changez la région dans le sélecteur (4) pour **US East (N. Virginia)** et relevez de nouveau le prix de la `t3.micro`. Revenez sur **Paris** et cliquez sur **Cancel**.

</TabItem>
</Comptes>

La même information, ou presque, s'obtient en ligne de commande. Revenez dans CloudShell :

```bash title="CloudShell"
aws ec2 describe-instance-types --instance-types t3.micro t3.large m7i.4xlarge \
  --query "InstanceTypes[].[InstanceType, VCpuInfo.DefaultVCpus, MemoryInfo.SizeInMiB]" --output table
aws ec2 describe-instance-types --query "length(InstanceTypes)"
```

La première commande affiche le nombre de processeurs virtuels et la mémoire, en Mio, des trois types. Le prix n'y figure pas : il relève d'un autre service, l'API Price List. La seconde compte les types d'instances proposés dans votre région. Comparez ce nombre avec celui donné en cours pour l'ensemble d'AWS : toutes les régions ne proposent pas tous les types, et les plus récents arrivent d'abord dans les grandes régions américaines.

Avec ces chiffres, calculez ce que coûterait chacune des trois machines si on l'oubliait allumée pendant un mois (comptez 730 heures).

:::cout
Faites ce calcul sérieusement : c'est le réflexe à avoir avant de lancer quoi que ce soit. L'écart entre la plus petite et la plus grosse de ces trois machines vous donnera une idée de ce qu'un mauvais choix dans une liste déroulante peut coûter.
:::

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Sur un compte personnel, ce coût se paie en crédits. Ouvrez la page d'accueil de **Billing and Cost Management** : elle affiche le solde de vos crédits et la date de fin de votre plan gratuit[^plan-gratuit]. Rien ne vous sera facturé, mais quand les crédits sont épuisés, le compte se ferme, et vous perdez l'accès à vos ressources. Une `m7i.4xlarge` oubliée une semaine suffirait à les consommer. Revenez sur cette page à la fin de chaque TP.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Sur le compte du cours, c'est l'enseignant qui paie, pour tout le groupe : une machine oubliée par un étudiant se retrouve sur la facture de tous.

</TabItem>
</Comptes>

## 5. Savoir retrouver ce qui tourne

<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Votre compte ne travaille que dans sa région, si bien qu'aucune ressource ne peut se cacher ailleurs. Il en reste beaucoup à surveiller : instances, volumes, adresses IP, buckets. La page <Chemin>EC2 › Dashboard</Chemin> compte, en haut, les instances, les volumes et les Security Groups de votre région ; vous y verrez déjà un VPC et un Security Group, ceux qu'AWS crée par défaut, dont nous reparlerons au module 2. C'est elle que vous consulterez à la fin de chaque TP, avec la page des crédits, pour vérifier que vous n'avez rien oublié.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

La région explique la plupart des « ma ressource a disparu » : une instance lancée par erreur en Virginie du Nord n'apparaît pas quand la console est réglée sur Paris, mais elle tourne, et elle coûte. EC2 propose une page qui regarde toutes les régions à la fois.

Dans EC2, ouvrez <Chemin>EC2 › Global View</Chemin> (le lien se trouve aussi en haut du tableau de bord). La page compte, région par région, les instances, les VPC, les Security Groups et les volumes du compte. Vous y verrez sans doute un VPC et un Security Group par région : ce sont les éléments par défaut qu'AWS crée dans chaque région, nous en reparlerons au module 2. Ajoutez cette page à vos favoris : c'est elle que vous consulterez à la fin de chaque TP pour vérifier que vous n'avez rien oublié.

</TabItem>
</Comptes>

Ouvrez enfin le tableau de bord de santé, en cherchant **Health** dans la barre de recherche. Il signale les incidents en cours chez AWS et les opérations de maintenance prévues sur les ressources du compte. Quand un service se comporte bizarrement, c'est le premier endroit où regarder, avant de soupçonner votre propre configuration.

## Avant de partir

Vous n'avez rien créé, il n'y a donc rien à nettoyer. Profitez-en, ce sera la seule fois du cours.

Vérifiez simplement que vous savez répondre à ces quatre questions ; nous les reprendrons au début du module 2.

1. Quel est l'ARN de votre identité, et que signifie chacune de ses parties ?
2. Pourquoi la page d'IAM n'affiche-t-elle pas de région, alors que celle d'EC2 en affiche une ?
3. Combien coûterait une `t3.micro` oubliée un mois dans votre région ? Et en Virginie du Nord ?
4. D'où viennent les identifiants qu'utilise la CLI dans CloudShell, et combien de temps restent-ils valables, à votre avis ?

[^inscription]: AWS, « AWS reimagines the getting started experience », *AWS News Blog*, 16 septembre 2026, [aws.amazon.com/blogs/aws/aws-reimagines-the-getting-started-experience](https://aws.amazon.com/blogs/aws/aws-reimagines-the-getting-started-experience).
[^deploiement-progressif]: AWS, « Compare sign-up options », *AWS Account Management Reference Guide*, qui précise que la nouvelle inscription est ouverte à un nombre limité de clients, [docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html](https://docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html).
[^region-projet]: AWS, « AWS Regions for your projects », *AWS Account Management Reference Guide*, [docs.aws.amazon.com/accounts/latest/reference/project-regions.html](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html).
[^acces-projet]: AWS, « Compare access management », dans « Compare sign-up options », *AWS Account Management Reference Guide*, [docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html](https://docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html).
[^scp-projets]: AWS, « Managed policies for your organization », *AWS Account Management Reference Guide*, [docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html](https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html).
[^plan-gratuit]: AWS, « Choosing a plan », *AWS Billing User Guide*, [docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).
[^aws-login]: AWS, « Login for AWS local development using console credentials », *AWS Command Line Interface User Guide*, [docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html) ; pour un projet de la nouvelle inscription, « Connect an AI coding tool », *AWS Account Management Reference Guide*, [docs.aws.amazon.com/accounts/latest/reference/connect-ai-coding-tool.html](https://docs.aws.amazon.com/accounts/latest/reference/connect-ai-coding-tool.html).
