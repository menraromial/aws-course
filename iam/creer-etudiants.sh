#!/bin/bash
# Crée les comptes student1 ... studentN (N = 100 par défaut) :
# utilisateur IAM, mot de passe provisoire à changer à la première connexion,
# groupe « etudiants », limite de permissions aws-cours-etudiant.
# Les identifiants sont écrits dans etudiants.csv (à garder pour vous).
# À lancer dans CloudShell avec un compte administrateur, après avoir créé
# les trois stratégies aws-cours-*. Relançable : les comptes existants sont
# laissés tels quels.
set -euo pipefail

N=${1:-100}
GROUPE=etudiants
COMPTE=$(aws sts get-caller-identity --query Account --output text)
STRATEGIE=arn:aws:iam::$COMPTE:policy/aws-cours-etudiant
SORTIE=etudiants.csv

aws iam get-policy --policy-arn "$STRATEGIE" >/dev/null \
  || { echo "Créez d'abord la stratégie aws-cours-etudiant"; exit 1; }

if ! aws iam get-group --group-name $GROUPE >/dev/null 2>&1; then
  aws iam create-group --group-name $GROUPE >/dev/null
fi
aws iam attach-group-policy --group-name $GROUPE --policy-arn "$STRATEGIE"

[ -f $SORTIE ] || echo "utilisateur,mot_de_passe_provisoire" > $SORTIE
for i in $(seq 1 "$N"); do
  U=student$i
  if aws iam get-user --user-name "$U" >/dev/null 2>&1; then
    echo "$U existe déjà"
    continue
  fi
  MDP="Aws-$(openssl rand -hex 5)-$((RANDOM % 90 + 10))Z"
  aws iam create-user --user-name "$U" --permissions-boundary "$STRATEGIE" >/dev/null
  aws iam create-login-profile --user-name "$U" --password "$MDP" --password-reset-required >/dev/null
  aws iam add-user-to-group --user-name "$U" --group-name $GROUPE
  echo "$U,$MDP" >> $SORTIE
  echo "$U créé"
done

echo
echo "Adresse de connexion : https://$COMPTE.signin.aws.amazon.com/console"
echo "Identifiants : $(pwd)/$SORTIE (téléchargez-le : Actions › Download file)"
