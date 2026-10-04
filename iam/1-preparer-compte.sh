#!/bin/bash
# 1/3 Prépare le compte AWS pour le cours, une fois pour toutes :
#   - les trois stratégies aws-cours-* (créées, ou mises à jour si elles existent) ;
#   - le groupe « etudiants », qui porte la stratégie aws-cours-etudiant ;
#   - les crédits CPU des t3 en mode standard par défaut à Paris ;
#   - la fonction « une seule instance en marche par étudiant ».
# À lancer dans CloudShell avec un compte administrateur, depuis le dépôt :
#   aws-course/iam/1-preparer-compte.sh
# Relançable sans risque.
export AWS_PAGER=""
set -euo pipefail
cd "$(dirname "$0")"

REGION=eu-west-3
GROUPE=etudiants
COMPTE=$(aws sts get-caller-identity --query Account --output text)

strategie() {  # nom fichier
  local arn=arn:aws:iam::$COMPTE:policy/$1
  if aws iam get-policy --policy-arn "$arn" >/dev/null 2>&1; then
    # IAM garde au plus cinq versions : on retire la plus ancienne si besoin
    local anciennes
    anciennes=$(aws iam list-policy-versions --policy-arn "$arn" \
      --query 'Versions[?!IsDefaultVersion].VersionId' --output text | tr -s '\t ' '\n' | grep . || true)
    if [ "$(echo "$anciennes" | grep -c .)" -ge 4 ]; then
      aws iam delete-policy-version --policy-arn "$arn" \
        --version-id "$(echo "$anciennes" | sed 's/^v//' | sort -n | head -1 | sed 's/^/v/')"
    fi
    aws iam create-policy-version --policy-arn "$arn" --policy-document "file://$2" --set-as-default >/dev/null
    echo "   $1 : mise à jour"
  else
    aws iam create-policy --policy-name "$1" --policy-document "file://$2" \
      --description "Cours Introduction a AWS" >/dev/null
    echo "   $1 : créée"
  fi
}

echo "1/4 Stratégies"
strategie aws-cours-limite-stagiaire aws-cours-limite-stagiaire.json
strategie aws-cours-limite-role aws-cours-limite-role.json
strategie aws-cours-etudiant aws-cours-etudiant.json

echo "2/4 Groupe $GROUPE"
aws iam get-group --group-name $GROUPE >/dev/null 2>&1 || aws iam create-group --group-name $GROUPE >/dev/null
aws iam attach-group-policy --group-name $GROUPE --policy-arn "arn:aws:iam::$COMPTE:policy/aws-cours-etudiant"

echo "3/4 Crédits CPU des t3 en mode standard par défaut ($REGION)"
aws ec2 modify-default-credit-specification --region $REGION --instance-family t3 --cpu-credits standard >/dev/null

echo "4/4 Fonction « une seule instance en marche par étudiant »"
./une-instance-par-etudiant/deployer.sh | sed 's/^/   /'

QUOTA=$(aws service-quotas get-service-quota --region $REGION --service-code ec2 \
  --quota-code L-1216C47A --query 'Quota.Value' --output text 2>/dev/null || echo "?")
echo
echo "Compte prêt. Quota de vCPU à la demande à Paris : $QUOTA"
echo "Il en faut 2 par étudiant (une t3.micro chacun) : demandez une augmentation"
echo "dans Service Quotas › Amazon EC2 si ce nombre est trop bas."
echo "Étape suivante : ./2-creer-etudiants.sh <nombre>"
