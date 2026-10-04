# Stratégies IAM des comptes étudiants

| Fichier | Nom à donner à la stratégie | Usage |
|---|---|---|
| `aws-cours-etudiant.json` | `aws-cours-etudiant` | attachée au groupe `etudiants`, et limite de permissions de chaque utilisateur étudiant |
| `aws-cours-limite-stagiaire.json` | `aws-cours-limite-stagiaire` | limite posée par l'étudiant sur l'utilisateur du TP 2 |
| `aws-cours-limite-role.json` | `aws-cours-limite-role` | limite posée par l'étudiant sur le rôle du TP 4 |

Les utilisateurs étudiants sont des utilisateurs IAM dont le nom est le prénom, en minuscules et sans accent. La procédure complète, ce que les stratégies autorisent et les précautions de coût sont dans le guide de l'enseignant, section « Avant le premier module ».
