---
title: "Projet final : la galerie"
sidebar_label: "Le projet"
description: "Cahier des charges, architecture et fonctionnement de l'application du projet final : Nginx, Gunicorn, Flask et boto3 sur EC2, fichiers dans S3, rôle IAM, Security Group."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import projetArchitecture from '@site/src/figures/projet-architecture.svg';
import projetRequete from '@site/src/figures/projet-requete.svg';
import architectureCible from '@site/src/figures/architecture-cible.svg';
import projetRepartition from '@site/src/figures/projet-repartition.svg';
import projetBeanstalk from '@site/src/figures/projet-beanstalk.svg';
import Telechargement from '@site/src/components/Telechargement';

<Seance items={['Module 5', 'Le projet']} />

Toutes les pièces sont sur la table. Vous savez lancer une instance et la protéger par un Security Group, vous avez un bucket privé, et un rôle qui permet à une instance d'y lire et d'y écrire sans aucune clé. Il reste à les assembler en une application que n'importe qui peut utiliser depuis son navigateur, et que vous êtes capable d'expliquer pièce par pièce.

L'application s'appelle **la galerie**. C'est une page web où l'on dépose des fichiers, qui les range dans votre bucket S3 et affiche la liste de ceux qu'il contient, avec un aperçu pour les images et un lien de téléchargement pour chacun. Le code vous est fourni : l'objet du projet n'est pas de programmer, mais de déployer proprement.

<Telechargement fichier="kits/galerie.tar.gz">Télécharger l'application (galerie.tar.gz)</Telechargement>

## Le cahier des charges

**Ce que l'application doit faire.** Un visiteur peut déposer un fichier de 10 Mo au plus, voir la liste des fichiers déposés, et télécharger chacun d'eux.

**Ce qui doit être vrai de votre déploiement.**

- L'application est joignable par n'importe qui sur Internet, en HTTP (port 80) et en HTTPS (port 443).
- Personne d'autre que vous ne peut se connecter à l'instance en SSH.
- L'application elle-même n'est pas exposée directement : seul le serveur web frontal l'est.
- Le bucket reste privé. Les fichiers ne sont téléchargeables que par des liens présignés, valables quelques minutes.
- Aucune clé d'accès AWS n'existe sur l'instance, ni dans le code, ni dans un fichier de configuration.
- Le rôle de l'instance n'a que les droits nécessaires : lister le bucket, y lire et y écrire des objets. Il ne peut rien supprimer et ne voit aucun autre bucket.
- L'application redémarre toute seule si elle plante, et au redémarrage de l'instance.

**Partie 2 : deux serveurs.** Une fois la première partie vérifiée, et si votre compte vous permet de faire tourner deux instances à la fois (c'est le cas d'un compte personnel), la galerie passe derrière un répartiteur de charge.

- La galerie est servie par deux instances, dans deux zones de disponibilité différentes, derrière un Application Load Balancer. Les visiteurs n'utilisent plus qu'une adresse, le nom DNS du répartiteur.
- Les instances n'acceptent plus le trafic web que du répartiteur ; seul le SSH reste ouvert, pour votre adresse.
- L'arrêt de l'une des deux instances n'interrompt pas le service.

## L'architecture

<Schema svg={projetArchitecture} num="5.1" alt="Des visiteurs atteignent en HTTP ou HTTPS, et vous en SSH, la passerelle Internet du VPC par défaut. Dans le sous-réseau public, le Security Group pare-feu-web-<prenom> autorise 80 et 443 pour tous et 22 pour votre adresse. Dans l'instance galerie-<prenom>, Nginx écoute sur les ports 80 et 443 (HTTPS autosigné) et relaie les requêtes à Gunicorn et Flask, qui écoutent sur 127.0.0.1:8000 sous l'utilisateur galerie, lancés par le service systemd galerie avec la configuration /etc/galerie.env. L'instance endosse le rôle role-galerie-<prenom> (List, Get, Put) et l'application parle au bucket privé galerie-<prenom>-<suffixe> (préfixes uploads/ et deploy/) avec boto3.">
  L'architecture du projet, jusqu'aux processus qui tournent dans l'instance.
</Schema>

Vous reconnaissez l'extérieur : le VPC par défaut, le Security Group du TP 2, le rôle et le bucket du TP 4. Ce qui est nouveau se passe à l'intérieur de l'instance. Voici, en résumé, qui y fait quoi :

| Composant | Rôle |
|---|---|
| **Nginx** | serveur frontal sur les ports 80 et 443 : chiffrement TLS, taille maximale des requêtes, relais vers l'application |
| **Gunicorn** | serveur d'application Python, deux processus, à l'écoute sur `127.0.0.1:8000` uniquement |
| **Flask et boto3** | l'application elle-même ; boto3 obtient les identifiants du rôle auprès du service de métadonnées (IMDSv2) |
| **systemd** | service `galerie` : démarrage au boot, relance en cas d'arrêt |
| **l'utilisateur `galerie`** | compte système sans aucun droit d'administration |
| **`/etc/galerie.env`** | la configuration : nom du bucket et région, aucun secret |

Les deux premiers se partagent le travail d'une façon qui mérite qu'on s'y arrête.

**Gunicorn** fait tourner l'application Python, écrite avec le framework Flask. Il lance deux processus qui traitent les requêtes en parallèle. Il n'écoute que sur `127.0.0.1:8000`, c'est-à-dire sur la machine elle-même : même si le Security Group laissait passer le port 8000, personne ne pourrait le joindre depuis l'extérieur.

**Nginx** est le seul programme exposé. Il reçoit les requêtes des visiteurs sur les ports 80 et 443 et les relaie à Gunicorn. Pourquoi ne pas exposer Gunicorn directement ? Parce que Nginx fait très bien des choses que Gunicorn fait mal ou pas du tout : gérer le chiffrement HTTPS, refuser les requêtes trop volumineuses avant qu'elles n'atteignent l'application, supporter des milliers de visiteurs lents sans bloquer les processus Python. C'est une organisation qu'on retrouve dans l'immense majorité des applications web en Python, en Ruby ou en PHP.

Deux autres choix méritent d'être remarqués. L'application tourne sous un utilisateur Linux dédié, `galerie`, qui n'a aucun droit d'administration : si quelqu'un trouvait une faille dans l'application, il n'obtiendrait que les droits de cet utilisateur. C'est le principe de moindre privilège, appliqué cette fois à l'intérieur de la machine. Et c'est **systemd**, le gestionnaire de services d'Amazon Linux, qui lance Gunicorn, le relance s'il plante, et le démarre au boot. Sa configuration tient dans un petit fichier, `/etc/galerie.env`, qui contient le nom du bucket et la région. Rien d'autre, et surtout aucun secret.

## Suivre une requête

Que se passe-t-il exactement quand quelqu'un dépose une photo, puis la télécharge ?

<Schema svg={projetRequete} num="5.2" alt="Diagramme de séquence entre le navigateur, Nginx, Flask avec boto3, le service de métadonnées et le bucket S3. 1 : le navigateur envoie POST /deposer avec la photo ; Nginx relaie à Flask ; boto3 demande les identifiants du rôle au service de métadonnées, qui renvoie des identifiants temporaires mis en cache ; Flask envoie PutObject uploads/... à S3, puis renvoie une redirection 302 vers /. 2 : le navigateur demande GET / ; Flask envoie ListObjectsV2 à S3, signe localement une URL par fichier sans aucun appel réseau, et renvoie la page avec les liens présignés. 3 : le navigateur télécharge le fichier avec l'URL présignée directement chez S3, sans solliciter l'instance.">
  Dépôt, affichage, téléchargement. Remarquez que le téléchargement ne passe pas par l'instance.
</Schema>

Trois détails de ce schéma valent la peine d'être médités.

Au premier appel à S3, `boto3` ne trouve aucune clé dans son environnement. Il interroge alors le service de métadonnées de l'instance, obtient les identifiants temporaires du rôle, et les garde en mémoire jusqu'à ce qu'ils approchent de leur expiration. Le code de l'application ne contient pas une ligne sur le sujet :

```python title="app.py (extrait)"
s3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)
```

Pour afficher la liste, l'application fabrique une URL présignée par fichier. Cette opération ne coûte aucun appel réseau : c'est un simple calcul de signature, fait sur l'instance avec les identifiants du rôle. Une page de cent fichiers ne génère donc qu'une seule requête vers S3, celle qui liste le bucket.

```python title="app.py (extrait)"
def lien_presigne(cle: str) -> str:
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": cle}, ExpiresIn=DUREE_LIEN
    )
```

Enfin, quand le visiteur clique sur un lien, son navigateur télécharge le fichier **directement chez S3**. L'instance n'est pas sollicitée, ni sa bande passante, ni ses processeurs. Une petite `t3.micro` peut ainsi servir une galerie dont les fichiers pèsent des gigaoctets.

## Les URL présignées

Le bucket est privé, et il doit le rester. Comment, alors, un visiteur qui n'a aucun compte AWS peut-il télécharger un fichier ? L'application aurait pu lire le fichier dans S3 et le renvoyer elle-même au navigateur, mais chaque téléchargement aurait alors traversé l'instance, en consommant sa bande passante et un processus Gunicorn pendant toute la durée du transfert.

Elle fabrique plutôt une **URL présignée** : l'adresse de l'objet, à laquelle on ajoute le nom de l'identité qui l'a signée, une date d'expiration et une signature calculée avec la clé secrète de cette identité[^presignee]. S3 accepte la requête de n'importe qui présente cette URL, exactement comme si l'identité signataire l'avait faite elle-même, tant que l'URL n'a pas expiré. Quelqu'un qui modifie l'adresse, pour demander un autre fichier ou repousser l'expiration, casse la signature et reçoit `AccessDenied`.

Trois propriétés en découlent :

- l'URL n'autorise que ce que la signataire a le droit de faire : si le rôle perd le droit `s3:GetObject`, toutes les URL déjà distribuées cessent de fonctionner ;
- l'URL est calculée sur l'instance, sans aucun appel à AWS ;
- sa durée de validité est bornée par celle des identifiants qui l'ont signée. Avec une clé d'accès permanente, elle peut atteindre sept jours ; avec les identifiants temporaires d'un rôle, elle expire au plus tard en même temps qu'eux, soit au bout de quelques heures. La galerie demande cinq minutes, ce qui est bien en deçà.

## HTTPS sans nom de domaine

Le cahier des charges demande HTTPS. Pour chiffrer, Nginx a besoin d'un **certificat**, qui atteste l'identité du serveur. Les autorités de certification reconnues par les navigateurs délivrent des certificats pour un **nom de domaine** qu'on possède, pas pour une adresse IP d'AWS qui change à chaque redémarrage. Faute de nom de domaine, vous fabriquerez un certificat **autosigné** : la connexion sera bel et bien chiffrée, mais le navigateur affichera un avertissement, parce que personne d'autre que vous ne se porte garant de ce certificat.

En production, on achète un nom de domaine, puis on obtient un certificat reconnu. Sur AWS, le plus simple est de placer devant l'application un répartiteur de charge ou la distribution CloudFront, et de laisser AWS Certificate Manager fournir et renouveler le certificat gratuitement. Sans service AWS supplémentaire, l'autorité de certification Let's Encrypt en délivre aussi gratuitement.

## Deux serveurs derrière un répartiteur

Avec une seule instance, le moindre redémarrage interrompt la galerie, et la panne d'une zone de disponibilité l'emporte entièrement. La réponse classique consiste à faire tourner plusieurs copies identiques du serveur, dans des zones différentes, et à placer devant elles un **répartiteur de charge** (*load balancer*), qui reçoit les requêtes des visiteurs et les distribue aux copies en bonne santé.

### Les répartiteurs d'AWS

Le service Elastic Load Balancing distribue le trafic entrant entre plusieurs cibles, instances EC2, conteneurs ou adresses IP, dans une ou plusieurs zones de disponibilité. Il surveille la santé des cibles, n'envoie de requêtes qu'à celles qui vont bien, et ajuste tout seul sa propre capacité au trafic[^elb]. Il propose quatre types de répartiteurs, qui ne travaillent pas au même niveau du réseau.

| Type | Couche (modèle OSI) | Ce qu'il comprend | Usage typique |
|---|---|---|---|
| **Application Load Balancer** (ALB) | 7, application | les requêtes HTTP, HTTPS et gRPC : chemin, nom d'hôte, en-têtes | sites et API web ; c'est celui du projet |
| **Network Load Balancer** (NLB) | 4, transport | les connexions TCP, UDP et TLS, sans lire leur contenu | très gros débit (des millions de requêtes par seconde), adresse IP fixe par zone |
| **Gateway Load Balancer** (GWLB) | 3, réseau | tous les paquets IP, sur tous les ports | faire passer le trafic par des appliances virtuelles, des pare-feu par exemple |
| **Classic Load Balancer** (CLB) | 4 et 7 | la génération précédente | aucun nouveau projet ; AWS recommande de migrer |

L'ALB fonctionne à la couche application : pour chaque requête, il évalue les règles de son écouteur et choisit une cible dans le groupe correspondant[^alb]. Il peut donc envoyer `/api` à un groupe de serveurs et le reste à un autre, ou distinguer deux noms de domaine. Le NLB travaille à la couche transport ; il relaie des connexions sans les ouvrir, ce qui le rend très rapide, et il peut recevoir une adresse IP Elastic par sous-réseau, pratique quand un client doit inscrire l'adresse du service dans son pare-feu[^nlb]. Le GWLB, à la couche réseau, sert à intercaler des appliances virtuelles, pare-feu ou systèmes de détection d'intrusion, sur le chemin du trafic ; il échange les paquets avec elles par le protocole GENEVE, sur le port 6081[^gwlb]. Le Classic Load Balancer est l'ancienne génération, qu'AWS recommande de remplacer par l'un des trois autres[^elb].

### Écouteur, groupe cible, contrôle de santé

Un ALB s'organise en trois pièces. L'**écouteur** (*listener*) attend les connexions sur un port et un protocole, ici HTTP sur le port 80. Ses règles renvoient vers un **groupe cible** (*target group*), la liste des serveurs qui reçoivent les requêtes, ici vos deux instances, sur leur port 80, celui de Nginx. Le groupe cible fait aussi le **contrôle de santé** (*health check*) : à intervalle régulier, il demande une page à chaque cible et ne lui envoie du trafic que si elle répond correctement.

Les réglages par défaut d'un groupe cible d'instances sont un contrôle toutes les 30 secondes, un délai de réponse de 5 secondes, le code `200` comme seule réponse correcte, 2 échecs consécutifs pour déclarer une cible en mauvaise santé et 5 succès consécutifs pour la réintégrer[^sante]. Une instance qui tombe peut donc recevoir des requêtes pendant une minute environ avant d'être écartée, et une instance réparée attend deux minutes et demie avant de revenir. La galerie a déjà ce qu'il faut : sa route `/sante` répond `200` quand l'application tourne et atteint son bucket, et `503` sinon. Quand on retire une cible, le répartiteur cesse de lui envoyer de nouvelles requêtes mais laisse les requêtes en cours se terminer, pendant 300 secondes au plus par défaut (*deregistration delay*)[^attributs].

Un ALB doit être placé dans au moins deux zones de disponibilité, avec un sous-réseau dans chacune[^alb-creation]. Il répartit par défaut les requêtes entre les cibles de toutes les zones, et non seulement celles de la zone où la requête est arrivée : c'est la répartition entre zones (*cross-zone load balancing*), toujours active au niveau d'un ALB[^alb-creation].

### Pourquoi la galerie supporte d'être dupliquée

Le répartiteur peut envoyer deux requêtes successives d'un même visiteur à deux instances différentes. Cela ne marche que si aucune instance ne garde pour elle une information dont l'autre aurait besoin. C'est le cas de la galerie : les fichiers et leur liste sont dans S3, l'application ne garde aucune session, et chaque instance obtient ses propres identifiants du rôle. Les deux copies sont donc interchangeables. Une application qui rangerait les fichiers déposés sur le disque de l'instance, ou qui garderait les paniers des clients en mémoire, perdrait la moitié de ses données à chaque requête ; il faudrait d'abord déplacer cet état vers un service partagé, S3, une base de données ou un cache.

Pour fabriquer la seconde instance, on ne réinstalle rien. On prend une **image** (AMI) de la première, qui contient son disque tel qu'il est, avec Nginx, l'application, sa configuration et le service systemd, et on lance la seconde à partir de cette image. Seul le rôle IAM ne fait pas partie de l'image : il faut l'associer à la nouvelle instance.

### L'architecture de la partie 2

<Schema svg={projetRepartition} num="5.4" alt="Des visiteurs atteignent en HTTP, à l'adresse du nom DNS du répartiteur, l'Application Load Balancer alb-galerie-<prenom>, protégé par le Security Group repartiteur-<prenom> qui autorise le port 80 pour tous. Son groupe cible cibles-galerie-<prenom>, avec un contrôle de santé sur /sante, envoie les requêtes à deux instances : galerie-<prenom> dans la zone a et galerie2-<prenom> dans la zone b de la région du compte. Les deux instances sont dans le Security Group pare-feu-web-<prenom>, qui autorise le port 80 depuis le répartiteur seulement et le port 22 depuis votre adresse. Elles endossent le rôle role-galerie-<prenom> et écrivent avec boto3 dans le bucket galerie-<prenom>-<suffixe>.">
  La galerie sur deux instances, dans deux zones, derrière un Application Load Balancer.
</Schema>

Le Security Group des instances change de nature. Sa règle HTTP n'a plus pour source une plage d'adresses, mais un autre Security Group, celui du répartiteur : seules les machines qui portent ce groupe, c'est-à-dire les nœuds du répartiteur, peuvent joindre le port 80 des instances[^sg-reference]. On ne connaît pas à l'avance les adresses de ces nœuds, qui changent quand le répartiteur s'agrandit ou se réduit ; la référence à un groupe suit ces changements toute seule.

Le répartiteur reste en HTTP. Pour qu'il accepte le HTTPS, il lui faudrait un certificat délivré par AWS Certificate Manager, qui ne délivre de certificat public que pour un nom de domaine dont on prouve qu'on le contrôle[^acm]. Le certificat autosigné de la première partie reste sur les instances, mais le port 443 n'est plus joignable depuis Internet.

Un ALB se paie à l'heure, plus une part qui dépend du trafic, mesurée en unités de capacité (LCU). L'exemple de la page de tarification, en Virginie du Nord, donne 0,0225 $ par heure et 0,008 $ par LCU et par heure, soit 0,031 $ par heure pour un site modeste[^prix-elb]. Une séance de TP de trois heures coûte donc une dizaine de centimes, prélevés sur les crédits d'un compte personnel. Laissé allumé un mois, le répartiteur coûterait plus de 20 $, sans compter les deux instances.

## Redéployer avec Elastic Beanstalk

Dans les deux premières parties, vous avez tout monté à la main : l'installation de Python et de Nginx, le service systemd, l'utilisateur dédié, puis l'image, la seconde instance, le groupe cible, le répartiteur et ses Security Groups. AWS Elastic Beanstalk fait tout cela à partir d'une simple archive zip. On lui donne le code de l'application et on choisit une plateforme, ici Python 3.12 sur Amazon Linux 2023 ; il crée les instances, le groupe Auto Scaling, le répartiteur et les Security Groups, installe Nginx et Gunicorn sur les instances et y déploie le code. C'est un service de type PaaS (*Platform as a Service*) : vous fournissez l'application, AWS s'occupe de la plateforme qui la fait tourner.

Le service lui-même est gratuit. On ne paie que les ressources qu'il crée, instances, répartiteur et stockage[^eb-prix]. Un environnement qui reprend l'architecture de la partie 2 coûte donc exactement ce qu'elle coûtait.

### Application, version, environnement

Beanstalk organise le travail en quelques objets, qu'on retrouve dans sa console.

| Objet | Ce que c'est | Dans le projet |
|---|---|---|
| Application | le dossier qui regroupe tout le reste | `galerie-<prenom>` |
| Version d'application | une archive zip déposée, avec une étiquette | `v1`, puis `v2` |
| Environnement | les ressources qui font tourner une version : instances, répartiteur, etc. | `galerie-<prenom>-env` |
| Plateforme | le système et les logiciels installés sur les instances | Python 3.12 sur Amazon Linux 2023 |

Un environnement est soit à **instance unique** (une instance avec une adresse Elastic IP, dans un groupe Auto Scaling bloqué à une instance, sans répartiteur), soit **avec répartiteur** (*load balanced*), plusieurs instances derrière un Elastic Load Balancer[^eb-types]. Le premier convient au développement ; le second, que vous utiliserez, reproduit la partie 2.

Beanstalk ne crée pas les ressources lui-même. Il décrit l'environnement dans un modèle et confie sa création à AWS CloudFormation, le service qui fabrique des ressources à partir d'une description écrite. Chaque environnement est une pile (*stack*) CloudFormation, que l'on peut ouvrir pour voir la liste exacte de ce qui a été créé[^eb-lt]. Les versions de l'application, elles, sont rangées dans un bucket que Beanstalk crée dans chaque région où il sert, nommé `elasticbeanstalk-<région>-<compte>`[^eb-s3].

<Schema svg={projetBeanstalk} num="5.5" alt="Vous envoyez une archive zip à Elastic Beanstalk, application galerie-<prenom>, qui range les versions v1 et v2 dans un bucket et crée une pile CloudFormation. Cette pile contient un Application Load Balancer, qui reçoit les visiteurs et fait un contrôle de santé sur /sante, et un groupe Auto Scaling de deux instances t3.micro, une dans chacune des zones a et b, qui font tourner Nginx et Gunicorn. Les instances téléchargent la version depuis le bucket des versions, endossent le rôle role-galerie-<prenom> complété de la stratégie WebTier, et lisent et écrivent les fichiers dans le bucket galerie-<prenom>-<suffixe> avec boto3.">
  La galerie redéployée par Elastic Beanstalk, avec l'architecture de la partie 2, créée à partir d'une archive.
</Schema>

### Ce que l'archive doit contenir

L'archive de la partie 3 contient l'application, inchangée (`app.py`, `templates/`, `requirements.txt`), et trois fichiers qui disent à Beanstalk comment la faire tourner. Ils remplacent ce que vous aviez fait à la main dans la partie 1.

- `Procfile` contient la commande qui lance l'application, `web: gunicorn --bind :8000 --workers 2 app:app`. Sur la plateforme Python, Nginx relaie les requêtes vers le port 8000, celui que Gunicorn doit donc écouter[^eb-procfile]. C'est l'équivalent de la ligne `ExecStart` du service systemd.
- `.platform/nginx/conf.d/taille.conf` complète la configuration de Nginx installée par Beanstalk, qui inclut les fichiers de ce dossier dans son bloc `http`[^eb-nginx]. Il contient une seule ligne, `client_max_body_size 20M;`, sans laquelle Nginx refuserait tout fichier de plus d'un mégaoctet. C'est le réglage que contenait déjà `galerie-nginx.conf`.
- `.ebextensions/galerie.config` fixe deux options de l'environnement, IMDSv2 obligatoire sur les instances et `/sante` comme page du contrôle de santé.

Le nom du bucket et sa région ne sont pas dans l'archive. Ce sont des **propriétés d'environnement**, que Beanstalk transmet à l'application sous forme de variables d'environnement, comme le faisait `/etc/galerie.env`. Une même archive peut ainsi servir à tous les étudiants.

Deux contraintes viennent d'AWS. Les instances endossent un **profil d'instance**, obligatoire, qui doit permettre de télécharger les versions depuis le bucket de Beanstalk et d'y écrire les journaux, ce que permet la stratégie gérée `AWSElasticBeanstalkWebTier`[^eb-profil]. Vous l'ajouterez à `role-galerie-<prenom>`, qui garde ainsi son accès au bucket de la galerie. Et depuis le 1er octobre 2024, Auto Scaling n'accepte plus les configurations de lancement pour les comptes créés après cette date. L'environnement doit donc utiliser un modèle de lancement, ce que l'on obtient par exemple en désactivant IMDSv1 ou en choisissant des volumes `gp3`[^eb-lt].

### Déployer une nouvelle version

Le grand intérêt de Beanstalk apparaît au deuxième déploiement. On dépose une nouvelle archive, on lui donne une étiquette, et on demande à l'environnement de passer à cette version. La **politique de déploiement** décide de la façon dont les instances sont mises à jour[^eb-deploiement].

| Politique | Ce qui se passe | Interruption |
|---|---|---|
| All at once | toutes les instances reçoivent la nouvelle version en même temps | oui, brève |
| Rolling | les instances sont mises à jour par lots ; chaque lot sort du répartiteur pendant sa mise à jour | non, mais capacité réduite |
| Rolling with additional batch | comme Rolling, après avoir lancé un lot supplémentaire | non, capacité maintenue |
| Immutable | un jeu complet de nouvelles instances, dans un groupe Auto Scaling à part | non |
| Traffic splitting | comme Immutable, avec une part du trafic envoyée d'abord à la nouvelle version | non |

Par défaut, un environnement déploie tout d'un coup (*All at once*). Vous choisirez *Rolling* par lots d'une instance, si bien que pendant la mise à jour de l'une, l'autre continue de servir la galerie. Revenir en arrière est un nouveau déploiement, celui de l'ancienne version, qui reste disponible dans l'application.

### Ce que l'on gagne, ce que l'on cède

Avec Beanstalk, la configuration de la galerie tient dans quelques fichiers et quelques choix de console ; un nouvel environnement identique se recrée en quelques minutes, et un déploiement ne demande plus de se connecter aux instances. En contrepartie, c'est Beanstalk qui décide de l'organisation des instances ; on ne choisit plus l'utilisateur sous lequel tourne l'application, ni l'emplacement de ses fichiers, et la pile CloudFormation contient des ressources qu'on n'a pas demandées une à une. Ce que vous avez appris dans les parties 1 et 2 reste nécessaire, car c'est ce qui permet de comprendre ce que Beanstalk a créé, et de réparer un environnement qui ne démarre pas.

Sur le compte fourni par l'enseignant, cette partie se fait en démonstration. Pour créer un environnement, l'utilisateur doit avoir lui-même le droit de créer toutes les ressources sous-jacentes, instances, groupes Auto Scaling, répartiteurs, piles CloudFormation, et AWS indique qu'on ne sait pas l'empêcher ensuite de créer d'autres ressources dans ces services[^eb-droits]. Ce n'est pas compatible avec les garde-fous du compte partagé.

## Ce que ce projet ne fait pas

Votre galerie est sécurisée, mais elle a des limites qu'il faut savoir nommer. Après la première partie, elle tourne sur une seule instance, dans une seule zone : un redémarrage, et à plus forte raison la panne de la zone, interrompt le service. La seconde partie lève cette limite, pas les suivantes : il faut toujours lancer une nouvelle instance à la main quand l'une tombe, et le nombre d'instances ne suit pas le trafic. Son adresse IP change à chaque arrêt de l'instance, tant qu'elle n'est pas derrière un répartiteur. N'importe qui peut déposer des fichiers, sans compte ni limite de nombre. Le bucket n'est pas versionné, donc un fichier remplacé est perdu. Rien ne surveille l'application ni ne vous prévient si elle tombe. Et l'infrastructure a été créée à la main, dans la console, ce qui la rend difficile à reproduire à l'identique.

<Schema svg={architectureCible} num="5.3" alt="Architecture cible. Les utilisateurs résolvent le nom de l'application avec Route 53, puis atteignent un Application Load Balancer dans le VPC de la région eu-west-3. Celui-ci répartit les requêtes entre des instances EC2 d'un groupe Auto Scaling réparti sur deux zones de disponibilité. Une base RDS principale est répliquée de façon synchrone vers une base de secours dans l'autre zone. Les instances écrivent les fichiers dans S3 et envoient leurs métriques à CloudWatch.">
  Une architecture qui résisterait à la panne d'une instance, et même d'une zone entière.
</Schema>

Chacune de ces limites a une réponse sur AWS : un groupe Auto Scaling qui maintient le nombre d'instances derrière le répartiteur et l'ajuste au trafic, un nom de domaine avec Route 53, une authentification avec Cognito, le versionnage du bucket, des alarmes CloudWatch, CloudFormation ou Terraform pour décrire l'infrastructure dans des fichiers. Ce sont les étapes suivantes, au-delà de ce cours. Pour les aborder avec méthode, AWS publie le *Well-Architected Framework*, qui passe en revue une architecture selon six piliers : excellence opérationnelle, sécurité, fiabilité, efficacité des performances, optimisation des coûts et durabilité[^wa].

## Ce que vous rendrez

Chaque exigence du cahier des charges se prouve par une observation précise. Le TP détaille les commandes ; le tableau suivant les résume.

| Exigence | Vérification |
|---|---|
| Application publique | `http://IP` et `https://IP` répondent |
| SSH restreint | le port 22 est fermé quand on le teste depuis CloudShell |
| Application non exposée | le port 8000 est fermé ; sur l'instance, `ss -ltn` montre `127.0.0.1:8000` |
| Bucket privé | l'adresse directe d'un objet renvoie `AccessDenied` ; l'URL présignée fonctionne, puis expire |
| Aucune clé | pas de dossier `~/.aws`, aucune clé dans l'application ni dans sa configuration |
| Moindre privilège | `aws s3 rm` est refusé |
| Résilience | l'application revient après un `kill -9` et après un redémarrage de l'instance |
| Partie 2 : deux serveurs | le nom DNS du répartiteur sert la galerie, et le pied de page alterne entre deux identifiants d'instance, dans deux zones |
| Partie 2 : instances fermées | `http://IP` d'une instance ne répond plus ; le Security Group n'autorise le port 80 que depuis `repartiteur-<prenom>` |
| Partie 2 : panne d'une instance | le service de l'une est arrêté, le site répond toujours, et le groupe cible la montre `unhealthy` |

À la fin du module, votre enseignant vérifiera avec vous les points suivants :

1. L'adresse publique de votre galerie, qui fonctionne en HTTP et en HTTPS, avec au moins une image déposée et affichée.
2. La preuve que le port 22 est fermé à tout autre que vous, et que le port 8000 n'est joignable par personne.
3. La preuve que le bucket est privé : l'adresse directe d'un objet renvoie `AccessDenied`, le lien présigné fonctionne, puis expire.
4. La preuve qu'aucune clé d'accès n'existe sur l'instance, et que le rôle ne peut pas supprimer d'objet.
5. Si vous avez fait la seconde partie : la galerie servie par le répartiteur, l'alternance des deux instances, et le site qui continue de répondre quand l'une est arrêtée.
6. La réponse, à l'oral, à deux questions tirées au hasard parmi celles des TP.

[^presignee]: AWS, *Download and upload objects with presigned URLs*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).
[^wa]: AWS, *AWS Well-Architected Framework*, [docs.aws.amazon.com](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html).
[^elb]: AWS, « What is Elastic Load Balancing? », *Elastic Load Balancing User Guide*, [docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html).
[^alb]: AWS, « What is an Application Load Balancer? », *User Guide for Application Load Balancers*, [docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html).
[^nlb]: AWS, « What is a Network Load Balancer? », *User Guide for Network Load Balancers*, [docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html).
[^gwlb]: AWS, « What is a Gateway Load Balancer? », *User Guide for Gateway Load Balancers*, [docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html).
[^sante]: AWS, « Health checks for Application Load Balancer target groups », *User Guide for Application Load Balancers*, [docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html).
[^attributs]: AWS, « Edit target group attributes for your Application Load Balancer », section *Deregistration delay*, [docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html).
[^alb-creation]: AWS, « Application Load Balancers », *User Guide for Application Load Balancers*, sections *Availability Zones* et *Cross-zone load balancing*, [docs.aws.amazon.com/elasticloadbalancing/latest/application/application-load-balancers.html](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/application-load-balancers.html).
[^sg-reference]: AWS, « Security group rules », *Amazon VPC User Guide*, [docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html).
[^acm]: AWS, « AWS Certificate Manager public certificates », *AWS Certificate Manager User Guide*, [docs.aws.amazon.com/acm/latest/userguide/acm-public-certificates.html](https://docs.aws.amazon.com/acm/latest/userguide/acm-public-certificates.html).
[^prix-elb]: AWS, « Elastic Load Balancing pricing », exemple de tarification d'un Application Load Balancer, [aws.amazon.com/elasticloadbalancing/pricing](https://aws.amazon.com/elasticloadbalancing/pricing/).
[^eb-prix]: AWS, « AWS Elastic Beanstalk pricing », [aws.amazon.com/elasticbeanstalk/pricing](https://aws.amazon.com/elasticbeanstalk/pricing/).
[^eb-types]: AWS, « Environment types », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features-managing-env-types.html).
[^eb-lt]: AWS, « Migrating your Elastic Beanstalk environment to launch templates », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/environments-cfg-autoscaling-launch-templates.html).
[^eb-s3]: AWS, « Using Elastic Beanstalk with Amazon S3 », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/AWSHowTo.S3.html).
[^eb-procfile]: AWS, « Configuring the WSGI server with a Procfile on Elastic Beanstalk », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/python-configuration-procfile.html).
[^eb-nginx]: AWS, « Reverse proxy configuration », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/platforms-linux-extend.proxy.html).
[^eb-profil]: AWS, « Elastic Beanstalk instance profile », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/concepts-roles-instance.html).
[^eb-deploiement]: AWS, « Deployment policies and settings », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.rolling-version-deploy.html).
[^eb-droits]: AWS, « Managing Elastic Beanstalk user policies », *AWS Elastic Beanstalk Developer Guide*, [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/AWSHowTo.iam.managed-policies.html).
