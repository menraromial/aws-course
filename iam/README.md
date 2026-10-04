# Comptes étudiants du cours

| Fichier | Usage |
|---|---|
| `aws-cours-etudiant.json` | stratégie `aws-cours-etudiant` : attachée au groupe `etudiants`, et limite de permissions de chaque étudiant |
| `aws-cours-limite-stagiaire.json` | stratégie `aws-cours-limite-stagiaire` : limite posée par l'étudiant sur l'utilisateur du TP 2 |
| `aws-cours-limite-role.json` | stratégie `aws-cours-limite-role` : limite posée par l'étudiant sur le rôle du TP 4 |
| `formulaire/identifiants.gs` | script Apps Script de la feuille du formulaire d'inscription : noms d'utilisateur, mots de passe, envoi des identifiants |
| `creer-etudiants.sh` | crée les comptes à partir du CSV de cette feuille (ou `student1` à `studentN`), à lancer dans CloudShell après les trois stratégies |
| `une-instance-par-etudiant/` | fonction Lambda et script de déploiement : une seule instance en marche par étudiant |

Le nom d'utilisateur, tiré du prénom (`camille`, `camille2`), remplace `<prenom>` dans les énoncés. La procédure complète, ce que les stratégies autorisent, le quota d'instances et les précautions de coût sont dans le guide de l'enseignant, section « Avant le premier module ».
