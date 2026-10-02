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

## L'architecture

<Schema svg={projetArchitecture} num="5.1" alt="Des visiteurs atteignent en HTTP ou HTTPS, et vous en SSH, la passerelle Internet du VPC par défaut. Dans le sous-réseau public, le Security Group sg-web-<prenom> autorise 80 et 443 pour tous et 22 pour votre adresse. Dans l'instance galerie-<prenom>, Nginx écoute sur les ports 80 et 443 (HTTPS autosigné) et relaie les requêtes à Gunicorn et Flask, qui écoutent sur 127.0.0.1:8000 sous l'utilisateur galerie, lancés par le service systemd galerie avec la configuration /etc/galerie.env. L'instance endosse le rôle role-galerie-<prenom> (List, Get, Put) et l'application parle au bucket privé galerie-<prenom>-<suffixe> (préfixes uploads/ et deploy/) avec boto3.">
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

## Ce que ce projet ne fait pas

Votre galerie est sécurisée, mais elle a des limites qu'il faut savoir nommer. Elle tourne sur une seule instance, dans une seule zone : un redémarrage, et à plus forte raison la panne de la zone, interrompt le service. Son adresse IP change à chaque arrêt de l'instance. N'importe qui peut déposer des fichiers, sans compte ni limite de nombre. Le bucket n'est pas versionné, donc un fichier remplacé est perdu. Rien ne surveille l'application ni ne vous prévient si elle tombe. Et l'infrastructure a été créée à la main, dans la console, ce qui la rend difficile à reproduire à l'identique.

<Schema svg={architectureCible} num="5.3" alt="Architecture cible. Les utilisateurs résolvent le nom de l'application avec Route 53, puis atteignent un Application Load Balancer dans le VPC de la région eu-west-3. Celui-ci répartit les requêtes entre des instances EC2 d'un groupe Auto Scaling réparti sur deux zones de disponibilité. Une base RDS principale est répliquée de façon synchrone vers une base de secours dans l'autre zone. Les instances écrivent les fichiers dans S3 et envoient leurs métriques à CloudWatch.">
  Une architecture qui résisterait à la panne d'une instance, et même d'une zone entière.
</Schema>

Chacune de ces limites a une réponse sur AWS : un groupe d'instances derrière un répartiteur de charge dans plusieurs zones, un nom de domaine avec Route 53, une authentification avec Cognito, le versionnage du bucket, des alarmes CloudWatch, CloudFormation ou Terraform pour décrire l'infrastructure dans des fichiers. Ce sont les étapes suivantes, au-delà de ce cours. Pour les aborder avec méthode, AWS publie le *Well-Architected Framework*, qui passe en revue une architecture selon six piliers : excellence opérationnelle, sécurité, fiabilité, efficacité des performances, optimisation des coûts et durabilité[^wa].

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

À la fin du module, votre enseignant vérifiera avec vous les points suivants :

1. L'adresse publique de votre galerie, qui fonctionne en HTTP et en HTTPS, avec au moins une image déposée et affichée.
2. La preuve que le port 22 est fermé à tout autre que vous, et que le port 8000 n'est joignable par personne.
3. La preuve que le bucket est privé : l'adresse directe d'un objet renvoie `AccessDenied`, le lien présigné fonctionne, puis expire.
4. La preuve qu'aucune clé d'accès n'existe sur l'instance, et que le rôle ne peut pas supprimer d'objet.
5. La réponse, à l'oral, à deux questions tirées au hasard parmi celles des cinq TP.

[^presignee]: AWS, *Download and upload objects with presigned URLs*, [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).
[^wa]: AWS, *AWS Well-Architected Framework*, [docs.aws.amazon.com](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html).
