---
title: "Sécurité et gestion des accès"
sidebar_label: "Cours"
description: "IAM : vocabulaire, utilisateur racine, utilisateurs, groupes, rôles, stratégies, logique d'évaluation, bonnes pratiques. Réseau : VPC, sous-réseaux, CIDR, Security Groups et NACL."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import identites from '@site/src/figures/iam-identites.svg';
import politique from '@site/src/figures/politique-annotee.svg';
import evaluation from '@site/src/figures/evaluation-iam.svg';
import cleRole from '@site/src/figures/cle-vs-role.svg';
import topologie from '@site/src/figures/vpc-topologie.svg';
import securityGroup from '@site/src/figures/security-group.svg';

<Seance items={['Module 2', 'Cours']} />

Deux mécanismes décident de ce qui peut atteindre vos ressources sur AWS. Le premier, IAM, contrôle les requêtes envoyées à l'API : qui les envoie et ce que cette identité a le droit de faire. Le second, le réseau virtuel et ses pare-feu, contrôle le trafic qui arrive sur vos machines. Ce module traite les deux, dans cet ordre.

## IAM : Identity and Access Management

On l'a vu au module 1 : toute action sur AWS est une requête signée. IAM répond aux deux questions que pose chacune d'elles[^iam] :

- **l'authentification** : qui envoie la requête ? AWS le vérifie grâce au mot de passe (et au code MFA) dans la console, grâce à la signature cryptographique de la requête en ligne de commande ;
- **l'autorisation** : cette identité a-t-elle le droit d'effectuer cette action sur cette ressource ?

IAM s'applique à toutes les requêtes, quel que soit l'outil qui les envoie. C'est un service global, commun à toutes les régions, et gratuit.

## Le vocabulaire

| Terme | Définition |
|---|---|
| Principal | entité qui envoie une requête : utilisateur racine, utilisateur IAM, rôle, service AWS |
| Utilisateur IAM | identité permanente d'une personne ou d'une application ; il peut avoir un mot de passe (console) et des clés d'accès (CLI, SDK) |
| Groupe | ensemble d'utilisateurs qui partagent les mêmes stratégies ; un groupe ne peut pas se connecter |
| Rôle | identité sans identifiants permanents, endossée temporairement par qui en a reçu l'autorisation |
| Stratégie (*policy*) | document JSON qui autorise ou interdit des actions sur des ressources |

Il faut aussi distinguer le **compte AWS** de l'**utilisateur**. Le compte est un conteneur de ressources, avec une facture et un numéro à douze chiffres ; les utilisateurs sont des identités à l'intérieur de ce compte. Une entreprise possède souvent des dizaines de comptes, un par projet ou par environnement.

## L'utilisateur racine

L'utilisateur racine (*root user*) est créé avec le compte et identifié par l'adresse électronique d'inscription. Il a tous les droits, et aucune stratégie IAM ne peut les restreindre. AWS rend obligatoire l'authentification multifacteur (MFA) pour l'utilisateur racine de tous les types de comptes depuis juin 2025[^mfa-root], et recommande de le réserver aux rares opérations qui l'exigent : fermer le compte, changer le plan de support, restaurer des droits perdus. On ne crée jamais de clé d'accès pour lui.

Dans ce cours, vous travaillez avec un utilisateur IAM qui vous a été fourni ; vous n'aurez pas accès au compte racine.

## Utilisateurs, groupes et rôles

<Schema svg={identites} num="2.1" alt="Dans un compte AWS, le groupe developpeurs contient alice, bob et camille, le groupe stagiaires contient camille. La stratégie ec2-complet est attachée au premier groupe, lecture-ec2 au second. À droite, une instance EC2 endosse le rôle role-galerie, qui porte la stratégie de permissions galerie-s3 ; aucun mot de passe ni clé.">
  Les identités d'un compte. Les droits sont portés par des stratégies attachées aux groupes ; le rôle, lui, est endossé par une instance.
</Schema>

Un **utilisateur IAM** tout juste créé ne peut rien faire : il sait se connecter, mais toutes ses requêtes sont refusées tant qu'on ne lui a pas donné de droits. On les lui donne en général par l'intermédiaire de **groupes** : dans une entreprise, on attribue des droits au groupe « développeurs », et chaque personne qui rejoint l'équipe en hérite. Un utilisateur peut appartenir à plusieurs groupes ; il cumule alors leurs droits.

AWS recommande aujourd'hui que les personnes se connectent par **fédération d'identités**, via IAM Identity Center relié à l'annuaire de l'entreprise, plutôt qu'avec des utilisateurs IAM munis d'un mot de passe permanent[^bp]. La personne s'authentifie une fois auprès de l'annuaire et endosse un rôle dans le compte voulu. Les stratégies et les rôles fonctionnent exactement comme dans ce cours ; seule la porte d'entrée change.

## Les rôles

Un **rôle** n'a ni mot de passe ni clé permanente. Il est endossé temporairement par une entité autorisée : un service AWS (une instance EC2, une fonction Lambda), un utilisateur, un autre compte, un utilisateur fédéré. Celui qui endosse le rôle reçoit des **identifiants temporaires**, délivrés par le service AWS STS (*Security Token Service*), valables quelques heures et renouvelés automatiquement.

Un rôle se définit par deux stratégies :

- la **stratégie de confiance** dit qui a le droit de l'endosser ; pour un rôle destiné à une instance, elle désigne le service EC2 ;
- la ou les **stratégies de permissions** disent ce que l'on peut faire une fois le rôle endossé.

```json title="Stratégie de confiance d'un rôle pour EC2"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

Pour associer un rôle à une instance, on passe par un **profil d'instance** (*instance profile*), que la console crée automatiquement avec le même nom que le rôle[^roles-ec2]. L'application qui tourne sur l'instance n'a alors rien à configurer : la bibliothèque `boto3`, comme la commande `aws`, va chercher d'elle-même les identifiants du rôle auprès du service de métadonnées de l'instance (module 3). Une application qui tourne sur AWS n'a donc jamais besoin de clé d'accès.

## La structure d'une stratégie

Les droits s'écrivent dans des **stratégies** au format JSON. Voici celle que l'on attachera au rôle de l'application du projet final : elle l'autorise à lister le contenu d'un bucket et à y lire et écrire des fichiers, et à rien d'autre.

<Schema svg={politique} num="2.2" alt="Stratégie JSON à deux déclarations : s3:ListBucket sur arn:aws:s3:::galerie-camille ; s3:GetObject et s3:PutObject sur arn:aws:s3:::galerie-camille/*. Des annotations expliquent Version, Effect, Action et Resource.">
  Une stratégie lue ligne à ligne. Lister porte sur le bucket, lire et écrire portent sur ses objets.
</Schema>

Une stratégie contient une ou plusieurs **déclarations** (`Statement`). Chacune associe un **effet** (`Allow` ou `Deny`), des **actions** (les appels d'API, préfixés par le service : `s3:GetObject`, `ec2:RunInstances`), des **ressources** désignées par leur ARN, et éventuellement des **conditions**. Le joker `*` est accepté, avec prudence : `ec2:Describe*` couvre à lui seul des centaines d'actions.

Deux détails trompent souvent. Le champ `Version` contient la version du langage de stratégie, pas la date du document ; sa valeur est toujours `2012-10-17`[^version]. Et `s3:ListBucket` porte sur le bucket (`arn:aws:s3:::galerie-camille`), tandis que `s3:GetObject` et `s3:PutObject` portent sur les objets (`arn:aws:s3:::galerie-camille/*`) : confondre les deux donne un `AccessDenied` difficile à comprendre.

## Les conditions

Le bloc `Condition` restreint une déclaration à certains contextes. L'exemple suivant interdit toute action EC2 en dehors de la région de Paris ; attaché à un groupe, il empêche ses membres de créer des ressources dans une autre région, même par erreur.

```json title="Interdire EC2 hors de la région de Paris"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "UniquementParis",
    "Effect": "Deny",
    "Action": "ec2:*",
    "Resource": "*",
    "Condition": {
      "StringNotEquals": { "aws:RequestedRegion": "eu-west-3" }
    }
  }]
}
```

D'autres clés de condition reviennent souvent : `aws:SourceIp` (adresse d'origine de la requête), `aws:MultiFactorAuthPresent` (session ouverte avec MFA), `aws:ResourceTag/...` (étiquette portée par la ressource visée).

## Les types de stratégies

| Type | Description |
|---|---|
| Gérée par AWS | prête à l'emploi (`AdministratorAccess`, `AmazonS3ReadOnlyAccess`), maintenue par AWS, souvent plus large que nécessaire |
| Gérée par le client | écrite par le client, réutilisable sur plusieurs identités ; c'est l'outil du moindre privilège |
| En ligne (*inline*) | écrite dans une seule identité, supprimée avec elle |
| Basée sur la ressource | attachée à une ressource et non à une identité : stratégie de bucket S3, de file SQS |
| SCP, limite de permissions | plafonnent les droits possibles dans une organisation ou pour un utilisateur, sans en accorder |

`AmazonS3ReadOnlyAccess`, par exemple, permet de lire tous les buckets du compte. Pour qu'une identité ne lise qu'un bucket, il faut écrire sa propre stratégie.

## La logique d'évaluation

Une même identité est souvent concernée par plusieurs stratégies : celles de ses groupes, les siennes, celle de la ressource visée. AWS les évalue toutes ensemble selon une règle courte[^eval].

<Schema svg={evaluation} num="2.3" largeur="30rem" alt="Organigramme : une requête arrive ; AWS rassemble les stratégies concernées ; si l'une contient un Deny correspondant, la requête est refusée ; sinon, si l'une contient un Allow correspondant, elle est autorisée ; sinon, elle est refusée par défaut.">
  La logique d'évaluation, réduite à l'essentiel.
</Schema>

Par défaut, tout est refusé. Une autorisation explicite (`Allow`) lève ce refus, mais une interdiction explicite (`Deny`) l'emporte toujours, d'où qu'elle vienne.

Prenons un exemple. Camille appartient au groupe `developpeurs`, auquel est attachée `AmazonS3FullAccess` (qui autorise `s3:*` sur toutes les ressources). On lui attache en plus une stratégie qui interdit `s3:DeleteObject` sur le bucket `archives`. Camille peut lire un fichier de `archives` : `s3:*` l'autorise et aucun `Deny` ne concerne la lecture. Elle ne peut pas y supprimer de fichier : le `Deny` l'emporte. Elle peut supprimer un fichier dans un autre bucket : le `Deny` ne vise que `archives`. Enfin, elle ne peut pas lancer d'instance EC2 : aucune stratégie ne l'autorise, et le refus par défaut s'applique.

## Les ARN

Les ressources sont désignées par leur **ARN** (*Amazon Resource Name*), de la forme `arn:aws:service:région:compte:ressource`[^arn]. Les champs sans objet pour un service restent vides.

| ARN | Ce qu'il désigne |
|---|---|
| `arn:aws:iam::123456789012:user/camille` | un utilisateur IAM ; IAM est global, pas de région |
| `arn:aws:ec2:eu-west-3:123456789012:instance/i-0abc` | une instance dans la région de Paris |
| `arn:aws:s3:::galerie-camille` | un bucket : ni région ni compte, son nom est unique au monde |
| `arn:aws:s3:::galerie-camille/*` | tous les objets de ce bucket |

## Clés d'accès et identifiants temporaires

Pour qu'un programme accède à AWS, la solution qui vient spontanément à l'esprit est de créer un utilisateur IAM, de lui générer une clé d'accès et de l'écrire dans un fichier de configuration. C'est aussi la principale source de fuites. Une étude publiée en 2019 a trouvé des secrets exposés dans plus de 100 000 dépôts GitHub publics, et des milliers de nouveaux chaque jour, dont des clés AWS[^git]. AWS surveille d'ailleurs GitHub : lors d'un test, une clé publiée volontairement a été mise en quarantaine par AWS en une dizaine de secondes[^unit42].

<Schema svg={cleRole} num="2.4" alt="À gauche, une clé d'accès écrite dans app.py part dans un dépôt public par git push, où n'importe qui peut la copier ; elle est permanente. À droite, AWS STS délivre des identifiants temporaires à une instance EC2 qui signe avec eux ses requêtes vers un bucket S3.">
  Deux manières de donner à une application l'accès à S3 : une clé écrite dans le code, ou un rôle et des identifiants temporaires.
</Schema>

Une clé permanente, reconnaissable à son préfixe `AKIA`, reste valable jusqu'à ce que quelqu'un la désactive, et elle porte tous les droits de son propriétaire. Un identifiant temporaire, préfixé `ASIA`, expire au bout de quelques heures et ne porte que les droits du rôle. Avec un rôle, il n'y a tout simplement plus rien à voler dans le code.

## Les bonnes pratiques IAM

AWS les résume ainsi[^bp] :

- appliquer le **moindre privilège** : n'accorder que les droits nécessaires à la tâche, en partant de droits restreints que l'on élargit si besoin ;
- attribuer les droits à des **groupes**, pas à des utilisateurs un par un ;
- préférer les **rôles** et les identifiants temporaires aux clés d'accès ;
- exiger la **MFA** pour toutes les personnes ;
- utiliser la **fédération d'identités** (IAM Identity Center) en entreprise ;
- **supprimer** les utilisateurs, clés et droits inutilisés ;
- séparer les environnements (développement, production) dans des **comptes distincts**.

Et ne jamais versionner une clé d'accès dans un dépôt Git.

## Les outils IAM

| Outil | Usage |
|---|---|
| IAM Policy Simulator | tester l'effet d'une stratégie sans exécuter l'action |
| IAM Access Analyzer | repérer les ressources accessibles depuis l'extérieur, générer une stratégie à partir de l'activité réelle |
| Dernier accès (*last accessed*) | savoir quels services une identité a utilisés, et donc quels droits sont superflus |
| CloudTrail | journal des appels d'API : qui, quoi, quand, d'où (90 jours consultables gratuitement) |

## Le réseau : VPC

Un **VPC** (*Virtual Private Cloud*) est un réseau virtuel privé, isolé, propre au compte, dans une région. On lui donne une plage d'adresses en notation CIDR, par exemple `10.0.0.0/16`, puis on y crée des sous-réseaux, des tables de routage et des passerelles. Les instances EC2, les bases RDS et les répartiteurs de charge sont toujours placés dans un VPC. Un compte peut en contenir plusieurs, cinq par région par défaut.

Chaque région possède un **VPC par défaut**, créé automatiquement : plage `172.31.0.0/16`, un sous-réseau public par zone de disponibilité, une passerelle Internet déjà attachée. C'est lui que l'on utilise dans ce cours ; en entreprise, on construit ses propres VPC.

## Sous-réseaux et accès à Internet

Un **sous-réseau** est une portion de la plage du VPC, par exemple `10.0.1.0/24`, située dans **une seule** zone de disponibilité. Il est dit **public** si sa table de routage envoie le trafic vers une passerelle Internet, **privé** sinon : une ressource d'un sous-réseau privé n'est pas joignable depuis Internet.

- La **passerelle Internet** (*Internet Gateway*) relie le VPC à Internet ; elle est gratuite.
- La **NAT Gateway** permet aux ressources d'un sous-réseau privé de sortir vers Internet (pour télécharger des mises à jour, par exemple) sans être joignables ; elle coûte environ 0,045 dollar par heure plus 0,045 dollar par gigaoctet traité en `us-east-1`[^vpc-prix].
- Chaque adresse IPv4 publique est facturée 0,005 dollar par heure.

<Schema svg={topologie} num="2.5" alt="Une région eu-west-3, un VPC 10.0.0.0/16 avec une passerelle Internet, deux zones de disponibilité. Dans chaque zone, un sous-réseau public avec un serveur web et un sous-réseau privé avec une base de données. Une NAT Gateway dans le sous-réseau public de la zone a permet la sortie de la base de données.">
  Une topologie réseau type : les serveurs web dans des sous-réseaux publics, les bases de données dans des sous-réseaux privés, sur deux zones.
</Schema>

## La notation CIDR

| Notation | Signification | Nombre d'adresses |
|---|---|---|
| `10.0.0.0/16` | plage d'un VPC | 65 536 |
| `10.0.1.0/24` | plage d'un sous-réseau | 256, dont 251 utilisables |
| `203.0.113.25/32` | une seule adresse | 1 |
| `0.0.0.0/0` | toutes les adresses IPv4 | |
| `::/0` | toutes les adresses IPv6 | |

Le nombre après la barre indique combien de bits de l'adresse sont fixés : plus il est grand, plus la plage est petite. AWS réserve cinq adresses dans chaque sous-réseau (le réseau, le routeur, le DNS, une adresse réservée et la diffusion), d'où les 251 adresses utilisables d'un `/24`.

## Les Security Groups

Un **Security Group** est un pare-feu virtuel attaché à l'interface réseau d'une ressource : une instance, une base RDS, un répartiteur de charge[^sg]. Il est composé de règles qui indiquent un protocole, un port ou une plage de ports, et une source (une plage d'adresses ou un autre Security Group).

Son comportement tient en quelques propriétés :

- il ne contient que des **autorisations** : tout ce qui n'est pas explicitement autorisé est bloqué ;
- par défaut, tout trafic **entrant** est refusé et tout trafic **sortant** autorisé ;
- il est **à état** (*stateful*) : la réponse à une connexion autorisée est autorisée d'office, sans règle à écrire ;
- les modifications s'appliquent immédiatement ;
- une ressource peut avoir plusieurs Security Groups, dont les règles s'additionnent.

<Schema svg={securityGroup} num="2.6" alt="Une instance EC2 dans le Security Group sg-web-camille. Les internautes atteignent les ports 80 et 443. Votre poste atteint le port 22 et la réponse repart d'office. Un robot de balayage est bloqué sur le port 22. Le trafic sortant est autorisé. Un tableau rappelle les trois règles entrantes.">
  Le Security Group d'un serveur web : le site est ouvert à tous, l'administration par SSH à une seule adresse.
</Schema>

Une source peut aussi être un autre Security Group. Dans une application à deux niveaux, on autorise ainsi le port de la base de données « depuis le Security Group des serveurs web » plutôt que depuis une plage d'adresses : tout serveur web ajouté plus tard à ce groupe pourra joindre la base, et rien d'autre ne le pourra.

## Security Groups et NACL

Les VPC disposent d'un second mécanisme de filtrage, les listes de contrôle d'accès réseau (*Network ACL*).

| | Security Group | Network ACL |
|---|---|---|
| Portée | interface réseau (instance) | sous-réseau entier |
| Règles | autorisations uniquement | autorisations et interdictions |
| État | à état | sans état : le trafic retour doit être autorisé |
| Évaluation | toutes les règles | par numéro, la première règle qui correspond |
| Par défaut | entrant refusé, sortant autorisé | NACL par défaut : tout est autorisé |

En pratique, l'essentiel du filtrage se fait dans les Security Groups ; les NACL servent à poser des interdictions larges au niveau d'un sous-réseau, par exemple bloquer une plage d'adresses malveillante.

## Les bonnes pratiques réseau

- N'ouvrir que les ports nécessaires.
- Limiter SSH (port 22) à une adresse précise, jamais à `0.0.0.0/0`.
- Placer les bases de données dans des sous-réseaux privés.
- Entre les niveaux d'une application, utiliser un Security Group comme source plutôt qu'une plage d'adresses.
- Envisager Session Manager (service Systems Manager), qui permet d'administrer une instance sans aucun port SSH ouvert.

Laisser SSH ouvert à tous est dangereux parce qu'Internet est balayé en permanence : dès 2013, l'outil ZMap montrait qu'une seule machine bien connectée parcourt tout l'espace IPv4 en moins de 45 minutes[^zmap]. Une instance dont le port 22 est ouvert au monde reçoit des tentatives de connexion très peu de temps après son lancement.

Le TP 2 met tout cela en pratique : vous créerez un utilisateur aux droits volontairement étroits, vous vérifierez qu'il ne peut rien faire de plus, puis vous préparerez le Security Group de votre futur serveur web.

[^iam]: AWS, *What is IAM?*, IAM User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html).
[^mfa-root]: AWS, « AWS IAM now enforces MFA for root users across all account types », 2025, [aws.amazon.com](https://aws.amazon.com/about-aws/whats-new/2025/06/aws-iam-mfa-root-users-across-all-account-types/).
[^bp]: AWS, *Security best practices in IAM*, IAM User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).
[^roles-ec2]: AWS, *IAM roles for Amazon EC2*, Amazon EC2 User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html).
[^version]: AWS, *IAM JSON policy elements: Version*, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_version.html).
[^eval]: AWS, *Policy evaluation logic*, IAM User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html).
[^arn]: AWS, *Identify AWS resources with Amazon Resource Names (ARNs)*, [docs.aws.amazon.com](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html).
[^git]: M. Meli, M. R. McNiece et B. Reaves, « How Bad Can It Git? Characterizing Secret Leakage in Public GitHub Repositories », *NDSS Symposium*, 2019, [ndss-symposium.org](https://www.ndss-symposium.org/ndss-paper/how-bad-can-it-git-characterizing-secret-leakage-in-public-github-repositories/).
[^unit42]: Unit 42, Palo Alto Networks, « From Exposure to Lockdown: How AWS Neutralizes Compromised IAM Credentials through Managed Policies », [unit42.paloaltonetworks.com](https://unit42.paloaltonetworks.com/detecting-exposed-aws-iam-credentials/).
[^vpc-prix]: AWS, *Amazon VPC pricing*, [aws.amazon.com](https://aws.amazon.com/vpc/pricing/).
[^sg]: AWS, *Control traffic to your AWS resources using security groups*, Amazon VPC User Guide, [docs.aws.amazon.com](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html).
[^zmap]: Z. Durumeric, E. Wustrow et J. A. Halderman, « ZMap: Fast Internet-Wide Scanning and its Security Applications », *USENIX Security Symposium*, 2013, [usenix.org](https://www.usenix.org/conference/usenixsecurity13/technical-sessions/paper/durumeric).
