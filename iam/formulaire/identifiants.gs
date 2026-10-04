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
