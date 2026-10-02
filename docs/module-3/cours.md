---
title: "Calcul : Amazon EC2"
sidebar_label: "Cours"
description: "Instances EC2 : nomenclature, familles, instances à crédits, modes d'achat, AMI, stockage, paires de clés, connexion, cycle de vie, adresses IP, user data, service de métadonnées, tags, supervision, coûts."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import typeInstance from '@site/src/figures/type-instance.svg';
import creditsCpu from '@site/src/figures/credits-cpu.svg';
import amiEbs from '@site/src/figures/ami-instance-ebs.svg';
import sshCles from '@site/src/figures/ssh-cles.svg';
import cycleVie from '@site/src/figures/cycle-vie.svg';
import imds from '@site/src/figures/imds.svg';

<Seance items={['Module 3', 'Cours']} />

EC2 est le service qui fournit des machines virtuelles. C'est le plus ancien service de calcul d'AWS et celui sur lequel tournera l'application du projet final. Avant de lancer une instance, l'assistant de la console demande une dizaine de choix : type d'instance, image, paire de clés, réseau, stockage. Ce module explique chacun d'eux et leurs conséquences sur le prix, la sécurité et la conservation des données.

## Amazon EC2 : Elastic Compute Cloud

EC2 loue des machines virtuelles, appelées **instances**, à la demande. C'est un service de type IaaS : AWS fournit la machine, le client installe et administre tout ce qui tourne dessus. Ouvert en 2006 avec un seul type de machine, le service propose aujourd'hui plus de 1 200 types d'instances dans 39 régions[^ec2-20] : machines d'usage général, optimisées pour le calcul, pour la mémoire ou pour le stockage, machines à processeurs graphiques.

Une instance démarre en quelques dizaines de secondes à partir d'une image (une AMI). Elle peut tourner sous Linux, Windows ou macOS, sur des processeurs Intel, AMD ou AWS Graviton (architecture Arm). Les instances Linux sont facturées à la seconde, avec un minimum de 60 secondes.

## Les caractéristiques d'une instance

| Ressource | Ce qu'elle désigne |
|---|---|
| Calcul | nombre de processeurs virtuels (vCPU), génération et fabricant du processeur |
| Mémoire | de 0,5 Gio pour une `t3.nano` à plusieurs Tio pour les plus grosses instances |
| Stockage | volumes EBS (disques réseau) et, selon le type, disques locaux (*instance store*) |
| Réseau | bande passante, de quelques Gbit/s à plusieurs centaines |
| Emplacement | une région, une zone de disponibilité, un sous-réseau |

## La nomenclature des types d'instances

Un nom de type d'instance se lit comme une fiche technique abrégée[^noms].

<Schema svg={typeInstance} num="3.1" alt="Le nom m7i.large décomposé : m est la série (usage général), 7 la génération, i l'option (processeur Intel), large la taille. Trois tableaux listent les séries courantes, les options fréquentes et les tailles de la famille m7i.">
  Le nom d'un type d'instance : série, génération, options, taille.
</Schema>

La **série** indique l'usage : `m` pour l'usage général, `c` pour le calcul, `r` pour la mémoire. La **génération** progresse avec les processeurs ; à taille égale, une génération récente est généralement plus rapide et souvent un peu moins chère. Les **options** précisent le processeur (`a` pour AMD, `g` pour Graviton, `i` pour Intel) ou une particularité (`d` pour des disques locaux, `n` pour un réseau renforcé). La **taille**, enfin, fixe les vCPU et la mémoire ; dans une même famille, chaque taille double les ressources et le prix de la précédente.

## Les familles d'instances

| Exemples | Famille | Usages |
|---|---|---|
| `t3`, `t4g` | performances extensibles (crédits CPU) | petits sites, environnements de test |
| `m7i`, `m8g` | usage général | serveurs d'applications, bases de taille moyenne |
| `c7i`, `c8g` | optimisée pour le calcul | calcul intensif, encodage vidéo |
| `r7i`, `r8g` | optimisée pour la mémoire | bases de données, caches en mémoire |
| `i4i`, `d3` | optimisée pour le stockage | bases NoSQL, entrepôts de données |
| `g6`, `p5` | accélérée par GPU | apprentissage automatique, rendu 3D |
| `inf2`, `trn2` | puces AWS Inferentia et Trainium | inférence et entraînement de modèles |

On choisit rarement le bon type du premier coup. La démarche habituelle consiste à partir d'une taille modeste, à mesurer l'utilisation du processeur et de la mémoire, puis à ajuster. Changer de type demande d'arrêter l'instance, de modifier son type et de la redémarrer : se tromper de dimensionnement coûte un redémarrage, pas un achat de serveur.

## Les instances à performances extensibles

Les instances de la série `t` partent d'un constat : la plupart des petits serveurs passent leur temps à attendre. Une `t3.micro` a droit en permanence à une **ligne de base** de 10 % de chacun de ses deux processeurs. Tant qu'elle reste en dessous, elle accumule des **crédits CPU**, à raison de 12 par heure ; quand une charge arrive, elle les dépense pour monter jusqu'à 100 %[^credits].

<Schema svg={creditsCpu} num="3.2" alt="Utilisation du processeur d'une t3.micro au fil du temps, avec la ligne de base à 10 %. Pendant les périodes calmes, le solde de crédits monte ; pendant un pic, il descend ; en pleine charge durable, les crédits s'épuisent et, en mode unlimited, le surplus est facturé.">
  Une instance à crédits accumule pendant les périodes calmes ce qu'elle dépense pendant les pics.
</Schema>

Quand les crédits sont épuisés, deux comportements sont possibles. En mode `standard`, l'instance est ramenée à sa ligne de base et devient lente. En mode `unlimited`, qui est le mode par défaut des `t3`, elle continue à pleine vitesse et le surplus est facturé. Une instance dont le processeur reste bloqué à 100 % (boucle infinie, programme de minage installé par un intrus) peut ainsi coûter bien plus que prévu ; dans les TP, on choisit le mode `standard`.

## Les modes d'achat

| Mode | Principe | Remise maximale |
|---|---|---|
| À la demande (*On-Demand*) | à la seconde, sans engagement | aucune |
| Savings Plans | engagement sur une dépense horaire pendant 1 ou 3 ans | jusqu'à 72 % |
| Instances réservées | engagement sur un type d'instance pendant 1 ou 3 ans | jusqu'à 72 % |
| Instances Spot | capacité inutilisée d'AWS, reprise avec un préavis de 2 minutes | jusqu'à 90 % |
| Hôtes dédiés | serveur physique réservé, pour des raisons de licence ou de conformité | |

Les TP utilisent le mode à la demande, le plus souple et le plus cher. Les Savings Plans conviennent aux serveurs qui tournent en permanence ; les instances Spot aux travaux que l'on peut interrompre et reprendre, comme des calculs par lots[^prix].

## Les AMI

Une instance démarre toujours à partir d'une **AMI** (*Amazon Machine Image*) : un modèle qui contient le système d'exploitation, sa configuration et éventuellement des logiciels préinstallés. Une AMI est propre à une région (son identifiant, de la forme `ami-0123…`, n'est pas le même à Paris et à Francfort) et à une architecture (`x86_64` ou `arm64`). Elle peut venir d'AWS, de l'AWS Marketplace, de la communauté, ou être fabriquée par le client avec EC2 Image Builder, Packer, ou à partir d'une instance existante.

Les TP utilisent **Amazon Linux 2023**, la distribution maintenue par AWS : proche de Fedora, administrée avec `dnf`, utilisateur par défaut `ec2-user`, CLI `aws` déjà installée[^al2023]. Son prédécesseur, Amazon Linux 2, n'est plus maintenu depuis le 30 juin 2026[^al2]. Une AMI de la Marketplace est une dépendance externe comme une autre : il faut vérifier qui la publie avant de s'en servir.

<Schema svg={amiEbs} num="3.3" alt="Une AMI Amazon Linux 2023 sert à lancer trois instances dans trois zones ; chacune a son volume EBS racine. Le volume de l'instance 2 est sauvegardé en instantané, à partir duquel on peut créer une nouvelle AMI.">
  Une AMI peut lancer autant d'instances qu'on veut, chacune avec son disque ; un instantané de disque peut devenir une nouvelle AMI.
</Schema>

## Le stockage d'une instance

| | Volume EBS | Instance store |
|---|---|---|
| Nature | disque réseau | disque physique du serveur hôte |
| Persistance | survit à l'arrêt de l'instance | perdu à l'arrêt ou à la résiliation |
| Instantané | oui, stocké dans S3 | non |
| Usage | disque système, données | cache, fichiers temporaires |

Le disque système d'une instance est presque toujours un volume EBS de type `gp3`. Par défaut, il est supprimé en même temps que l'instance lors de sa résiliation (option *DeleteOnTermination*). Les disques locaux (*instance store*), présents sur les types dont le nom comporte un `d`, sont très rapides mais éphémères.

## Les paires de clés et la connexion

Une instance Linux s'administre en SSH, et AWS impose l'authentification par paire de clés[^cles]. Lors de la création de la paire (de type RSA ou ED25519), EC2 garde la clé publique et remet la clé privée, sous forme d'un fichier `.pem`, **une seule fois** : AWS ne la conserve pas et ne pourra pas la renvoyer.

<Schema svg={sshCles} num="3.4" alt="Diagramme de séquence entre votre ordinateur, le service EC2 et l'instance : EC2 génère la paire et envoie la clé privée une seule fois ; au lancement, la clé publique est déposée dans authorized_keys ; à la connexion, l'instance envoie un défi, le client le signe avec la clé privée, l'instance vérifie avec la clé publique.">
  L'authentification par clé : la clé privée ne circule jamais sur le réseau, seule une signature le fait.
</Schema>

Au premier démarrage, le programme `cloud-init` écrit la clé publique dans le fichier `~/.ssh/authorized_keys` de l'utilisateur `ec2-user`. À la connexion, le serveur SSH envoie un défi que le client signe avec la clé privée, et vérifie la signature avec la clé publique. Le client SSH refuse une clé privée lisible par d'autres utilisateurs du poste : il faut restreindre ses droits (`chmod 400`).

| Méthode | Prérequis | Remarque |
|---|---|---|
| SSH | clé privée, port 22 ouvert à votre adresse | la méthode de référence, utilisée dans les TP |
| EC2 Instance Connect | port 22 ouvert aux adresses d'AWS | une clé temporaire est poussée par l'API |
| Session Manager | rôle avec la stratégie `AmazonSSMManagedInstanceCore` | aucun port entrant à ouvrir |
| EC2 Serial Console | droits IAM dédiés | dépannage d'une instance qui ne démarre plus |

## Le cycle de vie d'une instance

<Schema svg={cycleVie} num="3.5" alt="Diagramme d'états : Launch mène à pending puis running ; Stop mène à stopping puis stopped ; Start ramène à pending avec une nouvelle IPv4 publique ; Terminate mène à shutting-down puis terminated. Un tableau indique ce qui est facturé dans chaque état.">
  Le cycle de vie d'une instance et ce qui est facturé dans chaque état.
</Schema>

**Arrêter** une instance (*Stop*) revient à éteindre un ordinateur : le calcul n'est plus facturé, le disque EBS garde son contenu et reste facturé. **Résilier** (*Terminate*) revient à s'en débarrasser : l'instance disparaît définitivement, avec son volume racine. Il n'y a pas d'annulation possible.

## Les adresses IP

- L'**adresse privée** appartient au sous-réseau et reste la même jusqu'à la résiliation.
- L'**adresse IPv4 publique** est attribuée au démarrage et **change** après un arrêt suivi d'un démarrage (un simple redémarrage la conserve).
- Une **Elastic IP** est une adresse publique fixe, réservée dans le compte, que l'on attache à une instance.
- Les adresses **IPv6** sont publiques et ne sont pas facturées.

Toute adresse IPv4 publique est facturée, y compris une Elastic IP réservée mais non attachée. Autre particularité : l'instance ne connaît que son adresse privée. C'est la passerelle Internet du VPC qui traduit, à l'entrée et à la sortie, l'adresse publique en adresse privée.

## Le user data

Le champ **user data** de l'assistant de lancement contient un script que `cloud-init` exécute, en tant que `root`, au premier démarrage de l'instance[^userdata]. Il sert à installer et configurer l'instance sans intervention :

```bash title="User data"
#!/bin/bash
dnf install -y nginx
systemctl enable --now nginx
```

Une instance ainsi configurée se reconstruit à l'identique en une minute : quand elle pose problème, on la remplace au lieu de la réparer. Le journal d'exécution du script se trouve dans `/var/log/cloud-init-output.log`. Le user data est lisible par tout programme de l'instance via le service de métadonnées : on n'y met jamais de secret.

## Le service de métadonnées (IMDS)

Depuis l'intérieur d'une instance, l'adresse `169.254.169.254` donne accès au **service de métadonnées** : identifiant de l'instance, type, zone, adresses, et surtout identifiants temporaires du rôle IAM associé[^imds]. C'est là que `boto3` et la commande `aws` vont chercher ces identifiants.

C'est aussi par ce service que s'était produite la fuite de données de Capital One en 2019 : une faille dans une application avait permis à une attaquante de lui faire relayer une requête vers le service de métadonnées et d'en obtenir les identifiants du rôle[^capitalone]. Ce type de faille s'appelle SSRF (*Server-Side Request Forgery*).

<Schema svg={imds} num="3.6" alt="Deux panneaux. Avec IMDSv1, une application vulnérable relaie un GET de l'attaquant vers le service de métadonnées, et les identifiants du rôle repartent chez l'attaquant. Avec IMDSv2, le même GET est refusé, car il faut d'abord un jeton obtenu par PUT, puis l'envoyer dans un en-tête.">
  La même faille face aux deux versions du service de métadonnées.
</Schema>

Depuis novembre 2019, la version **IMDSv2** exige d'ouvrir une session : on obtient d'abord un jeton par une requête `PUT`, puis on le joint en en-tête à chaque requête. Les failles SSRF permettent rarement d'envoyer un `PUT` avec des en-têtes choisis, et le service refuse en plus les requêtes passées par un mandataire[^imdsv2]. Sur Amazon Linux 2023, IMDSv2 est exigé par défaut.

```bash title="Interroger le service de métadonnées (IMDSv2)"
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
          -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
     http://169.254.169.254/latest/meta-data/placement/availability-zone
```

## Les tags

Presque toutes les ressources AWS acceptent des **tags**, des paires clé-valeur comme `Name=web-camille` ou `Proprietaire=camille`. Ils servent à retrouver et regrouper des ressources, à répartir les coûts par projet ou par équipe, et à contrôler les accès par attributs (conditions `aws:ResourceTag` dans les stratégies IAM). On définit une convention dès le début d'un projet, et on n'y met jamais de données sensibles.

## La supervision

Chaque instance fait l'objet de deux **contrôles d'état** (*status checks*) : l'un vérifie le serveur hôte, l'autre le système d'exploitation de l'instance. **CloudWatch** collecte les métriques de processeur, de réseau et de disque toutes les cinq minutes (toutes les minutes en option). La mémoire et l'espace disque ne sont pas visibles de l'extérieur : il faut installer l'agent CloudWatch. Des **alarmes** peuvent envoyer une notification ou déclencher une action (arrêt, redémarrage, mise à l'échelle) quand un seuil est franchi.

## Un exemple de coût

Une `t3.micro` à Paris, avec un disque `gp3` de 8 Go et une adresse IPv4 publique, oubliée allumée :

| Poste | Une semaine | Un mois |
|---|---|---|
| Instance (environ 0,012 $ par heure) | 2,02 $ | 8,76 $ |
| Adresse IPv4 publique (0,005 $ par heure) | 0,84 $ | 3,65 $ |
| Disque gp3 de 8 Go (environ 0,09 $ par Go et par mois) | 0,17 $ | 0,72 $ |
| **Total** | **environ 3 $** | **environ 13 $** |

Ces montants sont des ordres de grandeur ; la page de tarification d'EC2 donne les valeurs exactes. Ils sont modestes pour une instance, mais se multiplient vite à l'échelle d'une promotion ou d'une entreprise. Le TP 3 se termine donc, comme les autres, par la suppression de tout ce qui a été créé.

[^ec2-20]: J. Barr, « Happy 20th Birthday, Amazon EC2 », *AWS News Blog*, 2026, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/aws/happy-20th-birthday-amazon-ec2/).
[^noms]: AWS, *Amazon EC2 instance type naming conventions*, [docs.aws.amazon.com](https://docs.aws.amazon.com/ec2/latest/instancetypes/instance-type-names.html).
[^credits]: AWS, *Burstable performance instances*, Amazon EC2 User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances.html).
[^prix]: AWS, *Amazon EC2 pricing*, [aws.amazon.com/ec2/pricing](https://aws.amazon.com/ec2/pricing/).
[^al2023]: AWS, *What is Amazon Linux 2023?*, [docs.aws.amazon.com](https://docs.aws.amazon.com/linux/al2023/ug/what-is-amazon-linux.html).
[^al2]: AWS, *Amazon Linux 2 FAQs*, [aws.amazon.com](https://aws.amazon.com/amazon-linux-2/faqs/).
[^cles]: AWS, *Amazon EC2 key pairs and Amazon EC2 instances*, Amazon EC2 User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).
[^userdata]: AWS, *Run commands when you launch an EC2 instance with user data input*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html).
[^imds]: AWS, *Use instance metadata to manage your EC2 instance*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html).
[^capitalone]: B. Krebs, « What We Can Learn from the Capital One Hack », *Krebs on Security*, 2019, [krebsonsecurity.com](https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/).
[^imdsv2]: C. MacCárthaigh, « Add defense in depth against open firewalls, reverse proxies, and SSRF vulnerabilities with enhancements to the EC2 Instance Metadata Service », *AWS Security Blog*, 2019, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/security/defense-in-depth-open-firewalls-reverse-proxies-ssrf-vulnerabilities-ec2-instance-metadata-service/).
