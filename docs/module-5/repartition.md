---
title: "TP 5, partie 2 : Deux serveurs derrière un répartiteur"
sidebar_label: "Partie 2 : deux serveurs"
description: "Image de la galerie, seconde instance dans une autre zone, groupe cible et contrôle de santé, Application Load Balancer, Security Group référencé, panne simulée."
---

import Seance from '@site/src/components/Seance';
import Schema from '@site/src/components/Schema';
import projetRepartition from '@site/src/figures/projet-repartition.svg';
import Chemin from '@site/src/components/Chemin';

<Seance items={['Module 5', 'Partie 2']} />

:::info[Avant de commencer]
Cette partie demande deux instances en marche à la fois. Un compte personnel le permet ; le compte fourni par l'enseignant n'en autorise qu'une par étudiant, et votre enseignant vous dira s'il lève cette règle pour la séance.

La première partie doit être terminée et vérifiée : la galerie fonctionne sur `galerie-<prenom>`, et vous n'avez **pas** fait l'étape de rangement. Si vous l'avez faite, refaites d'abord les étapes 1 à 6 du [pas-à-pas](tp.md).
:::

Votre galerie tourne sur une seule machine. Vous allez la dupliquer dans une seconde zone de disponibilité, placer un Application Load Balancer devant les deux copies, fermer l'accès direct aux instances, puis arrêter l'une d'elles pour vérifier que les visiteurs ne s'en aperçoivent presque pas. Relisez avant la section [Deux serveurs derrière un répartiteur](projet.md#deux-serveurs-derrière-un-répartiteur) de la page du projet.

<Schema svg={projetRepartition} num="TP5" alt="Des visiteurs atteignent en HTTP l'Application Load Balancer alb-galerie-<prenom>, protégé par le Security Group repartiteur-<prenom>. Son groupe cible cibles-galerie-<prenom>, avec un contrôle de santé sur /sante, envoie les requêtes à galerie-<prenom> dans la zone a et à galerie2-<prenom> dans la zone b. Le Security Group pare-feu-web-<prenom> des instances autorise le port 80 depuis le répartiteur seulement, et le port 22 depuis votre adresse. Les deux instances endossent le rôle role-galerie-<prenom> et écrivent dans le bucket galerie-<prenom>-<suffixe>.">
  Ce que vous allez construire.
</Schema>

Cette partie consomme davantage de crédits que les précédentes : deux instances, deux adresses IPv4 publiques et un répartiteur, soit quelques centimes de l'heure. Faites-la d'une traite, et rangez tout à la fin.

## 10. Prendre une image de la galerie

Une AMI est un modèle d'instance : elle contient un instantané du disque, avec le système, Nginx, l'application, sa configuration et le service systemd. Toute instance lancée à partir d'elle démarre avec exactement le même contenu.

1. Dans <Chemin>EC2 › Instances</Chemin>, sélectionnez `galerie-<prenom>`, puis <Chemin>Actions › Image and templates › Create image</Chemin>.
2. Nom : `galerie-<prenom>-image`. Description : `Galerie, partie 1 verifiee`.
3. Laissez **Reboot instance** coché. AWS redémarre l'instance pour que le disque soit dans un état cohérent au moment de l'instantané ; la galerie sera indisponible une minute.
4. Cliquez sur **Create image**.

Ouvrez <Chemin>EC2 › AMIs</Chemin>. Votre image passe de `Pending` à `Available` en quelques minutes. Pendant ce temps, ouvrez <Chemin>EC2 › Snapshots</Chemin> : un instantané de 8 Gio est apparu, dont la description mentionne votre AMI. C'est lui qui contient le disque, et c'est lui qui vous sera facturé tant que l'image existera.

## 11. Lancer la seconde instance

1. Dans <Chemin>EC2 › AMIs</Chemin>, sélectionnez `galerie-<prenom>-image`, puis **Launch instance from AMI**.
2. Nom : `galerie2-<prenom>`. L'AMI est déjà choisie. Type : `t3.micro`. Paire de clés : `cle-<prenom>`.
3. **Network settings** : cliquez sur **Edit**. Choisissez le sous-réseau de la zone `<région>b`, une autre zone que celle de la première instance. Laissez **Auto-assign public IP** sur *Enable* et choisissez le Security Group existant `pare-feu-web-<prenom>`.
4. **Advanced details** : dans **IAM instance profile**, choisissez `role-galerie-<prenom>`. Le rôle ne fait pas partie de l'image : sans lui, la seconde instance n'aurait aucun droit sur le bucket. Réglez aussi **Credit specification** sur *Standard* et vérifiez **Metadata version** : *V2 only (token required)*.
5. Lancez l'instance et attendez `2/2 checks passed`.

Ouvrez `http://<IP-publique-de-galerie2>` dans votre navigateur. La galerie s'affiche, avec les fichiers que vous aviez déposés : ils sont dans le bucket, pas sur l'instance. Descendez en bas de la page. Le pied de page indique un autre identifiant d'instance, et la zone `<région>b`. Vous n'avez rien installé : Nginx et le service `galerie` étaient déjà activés dans l'image, et ils ont démarré avec la machine.

## 12. Créer le Security Group du répartiteur

1. Ouvrez <Chemin>EC2 › Security Groups › Create security group</Chemin>.
2. Nom : `repartiteur-<prenom>`. Description : `Repartiteur de la galerie, HTTP public`. VPC : le VPC par défaut.
3. Une règle entrante : **HTTP**, source **Anywhere-IPv4**.
4. Laissez la règle sortante par défaut : le répartiteur doit pouvoir joindre les instances sur leur port 80. Créez le groupe.

## 13. Créer le groupe cible

1. Ouvrez <Chemin>EC2 › Target groups › Create target group</Chemin>.
2. **Target type** : *Instances*. Nom : `cibles-galerie-<prenom>` (32 caractères au plus). **Protocol** : HTTP, **Port** : 80. **VPC** : le VPC par défaut. **Protocol version** : HTTP1.
3. **Health checks** : protocole HTTP, chemin `/sante`. Dépliez **Advanced health check settings** et lisez les valeurs par défaut sans les modifier : seuil de bonne santé 5, seuil de mauvaise santé 2, délai 5 secondes, intervalle 30 secondes, code de succès 200. Cliquez sur **Next**.
4. Cochez `galerie-<prenom>` et `galerie2-<prenom>`, laissez le port 80, cliquez sur **Include as pending below**, puis sur **Create target group**.

Ouvrez le groupe, onglet **Targets**. Les deux instances y figurent, à l'état `unused` : aucun répartiteur n'utilise encore ce groupe, donc personne ne les contrôle.

## 14. Créer le répartiteur

1. Ouvrez <Chemin>EC2 › Load Balancers › Create load balancer</Chemin> et choisissez **Application Load Balancer**.
2. Nom : `alb-galerie-<prenom>`. **Scheme** : *Internet-facing*. **Load balancer IP address type** : *IPv4*.
3. **Network mapping** : le VPC par défaut. Cochez au moins deux zones, `<région>a` et `<région>b`, avec le sous-réseau proposé pour chacune. Un ALB en exige deux.
4. **Security groups** : retirez le groupe `default` proposé et choisissez `repartiteur-<prenom>`.
5. **Listeners and routing** : protocole HTTP, port 80, action **Forward to** `cibles-galerie-<prenom>`.
6. Relisez le résumé et cliquez sur **Create load balancer**.

Le répartiteur passe de `Provisioning` à `Active` en quelques minutes. Relevez son **DNS name**, de la forme `alb-galerie-<prenom>-1234567890.<région>.elb.amazonaws.com`. Revenez sur l'onglet **Targets** du groupe cible : les instances passent par l'état `initial`, le temps des premiers contrôles, puis `healthy`.

## 15. Vérifier la répartition

Ouvrez `http://<DNS-du-répartiteur>` dans votre navigateur. La galerie s'affiche. Rechargez la page plusieurs fois en regardant le pied de page : l'identifiant d'instance et la zone changent d'une requête à l'autre. Déposez un fichier : il apparaît, quelle que soit l'instance qui sert la page suivante.

Comptez maintenant, depuis CloudShell, quelle instance sert chaque requête :

```bash title="CloudShell"
ALB=<DNS-du-répartiteur>
for i in $(seq 1 20); do
  curl -s "http://$ALB/" | grep -o "instance i-[0-9a-f]* en zone [a-z0-9-]*"
done | sort | uniq -c
```

Vous devez obtenir deux lignes, une par instance, avec des nombres voisins de 10. Interrogez aussi le point de contrôle, comme le fait le répartiteur : `curl -s "http://$ALB/sante"`. La réponse JSON indique le bucket et l'instance qui a répondu.

## 16. Fermer l'accès direct aux instances

Les instances acceptent encore le HTTP de n'importe qui. Les visiteurs n'en ont plus besoin : ils passent par le répartiteur.

1. Ouvrez le Security Group `pare-feu-web-<prenom>`, onglet **Inbound rules**, **Edit inbound rules**.
2. Supprimez la règle **HTTP** dont la source est `0.0.0.0/0` et la règle **HTTPS**.
3. Ajoutez une règle **HTTP** dont la source est *Custom* : commencez à taper `repartiteur` et choisissez le groupe `repartiteur-<prenom>` (son identifiant commence par `sg-`). Description : `Trafic du repartiteur seulement`.
4. Gardez la règle SSH. Enregistrez.

Vérifiez depuis CloudShell :

```bash title="CloudShell"
curl -m 5 -s -o /dev/null -w "instance directe : %{http_code}\n" http://<IP-publique-de-galerie>/
curl -s -o /dev/null -w "répartiteur : %{http_code}\n" "http://$ALB/"
```

La première commande attend 5 secondes et affiche `000` : plus rien ne répond sur l'adresse de l'instance. La seconde affiche `200`. La règle ne désigne aucune adresse : elle autorise les machines qui portent le groupe `repartiteur-<prenom>`, c'est-à-dire les nœuds du répartiteur, quelles que soient leurs adresses, qui changent quand le répartiteur s'agrandit.

## 17. Arrêter l'application sur une instance

Connectez-vous en SSH à `galerie-<prenom>` (le SSH est toujours ouvert pour votre adresse). Préparez d'abord, dans CloudShell, une boucle qui interroge le répartiteur chaque seconde pendant deux minutes et affiche le code de chaque réponse :

```bash title="CloudShell"
for i in $(seq 1 120); do
  printf '%s ' "$(curl -s -o /dev/null -w '%{http_code}' "http://$ALB/")"; sleep 1
done; echo
```

Lancez-la, puis, sans attendre, arrêtez l'application sur l'instance :

```bash title="Sur l'instance (galerie)"
sudo systemctl stop galerie
```

Nginx répond encore, mais il ne trouve plus rien derrière lui : il renvoie `502 Bad Gateway` à toutes les requêtes, y compris aux contrôles de santé. Regardez défiler la boucle. Pendant quelques dizaines de secondes, une réponse sur deux environ est `502` : le répartiteur envoie toujours la moitié des requêtes à l'instance malade, parce qu'il ne l'a pas encore déclarée en mauvaise santé. Puis il n'y a plus que des `200`. Ouvrez l'onglet **Targets** du groupe cible : `galerie-<prenom>` est `unhealthy`, avec la raison *Health checks failed with these codes: [502]*.

Comptez les `502`. Avec les réglages par défaut, il faut 2 contrôles ratés, à 30 secondes d'intervalle, pour écarter une cible : la fenêtre pendant laquelle des visiteurs voient des erreurs dure jusqu'à une minute environ.

Redémarrez l'application :

```bash title="Sur l'instance (galerie)"
sudo systemctl start galerie
```

L'instance redevient `healthy` après 5 contrôles réussis, deux minutes et demie environ. Elle ne reçoit aucune requête de visiteur pendant ce temps : le répartiteur est prudent dans les deux sens.

## 18. Ranger, pour de bon

:::tip[Vous faites la partie 3 ?]
Supprimez seulement les points 1 à 5 ci-dessous, et gardez le bucket, le rôle `role-galerie-<prenom>` et la stratégie `galerie-s3-<prenom>` : la [partie 3](beanstalk.md) en a besoin, et se termine par le rangement du reste.
:::

Tout doit disparaître, et l'ordre compte, car certaines ressources en utilisent d'autres :

1. **Le répartiteur** `alb-galerie-<prenom>` : <Chemin>EC2 › Load Balancers</Chemin>, <Chemin>Actions › Delete load balancer</Chemin>, puis confirmez. Il est facturé à l'heure : c'est le premier à supprimer.
2. **Le groupe cible** `cibles-galerie-<prenom>` : <Chemin>EC2 › Target groups</Chemin>, **Delete**.
3. **Les deux instances** `galerie-<prenom>` et `galerie2-<prenom>` : <Chemin>Instance state › Terminate (delete) instance</Chemin>. Attendez l'état `Terminated`.
4. **L'image** : <Chemin>EC2 › AMIs</Chemin>, sélectionnez `galerie-<prenom>-image`, <Chemin>Actions › Deregister AMI</Chemin>. Puis **son instantané** : <Chemin>EC2 › Snapshots</Chemin>, sélectionnez celui dont la description mentionne l'AMI, **Delete snapshot**. Supprimer l'image ne supprime pas l'instantané, qui continuerait d'être facturé.
5. **Les Security Groups** : d'abord `pare-feu-web-<prenom>`, qui fait référence au groupe du répartiteur, puis `repartiteur-<prenom>`.
6. **Le reste du projet**, comme à l'[étape 9 de la première partie](tp.md#9-ranger-pour-de-bon) : le bucket (vidé puis supprimé), le rôle `role-galerie-<prenom>` et la stratégie `galerie-s3-<prenom>`, la paire de clés `cle-<prenom>` et son fichier `.pem`.

Vérifiez enfin, dans <Chemin>EC2 › Instances</Chemin>, <Chemin>EC2 › Load Balancers</Chemin> et <Chemin>EC2 › Snapshots</Chemin>, qu'il ne reste rien à votre nom, puis jetez un dernier coup d'œil au solde de vos crédits dans **Billing and Cost Management**.

## Pour aller plus loin

**Écarter une instance plus vite.** Dans le groupe cible, onglet **Health checks**, passez l'intervalle à 10 secondes et le seuil de mauvaise santé à 2. Refaites l'étape 17 : combien de `502` voyez-vous maintenant ? Qu'est-ce qui empêche de descendre l'intervalle à 1 seconde ?

**Laisser AWS remplacer les instances.** Créez un modèle de lancement (*launch template*) à partir de `galerie-<prenom>-image`, avec le rôle, le type `t3.micro` et le Security Group des instances. Créez ensuite un groupe Auto Scaling qui utilise ce modèle, dans les zones `a` et `b`, avec une capacité minimale et souhaitée de 2, rattaché au groupe cible, et qui se fie aux contrôles de santé du répartiteur. Résiliez à la main l'une de ses instances et regardez le groupe en lancer une autre. Au rangement, supprimez le groupe Auto Scaling **avant** tout le reste : sinon, il relancera les instances que vous résiliez.

## Questions

1. Pourquoi placer la seconde instance dans une autre zone de disponibilité, et pas dans la même ?
2. Combien de requêtes ont échoué à l'étape 17, et pourquoi ce nombre n'est-il pas nul ? Que coûterait le fait de réduire cette fenêtre ?
3. Pourquoi la règle HTTP des instances désigne-t-elle un Security Group plutôt que des adresses IP ?
4. Imaginez que l'application range les fichiers déposés sur le disque de l'instance, dans `/opt/galerie/uploads`, et non dans S3. Que verrait un visiteur qui dépose un fichier puis recharge la page derrière le répartiteur ?
5. Quel type de répartiteur choisiriez-vous pour un serveur de jeu en UDP ? Pour faire passer tout le trafic d'un VPC par un pare-feu virtuel d'un éditeur tiers ?
