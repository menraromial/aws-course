---
title: "TP 1 : Prendre ses marques"
sidebar_label: "Le TP"
description: "Connexion au compte, réglages de la console, premiers appels depuis CloudShell, prix et caractéristiques des instances, vue globale du compte."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import consoleBarre from '@site/src/figures/console-barre.svg';
import Chemin from '@site/src/components/Chemin';

<Seance items={['Module 1', 'Travaux pratiques']} />

Ce premier TP sert à se sentir chez soi dans la console : se connecter, régler deux ou trois choses qui vous feront gagner du temps pendant tout le cours, envoyer vos premières requêtes depuis un terminal et regarder combien coûte une machine avant d'en lancer une. Ce TP ne crée aucune ressource.

Pour commencer, vous avez besoin de ce qui vous a été remis : l'adresse de connexion du compte AWS du cours, votre nom d'utilisateur et un mot de passe provisoire.

## 1. Se connecter

Ouvrez l'adresse de connexion. Elle ressemble à `https://<compte>.signin.aws.amazon.com/console`, et la page demande directement un nom d'utilisateur et un mot de passe. Si vous arrivez sur une page qui vous propose de choisir entre *Root user* et *IAM user*, choisissez **IAM user** et saisissez l'identifiant du compte qui vous a été donné.

Au premier passage, AWS vous demande sans doute de remplacer le mot de passe provisoire. Choisissez-en un vrai, que vous ne réutilisez nulle part ailleurs, et rangez-le dans votre gestionnaire de mots de passe.

Une fois connecté, regardez en haut à droite. Vous devez y lire votre nom d'utilisateur, suivi du nom ou du numéro du compte. Si c'est le cas, vous êtes au bon endroit.

## 2. Faire le tour de la console

La console change régulièrement d'apparence, mais sa barre supérieure reste organisée de la même façon depuis des années. C'est elle que vous utiliserez le plus.

<Schema svg={consoleBarre} num="TP1" alt="Barre supérieure de la console AWS, avec cinq zones numérotées : 1 le menu des services, 2 la barre de recherche (raccourci Alt+S), 3 l'icône de CloudShell, 4 le sélecteur de région affichant Europe (Paris), 5 le menu du compte affichant l'utilisateur et le numéro du compte.">
  La barre supérieure de la console. En pratique, vous passerez surtout par la recherche (2) et vous garderez un œil sur la région (4).
</Schema>

Commencez par la région. Cliquez sur le sélecteur (4) et choisissez **Europe (Paris) eu-west-3**. Pour ne plus avoir à le refaire à chaque connexion, ouvrez le menu du compte (5), puis <Chemin>Settings › Localization and default Region › Edit</Chemin>, et fixez **Default Region** sur Paris.

Ensuite, ouvrez un service par la recherche : tapez <kbd>Alt</kbd>+<kbd>S</kbd>, puis `ec2`, et validez. Vous arrivez sur le tableau de bord d'EC2. Survolez son nom dans les résultats de recherche : une petite étoile permet de l'ajouter aux favoris, qui s'affichent ensuite dans la barre. Faites-le pour **EC2**, **S3**, **IAM** et **CloudShell**, les quatre services que vous ouvrirez le plus souvent.

Pour finir, ouvrez IAM et regardez le sélecteur de région : il affiche « Global ». Revenez sur EC2 : il affiche de nouveau « Europe (Paris) ». C'est la différence entre service global et service régional dont on a parlé en cours.

## 3. Vos premières requêtes depuis CloudShell

Cliquez sur l'icône de CloudShell (3). Un terminal Linux s'ouvre en bas de la fenêtre après quelques secondes. Il est déjà authentifié avec votre identité : pas de clé à configurer, pas d'installation.

Première question à poser à AWS : qui suis-je ?

```bash title="CloudShell"
aws sts get-caller-identity
```

La réponse est un petit document JSON. `Account` est le numéro du compte, sur douze chiffres. `Arn` est l'identifiant complet de votre utilisateur, de la forme `arn:aws:iam::123456789012:user/camille`. Comparez avec ce qu'affiche le menu du compte (5) : c'est la même identité, vue de deux façons.

Demandez maintenant la liste des zones de disponibilité :

```bash title="CloudShell"
aws ec2 describe-availability-zones --query "AvailabilityZones[].ZoneName" --output text
```

Vous devez obtenir `eu-west-3a`, `eu-west-3b` et `eu-west-3c`. Vous n'avez pourtant pas précisé de région. Tapez `echo $AWS_REGION` pour comprendre comment CloudShell l'a devinée.

Posez la même question pour une autre région, en le précisant cette fois :

```bash title="CloudShell"
aws ec2 describe-availability-zones --region us-east-1 --query "AvailabilityZones[].ZoneName" --output text
```

La Virginie du Nord en compte davantage. Combien ?

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
4. Changez la région dans le sélecteur (4) pour **US East (N. Virginia)**. L'assistant se recharge. Relevez de nouveau le prix de la `t3.micro`.
5. Revenez sur **Paris** et cliquez sur **Cancel** en bas de la page. Ne cliquez surtout pas sur *Launch instance*.

La même information, ou presque, s'obtient en ligne de commande. Revenez dans CloudShell :

```bash title="CloudShell"
aws ec2 describe-instance-types --instance-types t3.micro t3.large m7i.4xlarge \
  --query "InstanceTypes[].[InstanceType, VCpuInfo.DefaultVCpus, MemoryInfo.SizeInMiB]" --output table
aws ec2 describe-instance-types --query "length(InstanceTypes)"
```

La première commande affiche le nombre de processeurs virtuels et la mémoire, en Mio, des trois types. Le prix n'y figure pas : il relève d'un autre service, l'API Price List. La seconde compte les types d'instances proposés à Paris. Comparez ce nombre avec celui donné en cours pour l'ensemble d'AWS : toutes les régions ne proposent pas tous les types, et les plus récents arrivent d'abord dans les grandes régions américaines.

Avec ces chiffres, calculez ce que coûterait chacune des trois machines si on l'oubliait allumée pendant un mois (comptez 730 heures).

:::cout
Faites ce calcul sérieusement : c'est le réflexe à avoir avant de lancer quoi que ce soit. L'écart entre la plus petite et la plus grosse de ces trois machines vous donnera une idée de ce qu'un mauvais choix dans une liste déroulante peut coûter.
:::

## 5. Savoir retrouver ce qui tourne

La région explique la plupart des « ma ressource a disparu » : une instance lancée par erreur en Virginie du Nord n'apparaît pas quand la console est réglée sur Paris, mais elle tourne, et elle coûte. EC2 propose une page qui regarde toutes les régions à la fois.

Dans EC2, ouvrez <Chemin>EC2 › Global View</Chemin> (le lien se trouve aussi en haut du tableau de bord). La page compte, région par région, les instances, les VPC, les Security Groups et les volumes du compte. Vous y verrez sans doute un VPC et un Security Group par région : ce sont les éléments par défaut qu'AWS crée dans chaque région, nous en reparlerons au module 2. Ajoutez cette page à vos favoris : c'est elle que vous consulterez à la fin de chaque TP pour vérifier que vous n'avez rien oublié.

Ouvrez enfin le tableau de bord de santé, en cherchant **Health** dans la barre de recherche. Il signale les incidents en cours chez AWS et les opérations de maintenance prévues sur les ressources du compte. Quand un service se comporte bizarrement, c'est le premier endroit où regarder, avant de soupçonner votre propre configuration.

## Avant de partir

Vous n'avez rien créé, il n'y a donc rien à nettoyer. Profitez-en, ce sera la seule fois du cours.

Vérifiez simplement que vous savez répondre à ces quatre questions ; nous les reprendrons au début du module 2.

1. Quel est l'ARN de votre utilisateur, et que signifie chacune de ses parties ?
2. Pourquoi la page d'IAM n'affiche-t-elle pas de région, alors que celle d'EC2 en affiche une ?
3. Combien coûterait une `t3.micro` oubliée un mois à Paris ? Et en Virginie du Nord ?
4. D'où viennent les identifiants qu'utilise la CLI dans CloudShell, et combien de temps restent-ils valables, à votre avis ?
