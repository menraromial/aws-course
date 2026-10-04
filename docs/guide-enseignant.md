---
title: "Guide de l'enseignant"
sidebar_label: "Guide de l'enseignant"
description: "Points à dessiner au tableau, questions à poser, corrigés et pannes fréquentes des TP."
---

<head>
  <meta name="robots" content="noindex, nofollow" />
</head>

import Chemin from '@site/src/components/Chemin';

Cette page rassemble ce qui ne s'adresse pas aux étudiants : ce qu'il vaut la peine de dessiner au tableau, les questions qui font réagir une salle, les corrigés et les pannes que l'on rencontre le plus souvent en TP. Elle suit l'ordre des modules.

## Avant le premier module

### Créer les comptes des étudiants

Les comptes sont des **utilisateurs IAM** (pas IAM Identity Center) dont le nom est tiré du prénom de l'étudiant : `camille`, `jeanpaul`, `camille2`. Ce nom est la valeur de `<prenom>` dans tous les énoncés, qui le rappellent en tête de chaque TP, et les stratégies s'appuient dessus par la variable `${aws:username}`. La chaîne complète part d'un formulaire Google et arrive dans IAM sans recopie à la main :

1. les étudiants remplissent un formulaire, dont les réponses arrivent dans une feuille Google Sheets ;
2. un script Apps Script attaché à la feuille ajoute à chaque ligne un nom d'utilisateur et un mot de passe ;
3. vous téléchargez la feuille en CSV et la donnez au script `creer-etudiants.sh`, qui crée les comptes dans AWS ;
4. un clic sur **Envoyer les identifiants** envoie à chaque étudiant son nom d'utilisateur et son mot de passe.

Tout se trouve dans le dossier [`iam/`](https://github.com/menraromial/aws-course/tree/main/iam) du dépôt :

| Fichier | Rôle |
|---|---|
| `aws-cours-etudiant.json` | droits de l'étudiant, et limite de permissions de son propre utilisateur |
| `aws-cours-limite-stagiaire.json` | limite que l'étudiant doit poser sur l'utilisateur créé au TP 2 |
| `aws-cours-limite-role.json` | limite que l'étudiant doit poser sur le rôle créé au TP 4 |
| `formulaire/identifiants.gs` | script Apps Script de la feuille des réponses |
| `creer-etudiants.sh` | crée les comptes à partir du CSV de la feuille |
| `une-instance-par-etudiant/` | fonction qui arrête la seconde instance d'un étudiant (voir plus bas) |

#### 1. Le formulaire

Dans Google Forms, créez un formulaire avec trois questions obligatoires, de type *Réponse courte* :

- **Nom** ;
- **Prénoms**, avec pour description « Tous vos prénoms, séparés par des espaces » ;
- **Adresse e-mail**, avec la validation *Texte › Adresse e-mail*. Vous pouvez aussi activer <Chemin>Paramètres › Réponses › Collecter les adresses e-mail</Chemin>, qui ajoute la colonne d'elle-même.

Dans l'onglet **Réponses**, cliquez sur **Associer à Sheets** pour créer la feuille. Les intitulés comptent un peu : le script cherche, sur la première ligne, une colonne qui commence par « Nom », une qui contient « Prénom » et une qui contient « mail ».

#### 2. Le script de la feuille

Dans la feuille, ouvrez <Chemin>Extensions › Apps Script</Chemin>, remplacez le contenu du fichier `Code.gs` par celui de `identifiants.gs` (reproduit ci-dessous), puis remplacez `URL_CONNEXION` par l'adresse de connexion de votre compte AWS (affichée sur le tableau de bord d'IAM, ou par le script `creer-etudiants.sh`). Enregistrez et rechargez la feuille : un menu **Comptes AWS** apparaît. Au premier usage, Google demande d'autoriser le script à modifier la feuille et à envoyer des e-mails en votre nom ; comme le script n'est pas publié, il affiche un avertissement « Google n'a pas validé cette application », que l'on passe par <Chemin>Paramètres avancés › Accéder au projet</Chemin>.

Le menu propose trois commandes :

- **Générer les identifiants** ajoute, si elles n'existent pas, les colonnes `username`, `password` et `envoye_le`, et remplit les deux premières pour chaque ligne qui n'en a pas encore ;
- **Envoyer les identifiants** commence par générer ce qui manque, demande confirmation, puis envoie un e-mail à chaque étudiant dont la colonne `envoye_le` est vide, et y inscrit la date d'envoi ;
- **Renvoyer à la sélection** renvoie l'e-mail aux lignes sélectionnées, pour un étudiant qui l'a perdu.

Pour avoir un vrai bouton dans la feuille, insérez un dessin (<Chemin>Insertion › Dessin</Chemin>), puis, dans son menu à trois points, <Chemin>Attribuer un script</Chemin> et saisissez `envoyerIdentifiants`.

Les règles de génération, appliquées dans l'ordre des réponses :

- le **nom d'utilisateur** est le premier des prénoms de l'étudiant qui n'est pas encore pris, en minuscules, sans accent ni tiret ; si tous ses prénoms sont pris, c'est le premier suivi du plus petit numéro libre ;
- le **mot de passe** est ce prénom, avec une majuscule, suivi de `@2026`, complété par des `!` s'il fait moins des 8 caractères qu'exige AWS.

| Prénoms saisis | Nom d'utilisateur | Mot de passe |
|---|---|---|
| Camille | `camille` | `Camille@2026` |
| Jean-Paul Marie | `jeanpaul` | `Jeanpaul@2026` |
| Camille Hélène | `helene` | `Helene@2026` |
| Camille | `camille2` | `Camille@2026` |
| Bo | `bo` | `Bo@2026!` |

Un nom d'utilisateur ne contient que des minuscules et des chiffres. Ce n'est pas qu'une question d'esthétique : il entre dans des noms de buckets, qui refusent majuscules et accents, et dans les motifs des stratégies, où un tiret créerait des confusions (`galerie-jean-*` couvrirait les buckets d'un `jean-paul`).

:::danger[Un mot de passe que tout le monde peut deviner]
Avec la règle `<Prenom>@2026`, n'importe quel étudiant connaît le mot de passe de ses camarades : il suffit de connaître leur prénom. AWS impose de le changer à la première connexion, mais celui qui se connecte le premier le choisit à la place de l'intéressé et s'empare de son compte. Deux parades, à combiner :

- passez `SUFFIXE_ALEATOIRE` à `true` en tête du script : le mot de passe devient `Camille@2026-4821`, toujours facile à recopier, mais impossible à deviner ;
- envoyez les identifiants juste avant la séance, en demandant à chacun de se connecter et de changer son mot de passe sur-le-champ.
:::

Le nombre d'e-mails est limité par Google : une centaine de destinataires par jour avec un compte Gmail personnel, bien davantage avec un compte Google Workspace. Le script s'arrête quand le quota est épuisé ; relancez **Envoyer les identifiants** le lendemain, il reprend où il s'était arrêté.

<details>
<summary>Le script <code>identifiants.gs</code></summary>

```javascript title="identifiants.gs"
/**
 * Comptes AWS du cours, à partir des réponses au formulaire d'inscription.
 *
 * À coller dans Extensions › Apps Script de la feuille liée au formulaire.
 * Ajoute un menu « Comptes AWS » :
 *  - Générer les identifiants : remplit les colonnes username et password
 *    des lignes qui n'en ont pas encore ;
 *  - Envoyer les identifiants : génère ce qui manque, puis envoie un e-mail
 *    à chaque étudiant qui ne l'a pas encore reçu (colonne envoye_le) ;
 *  - Renvoyer à la sélection : renvoie l'e-mail aux lignes sélectionnées.
 *
 * Le nom d'utilisateur est l'un des prénoms de l'étudiant, en minuscules,
 * sans accent ni tiret : le premier qui n'est pas déjà pris. Si tous ses
 * prénoms sont pris, le premier suivi d'un numéro (jean2, jean3...).
 * Les lignes sont traitées dans l'ordre des réponses.
 */

const ANNEE = '2026';
const URL_CONNEXION = 'https://<compte>.signin.aws.amazon.com/console'; // à remplacer
const URL_COURS = 'https://menraromial.com/aws-course/';
// true : ajoute quatre chiffres au hasard au mot de passe (Camille@2026-4821).
// Fortement conseillé, voir le guide de l'enseignant.
const SUFFIXE_ALEATOIRE = false;
const ENTETES = {username: 'username', password: 'password', envoi: 'envoye_le'};

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Comptes AWS')
    .addItem('Générer les identifiants', 'genererIdentifiants')
    .addItem('Envoyer les identifiants', 'envoyerIdentifiants')
    .addItem('Renvoyer à la sélection', 'renvoyerSelection')
    .addToUi();
}

/* ---------- fonctions pures (sans dépendance à Google) ---------- */

function normaliser_(texte) {
  return String(texte)
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]/g, '');
}

/** Liste des prénoms normalisés d'une réponse ("Jean-Paul  Marie" → ["jeanpaul", "marie"]). */
function prenoms_(texte) {
  return String(texte).split(/[\s,;/]+/).map(normaliser_).filter(Boolean);
}

/** Premier prénom libre, sinon le premier prénom suivi du plus petit numéro libre. */
function choisirUsername_(prenoms, pris) {
  const libre = prenoms.find(p => !pris.has(p));
  if (libre) return libre;
  let i = 2;
  while (pris.has(prenoms[0] + i)) i++;
  return prenoms[0] + i;
}

/** <Prenom>@2026 à partir du prénom retenu (sans le numéro éventuel). */
function motDePasse_(username) {
  const prenom = username.replace(/[0-9]+$/, '');
  let mdp = prenom.charAt(0).toUpperCase() + prenom.slice(1) + '@' + ANNEE;
  if (SUFFIXE_ALEATOIRE) mdp += '-' + Math.floor(1000 + Math.random() * 9000);
  while (mdp.length < 8) mdp += '!'; // longueur minimale exigée par AWS
  return mdp;
}

/* ---------- accès à la feuille ---------- */

function feuille_() {
  return SpreadsheetApp.getActive().getSheets()[0]; // la feuille des réponses
}

/** Numéros (à partir de 1) des colonnes utiles ; crée les colonnes de sortie si besoin. */
function colonnes_(sh) {
  const entetes = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(h => String(h).trim());
  const trouver = re => entetes.findIndex(h => re.test(h)) + 1;
  const c = {nom: trouver(/^nom\b/i), prenoms: trouver(/pr[ée]nom/i), mail: trouver(/mail/i)};
  if (!c.nom || !c.prenoms || !c.mail) {
    throw new Error('Colonnes « Nom », « Prénoms » et « adresse e-mail » introuvables en ligne 1.');
  }
  for (const cle of Object.keys(ENTETES)) {
    let i = entetes.indexOf(ENTETES[cle]) + 1;
    if (!i) {
      entetes.push(ENTETES[cle]);
      i = entetes.length;
      sh.getRange(1, i).setValue(ENTETES[cle]).setFontWeight('bold');
    }
    c[cle] = i;
  }
  return c;
}

function lignes_(sh) {
  const n = sh.getLastRow() - 1;
  return n < 1 ? [] : sh.getRange(2, 1, n, sh.getLastColumn()).getValues();
}

/* ---------- menu ---------- */

function genererIdentifiants() {
  const sh = feuille_();
  const c = colonnes_(sh);
  const lignes = lignes_(sh);
  const pris = new Set(lignes.map(l => String(l[c.username - 1]).trim().toLowerCase()).filter(Boolean));
  let crees = 0;
  const sansPrenom = [];
  lignes.forEach((l, k) => {
    const ligne = k + 2;
    let username = String(l[c.username - 1]).trim();
    if (!username) {
      const prenoms = prenoms_(l[c.prenoms - 1]);
      if (!prenoms.length) { sansPrenom.push(ligne); return; }
      username = choisirUsername_(prenoms, pris);
      pris.add(username);
      sh.getRange(ligne, c.username).setValue(username);
      crees++;
    }
    if (!String(l[c.password - 1]).trim()) {
      sh.getRange(ligne, c.password).setNumberFormat('@').setValue(motDePasse_(username));
    }
  });
  SpreadsheetApp.flush();
  let message = crees + ' identifiant(s) généré(s).';
  if (sansPrenom.length) message += ' Lignes sans prénom : ' + sansPrenom.join(', ') + '.';
  SpreadsheetApp.getActive().toast(message, 'Comptes AWS', 8);
  return crees;
}

function envoyerIdentifiants() {
  genererIdentifiants();
  const ui = SpreadsheetApp.getUi();
  const sh = feuille_();
  const c = colonnes_(sh);
  const lignes = lignes_(sh);
  const aEnvoyer = [];
  lignes.forEach((l, k) => { if (!l[c.envoi - 1] && l[c.username - 1]) aEnvoyer.push(k); });
  if (!aEnvoyer.length) { ui.alert('Tous les étudiants ont déjà reçu leurs identifiants.'); return; }
  if (ui.alert('Envoyer les identifiants à ' + aEnvoyer.length + ' étudiant(s) ?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  const bilan = envoyerLignes_(sh, c, lignes, aEnvoyer);
  ui.alert(bilan);
}

function renvoyerSelection() {
  genererIdentifiants();
  const ui = SpreadsheetApp.getUi();
  const sh = feuille_();
  const c = colonnes_(sh);
  const lignes = lignes_(sh);
  const plage = sh.getActiveRange();
  const indices = [];
  for (let r = plage.getRow(); r < plage.getRow() + plage.getNumRows(); r++) {
    if (r >= 2 && r - 2 < lignes.length) indices.push(r - 2);
  }
  if (!indices.length) { ui.alert('Sélectionnez une ou plusieurs lignes d\'étudiants.'); return; }
  if (ui.alert('Renvoyer les identifiants à ' + indices.length + ' étudiant(s) ?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  ui.alert(envoyerLignes_(sh, c, lignes, indices));
}

function envoyerLignes_(sh, c, lignes, indices) {
  let envoyes = 0;
  const erreurs = [];
  for (const k of indices) {
    if (MailApp.getRemainingDailyQuota() < 1) {
      erreurs.push('quota d\'envoi du jour épuisé : relancez demain pour les suivants');
      break;
    }
    const l = lignes[k];
    const mail = String(l[c.mail - 1]).trim();
    if (!mail) { erreurs.push('ligne ' + (k + 2) + ' sans adresse e-mail'); continue; }
    try {
      MailApp.sendEmail({to: mail, subject: 'Cours AWS : vos identifiants', body: corpsDuMail_(l, c)});
      sh.getRange(k + 2, c.envoi).setValue(new Date());
      envoyes++;
    } catch (e) {
      erreurs.push('ligne ' + (k + 2) + ' : ' + e.message);
    }
  }
  return envoyes + ' e-mail(s) envoyé(s).' + (erreurs.length ? '\n' + erreurs.join('\n') : '');
}

function corpsDuMail_(l, c) {
  const prenom = String(l[c.prenoms - 1]).trim().split(/\s+/)[0];
  const username = String(l[c.username - 1]).trim();
  return [
    'Bonjour ' + prenom + ',',
    '',
    'Voici vos identifiants pour le compte AWS du cours.',
    '',
    'Adresse de connexion : ' + URL_CONNEXION,
    'Nom d\'utilisateur : ' + username,
    'Mot de passe provisoire : ' + String(l[c.password - 1]).trim(),
    '',
    'À la première connexion, AWS vous demandera de choisir votre propre mot de passe.',
    'Faites-le dès réception de ce message.',
    '',
    'Dans les énoncés des TP, remplacez <prenom> par votre nom d\'utilisateur : ' + username + '.',
    '',
    'Le cours : ' + URL_COURS,
  ].join('\n');
}

if (typeof module !== 'undefined') {
  module.exports = {normaliser_, prenoms_, choisirUsername_, motDePasse_};
}
```

</details>

#### 3. Créer les comptes dans AWS

Avec un compte administrateur :

1. <Chemin>IAM › Policies › Create policy</Chemin>, mode JSON : créez les trois stratégies en collant le contenu des trois fichiers JSON, sous les noms `aws-cours-etudiant`, `aws-cours-limite-stagiaire` et `aws-cours-limite-role`. Les noms comptent : la première exige les deux autres sous ces noms exacts.
2. Dans la feuille, lancez **Générer les identifiants**, puis téléchargez-la : <Chemin>Fichier › Télécharger › Valeurs séparées par des virgules (.csv)</Chemin>.
3. Dans CloudShell, déposez ce fichier (<Chemin>Actions › Upload file</Chemin>), récupérez le dépôt et lancez le script :

    ```bash title="CloudShell (administrateur)"
    git clone https://github.com/menraromial/aws-course.git
    aws-course/iam/creer-etudiants.sh ~/reponses.csv
    rm ~/reponses.csv
    ```

    Remplacez `reponses.csv` par le nom du fichier téléchargé. Le script crée le groupe `etudiants` (avec la stratégie `aws-cours-etudiant`), puis, pour chaque ligne, l'utilisateur avec le mot de passe de la colonne `password`, à changer à la première connexion, l'ajout au groupe et la limite de permissions `aws-cours-etudiant`. Il ignore les autres colonnes et signale les lignes qu'il n'a pas traitées : nom d'utilisateur invalide, ou déjà présent dans le compte, par exemple un administrateur qui porterait le même prénom qu'un étudiant. Dans ce cas, changez le nom de cet étudiant dans la feuille avant d'envoyer les identifiants. Le script est relançable : pour des inscriptions tardives, régénérez, retéléchargez et relancez, seuls les nouveaux comptes sont créés.

4. Seulement alors, lancez **Envoyer les identifiants** depuis la feuille.

Sans formulaire, `creer-etudiants.sh 100` crée des comptes `student1` à `student100` avec des mots de passe tirés au hasard, écrits dans `etudiants.csv` ; il faut alors indiquer aux étudiants que leur `<prenom>` est leur numéro de compte.

La limite de permissions posée sur chaque étudiant n'est pas une précaution de trop. Au TP 2, chaque étudiant peut ajouter n'importe quel utilisateur à son groupe `stagiaires-<prenom>`, y compris lui-même, et ce groupe porte une stratégie qu'il a écrite. Avec sa propre stratégie comme limite, il ne peut jamais obtenir plus que ce qu'elle accorde.

### Une seule instance en marche par étudiant

Aucune stratégie IAM ne sait compter : elle peut limiter le type d'instance, pas leur nombre. La limite d'une instance en marche par étudiant est donc assurée par une petite fonction Lambda, déclenchée par EventBridge chaque fois qu'une instance passe à l'état `running`. Elle regroupe les instances en marche par valeur du tag `Proprietaire`, garde celle qui tourne depuis le plus longtemps et **arrête** les autres, en leur ajoutant un tag `ArreteeAutomatiquement`. Elle arrête au lieu de résilier : un étudiant ne perd jamais son disque. Le tag `Proprietaire` est obligatoire au lancement et les étudiants ne peuvent plus le modifier ensuite : ils ne peuvent pas échapper au comptage.

Pour la déployer, toujours dans CloudShell :

```bash title="CloudShell (administrateur)"
cd ~/aws-course/iam/une-instance-par-etudiant
./deployer.sh
```

Le script crée le rôle d'exécution `une-instance-par-etudiant` (lecture des instances, arrêt et tags des instances de `eu-west-3`), la fonction et la règle EventBridge du même nom. Ses décisions apparaissent dans <Chemin>CloudWatch › Log groups › /aws/lambda/une-instance-par-etudiant</Chemin>. Son coût est nul en pratique : quelques centaines d'appels par séance. La logique a été testée avec un faux EC2 (`pytest test_lambda.py`, avec `moto`) ; faites tout de même un essai avec un compte étudiant avant le premier TP 3, en lançant deux instances à la suite.

Les étudiants n'ont aucun droit sur Lambda ni sur EventBridge : ils ne peuvent ni voir ni désactiver la fonction.

### Le quota d'instances du compte

Indépendamment des stratégies, AWS limite le nombre de processeurs virtuels en marche dans chaque région. Le quota qui compte ici est *Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances*, exprimé en vCPU. Une `t3.micro` en compte 2 : cent étudiants avec une instance chacun demandent **200 vCPU**. Sur un compte récent, ce quota est souvent bien plus bas. Vérifiez-le avant le premier TP 3 :

```bash title="CloudShell (administrateur)"
aws service-quotas get-service-quota --region eu-west-3 --service-code ec2 \
  --quota-code L-1216C47A --query Quota.Value
```

S'il est inférieur au nombre d'étudiants multiplié par deux, demandez une augmentation dans <Chemin>Service Quotas › Amazon EC2</Chemin>, quelques jours à l'avance : la demande est examinée par AWS. Ce quota sert aussi de plafond global : même en cas de problème, le compte ne pourra pas faire tourner plus de vCPU que lui.

### Ce que les stratégies autorisent et interdisent

- **Lecture** partout : EC2, IAM, CloudWatch, prix, tableau de bord de santé, CloudShell. Elle ne coûte rien et sert au TP 1 (zones de la Virginie du Nord, vue globale d'EC2) et au simulateur de stratégies.
- **EC2 à Paris uniquement** : instances `t3.micro` ou `t2.micro`, AMI publiées par Amazon, matériel partagé (pas d'instance dédiée), disques `gp3` ou `gp2` de 16 Gio au plus, tag `Proprietaire` égal au nom d'utilisateur obligatoire au lancement. Un étudiant ne peut arrêter, redémarrer, résilier ou modifier que les instances qui portent son nom, et ne peut pas changer ce tag. Une seule instance en marche à la fois (voir plus haut). Les Security Groups et les paires de clés sont modifiables par tous, ce qui ne coûte rien.
- **IAM** : seulement les ressources des TP, à son nom (`lecture-ec2-<prenom>`, `galerie-s3-<prenom>`, `stagiaires-<prenom>`, `stagiaire-<prenom>`, `role-galerie-<prenom>`). L'utilisateur stagiaire et le rôle ne peuvent être créés qu'avec leur limite, qui les plafonne respectivement à `ec2:Describe*` et CloudShell, et à S3 sur les buckets `galerie-*` et SQS sur les files `file-*`. Aucune limite ne peut être retirée, aucune stratégie `aws-cours-*` modifiée. Pas de clé d'accès : CloudShell suffit.
- **S3** : tout, mais seulement sur les buckets `galerie-<prenom>-*`, créés à Paris. Stratégies de bucket, ACL, réplication et accélération de transfert sont interdites : un bucket ne peut pas devenir public, et donc pas servir de point de téléchargement payant pour le monde entier.
- **SQS** : tout, sur sa file `file-<prenom>`.
- Tout le reste (RDS, NAT Gateway, adresses Elastic IP, Lambda, répartiteurs de charge, autres régions…) est refusé par défaut, puisque rien ne l'autorise.

### Ce qui coûte, et comment s'en protéger

À Paris, une `t3.micro` coûte environ 0,012 $ par heure, plus 0,005 $ par heure pour son adresse IPv4 publique. Les cinq TP représentent une dizaine d'heures d'instance par étudiant, soit **moins de 0,20 $ par étudiant**, une vingtaine de dollars pour cent étudiants. Le vrai risque est l'instance oubliée : environ **12 $ par mois** chacune. Dix instances oubliées pendant un mois suffisent à épuiser un crédit de 120 $ ; avec cent étudiants et une instance chacun, une semaine d'oubli collectif coûte déjà environ 280 $. Trois précautions :

1. **Une alerte de budget.** <Chemin>Billing and Cost Management › Budgets › Create budget</Chemin>, budget de coûts mensuel de 120 $, avec des alertes par e-mail à 25 %, 50 % et 80 %. Dans les options avancées, décochez les **crédits** dans les types de charges : sinon le budget voit des coûts nuls tant que le crédit les absorbe. Une action de budget peut aussi attacher automatiquement une stratégie de refus au groupe `etudiants` quand un seuil est atteint.
2. **Les crédits CPU en mode standard par défaut.** Les `t3` sont en mode *unlimited* par défaut et aucune condition IAM ne permet d'imposer le mode standard au lancement. Basculez le réglage par défaut du compte, une fois pour toutes :

    ```bash title="CloudShell (administrateur)"
    aws ec2 modify-default-credit-specification --region eu-west-3 --instance-family t3 --cpu-credits standard
    ```

3. **Une vérification après chaque séance**, qui liste les instances encore présentes et leur propriétaire :

    ```bash title="CloudShell (administrateur)"
    aws ec2 describe-instances --region eu-west-3 \
      --filters Name=instance-state-name,Values=pending,running,stopping,stopped \
      --query "Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key=='Proprietaire']|[0].Value,LaunchTime]" \
      --output table
    ```

    Une instance arrêtée ne coûte plus que son disque, quelques centimes par mois ; une instance en marche coûte. Les buckets et les files vides ne coûtent rien.

Si les étudiants se connectent par IAM Identity Center plutôt qu'avec des utilisateurs IAM, les stratégies ci-dessus ne s'appliquent pas telles quelles (la variable `${aws:username}` n'existe pas pour une session Identity Center), et le TP 1 change : la page de connexion est un portail d'accès, et `aws sts get-caller-identity` renvoie un ARN de la forme `arn:aws:sts::<compte>:assumed-role/<ensemble-de-permissions>/<utilisateur>` au lieu de `arn:aws:iam::<compte>:user/<utilisateur>`.

## Module 1 : Introduction à AWS

### Ouvrir le module

Commencez par montrer l'application du projet final, déployée sur votre compte : on dépose un fichier dans le navigateur d'un étudiant, puis on le retrouve dans le bucket S3 affiché au vidéoprojecteur. Trois minutes suffisent. Dites simplement qu'à la fin du cours, chacun aura construit la même chose seul. Les notions qui suivent prennent tout de suite plus de sens.

### Au tableau

Pour les régions, une carte de France très schématique suffit : un grand cercle autour de Paris, trois petits cercles dedans pour les zones. Barrez-en un d'une croix en disant « incendie », puis placez une seule instance dans le cercle barré et demandez ce qu'il advient du site. Placez ensuite deux instances dans deux cercles différents et reposez la question. C'est la manière la plus rapide de faire comprendre la haute disponibilité sans en faire un cours.

Pour la responsabilité partagée, dessinez trois colonnes (EC2, RDS, S3) et demandez à la salle, couche par couche, qui s'en occupe. Les étudiants se trompent presque toujours sur la dernière ligne pour S3 : ils pensent qu'AWS protège les données contre une mauvaise configuration.

### Questions qui font réagir

- « Vous supprimez un fichier par erreur dans S3. AWS peut-il le récupérer ? » Non, sauf si le versionnage du bucket avait été activé. La durabilité de S3 protège contre la perte d'un disque, pas contre vos propres ordres.
- « Votre voisin affirme avoir lancé une instance dans le compte, vous ne la voyez pas. Pourquoi ? » La région.
- « Quelqu'un n'a pas le droit de lancer une instance dans la console. Peut-il le faire avec la ligne de commande ? » Non : même API, même contrôle.
- « Dans l'affaire Capital One, qu'aurait-il fallu changer pour que la fuite soit limitée ? » Un rôle limité à un seul bucket, voire à une seule action. C'est le principe de moindre privilège, qui ouvre le module 2.

### Corrigé du TP 1

1. `arn:aws:iam::123456789012:user/camille` se lit : `arn` (c'est un ARN), `aws` (la partition, c'est-à-dire l'ensemble des régions commerciales), `iam` (le service), un champ région vide (IAM est global), le numéro du compte, puis le type de ressource et son nom.
2. IAM est un service global : ses utilisateurs, groupes et rôles valent pour toutes les régions. EC2 est régional.
3. Avec un tarif de l'ordre de 0,012 USD par heure à Paris, environ 8,8 USD par mois ; en Virginie du Nord, le tarif est un peu plus bas (de l'ordre de 0,010 USD par heure, soit environ 7,6 USD par mois). Les valeurs exactes sont celles relevées par les étudiants dans l'assistant. Pour `m7i.4xlarge`, on dépasse plusieurs centaines de dollars par mois : c'est l'ordre de grandeur qui compte.

La commande `echo $AWS_REGION` affiche `eu-west-3` : CloudShell fixe cette variable à la région choisie dans la console au moment où il s'ouvre. Si l'on change de région ensuite, il faut ouvrir un nouvel onglet CloudShell ou préciser `--region`.

### Pannes fréquentes

| Symptôme | Cause | Remède |
|---|---|---|
| La page de connexion refuse le mot de passe provisoire | Mauvais identifiant de compte, ou page « Root user » au lieu de « IAM user » | Utiliser l'adresse de connexion fournie, qui préremplit le compte |
| CloudShell ne s'ouvre pas | Permission CloudShell absente de la stratégie de l'étudiant | Ajouter la stratégie gérée `AWSCloudShellFullAccess` au groupe des étudiants |
| `describe-regions` ou `describe-availability-zones` refusé | Stratégie trop restrictive (par exemple limitée par condition de région) | Autoriser `ec2:DescribeRegions` et `ec2:DescribeAvailabilityZones`, qui ne coûtent rien |
| Le prix n'apparaît pas dans la liste des types d'instances | Affichage compact de la console | Cliquer sur « Compare instance types », qui affiche une colonne de prix |

## Module 2 : Sécurité et gestion des accès

### Les droits que demande le TP

Ils sont couverts par `aws-cours-etudiant` (voir [Avant le premier module](#avant-le-premier-module)). Le piège classique d'un compte partagé, un étudiant qui crée un utilisateur, lui attache une stratégie `"Action": "*"` et se connecte sous ce nom, est fermé par la limite `aws-cours-limite-stagiaire`, que la création de l'utilisateur exige. C'est un bon exemple à montrer aux étudiants les plus avancés : ils se heurtent eux-mêmes à une limite de permissions avant d'en poser une.

### Au tableau

Le schéma 2.3 (logique d'évaluation) se dessine en deux losanges. Faites ensuite dérouler l'exemple de Camille à voix haute par la salle, question par question, en pointant le losange concerné.

Pour les Security Groups, un rectangle (l'instance), un cadre autour (le groupe), trois flèches venant de la gauche. Tracez la réponse HTTP en pointillé vers l'extérieur et demandez quelle règle l'autorise. La réponse « aucune, le groupe est à état » surprend toujours.

### Questions qui font réagir

- « La stratégie de quarantaine d'AWS est faite de `Deny`. Pourquoi pas d'un simple retrait des `Allow` ? » Retirer des `Allow` obligerait AWS à modifier des stratégies écrites par le client. Un `Deny` ajouté produit l'effet voulu sans y toucher, puisqu'il l'emporte sur tout.
- « Un rôle a-t-il un mot de passe ? » Non, et c'est tout son intérêt.
- « Si l'attaquante de Capital One avait volé des identifiants temporaires d'un rôle limité à un seul bucket, qu'aurait-elle obtenu ? » Le contenu de ce seul bucket, et pour quelques heures.

### Corrigé du TP 2

1. Un nouveau stagiaire n'a qu'à être ajouté au groupe ; une modification des droits s'applique à tous d'un coup. On évite ainsi d'avoir des droits différents pour des personnes qui font le même travail.
2. Un refus par défaut : le message d'erreur ne mentionne aucune stratégie de refus, et le simulateur indique `implicitly denied` (aucune stratégie ne correspond). Un refus explicite serait signalé comme tel, avec le nom de la stratégie responsable.
3. L'authentification par clé protège contre les mots de passe devinés, pas contre une faille du serveur SSH lui-même, et elle n'empêche pas les tentatives de remplir les journaux et de consommer des ressources. Le moindre privilège vaut aussi pour le réseau : un seul administrateur, une seule adresse.
4. Les Security Groups sont à état : les réponses à une connexion entrante autorisée sont autorisées d'office.

Le stagiaire ne peut pas lister les utilisateurs IAM (`ListUsers` : `denied`), faute de stratégie qui l'y autorise.

### Solution du « pour aller plus loin »

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DemarrerArreterInstancesDeFormation",
      "Effect": "Allow",
      "Action": ["ec2:StartInstances", "ec2:StopInstances"],
      "Resource": "arn:aws:ec2:eu-west-3:*:instance/*",
      "Condition": {
        "StringEquals": { "aws:ResourceTag/Projet": "formation" }
      }
    }
  ]
}
```

Dans le simulateur, il faut renseigner l'ARN d'une instance et la valeur du tag dans les paramètres de la ressource simulée pour voir la différence entre instance taguée et non taguée.

### Pannes fréquentes

| Symptôme | Cause | Remède |
|---|---|---|
| Le stagiaire ne peut pas se connecter | Adresse de connexion du compte mal recopiée, ou page « Root user » | Reprendre l'adresse affichée à la fin de la création de l'utilisateur |
| CloudShell ne s'ouvre pas pour le stagiaire | `AWSCloudShellFullAccess` oubliée sur le groupe | L'attacher au groupe `stagiaires-<prenom>` |
| La création de l'utilisateur échoue sur `iam:CreateLoginProfile` | Droits de l'étudiant incomplets | Ajouter l'action à la stratégie des étudiants |
| `describe-volumes` n'est pas refusé à l'étape 5 | Stratégie en ligne créée sur l'utilisateur de l'étudiant au lieu du groupe du stagiaire | La recréer sur le groupe `stagiaires-<prenom>` |
| « My IP » affiche une adresse inattendue | VPN actif, ou proxy de l'école | Désactiver le VPN, ou saisir l'adresse donnée par `checkip.amazonaws.com` |
| Deux étudiants ne voient pas le même `pare-feu-web` | Chacun a le sien, c'est normal | Rappeler la convention du prénom dans les noms |

## Module 3 : Calcul, Amazon EC2

### Avant le module

Vérifiez depuis une salle de TP que le réseau de l'établissement laisse sortir les connexions SSH (port 22) vers Internet. Si ce n'est pas le cas, prévoyez une solution de repli : le partage de connexion des téléphones, ou l'accès par Session Manager, qui passe par HTTPS mais demande d'associer à l'instance un rôle muni de la stratégie `AmazonSSMManagedInstanceCore`.

Les droits des étudiants doivent maintenant couvrir `ec2:RunInstances` (idéalement limité à `t3.micro` par une condition `ec2:InstanceType` et à la région `eu-west-3`), `ec2:CreateKeyPair`, `ec2:StartInstances`, `ec2:StopInstances`, `ec2:TerminateInstances` et `ec2:CreateTags`. Une condition sur le tag `Proprietaire` évite qu'un étudiant arrête l'instance d'un autre par erreur.

### Au tableau

Le cycle de vie (schéma 3.5) mérite d'être redessiné en posant pour chaque état la question « qu'est-ce que je paie ici ? ». Les étudiants retiennent mieux le tableau quand ils l'ont rempli eux-mêmes.

Pour l'authentification SSH, un dessin à trois colonnes (vous, EC2, l'instance) suffit. Insistez sur le fait qu'AWS ne garde pas la clé privée : c'est ce qui rend la perte du fichier `.pem` sans remède simple.

### Questions qui font réagir

- « Vous arrêtez une instance pour le week-end. Que payez-vous ? » Le disque, et une éventuelle Elastic IP.
- « Pourquoi l'adresse publique n'apparaît-elle pas dans `ip address` ? » La traduction d'adresse est faite par la passerelle Internet du VPC, pas par l'instance.
- « Une faille SSRF sur une instance en IMDSv1, avec un rôle `AdministratorAccess` : que risque le compte ? » Tout.

### Corrigé du TP 3

1. L'instance ne connaît que son adresse privée. La passerelle Internet associe l'adresse publique à l'adresse privée et traduit les paquets dans les deux sens.
2. Conservés : le disque et son contenu (donc Nginx installé et la page générée), l'adresse privée, l'identifiant de l'instance. Changée : l'adresse publique, rendue à AWS à l'arrêt. La page affiche l'ancienne adresse parce qu'elle a été générée une fois pour toutes.
3. Impossible de se connecter en SSH : AWS n'a pas conservé la clé privée. Il faudrait relancer une instance avec une nouvelle paire (ou, pour une instance déjà configurée, passer par Session Manager ou détacher le volume pour modifier `authorized_keys` depuis une autre instance).
4. Avantage : l'instance se reconstruit à l'identique, sans intervention, autant de fois qu'on veut. Inconvénient : une erreur dans le script ne se voit qu'après le démarrage, et il faut aller lire `/var/log/cloud-init-output.log` pour la comprendre.

### Pannes fréquentes

| Symptôme | Cause | Remède |
|---|---|---|
| `Connection timed out` en SSH | Adresse de l'étudiant différente de la règle, ou port 22 bloqué par le réseau de l'établissement | Mettre à jour la règle ; tester depuis un partage de connexion |
| `Permission denied (publickey)` | Mauvaise clé, utilisateur `root` au lieu de `ec2-user`, ou instance lancée sans paire de clés | Vérifier la paire dans l'onglet *Details* de l'instance |
| L'assistant refuse le lancement (`UnauthorizedOperation`) | Type d'instance ou région non autorisés par la stratégie des étudiants, ou tag obligatoire manquant | Lire le message décodé : `aws sts decode-authorization-message --encoded-message <message>` |
| La page de `web2` n'apparaît pas | Le script de user data a échoué, ou n'est pas encore terminé | `sudo cat /var/log/cloud-init-output.log` sur l'instance |
| `http://IP` ne répond pas mais `curl localhost` fonctionne | Règle HTTP absente du Security Group, ou mauvais Security Group choisi au lancement | Onglet *Security* de l'instance |
| Le navigateur force `https://` | Mode « HTTPS uniquement » du navigateur | Taper explicitement `http://`, ou tester avec `curl` |

## Module 4 : Stockage, bases de données et messages

### Les droits que demande le TP

Ils sont couverts par `aws-cours-etudiant`. Le piège d'escalade du module 2 se retrouve ici sous une autre forme : un étudiant qui peut créer un rôle, lui attacher n'importe quelle stratégie et le passer à une instance obtiendrait, via cette instance, des droits qu'il n'a pas lui-même. La création du rôle exige donc la limite `aws-cours-limite-role`, et `iam:PassRole` n'est accordé que sur `role-galerie-<prenom>`. Seule faiblesse assumée : cette limite vaut pour tous les buckets `galerie-*`, si bien qu'un étudiant qui le voudrait vraiment pourrait, depuis son instance, lire le bucket d'un voisin en écrivant sa stratégie en conséquence.

### Au tableau

Le schéma 4.3 (qui peut lire un objet) gagne à être dessiné en direct à partir d'une question : « le bucket est privé, comment un visiteur télécharge-t-il sa photo ? ». Les étudiants proposent presque toujours de rendre le bucket public ; c'est le moment de raconter l'affaire Verizon, puis d'introduire l'URL présignée.

Pour le délai de visibilité, trois lignes horizontales (file, A, B) et une frise suffisent. Faites prédire à la salle ce qui arrive au message quand A plante, avant de montrer la réponse.

### Questions qui font réagir

- « S3 garantit onze neuf de durabilité. Pourquoi active-t-on quand même le versionnage ? » Parce que la durabilité protège contre le matériel, pas contre un `aws s3 rm` malheureux.
- « Pourquoi ne pas stocker les photos directement dans DynamoDB ? » Un élément DynamoDB est limité à 400 Ko et coûte bien plus cher au gigaoctet ; on y met la clé S3 de la photo, pas la photo.
- « Un message SQS peut-il être traité deux fois ? » Oui, avec une file standard. D'où l'exigence d'idempotence pour les consommateurs.

### Corrigé du TP 4

1. L'**Object URL** est une requête anonyme, non signée : le bucket étant privé, elle est refusée. Le bouton **Open** fabrique une URL présignée avec l'identité de l'utilisateur connecté à la console.
2. Non. Une URL présignée ne peut pas survivre aux identifiants qui l'ont signée. Celle-ci est signée avec les identifiants temporaires du rôle, qui expirent au bout de quelques heures ; au-delà, l'URL devient invalide quelle que soit la durée demandée. (Avec des identifiants permanents, la durée maximale est de sept jours.)
3. `aws s3 ls` sans argument appelle `ListBuckets`, qui demande `s3:ListAllMyBuckets` sur toutes les ressources. La stratégie n'accorde que `s3:ListBucket` sur un bucket précis.
4. Le délai de visibilité expire et le message redevient visible : il sera traité une seconde fois. Le consommateur doit donc être idempotent, c'est-à-dire produire le même résultat s'il traite deux fois le même message.

### Pannes fréquentes

| Symptôme | Cause | Remède |
|---|---|---|
| `Bucket name already exists` | Nom pris par quelqu'un d'autre, n'importe où dans le monde | Changer de suffixe |
| Le rôle n'apparaît pas dans **Modify IAM role** | Rôle créé sans profil d'instance (par la CLI, ou avec un autre cas d'usage que EC2) | Recréer le rôle dans la console avec le cas d'usage *EC2*, qui crée le profil d'instance |
| `Unable to locate credentials` persiste après l'association | Délai de propagation, ou association échouée faute de `iam:PassRole` | Attendre une minute ; vérifier l'onglet *Security* de l'instance |
| `aws s3 cp` vers le bucket renvoie `AccessDenied` alors que `ls` fonctionne | `/*` oublié dans la ressource de la déclaration `LireEtEcrire` | Corriger l'ARN : les objets sont `arn:aws:s3:::<bucket>/*` |
| La console refuse d'enregistrer la stratégie modifiée | Virgule manquante entre deux déclarations | Relire le JSON ; l'éditeur signale la ligne fautive |
| `receive-message` ne renvoie rien alors qu'un message vient d'être envoyé | Message encore invisible après une réception précédente, ou interrogation courte sans attente | Utiliser `--wait-time-seconds`, attendre la fin du délai de visibilité |

## Module 5 : Projet final

### Avant le module

Déployez vous-même la galerie avec le script `deploy/user-data.sh` de l'archive : c'est la démonstration d'ouverture du module 1, et une référence si un étudiant bloque. L'application et le script ont été rejoués sur Amazon Linux 2023 (Python 3.12, Nginx 1.30), dans un conteneur avec systemd et un faux S3 ; les tests automatisés de l'application se lancent avec `pytest` dans `kits/galerie/tests`.

Le rôle `role-galerie-<prenom>` et le bucket doivent exister depuis le TP 4. Les étudiants qui les ont supprimés peuvent les recréer en dix minutes (TP 4, étapes 1 et 5).

### Grille d'évaluation proposée

| Critère | Vérification | Points |
|---|---|---|
| La galerie fonctionne en HTTP | dépôt d'une image puis affichage, depuis le poste de l'enseignant | 3 |
| Elle fonctionne en HTTPS | `https://IP`, certificat autosigné au nom de l'étudiant | 2 |
| SSH n'est ouvert qu'à l'étudiant | test du port 22 depuis CloudShell ou le poste de l'enseignant | 2 |
| L'application n'est pas exposée directement | port 8000 fermé ; `ss -ltn` montre `127.0.0.1:8000` | 2 |
| Le bucket est privé | Object URL en `AccessDenied`, lien présigné valide puis expiré | 3 |
| Aucune clé d'accès sur l'instance | pas de `~/.aws`, recherche de clés vide hors `venv/` | 3 |
| Le rôle est au moindre privilège | suppression refusée, stratégie limitée au bucket | 2 |
| Le service résiste aux pannes | redémarrage après `kill -9` et après `reboot` | 1 |
| Explication orale | deux questions tirées au hasard parmi celles des TP | 2 |
| | **Total** | **20** |

Le nettoyage se vérifie en fin de séance : instance résiliée, bucket supprimé. On peut en faire une condition de validation plutôt qu'un critère noté.

### Questions à poser pendant la vérification

- « Montrez-moi l'endroit du code où l'application s'authentifie auprès d'AWS. » Il n'y en a pas : c'est tout le propos.
- « Si je vous vole l'instance, à quoi ai-je accès ? » Aux identifiants temporaires du rôle, donc à la lecture et à l'écriture de ce seul bucket, pour quelques heures.
- « Pourquoi le téléchargement d'une photo ne consomme-t-il pas de bande passante sur votre instance ? » L'URL présignée envoie le navigateur directement chez S3.
- « Que se passe-t-il si vous arrêtez puis redémarrez l'instance ? » L'adresse publique change ; il faudrait une Elastic IP ou un nom de domaine.

### Pannes fréquentes

| Symptôme | Cause | Remède |
|---|---|---|
| `502 Bad Gateway` dans le navigateur | Nginx fonctionne mais Gunicorn ne répond pas | `systemctl status galerie`, puis `journalctl -u galerie -n 50` |
| Le service s'arrête aussitôt avec `GALERIE_BUCKET n'est pas définie` | `/etc/galerie.env` vide ou absent (variable `B` non définie dans la session SSH) | Redéfinir `B` et réécrire le fichier, puis `sudo systemctl restart galerie` |
| La page affiche « Aucun identifiant AWS disponible » | Instance lancée sans profil d'instance | Actions › Security › Modify IAM role, puis redémarrer le service |
| La page affiche « Accès refusé par S3 » | Nom de bucket différent dans `/etc/galerie.env` et dans la stratégie, ou `/*` oublié | Comparer les deux ; corriger la stratégie ou le fichier |
| `502` et, dans `/var/log/nginx/error.log`, `Permission denied` en se connectant à `127.0.0.1:8000` | SELinux en mode *enforcing* (il est *permissive* par défaut sur Amazon Linux 2023) | `sudo setsebool -P httpd_can_network_connect 1` |
| `nginx -t` signale `duplicate default server` | Une autre configuration de `conf.d` revendique déjà `default_server` | Ne garder qu'un fichier avec `default_server` par port |
| `pip install` échoue | L'instance n'a pas d'accès sortant (Security Group sortant modifié) | Rétablir la règle sortante par défaut |
| Le lien présigné renvoie `SignatureDoesNotMatch` | Région de `/etc/galerie.env` différente de celle du bucket | Mettre `GALERIE_REGION` à la région réelle du bucket |
