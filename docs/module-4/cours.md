---
title: "Stockage, bases de données et messages"
sidebar_label: "Cours"
description: "S3 (objets, classes, durabilité, fonctionnalités, contrôle d'accès, URL présignées, tarification), EBS et EFS, bases relationnelles et NoSQL, RDS, DynamoDB, files de messages SQS."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import stockageTypes from '@site/src/figures/stockage-types.svg';
import s3Modele from '@site/src/figures/s3-modele.svg';
import s3Acces from '@site/src/figures/s3-acces.svg';
import galerie from '@site/src/figures/galerie-evoluee.svg';
import sqsVisibilite from '@site/src/figures/sqs-visibilite.svg';

<Seance items={['Module 4', 'Cours']} />

Une application ne se résume pas à une machine qui calcule : il faut ranger ses fichiers, interroger ses données, faire communiquer ses composants. Ce module présente les trois formes de stockage d'AWS, en s'attardant sur S3, puis les bases de données managées et le service de files de messages SQS.

## Trois types de stockage

<Schema svg={stockageTypes} num="4.1" alt="Trois panneaux. En bloc (EBS) : un volume attaché à une seule instance. En fichiers (EFS) : un système de fichiers partagé par deux instances. En objets (S3) : une instance, un ordinateur et une fonction Lambda accèdent à un bucket par HTTPS.">
  Trois façons de stocker des données sur AWS.
</Schema>

Le stockage **en bloc** (EBS) se comporte comme un disque dur : l'instance y crée un système de fichiers et elle seule s'en sert. Le stockage **en fichiers** (EFS) est un dossier partagé, monté simultanément par plusieurs instances. Le stockage **en objets** (S3) fonctionne autrement : on n'y monte rien, on y dépose un fichier entier par une requête HTTPS et on le relit de la même façon, depuis n'importe quel programme autorisé, où qu'il soit.

Le choix dépend de l'usage. Les fichiers que les utilisateurs déposent dans une application ne doivent pas rester sur le disque de l'instance : si elle disparaît, ou si l'on en lance une seconde, ils seraient perdus ou invisibles. On les range donc dans S3.

## Amazon S3

S3 (*Simple Storage Service*) est le service de stockage objet d'AWS, ouvert en 2006. Il stocke aujourd'hui plus de 500 000 milliards d'objets et traite plus de 200 millions de requêtes par seconde[^s3-20].

Ses notions de base sont les suivantes :

- un **objet** est un fichier, avec sa clé, ses données et ses métadonnées ; il pèse de 0 octet à 50 To[^faq] ;
- un envoi en une seule requête est limité à 5 Go ; au-delà, on téléverse l'objet en plusieurs parties, ce que la CLI et les SDK font automatiquement ;
- un **bucket** est un conteneur d'objets, créé dans une région, où ses données restent ;
- le nom d'un bucket est **unique au monde** (de 3 à 63 caractères, en minuscules) : si quelqu'un a déjà pris un nom, il n'est plus disponible ;
- depuis décembre 2020, S3 garantit une **cohérence forte** : dès qu'une écriture a réussi, toute lecture renvoie la nouvelle version.

## Buckets, clés et préfixes

<Schema svg={s3Modele} num="4.2" alt="À gauche, le bucket galerie-camille-4821 contient une liste plate de clés comme uploads/2026/chat.jpg. Au milieu, la console affiche des dossiers qui ne sont que des préfixes. À droite, un objet se compose d'une clé, de données, de métadonnées et, si le versionnage est activé, d'une version.">
  Ce que contient réellement un bucket, et ce que la console en affiche.
</Schema>

Chaque objet est identifié par sa **clé**, par exemple `uploads/2026/chat.jpg`. Il n'y a pas de dossiers dans S3 : un bucket contient une liste plate de clés, et la console affiche comme des dossiers les morceaux de clé séparés par `/`. Conséquence pratique : « renommer un dossier » revient à copier puis supprimer tous les objets dont la clé commence par ce préfixe. Chaque objet porte aussi des **métadonnées**, dont son type de contenu (`Content-Type: image/jpeg`), qui indique au navigateur comment l'afficher.

## Les classes de stockage

| Classe | Usage |
|---|---|
| S3 Standard | données lues fréquemment (classe par défaut) |
| S3 Intelligent-Tiering | accès imprévisible : S3 déplace automatiquement les objets entre niveaux |
| S3 Standard-IA | données lues rarement, mais disponibles immédiatement |
| S3 One Zone-IA | comme Standard-IA, dans une seule zone de disponibilité |
| S3 Glacier Instant Retrieval | archives consultées environ une fois par trimestre |
| S3 Glacier Flexible Retrieval | archives, récupération en quelques minutes à quelques heures |
| S3 Glacier Deep Archive | archives de longue durée, récupération en 12 à 48 heures |
| S3 Express One Zone | latence très faible, dans une seule zone |

Les classes les moins chères au stockage font payer la récupération des données. Des règles de **cycle de vie** peuvent faire passer automatiquement les objets d'une classe à l'autre en fonction de leur âge, puis les supprimer[^classes].

## Durabilité et disponibilité

S3 Standard est conçu pour une durabilité de 99,999999999 % par an, les « onze neuf », en copiant les données dans plusieurs zones de disponibilité. Concrètement, cela correspond à une probabilité de perte de 10<sup>-11</sup> par objet et par an : sur 10 millions d'objets, on peut s'attendre à en perdre un tous les 10 000 ans environ. L'engagement de disponibilité de S3 Standard est de 99,9 %[^sla-s3].

Cette durabilité protège contre les pannes de disques et de serveurs, pas contre les erreurs humaines : un objet supprimé par erreur est bel et bien supprimé. Pour s'en prémunir, on active le **versionnage** du bucket.

## Les fonctionnalités de S3

- **Versionnage** : chaque écriture conserve la version précédente de l'objet, y compris en cas de suppression.
- **Cycle de vie** : changement de classe ou suppression automatique selon l'âge des objets.
- **Réplication** : copie automatique des objets vers un autre bucket, dans la même région ou une autre.
- **Chiffrement** : tout objet déposé est chiffré par défaut depuis janvier 2023 (SSE-S3) ; on peut utiliser ses propres clés KMS (SSE-KMS)[^chiffrement].
- **Notifications d'événements** : un dépôt ou une suppression peut déclencher un message SQS ou SNS, une fonction Lambda, une règle EventBridge.
- **Hébergement de site statique** : un bucket peut servir directement des pages HTML.
- **Object Lock** : interdiction de modifier ou supprimer un objet pendant une durée donnée.

## Le contrôle d'accès à S3

Trois mécanismes décident de l'accès à un objet :

- les **stratégies IAM** de l'appelant (utilisateur ou rôle), vues au module 2 ;
- la **stratégie de bucket**, attachée au bucket lui-même, qui dit qui peut y accéder et à quelles conditions ;
- le **blocage de l'accès public** (*Block Public Access*), qui passe par-dessus les deux précédents : tant qu'il est actif, aucune règle ne peut rendre le bucket accessible à des anonymes.

Depuis avril 2023, tout nouveau bucket est créé avec le blocage de l'accès public activé et les anciennes listes de contrôle d'accès (ACL) désactivées[^defauts]. Ce changement fait suite à de nombreuses fuites de données. En juin 2017, par exemple, un chercheur de la société UpGuard avait trouvé, dans un bucket ouvert à tous appartenant à un sous-traitant de l'opérateur Verizon, les données de 6 à 14 millions de clients, selon les sources[^verizon].

<Schema svg={s3Acces} num="4.3" alt="Un bucket privé protégé par le blocage de l'accès public. Un internaute anonyme reçoit 403 AccessDenied. Une instance munie d'un rôle envoie une requête signée autorisée par IAM. Un navigateur muni d'une URL présignée accède aussi à l'objet.">
  Trois demandeurs face à un bucket privé : l'anonyme est refusé, le rôle et l'URL présignée sont acceptés.
</Schema>

Pour partager un objet précis sans ouvrir le bucket, on utilise une **URL présignée** : une adresse qui contient la signature d'une identité autorisée, pour un objet donné et une durée limitée[^presignee]. Le navigateur qui reçoit cette URL peut télécharger l'objet jusqu'à son expiration. C'est ainsi que l'application du projet final permet de télécharger les fichiers.

## La stratégie de bucket

Une stratégie de bucket s'écrit comme une stratégie IAM, avec en plus un champ `Principal` qui désigne à qui elle s'applique. L'exemple suivant, très répandu, refuse toute requête qui n'utilise pas HTTPS :

```json title="Refuser les requêtes non chiffrées"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "HTTPSUniquement",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::galerie-camille", "arn:aws:s3:::galerie-camille/*"],
    "Condition": { "Bool": { "aws:SecureTransport": "false" } }
  }]
}
```

## La tarification de S3

S3 facture le volume stocké par mois selon la classe (un peu plus de 0,02 dollar par gigaoctet en Standard), les requêtes (les écritures et les listes coûtent plus cher que les lectures), le transfert de données vers Internet (le transfert entrant est gratuit), la récupération des données pour les classes IA et Glacier, et certaines fonctionnalités optionnelles comme la réplication[^s3-prix].

## Amazon EBS

EBS (*Elastic Block Store*) fournit les disques des instances. Un volume EBS se comporte comme un disque brut sur lequel on crée un système de fichiers ; il est situé dans une seule zone de disponibilité, répliqué à l'intérieur de cette zone, et attaché à une seule instance à la fois (sauf l'option Multi-Attach des volumes `io1` et `io2`). On peut en prendre des **instantanés**, incrémentaux et stockés dans S3, qui servent de sauvegarde, peuvent être copiés dans une autre région et permettent de recréer le volume dans une autre zone. Volumes et instantanés peuvent être chiffrés avec KMS.

| Type | Support | Usage | Taille maximale |
|---|---|---|---|
| `gp3` | SSD | usage général : 3 000 IOPS de base, jusqu'à 80 000 IOPS et 2 000 Mio/s | 64 Tio |
| `gp2` | SSD | génération précédente, performances liées à la taille | 16 Tio |
| `io2` Block Express | SSD | bases de données critiques, jusqu'à 256 000 IOPS | 64 Tio |
| `st1` | HDD | débit séquentiel élevé (journaux, traitements par lots) | 16 Tio |
| `sc1` | HDD | données rarement lues, coût minimal | 16 Tio |

Le type `gp3` convient à la grande majorité des usages ; ses limites ont été relevées en 2025[^gp3].

## Amazon EFS et comparaison

EFS (*Elastic File System*) est un système de fichiers NFS managé et élastique : sa taille suit le volume réellement stocké, il est partagé par plusieurs instances et réparti sur plusieurs zones.

| | S3 | EBS | EFS |
|---|---|---|---|
| Type | objet | bloc | fichiers (NFS) |
| Accès | API HTTPS, de partout | une instance de la même zone | plusieurs instances |
| Redondance | plusieurs zones (selon la classe) | une zone | plusieurs zones |
| Facturation | volume réel et requêtes | volume réservé | volume réel |
| Usage type | fichiers d'application, sauvegardes, site statique | disque système, base de données | dossier partagé entre instances |

## Bases relationnelles et NoSQL

S3 sait ranger des fichiers et les retrouver par leur clé, mais il ne sait pas répondre à une question comme « toutes les photos de Camille prises en 2026, triées par date ». Pour interroger des données, il faut une base de données.

| | Relationnel (SQL) | NoSQL |
|---|---|---|
| Modèle | tables, schéma fixe, jointures | clé-valeur, document, graphe ; schéma souple |
| Requêtes | SQL | API propre à chaque moteur |
| Mise à l'échelle | surtout verticale (machine plus puissante) | horizontale (partitionnement sur plusieurs machines) |
| Garanties | transactions ACID | souvent cohérence à terme, transactions plus limitées |
| Exemples | PostgreSQL, MySQL, Oracle | DynamoDB, MongoDB, Redis, Neo4j |

## Les bases de données managées sur AWS

| Service | Description |
|---|---|
| Amazon RDS | bases relationnelles PostgreSQL, MySQL, MariaDB, Oracle, SQL Server et Db2 |
| Amazon Aurora | moteur compatible PostgreSQL et MySQL conçu par AWS, stockage réparti sur 3 zones |
| Amazon DynamoDB | base clé-valeur et document, sans serveur à gérer |
| Amazon ElastiCache | cache en mémoire : Valkey, Redis OSS, Memcached |
| Amazon DocumentDB | base orientée documents, compatible MongoDB |
| Amazon Neptune | base orientée graphes |
| Amazon OpenSearch Service | recherche plein texte et analyse de journaux |

### Amazon RDS

Avec RDS, AWS installe le moteur de base de données, applique ses correctifs, réalise des sauvegardes automatiques (stockées dans S3) qui permettent de restaurer la base à un instant donné, et peut maintenir une copie de secours synchrone dans une autre zone (déploiement Multi-AZ)[^rds]. Le client choisit le moteur et sa version, la classe d'instance (`db.t4g.micro`, `db.r7g.large`…), le stockage, l'activation du Multi-AZ et des réplicas en lecture, le réseau, le Security Group et les utilisateurs de la base. Une base RDS est facturée à l'heure tant qu'elle existe, même si elle ne reçoit aucune requête.

### Amazon DynamoDB

DynamoDB est une base clé-valeur et document entièrement managée : il n'y a ni serveur à dimensionner ni moteur à mettre à jour[^dynamodb]. Elle promet une latence de quelques millisecondes quelle que soit la taille de la table. Chaque élément est identifié par une clé primaire (une clé de partition, éventuellement complétée d'une clé de tri) et pèse au plus 400 Ko. On paie à la requête (mode *on-demand*) ou une capacité réservée. La contrepartie de ces performances est que l'on interroge surtout par clé : la table se conçoit à partir des requêtes qu'elle devra servir, et une requête imprévue est difficile à réaliser.

### Que choisir ?

<Schema svg={galerie} num="4.4" alt="Une application sur EC2 reçoit une photo, la dépose dans S3, écrit ses informations dans DynamoDB ou RDS et envoie un message dans SQS. Un travailleur lit le message, lit l'original dans S3 et y écrit une miniature.">
  Une galerie de photos plus ambitieuse : S3 garde les fichiers, la base garde les informations qu'on interroge, SQS fait patienter le travail qui peut attendre.
</Schema>

S3 convient aux fichiers : images, documents, sauvegardes. RDS convient aux données structurées, reliées entre elles et modifiées par des transactions. DynamoDB convient aux accès par clé à très grande échelle, avec un schéma souple. Le choix dépend du volume, de la fréquence d'accès, du type de requêtes, des garanties de cohérence attendues et du coût. L'application du projet final se contente de S3 : la liste des fichiers d'un bucket lui suffit.

## Amazon SQS

Dans la galerie du schéma 4.4, fabriquer une miniature prend une ou deux secondes. Si l'application la fabriquait pendant que l'utilisateur attend, chaque dépôt serait lent, et un afflux de dépôts saturerait la machine. On note plutôt le travail à faire dans une **file de messages**, on répond tout de suite à l'utilisateur, et un autre programme traite la file à son rythme.

SQS (*Simple Queue Service*), lancé en 2006, est le service de files de messages d'AWS[^sqs-20]. Un **producteur** y dépose des messages (`SendMessage`), un **consommateur** vient les chercher (`ReceiveMessage`), les traite, puis les supprime (`DeleteMessage`). Les deux programmes ne se connaissent pas et n'ont pas besoin de fonctionner en même temps : si le consommateur est arrêté, les messages attendent dans la file ; si les dépôts affluent, on ajoute des consommateurs. Un message contient jusqu'à 1 Mio de texte (la limite était de 256 Kio avant août 2025) et reste dans la file 4 jours par défaut, de 1 minute à 14 jours selon le réglage[^sqs-quotas].

## Le délai de visibilité

Recevoir un message ne le supprime pas.

<Schema svg={sqsVisibilite} num="4.5" alt="Chronologie : un message est envoyé ; le consommateur A le reçoit, il devient invisible pendant le délai de visibilité ; A plante ; le message redevient visible ; le consommateur B le reçoit, le traite et le supprime.">
  Un message reçu devient invisible pour les autres consommateurs ; s'il n'est pas supprimé avant la fin du délai, il réapparaît.
</Schema>

Quand un consommateur reçoit un message, SQS le rend invisible aux autres pendant le **délai de visibilité**, de 30 secondes par défaut (jusqu'à 12 heures). Si le consommateur termine son travail et supprime le message, tout va bien. S'il plante avant, le message redevient visible et un autre consommateur le reprendra : aucun travail n'est perdu. En contrepartie, un même message peut être traité deux fois. Le consommateur doit donc être **idempotent** : traiter deux fois le même message ne doit pas causer de dommage (fabriquer deux fois la même miniature, par exemple, ne pose aucun problème).

## Files standard et FIFO

| | Standard | FIFO |
|---|---|---|
| Livraison | au moins une fois | traitement unique |
| Ordre | au mieux | strict, par groupe de messages |
| Débit | quasi illimité | 300 messages par seconde et par action, 3 000 par lots, davantage en mode haut débit |
| Nom | libre | suffixe `.fifo` |

Deux réglages complètent le fonctionnement d'une file. Une **file de lettres mortes** (*dead-letter queue*) recueille les messages qui ont échoué un certain nombre de fois, au lieu de les laisser bloquer les consommateurs. L'**attente longue** (*long polling*), jusqu'à 20 secondes, permet à un consommateur d'attendre l'arrivée d'un message au lieu d'interroger la file en boucle, ce qui évite de payer des milliers de requêtes vides.

## SQS, SNS et EventBridge

| Service | Modèle | Usage |
|---|---|---|
| SQS | file : un message est traité par un consommateur | tâches en arrière-plan, lissage de la charge |
| SNS | publication-abonnement : un message est reçu par tous les abonnés | notifications, diffusion vers plusieurs files |
| EventBridge | bus d'événements avec des règles de routage | intégration entre services et applications |

SQS est facturé à la requête : le premier million de requêtes de chaque mois est gratuit, puis il en coûte environ 0,40 dollar par million pour une file standard[^sqs-prix].

Le TP 4 met en pratique la partie S3 de bout en bout, puis vous fait observer le délai de visibilité sur une vraie file.

[^s3-20]: S. Stormacq, « Twenty years of Amazon S3 and building what's next », *AWS News Blog*, 2026, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/aws/twenty-years-of-amazon-s3-and-building-whats-next/).
[^faq]: AWS, *Amazon S3 FAQs*, [aws.amazon.com/s3/faqs](https://aws.amazon.com/s3/faqs/).
[^classes]: AWS, *Amazon S3 storage classes*, [aws.amazon.com](https://aws.amazon.com/s3/storage-classes/).
[^sla-s3]: AWS, *Amazon S3 Service Level Agreement*, [aws.amazon.com](https://aws.amazon.com/s3/sla/).
[^chiffrement]: AWS, *Setting default server-side encryption behavior for Amazon S3 buckets*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html).
[^defauts]: AWS, « Amazon S3 now applies two security best practices to all new buckets by default », 2023, [aws.amazon.com](https://aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/).
[^verizon]: UpGuard, « Cloud Leak: How A Verizon Partner Exposed Millions of Customer Accounts », 2017, [upguard.com](https://www.upguard.com/breaches/verizon-cloud-leak).
[^presignee]: AWS, *Download and upload objects with presigned URLs*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).
[^s3-prix]: AWS, *Amazon S3 pricing*, [aws.amazon.com/s3/pricing](https://aws.amazon.com/s3/pricing/).
[^gp3]: AWS, « Amazon EBS increases the maximum size and provisioned performance of General Purpose (gp3) volumes », 2025, [aws.amazon.com](https://aws.amazon.com/about-aws/whats-new/2025/09/amazon-ebs-size-provisioned-performance-gp3-volumes/) ; *Amazon EBS volume types*, [docs.aws.amazon.com](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html).
[^rds]: AWS, *Amazon RDS*, [aws.amazon.com/rds](https://aws.amazon.com/rds/).
[^dynamodb]: AWS, *What is Amazon DynamoDB?*, [docs.aws.amazon.com](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html).
[^sqs-20]: E. Kayabali, « Amazon SQS turns 20: Two decades of reliable messaging at scale », *AWS News Blog*, 2026, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/aws/amazon-sqs-turns-20-two-decades-of-reliable-messaging-at-scale/).
[^sqs-quotas]: AWS, *Amazon SQS message quotas*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html).
[^sqs-prix]: AWS, *Amazon SQS pricing*, [aws.amazon.com/sqs/pricing](https://aws.amazon.com/sqs/pricing/).
