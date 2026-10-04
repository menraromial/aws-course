# Comptes étudiants du cours

| Fichier | Usage |
|---|---|
| `aws-cours-etudiant.json` | stratégie `aws-cours-etudiant` : attachée au groupe `etudiants`, et limite de permissions de chaque étudiant |
| `aws-cours-limite-stagiaire.json` | stratégie `aws-cours-limite-stagiaire` : limite posée par l'étudiant sur l'utilisateur du TP 2 |
| `aws-cours-limite-role.json` | stratégie `aws-cours-limite-role` : limite posée par l'étudiant sur le rôle du TP 4 |
| `creer-etudiants.sh` | crée les utilisateurs `student1` à `studentN` (à lancer dans CloudShell, après les trois stratégies) |
| `une-instance-par-etudiant/` | fonction Lambda et script de déploiement : une seule instance en marche par étudiant |

Le nom d'utilisateur (`student12`) remplace `<prenom>` dans les énoncés. La procédure complète, ce que les stratégies autorisent, le quota d'instances et les précautions de coût sont dans le guide de l'enseignant, section « Avant le premier module ».
