---
title: "Introduction à AWS"
sidebar_label: "Cours"
description: "AWS en quelques chiffres, modèles de service, responsabilité partagée, catalogue, régions et zones de disponibilité, haute disponibilité, tarification, accès à AWS."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import responsabilite from '@site/src/figures/responsabilite.svg';
import familles from '@site/src/figures/familles-services.svg';
import correspondance from '@site/src/figures/infra-correspondance.svg';
import regions from '@site/src/figures/region-az.svg';
import hauteDispo from '@site/src/figures/haute-dispo.svg';
import appelApi from '@site/src/figures/appel-api.svg';

<Seance items={['Module 1', 'Cours']} />

Ce premier module pose le décor. Avant de créer la moindre ressource, il faut savoir ce qu'est AWS, comment son catalogue est organisé, où se trouvent physiquement ses machines, qui est responsable de quoi en cas de problème, et comment on est facturé. Toutes les notions de ce module servent dans les suivants : on y reviendra sans cesse.

## Amazon Web Services

AWS est la filiale d'Amazon qui vend de l'informatique à la demande. Le principe est simple : au lieu d'acheter des serveurs, des disques et des équipements réseau, on loue chez AWS des ressources virtuelles, que l'on crée en quelques minutes et que l'on rend quand on n'en a plus besoin. On paie ce que l'on consomme : des secondes de calcul, des gigaoctets stockés, des requêtes traitées.

AWS est aujourd'hui le premier fournisseur mondial de cloud, avec 28 % du marché de l'infrastructure au deuxième trimestre 2026[^marche]. En 2025, son chiffre d'affaires a atteint 128,7 milliards de dollars, en hausse de 20 % sur un an[^ca].

Trois principes, présents dès l'origine, expliquent la manière dont on travaille avec AWS :

- **API d'abord.** Tout ce que propose AWS se pilote par une interface de programmation. La console web n'est qu'un client parmi d'autres de ces API.
- **Libre-service.** Une ressource s'obtient sans contrat ni intervention humaine : on la demande, elle est disponible en quelques secondes ou quelques minutes.
- **Paiement à l'usage.** Pas d'engagement par défaut : on est facturé pour ce qui a réellement été consommé.

## Quelques dates

| Année | Événement |
|---|---|
| 2002 | Amazon ouvre ses premiers services web aux développeurs |
| 2006 | lancement des trois services d'origine : S3 (mars), SQS (juillet), EC2 (août) |
| 2009 | arrivée des réseaux privés virtuels (VPC) et des bases de données managées (RDS) |
| 2012 | DynamoDB, la base NoSQL d'AWS |
| 2014 | Lambda, le calcul sans serveur à gérer |
| 2017 | ouverture de la région de Paris (`eu-west-3`) |
| 2026 | 39 régions, 123 zones de disponibilité, plus de 1 200 types de machines virtuelles |

Les trois services de 2006 sont ceux qui structurent encore ce cours : S3 pour le stockage, SQS pour les files de messages, EC2 pour les machines virtuelles. Vingt ans plus tard, S3 stocke plus de 500 000 milliards d'objets et EC2 propose plus de 1 200 types d'instances[^vingt-ans].

## Parts de marché

Au deuxième trimestre 2026, les entreprises ont dépensé 143,4 milliards de dollars en infrastructure cloud, soit environ 43 % de plus qu'un an plus tôt. AWS en a capté 28 %, Microsoft Azure 20 % et Google Cloud 15 %. Ensemble, ces trois acteurs représentent 63 % du marché[^marche]. Le reste se partage entre de nombreux fournisseurs : Oracle, Alibaba, IBM, des acteurs européens comme OVHcloud ou Scaleway, et une nouvelle génération de clouds spécialisés dans le calcul pour l'intelligence artificielle.

Ces chiffres expliquent pourquoi on enseigne AWS en premier, mais pas que les autres fournisseurs fonctionnent différemment : les notions de ce cours (régions, machines virtuelles, stockage objet, identités et droits) existent chez tous, sous d'autres noms.

## Modèles de service

On distingue habituellement trois modèles, selon la part du travail que le fournisseur prend en charge.

| Modèle | Ce que gère le client | Exemples chez AWS |
|---|---|---|
| IaaS (infrastructure) | système d'exploitation, logiciels, données, accès | EC2, EBS, VPC |
| PaaS (plateforme) | code de l'application, données, accès | RDS, Lambda, Elastic Beanstalk |
| SaaS (logiciel) | données, accès | Amazon WorkMail, Amazon Connect |

Plus un service est géré par AWS, moins il demande d'administration, mais moins on garde la main sur ses réglages. Une base PostgreSQL installée soi-même sur une instance EC2 permet de tout configurer ; la même base sur RDS évite d'appliquer les correctifs et de gérer les sauvegardes, au prix de certaines options auxquelles on n'a plus accès.

## Le modèle de responsabilité partagée

En matière de sécurité, AWS formule le partage des tâches ainsi : AWS est responsable de la sécurité **du** cloud, le client de la sécurité **dans** le cloud[^srm]. AWS garantit les bâtiments, le matériel, le réseau physique et la couche de virtualisation qui isole les clients les uns des autres. Tout ce que le client installe et configure par-dessus relève de sa responsabilité.

<Schema svg={responsabilite} num="1.1" alt="Trois colonnes, Amazon EC2, Amazon RDS et Amazon S3, découpées en sept couches, des centres de données jusqu'aux données et droits d'accès. Sur EC2, le client gère le système d'exploitation, le logiciel, l'exposition réseau et les accès. Sur RDS et S3, AWS gère jusqu'au logiciel compris ; le client gère l'exposition réseau et les accès.">
  La frontière de responsabilité sur trois services. Plus le service est managé, plus AWS en prend en charge ; la dernière ligne, les données et les droits d'accès, reste toujours au client.
</Schema>

La frontière se déplace d'un service à l'autre. Sur une instance EC2, c'est au client d'appliquer les mises à jour de sécurité du système : AWS n'a aucun accès à l'intérieur de la machine virtuelle. Sur RDS, AWS applique lui-même les correctifs du moteur de base de données, dans une fenêtre de maintenance que le client choisit. Sur S3, il n'y a plus aucun serveur à gérer. Mais dans les trois cas, c'est le client qui décide qui peut accéder aux données, et c'est là que se produisent la plupart des incidents de sécurité : un bucket rendu public par erreur, un rôle doté de droits trop larges.

## Le catalogue de services

AWS propose plus de deux cents services[^overview]. Personne ne les connaît tous ; l'important est de savoir les ranger, pour comprendre à quoi sert un service que l'on découvre.

<Schema svg={familles} num="1.2" alt="Carte des services AWS en trois étages : services fondamentaux (calcul, stockage, bases de données, réseau), services de plateforme (sécurité, gestion, intégration, analytique), services applicatifs (IA, applications métier, postes et front-end). Les services utilisés dans le cours sont en gras.">
  Les services AWS en trois étages. Les services en gras sont ceux que l'on utilise dans ce cours.
</Schema>

Les **services fondamentaux** sont les briques que l'on retrouverait dans n'importe quel centre de données : machines (EC2), disques et stockage (EBS, S3), bases de données (RDS, DynamoDB), réseau (VPC). Les **services de plateforme** s'appuient sur eux : ils contrôlent les accès (IAM), surveillent (CloudWatch), font communiquer les composants (SQS) ou analysent les données. Les **services applicatifs** sont des produits presque finis, que l'on consomme sans se soucier de ce qui se trouve dessous.

Une autre façon de situer AWS est de partir de ce que l'on connaît d'un centre de données classique.

<Schema svg={correspondance} num="1.3" alt="Correspondance entre infrastructure classique et AWS : pare-feu et annuaire deviennent IAM, Security Groups et NACL ; routeurs et commutateurs deviennent VPC, sous-réseaux et passerelles ; serveurs physiques deviennent EC2 ; SAN, NAS et partages deviennent EBS, EFS et S3 ; un SGBD installé sur un serveur devient RDS, Aurora ou DynamoDB.">
  Chaque élément d'une infrastructure classique a son équivalent chez AWS.
</Schema>

## L'infrastructure mondiale

### Les régions

Une **région** est une zone géographique où AWS exploite plusieurs centres de données : Paris, Francfort, l'Irlande, la Virginie du Nord, Le Cap, et une quarantaine d'autres[^regions]. Chaque région a un code que l'on retrouve partout, dans la console comme dans les commandes : `eu-west-3` pour Paris, `eu-central-1` pour Francfort, `us-east-1` pour la Virginie du Nord.

Les régions sont indépendantes les unes des autres. Une panne reste en principe confinée à sa région, et les données ne quittent jamais une région sans que le client l'ait demandé : un fichier déposé dans un bucket de la région de Paris reste à Paris, sauf si l'on configure une réplication. Certaines régions récentes, comme `af-south-1` (Le Cap) ou `eu-south-1` (Milan), doivent être activées explicitement dans le compte avant de pouvoir être utilisées.

<Schema svg={regions} num="1.4" alt="Dans le cloud AWS, la région Europe (Paris) eu-west-3 contient trois zones de disponibilité, chacune formée de centres de données et reliée aux autres par des liaisons privées. Un incident dans une zone laisse les deux autres intactes. À droite, la région de Francfort, indépendante, et des points de présence.">
  Une région regroupe plusieurs zones de disponibilité isolées les unes des autres ; une autre région est totalement indépendante.
</Schema>

### Les zones de disponibilité

À l'intérieur d'une région, les centres de données sont regroupés en **zones de disponibilité** (*Availability Zones*, AZ). Chaque zone dispose de sa propre alimentation électrique, de son refroidissement et de ses liaisons réseau. Les zones d'une région sont assez éloignées pour qu'un même incident (incendie, inondation, coupure de courant) ne les touche pas toutes, mais situées à moins de 100 kilomètres les unes des autres, ce qui permet de les relier avec une latence de l'ordre de la milliseconde. Paris compte trois zones : `eu-west-3a`, `eu-west-3b` et `eu-west-3c`.

Un détail a beaucoup de conséquences dans la suite du cours : un sous-réseau, un volume EBS et une instance EC2 appartiennent chacun à **une seule** zone. Si cette zone a un problème, la ressource devient inaccessible.

Il existe enfin plusieurs centaines de **points de présence**, de petits sites placés près des utilisateurs, qui servent au réseau de diffusion de contenu CloudFront et au DNS Route 53. On ne les utilise pas dans ce cours.

### La haute disponibilité

Puisqu'une instance vit dans une seule zone, une application qui tourne sur une seule instance s'arrête si cette zone tombe. Pour qu'elle continue à fonctionner, il faut la répartir sur au moins deux zones.

<Schema svg={hauteDispo} num="1.5" alt="À gauche, une seule instance dans la zone a : la zone tombe, le service est interrompu. À droite, deux instances dans les zones a et b derrière un répartiteur de charge : la zone a tombe, le service est maintenu par la zone b.">
  Avec une seule instance, la panne d'une zone interrompt le service ; avec deux instances dans deux zones derrière un répartiteur, le service continue.
</Schema>

Pour EC2, cela signifie plusieurs instances placées dans des zones différentes, derrière un répartiteur de charge (Elastic Load Balancing) qui n'envoie le trafic qu'aux instances en bonne santé. Pour une base RDS, on active le déploiement Multi-AZ : AWS maintient une copie de secours synchronisée dans une autre zone et bascule dessus en cas de panne. L'application du projet final ne tournera que sur une instance : elle sera sécurisée, mais pas hautement disponible, et il faut savoir le dire.

### Services régionaux et services globaux

Tous les services ne sont pas proposés dans toutes les régions, les nouveautés arrivent souvent d'abord en `us-east-1`, et les prix varient d'une région à l'autre[^regional]. Surtout, la plupart des services sont **régionaux** : EC2, EBS, VPC, RDS, SQS. Dans la console, un sélecteur en haut à droite indique la région dans laquelle on travaille, et une instance créée à Paris n'apparaît pas si le sélecteur est positionné sur l'Irlande. Elle continue pourtant de tourner et d'être facturée : c'est la cause la plus fréquente de ressources oubliées.

Quelques services sont **globaux** : IAM, Route 53, CloudFront. La console affiche alors « Global » à la place du sélecteur. S3 est un cas intermédiaire : la liste des buckets s'affiche quelle que soit la région, mais chaque bucket appartient à une région précise, choisie à sa création.

### Choisir une région

Le choix d'une région se fait selon quatre critères, dans cet ordre de priorité :

1. **la réglementation** : localisation imposée pour les données personnelles (RGPD), les données de santé, certaines données publiques ;
2. **la latence** : plus la région est proche des utilisateurs, plus l'application répond vite ; la distance sur une carte donne une idée, mais seule une mesure fait foi ;
3. **les services disponibles** dans la région ;
4. **le prix**.

Dans ce cours, tout le monde travaille dans la région de Paris, `eu-west-3`, ouverte en décembre 2017 avec trois zones de disponibilité.

## Deux idées reçues

### « Le cloud n'est pas fiable »

AWS publie pour chaque service un engagement de niveau de service (SLA). Pour EC2, il est de 99,99 % de disponibilité mensuelle pour une application répartie sur plusieurs zones, et de 99,5 % pour une instance seule[^sla-ec2]. Pour S3 Standard, l'engagement de disponibilité est de 99,9 %, et la durabilité des données est conçue pour atteindre 99,999999999 % par an (« onze neuf »), les objets étant copiés dans plusieurs zones[^sla-s3].

Les pannes existent pourtant, et il faut les connaître. Le 28 février 2017, une commande de maintenance mal saisie a rendu S3 indisponible pendant plus de quatre heures dans la région de Virginie du Nord[^panne-2017]. Les 19 et 20 octobre 2025, une erreur dans le système DNS interne de DynamoDB a provoqué, dans la même région, une panne d'environ quatorze heures qui s'est propagée à EC2, Lambda, STS et à de nombreux autres services[^panne-2025]. Dans les deux cas, les autres régions ont continué à fonctionner : c'est l'intérêt de leur indépendance, et la raison pour laquelle les applications critiques sont réparties sur plusieurs zones, voire plusieurs régions.

### « Je perds le contrôle de mes données »

Le client reste propriétaire de ses données. Il choisit la région où elles sont stockées, il peut les chiffrer au repos comme en transit, avec des clés gérées par AWS ou par lui-même (service KMS), et il peut les récupérer à tout moment. Enfin, tous les appels d'API effectués dans un compte sont journalisés par CloudTrail : on sait qui a fait quoi, quand et d'où.

## La tarification

Sur AWS, on paie à l'usage et on reçoit une facture mensuelle. Chaque service a ses propres unités : des secondes de calcul pour EC2, des gigaoctets par mois pour S3 et EBS, des requêtes pour SQS, des gigaoctets transférés vers Internet pour le trafic sortant (le trafic entrant est gratuit). Cette souplesse a un revers : sans estimation préalable, le coût est difficile à prévoir. Le simulateur [AWS Pricing Calculator](https://calculator.aws) permet de chiffrer une architecture avant de la construire.

Il n'existe pas d'arrêt automatique en cas de dépassement. Un **budget** AWS envoie une alerte quand un seuil est franchi, mais il ne coupe rien. Seuls les comptes créés depuis le 15 juillet 2025 et restés en « plan gratuit » sont plafonnés : ils reçoivent jusqu'à 200 dollars de crédits et se ferment au bout de six mois ou à l'épuisement des crédits[^freetier].

Le point le plus important à retenir est que certaines ressources coûtent même quand personne ne s'en sert.

| Ressource | Unité facturée | Facturée à l'arrêt ? |
|---|---|---|
| Instance EC2 démarrée | seconde de fonctionnement (au moins 60 s) | oui, même inactive |
| Instance EC2 arrêtée | rien pour le calcul | son disque EBS, oui |
| Volume EBS | gigaoctet réservé, par mois | oui, même vide |
| Adresse IPv4 publique | heure (0,005 $), depuis février 2024 | oui[^ipv4] |
| NAT Gateway | heure, plus gigaoctet traité | oui |
| Objet S3 | gigaoctet par mois, plus requêtes | selon le volume stocké |

D'où trois règles que l'on applique pendant tout le cours : travailler toujours dans la région de Paris, mettre son nom d'utilisateur dans le nom de chaque ressource pour la retrouver, et supprimer à la fin de chaque TP ce que l'on a créé.

## L'accès à AWS

Toute action sur AWS, sans exception, est un appel d'API HTTPS. Quand on clique sur *Launch instance* dans la console, celle-ci envoie une requête `RunInstances` au point d'entrée d'EC2 de la région. La console n'a aucun privilège particulier : elle fait exactement ce que ferait la ligne de commande.

<Schema svg={appelApi} num="1.6" alt="La console web, l'AWS CLI, les SDK comme boto3 et CloudFormation envoient une requête signée à l'API AWS. IAM vérifie qui envoie la requête et si cette identité en a le droit : si oui, la requête atteint EC2, S3 ou SQS ; sinon, la réponse est AccessDenied. Chaque appel est journalisé par CloudTrail.">
  Quel que soit l'outil, chaque action devient une requête signée, vérifiée par IAM et journalisée par CloudTrail.
</Schema>

Plusieurs outils émettent ces requêtes :

- **la console web**, pratique pour découvrir un service ou diagnostiquer un problème ;
- **la ligne de commande** (AWS CLI) et les **SDK** des langages de programmation (`boto3` pour Python), pour les scripts et les applications ;
- **l'infrastructure as code** (CloudFormation, CDK, Terraform, Pulumi), qui décrit l'infrastructure dans des fichiers versionnés.

Chaque requête est signée avec les identifiants de celui qui l'envoie, puis vérifiée par IAM avant d'atteindre le service : c'est l'objet du module 2. Il en découle qu'une action refusée dans la console l'est aussi en ligne de commande, et que toute action est tracée.

Pour la ligne de commande, AWS fournit **CloudShell**, un terminal intégré à la console, déjà authentifié avec l'identité de l'utilisateur et où la CLI est installée. C'est lui que l'on utilise dans les TP :

```bash title="CloudShell"
aws sts get-caller-identity
aws ec2 describe-availability-zones --region eu-west-3 --output table
```

La première commande indique sous quelle identité on travaille, la seconde liste les zones de disponibilité de la région de Paris. Le TP 1 commence par là.

[^marche]: Synergy Research Group, « Cloud Market Share Trends - Big Three Together Hold 63% », données du deuxième trimestre 2026, [srgresearch.com](https://www.srgresearch.com/articles/cloud-market-share-trends-big-three-together-hold-63-while-oracle-and-the-neoclouds-inch-higher).
[^ca]: Amazon, *Amazon.com Announces Fourth Quarter Results*, février 2026, [aboutamazon.com](https://www.aboutamazon.com/news/company-news/amazon-earnings-q4-2025-report).
[^vingt-ans]: S. Stormacq, « Twenty years of Amazon S3 », 2026, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/aws/twenty-years-of-amazon-s3-and-building-whats-next/) ; J. Barr, « Happy 20th Birthday, Amazon EC2 », 2026, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/aws/happy-20th-birthday-amazon-ec2/).
[^srm]: AWS, *Shared Responsibility Model*, [aws.amazon.com](https://aws.amazon.com/compliance/shared-responsibility-model/).
[^overview]: AWS, *Overview of Amazon Web Services*, livre blanc, [docs.aws.amazon.com](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html).
[^regions]: AWS, *Regions and Availability Zones*, [aws.amazon.com](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/).
[^regional]: AWS, *AWS Regional Services List*, [aws.amazon.com](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/).
[^sla-ec2]: AWS, *Amazon Compute Service Level Agreement*, [aws.amazon.com](https://aws.amazon.com/compute/sla/).
[^sla-s3]: AWS, *Amazon S3 Service Level Agreement*, [aws.amazon.com](https://aws.amazon.com/s3/sla/) ; *Amazon S3 FAQs*, [aws.amazon.com](https://aws.amazon.com/s3/faqs/).
[^panne-2017]: AWS, *Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region*, 2017, [aws.amazon.com](https://aws.amazon.com/message/41926/).
[^panne-2025]: AWS, *Summary of the Amazon DynamoDB Service Disruption in the Northern Virginia (US-EAST-1) Region*, 2025, [aws.amazon.com](https://aws.amazon.com/message/101925/).
[^freetier]: AWS, *AWS Free Tier*, [aws.amazon.com/free](https://aws.amazon.com/free/).
[^ipv4]: J. Barr, « New – AWS Public IPv4 Address Charge + Public IP Insights », *AWS News Blog*, 2023, [aws.amazon.com/blogs](https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/).
