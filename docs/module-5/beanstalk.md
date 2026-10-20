---
title: "TP 5, partie 3 : Redéployer avec Elastic Beanstalk"
sidebar_label: "Partie 3 : Elastic Beanstalk"
description: "Archive de la galerie pour Elastic Beanstalk, environnement avec répartiteur sur deux zones, ressources créées par la pile CloudFormation, déploiement progressif d'une version 2, retour à la version 1, rangement."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import projetBeanstalk from '@site/src/figures/projet-beanstalk.svg';
import Chemin from '@site/src/components/Chemin';
import Telechargement from '@site/src/components/Telechargement';
import Comptes from '@site/src/components/Comptes';
import TabItem from '@theme/TabItem';

<Seance items={['Module 5', 'Partie 3']} />

:::info[Avant de commencer]
<Comptes>
<TabItem value="personnel" label="Compte personnel AWS">

Cette partie part de ce qui reste après la partie 2 : le bucket `galerie-<prenom>-<suffixe>`, avec les fichiers que vous y avez déposés, et le rôle `role-galerie-<prenom>`. Si vous avez fait tout le rangement de la partie 2, recréez-les d'abord en suivant le [TP 4](../module-4/tp.md), étapes 1 et 5.

Elle consomme autant de crédits que la partie 2 : deux instances, deux adresses IPv4 publiques et un répartiteur. Faites-la d'une traite, et rangez tout à la fin.

</TabItem>
<TabItem value="enseignant" label="Compte fourni par l'enseignant">

Sur le compte du cours, votre enseignant fait cette partie en démonstration, car les droits de votre compte ne permettent pas de créer un environnement Elastic Beanstalk (la section [Redéployer avec Elastic Beanstalk](projet.md#redéployer-avec-elastic-beanstalk) du projet explique pourquoi). Suivez les étapes avec lui, ouvrez sa galerie quand il vous en donne l'adresse, et préparez les réponses aux questions de fin de page.

</TabItem>
</Comptes>
:::

Vous allez redéployer la galerie sans vous connecter à aucune instance. Vous donnerez une archive à Elastic Beanstalk, qui créera lui-même deux instances dans deux zones, le répartiteur et ses Security Groups. Vous déploierez ensuite une version modifiée sans interrompre le service, puis vous reviendrez à la première. Relisez avant la section [Redéployer avec Elastic Beanstalk](projet.md#redéployer-avec-elastic-beanstalk) du projet.

<Schema svg={projetBeanstalk} num="TP5" alt="Vous envoyez une archive zip à Elastic Beanstalk, application galerie-<prenom>, qui range les versions dans un bucket et crée une pile CloudFormation : un Application Load Balancer avec un contrôle de santé sur /sante, et un groupe Auto Scaling de deux instances t3.micro dans les zones a et b. Les instances endossent role-galerie-<prenom> et utilisent le bucket de la galerie.">
  Ce que vous allez faire créer par Elastic Beanstalk.
</Schema>

## 19. Compléter le rôle des instances

Les instances d'un environnement Beanstalk doivent télécharger la version de l'application dans le bucket de Beanstalk et y déposer leurs journaux. Le rôle `role-galerie-<prenom>` ne le permet pas encore, car il n'autorise que le bucket de la galerie.

1. Ouvrez <Chemin>IAM › Roles</Chemin>, puis `role-galerie-<prenom>`.
2. Onglet **Permissions**, puis <Chemin>Add permissions › Attach policies</Chemin>.
3. Cherchez `AWSElasticBeanstalkWebTier`, cochez-la et cliquez sur **Add permissions**.

Le rôle porte maintenant deux stratégies : `galerie-s3-<prenom>`, pour le bucket de la galerie, et `AWSElasticBeanstalkWebTier`, pour le fonctionnement de Beanstalk. Ouvrez la seconde et regardez à quels buckets elle donne accès. Leur nom commence par `elasticbeanstalk-`.

## 20. Récupérer l'archive

Téléchargez l'archive préparée pour Beanstalk.

<Telechargement fichier="kits/galerie-beanstalk.zip">galerie-beanstalk.zip</Telechargement>

Ne la décompressez pas pour la recompresser, car Beanstalk exige que les fichiers soient à la racine de l'archive, et une recompression depuis l'explorateur de fichiers ajoute souvent un dossier englobant ou oublie les dossiers dont le nom commence par un point. Regardez simplement son contenu, par exemple dans un terminal :

```bash title="Votre terminal"
unzip -l galerie-beanstalk.zip
```

Vous y trouvez `app.py`, `templates/` et `requirements.txt`, l'application de la partie 1, sans aucune modification, et trois fichiers pour Beanstalk : `Procfile`, `.platform/nginx/conf.d/taille.conf` et `.ebextensions/galerie.config`. La section [Ce que l'archive doit contenir](projet.md#ce-que-larchive-doit-contenir) du projet explique chacun d'eux.

## 21. Créer l'environnement

Ouvrez <Chemin>Elastic Beanstalk › Environments</Chemin> et cliquez sur **Create environment**. La console présente la création sur une seule page, découpée en sections ; parcourez-la de haut en bas. Seules les valeurs indiquées ci-dessous sont à changer, laissez les autres telles quelles. Si la page vous propose de revenir à l'ancienne console (*old console*), restez sur la nouvelle.

**Deployment mode** : *Standard*. Le mode *Cluster* fait tourner les applications sur Kubernetes (EKS) et ne sert pas ici.

**Environment details**

- **Application name** : `galerie-<prenom>`. Le champ propose les applications existantes ; s'il n'y en a pas, il crée celle-ci.
- **Environment name** : `galerie-<prenom>-env`. Laissez vides **Domain name prefix** et **Environment description**.

**Platform details**

- **Platform** : *Python*.
- **Platform branch** : *Python 3.12 running on 64bit Amazon Linux 2023*. La console propose la branche la plus récente ; choisissez la 3.12, la version de Python des parties 1 et 2.
- **Platform version** : celle marquée *Recommended*.

**Application code**

- Choisissez *Local file*, puis **Choose file**, et sélectionnez `galerie-beanstalk.zip`.
- **Version label** : `v1`.

**Environment properties** : cliquez sur **Add environment properties** et ajoutez deux propriétés. `GALERIE_BUCKET` : le nom de votre bucket, `galerie-<prenom>-<suffixe>`. `GALERIE_REGION` : votre région, `eu-north-1` à Stockholm ou `eu-west-3` à Paris. Sans la première, l'application s'arrête dès son démarrage.

**Environment tier** : *Web server environment*. **Environment type** : *Load balanced*.

**Platform-specific options** : ne changez rien. Le champ **WSGI path** est ignoré, car le `Procfile` de l'archive indique lui-même comment lancer l'application.

**Service access**

- **Service role** : laissez le réglage proposé. Beanstalk crée et gère lui-même le rôle de service.
- **EC2 instance profile** : cliquez sur **Customize** et choisissez `role-galerie-<prenom>`. Le profil que Beanstalk créerait de lui-même ne donnerait pas accès à votre bucket.
- **EC2 key pair** : laissez vide. Vous n'aurez à vous connecter à aucune instance.

**Tags** : aucun.

**Infrastructure**

- **Scaling** : **Min instances** `2`, **Max instances** `2`.
- **Compute** : **Architecture** *x86_64*. Dans **Instance types**, cliquez sur **Remove** à côté de `t3.small` pour ne garder que `t3.micro`.
- **Root volume** : **Root volume type** *General Purpose 3 (SSD)*, c'est-à-dire `gp3`. Laissez la taille par défaut.
- **Additional infrastructure details** : vérifiez que la rubrique **IMDSv1** indique que l'environnement n'active qu'IMDSv2. Ne touchez pas à l'AMI.

Sur un compte récent, le volume `gp3` ou la désactivation d'IMDSv1 est indispensable, car sans l'un des deux la création échoue sur une erreur de configuration de lancement. L'archive impose d'ailleurs les deux.

**Networking**

- **VPC** : le VPC par défaut.
- **Instance subnets** : cochez les sous-réseaux des zones `<région>a` et `<région>b`. Laissez **EC2 security groups** vide : Beanstalk crée ses propres groupes.
- **Load balancer** : **Load balancer type** *Application Load Balancer*, **Application Load Balancer type** *Dedicated*, **Visibility** *Public*.
- **Load balancer parameters** : gardez l'écouteur `Listener: 80`, en HTTP vers le processus `default`. Dans **Process: default**, dépliez **Health check** et mettez `/sante` comme chemin.
- **Load balancer subnets** : cochez les mêmes sous-réseaux, zones `<région>a` et `<région>b`.
- **Additional networking details** : **Instance public IP address** *Enabled*. Les instances doivent pouvoir télécharger les bibliothèques Python au démarrage. Laissez **IPv6** désactivé.

**Monitoring and updates**

- **Monitoring** : *Basic*. Ne cochez pas **Enable log streaming**.
- **Deployments** : **Deployment policy** *Rolling*. Dépliez **Additional deployment settings** et réglez la taille des lots (**Batch size**) sur *Fixed*, `1`.
- **Managed updates** : laissez **Enable managed updates** décoché. Beanstalk ne remplacera pas les instances pendant la séance pour appliquer une mise à jour de la plateforme.

**Review** : relisez le résumé, puis cliquez sur **Create**.

La création prend cinq à dix minutes. Restez sur la page de l'environnement et ouvrez l'onglet **Events**, où Beanstalk raconte ce qu'il fait, de la création de la pile CloudFormation au démarrage des instances. L'environnement est prêt quand son état est *Ok*, en vert.

:::warning
Si l'environnement passe en *Severe* ou en *Degraded*, lisez l'onglet **Events**. Les deux causes les plus fréquentes sont une propriété `GALERIE_BUCKET` absente ou mal orthographiée (l'application s'arrête au démarrage) et un rôle sans la stratégie de l'étape 19 (les instances ne peuvent pas télécharger la version). Corrigez dans <Chemin>Configuration</Chemin>, la page de l'environnement : Beanstalk applique la correction tout seul.
:::

## 22. Ouvrir la galerie

Sur la page de l'environnement, cliquez sur le **Domain**, de la forme `galerie-<prenom>-env.<identifiant>.<région>.elasticbeanstalk.com`. La galerie s'affiche, avec les fichiers que vous aviez déposés dans les parties précédentes : elle utilise le même bucket. Déposez un nouveau fichier, puis rechargez la page plusieurs fois en regardant le pied de page.

Faites le même comptage qu'à la partie 2, depuis CloudShell :

```bash title="CloudShell"
ENV=galerie-<prenom>-env
URL=$(aws elasticbeanstalk describe-environments --environment-names $ENV \
  --query "Environments[0].CNAME" --output text)
echo $URL
for i in $(seq 1 20); do
  curl -s "http://$URL/" | grep -o "instance i-[0-9a-f]* en zone [a-z0-9-]*"
done | sort | uniq -c
```

Deux lignes, une par instance et par zone, avec des nombres voisins de 10. C'est le résultat des étapes 10 à 16 de la partie 2, obtenu sans une seule commande sur les instances.

## 23. Ce que Beanstalk a créé

Ouvrez <Chemin>CloudFormation › Stacks</Chemin>. Une pile dont le nom commence par `awseb-` y est apparue. C'est votre environnement. Ouvrez-la, onglet **Resources**, et faites la liste des types de ressources qu'elle contient. Retrouvez ensuite chacune d'elles dans sa propre console :

- dans <Chemin>EC2 › Instances</Chemin>, deux instances nommées `galerie-<prenom>-env`, une par zone ;
- dans <Chemin>EC2 › Load Balancers</Chemin> et <Chemin>EC2 › Target groups</Chemin>, le répartiteur et son groupe cible, avec le contrôle de santé sur `/sante` ;
- dans <Chemin>EC2 › Auto Scaling groups</Chemin>, le groupe qui maintient deux instances ;
- dans <Chemin>EC2 › Security Groups</Chemin>, deux groupes créés par Beanstalk, l'un pour le répartiteur et l'autre pour les instances. Ouvrez celui des instances et regardez la source de sa règle HTTP ;
- dans <Chemin>S3 › Buckets</Chemin>, le bucket `elasticbeanstalk-<région>-<compte>`, qui contient votre archive.

Comparez avec ce que vous aviez créé à la main dans la partie 2. Qu'est-ce que Beanstalk a ajouté ?

## 24. Déployer une version 2

Vous allez changer le titre de la page et déployer cette nouvelle version pendant que des requêtes arrivent. Ouvrez **deux onglets** CloudShell (<Chemin>Actions › New tab</Chemin>).

Dans le premier onglet, lancez une boucle qui affiche, toutes les deux secondes, le titre servi par la galerie :

```bash title="CloudShell, premier onglet"
ENV=galerie-<prenom>-env
URL=$(aws elasticbeanstalk describe-environments --environment-names $ENV \
  --query "Environments[0].CNAME" --output text)
for i in $(seq 1 150); do
  echo "$(date +%T) $(curl -s -o /tmp/p.html -w '%{http_code}' "http://$URL/") $(grep -o '<h1>[^<]*' /tmp/p.html | cut -c5-)"
  sleep 2
done
```

Chaque ligne affiche l'heure, le code HTTP et le titre de la page, soit `200 Galerie` pour l'instant.

Dans le second onglet, fabriquez la version 2 et demandez à Beanstalk de la déployer :

```bash title="CloudShell, second onglet"
APP=galerie-<prenom>
ENV=galerie-<prenom>-env
curl -sO https://menraromial.com/aws-course/kits/galerie-beanstalk.zip
mkdir v2 && cd v2 && unzip -q ../galerie-beanstalk.zip
sed -i 's|<h1>Galerie</h1>|<h1>Galerie, version 2</h1>|' templates/index.html
zip -qr ../galerie-v2.zip . && cd ..
B=$(aws elasticbeanstalk create-storage-location --query S3Bucket --output text)
aws s3 cp galerie-v2.zip s3://$B/$APP/galerie-v2.zip
aws elasticbeanstalk create-application-version --application-name $APP --version-label v2 \
  --source-bundle S3Bucket=$B,S3Key=$APP/galerie-v2.zip
aws elasticbeanstalk update-environment --environment-name $ENV --version-label v2
```

Les quatre dernières commandes refont ce que la console faisait à l'étape 21 : `create-storage-location` donne le nom du bucket de Beanstalk, `aws s3 cp` y dépose l'archive, `create-application-version` en fait la version `v2` de l'application, et `update-environment` demande à l'environnement de passer à cette version. Ici, `zip -qr ../galerie-v2.zip .` comprime le contenu du dossier `v2`, dossiers cachés compris, et non le dossier lui-même.

Revenez au premier onglet et regardez défiler les lignes. Pendant une à deux minutes, les deux titres alternent, car une instance sert déjà la version 2 pendant que l'autre sert encore la version 1. Puis seule la version 2 reste. Sur la page de l'environnement, l'onglet **Events** montre le déploiement lot par lot, une instance à la fois. Comptez les lignes qui ne sont pas en `200` : avec la politique *Rolling*, il ne doit y en avoir aucune, ou presque.

## 25. Revenir à la version 1

Imaginez que la version 2 contienne un bogue. Le retour en arrière ne demande rien de plus qu'un nouveau déploiement :

1. Relancez la boucle dans le premier onglet.
2. Dans <Chemin>Elastic Beanstalk › Applications</Chemin>, ouvrez `galerie-<prenom>`, puis **Application versions**. Les deux versions y sont, `v1` et `v2`.
3. Cochez `v1`, puis <Chemin>Actions › Deploy</Chemin>, choisissez `galerie-<prenom>-env` et confirmez.

La boucle montre le chemin inverse, une instance après l'autre, jusqu'à ce que le titre redevienne `Galerie`. La même opération en ligne de commande serait `aws elasticbeanstalk update-environment --environment-name $ENV --version-label v1`.

## 26. Ranger, pour de bon

L'ordre compte ici aussi.

1. **L'environnement** : dans <Chemin>Elastic Beanstalk › Environments</Chemin>, sélectionnez `galerie-<prenom>-env`, puis <Chemin>Actions › Terminate environment</Chemin> et saisissez son nom pour confirmer. Beanstalk supprime la pile CloudFormation, donc les instances, le répartiteur, le groupe cible, le groupe Auto Scaling et les deux Security Groups. Attendez que l'environnement apparaisse comme *Terminated*, une dizaine de minutes ; vérifiez dans <Chemin>CloudFormation › Stacks</Chemin> que la pile `awseb-` a disparu.
2. **Les versions et l'application** : dans **Application versions**, cochez `v1` et `v2`, <Chemin>Actions › Delete</Chemin>, en cochant **Delete versions from Amazon S3**. Puis supprimez l'application `galerie-<prenom>`.
3. **Le bucket de Beanstalk** `elasticbeanstalk-<région>-<compte>` : Beanstalk lui a donné une stratégie qui en interdit la suppression. Ouvrez-le, onglet **Permissions**, supprimez la **Bucket policy**, puis videz le bucket (**Empty**) et supprimez-le (**Delete**). Les rôles que Beanstalk a créés pour lui-même ne coûtent rien ; laissez-les.
4. **Le reste du projet**, comme à l'[étape 18 de la partie 2](repartition.md#18-ranger-pour-de-bon), point 6 : le bucket de la galerie (vidé puis supprimé), le rôle `role-galerie-<prenom>` et la stratégie `galerie-s3-<prenom>`, la paire de clés `cle-<prenom>` et son fichier `.pem`.

Vérifiez enfin, dans <Chemin>EC2 › Instances</Chemin>, <Chemin>EC2 › Load Balancers</Chemin> et <Chemin>CloudFormation › Stacks</Chemin>, qu'il ne reste rien, puis regardez le solde de vos crédits dans **Billing and Cost Management**.

## Pour aller plus loin

**Déployer sans toucher aux instances en service.** Dans <Chemin>Configuration › Updates, monitoring, and logging</Chemin>, passez la politique de déploiement à *Immutable*, puis redéployez `v2`. Dans <Chemin>EC2 › Instances</Chemin>, regardez combien d'instances tournent pendant le déploiement, et ce que deviennent les anciennes à la fin.

**Remplacer une instance en panne.** Résiliez à la main l'une des deux instances de l'environnement. Que fait le groupe Auto Scaling, et combien de temps faut-il pour que l'environnement redevienne *Ok* ? Comparez avec la partie 2, où il fallait relancer l'instance vous-même.

## Questions

1. Quels fichiers de l'archive remplacent le service systemd et le fichier `galerie-nginx.conf` de la partie 1 ? Et `/etc/galerie.env` ?
2. Pourquoi faut-il ajouter `AWSElasticBeanstalkWebTier` au rôle des instances, alors que la galerie fonctionnait sans ?
3. Qu'est-ce que la pile CloudFormation de l'environnement contient de plus que ce que vous aviez construit à la main dans la partie 2 ?
4. Pendant le déploiement de la version 2, combien de temps les deux versions ont-elles cohabité ? Qu'aurait-on vu avec la politique *All at once* ?
5. Sur le compte fourni par l'enseignant, pourquoi les étudiants ne peuvent-ils pas créer leur propre environnement Beanstalk ?
