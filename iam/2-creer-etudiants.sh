#!/bin/bash
# 2/3 Crée les comptes student1 ... studentN : utilisateur IAM, mot de passe
# provisoire à changer à la première connexion, groupe « etudiants »,
# limite de permissions aws-cours-etudiant.
#   ./2-creer-etudiants.sh 100        crée student1 à student100
#   ./2-creer-etudiants.sh 120 101    ajoute student101 à student120
# Les identifiants sont ajoutés à etudiants.csv, dans le dossier courant.
# Les comptes déjà présents sont laissés tels quels.
export AWS_PAGER=""
set -euo pipefail

FIN=${1:?"usage : $0 dernier_numero [premier_numero]"}
DEBUT=${2:-1}
GROUPE=etudiants
SORTIE=etudiants.csv
COMPTE=$(aws sts get-caller-identity --query Account --output text)
STRATEGIE=arn:aws:iam::$COMPTE:policy/aws-cours-etudiant
CONNEXION=https://$COMPTE.signin.aws.amazon.com/console

if ! aws iam get-policy --policy-arn "$STRATEGIE" >/dev/null 2>&1 \
   || ! aws iam get-group --group-name $GROUPE >/dev/null 2>&1; then
  echo "Lancez d'abord 1-preparer-compte.sh"; exit 1
fi

[ -f $SORTIE ] || echo "utilisateur,mot_de_passe,adresse_de_connexion" > $SORTIE
CREES=0
for i in $(seq "$DEBUT" "$FIN"); do
  U=student$i
  if aws iam get-user --user-name "$U" >/dev/null 2>&1; then
    echo "$U existe déjà"
    continue
  fi
  MDP="Cours-$(shuf -i 1000-9999 -n 1)-$(openssl rand -hex 2)"
  aws iam create-user --user-name "$U" --permissions-boundary "$STRATEGIE" >/dev/null
  aws iam create-login-profile --user-name "$U" --password "$MDP" --password-reset-required >/dev/null
  aws iam add-user-to-group --user-name "$U" --group-name $GROUPE
  echo "$U,$MDP,$CONNEXION" >> $SORTIE
  echo "$U créé"
  CREES=$((CREES + 1))
done

echo
echo "$CREES compte(s) créé(s). Adresse de connexion : $CONNEXION"
echo "Identifiants : $(pwd)/$SORTIE"
echo "Téléchargez-le (Actions › Download file), puis effacez-le de CloudShell : rm $(pwd)/$SORTIE"
