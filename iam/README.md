# Comptes étudiants du cours

Trois scripts, à lancer dans CloudShell avec un compte administrateur :

| Script | Rôle |
|---|---|
| `1-preparer-compte.sh` | stratégies, groupe `etudiants`, crédits CPU standard, fonction « une instance par étudiant » ; affiche le quota de vCPU |
| `2-creer-etudiants.sh N [premier]` | crée `student1` à `studentN`, identifiants dans `etudiants.csv` |
| `3-tout-supprimer.sh [--avec-ressources]` | supprime ce que les deux premiers et les étudiants ont créé (inventaire puis confirmation) |

| Fichier | Rôle |
|---|---|
| `aws-cours-etudiant.json` | stratégie `aws-cours-etudiant` : groupe `etudiants`, et limite de permissions de chaque étudiant |
| `aws-cours-limite-stagiaire.json` | stratégie `aws-cours-limite-stagiaire` : limite posée par l'étudiant sur l'utilisateur du TP 2 |
| `aws-cours-limite-role.json` | stratégie `aws-cours-limite-role` : limite posée par l'étudiant sur le rôle du TP 4 |
| `une-instance-par-etudiant/` | fonction Lambda (et ses tests) qui arrête la seconde instance en marche d'un étudiant |

Le nom d'utilisateur (`student12`) remplace `<prenom>` dans les énoncés. Le détail est dans le guide de l'enseignant, section « Avant le premier module ».
