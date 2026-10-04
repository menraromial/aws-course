#!/bin/bash
# 3/3 Supprime ce que le cours a créé dans le compte, à la fin du cours :
#   - la fonction « une instance par étudiant » (règle, fonction, rôle, journaux) ;
#   - les comptes studentN et le groupe « etudiants » ;
#   - les ressources IAM créées par les étudiants pendant les TP
#     (stagiaire-studentN, stagiaires-studentN, role-galerie-studentN,
#     stratégies lecture-ec2-studentN et galerie-s3-studentN) ;
#   - les trois stratégies aws-cours-*.
# Avec --avec-ressources, supprime aussi les ressources des étudiants à Paris :
# instances au tag Proprietaire=studentN, buckets galerie-studentN-*, files
# file-studentN, paires de clés cle-studentN, groupes pare-feu-web-studentN.
#
# Le script dresse d'abord l'inventaire, puis demande de taper SUPPRIMER.
# Il ne touche qu'aux noms qui suivent exactement ces modèles.
export AWS_PAGER=""
set -uo pipefail

REGION=eu-west-3
FONCTION=une-instance-par-etudiant
AVEC_RESSOURCES=0
[ "${1:-}" = "--avec-ressources" ] && AVEC_RESSOURCES=1

# Sortie texte d'une commande aws, un élément par ligne, sans « None »
liste() { aws "$@" --output text 2>/dev/null | tr '\t' '\n' | grep -v -e '^None$' -e '^$' || true; }

# ---------- inventaire ----------
UTILISATEURS=$(liste iam list-users --query 'Users[].UserName' | grep -E '^(student[0-9]+|stagiaire-student[0-9]+)$')
GROUPES=$(liste iam list-groups --query 'Groups[].GroupName' | grep -E '^(etudiants|stagiaires-student[0-9]+)$')
ROLES=$(liste iam list-roles --query 'Roles[].RoleName' | grep -E "^(role-galerie-student[0-9]+|$FONCTION)\$")
STRATEGIES=$(aws iam list-policies --scope Local --query 'Policies[].[PolicyName,Arn]' --output text 2>/dev/null \
  | awk '$1 ~ /^(aws-cours-(etudiant|limite-stagiaire|limite-role)|lecture-ec2-student[0-9]+|galerie-s3-student[0-9]+)$/ {print $2}')
FONCTION_PRESENTE=$(aws lambda get-function --region $REGION --function-name $FONCTION >/dev/null 2>&1 && echo oui || echo non)

INSTANCES=$(aws ec2 describe-instances --region $REGION \
  --filters Name=tag-key,Values=Proprietaire Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query "Reservations[].Instances[].[InstanceId,Tags[?Key=='Proprietaire']|[0].Value]" --output text 2>/dev/null \
  | awk 'tolower($2) ~ /^student[0-9]+$/ {print $1}')
BUCKETS=$(liste s3api list-buckets --query 'Buckets[].Name' | grep -E '^galerie-student[0-9]+-')
FILES=$(liste sqs list-queues --region $REGION --queue-name-prefix file-student --query 'QueueUrls[]' | grep -E '/file-student[0-9]+$')
CLES=$(liste ec2 describe-key-pairs --region $REGION --query 'KeyPairs[].KeyName' | grep -E '^cle-student[0-9]+$')
PARE_FEU=$(aws ec2 describe-security-groups --region $REGION --query 'SecurityGroups[].[GroupId,GroupName]' --output text 2>/dev/null \
  | awk '$2 ~ /^pare-feu-web-student[0-9]+$/ {print $1}')

compte() { echo "$1" | grep -c . ; }
echo "Inventaire :"
echo "  fonction $FONCTION : $FONCTION_PRESENTE"
echo "  utilisateurs IAM   : $(compte "$UTILISATEURS")"
echo "  groupes IAM        : $(compte "$GROUPES")"
echo "  rôles IAM          : $(compte "$ROLES")"
echo "  stratégies IAM     : $(compte "$STRATEGIES")"
echo "  instances EC2      : $(compte "$INSTANCES")"
echo "  buckets S3         : $(compte "$BUCKETS")"
echo "  files SQS          : $(compte "$FILES")"
echo "  paires de clés     : $(compte "$CLES")"
echo "  Security Groups    : $(compte "$PARE_FEU")"
if [ $AVEC_RESSOURCES -eq 0 ]; then
  echo
  echo "Les instances, buckets, files, clés et Security Groups ne seront PAS supprimés."
  echo "Relancez avec --avec-ressources pour les supprimer aussi."
fi
echo
read -r -p "Tapez SUPPRIMER pour confirmer : " REPONSE
[ "$REPONSE" = "SUPPRIMER" ] || { echo "Abandon, rien n'a été supprimé."; exit 1; }

# ---------- suppression ----------
echo "Fonction $FONCTION"
aws events remove-targets --region $REGION --rule $FONCTION --ids 1 >/dev/null 2>&1
aws events delete-rule --region $REGION --name $FONCTION 2>/dev/null
aws lambda delete-function --region $REGION --function-name $FONCTION 2>/dev/null
aws logs delete-log-group --region $REGION --log-group-name /aws/lambda/$FONCTION 2>/dev/null

if [ $AVEC_RESSOURCES -eq 1 ]; then
  if [ -n "$INSTANCES" ]; then
    echo "Résiliation de $(compte "$INSTANCES") instance(s)"
    # shellcheck disable=SC2086
    aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCES >/dev/null
    # shellcheck disable=SC2086
    aws ec2 wait instance-terminated --region $REGION --instance-ids $INSTANCES
  fi
  for b in $BUCKETS; do aws s3 rb "s3://$b" --force >/dev/null && echo "   bucket $b"; done
  for q in $FILES; do aws sqs delete-queue --region $REGION --queue-url "$q" >/dev/null && echo "   file ${q##*/}"; done
  for k in $CLES; do aws ec2 delete-key-pair --region $REGION --key-name "$k" >/dev/null && echo "   clé $k"; done
  for g in $PARE_FEU; do aws ec2 delete-security-group --region $REGION --group-id "$g" >/dev/null && echo "   Security Group $g"; done
fi

supprimer_utilisateur() {
  local u=$1 x
  aws iam delete-login-profile --user-name "$u" 2>/dev/null
  for x in $(liste iam list-groups-for-user --user-name "$u" --query 'Groups[].GroupName'); do
    aws iam remove-user-from-group --user-name "$u" --group-name "$x"; done
  for x in $(liste iam list-attached-user-policies --user-name "$u" --query 'AttachedPolicies[].PolicyArn'); do
    aws iam detach-user-policy --user-name "$u" --policy-arn "$x"; done
  for x in $(liste iam list-user-policies --user-name "$u" --query 'PolicyNames[]'); do
    aws iam delete-user-policy --user-name "$u" --policy-name "$x"; done
  for x in $(liste iam list-access-keys --user-name "$u" --query 'AccessKeyMetadata[].AccessKeyId'); do
    aws iam delete-access-key --user-name "$u" --access-key-id "$x"; done
  for x in $(liste iam list-signing-certificates --user-name "$u" --query 'Certificates[].CertificateId'); do
    aws iam delete-signing-certificate --user-name "$u" --certificate-id "$x"; done
  for x in $(liste iam list-ssh-public-keys --user-name "$u" --query 'SSHPublicKeys[].SSHPublicKeyId'); do
    aws iam delete-ssh-public-key --user-name "$u" --ssh-public-key-id "$x"; done
  for x in $(liste iam list-service-specific-credentials --user-name "$u" --query 'ServiceSpecificCredentials[].ServiceSpecificCredentialId'); do
    aws iam delete-service-specific-credential --user-name "$u" --service-specific-credential-id "$x"; done
  for x in $(liste iam list-mfa-devices --user-name "$u" --query 'MFADevices[].SerialNumber'); do
    aws iam deactivate-mfa-device --user-name "$u" --serial-number "$x"
    aws iam delete-virtual-mfa-device --serial-number "$x" 2>/dev/null; done
  aws iam delete-user-permissions-boundary --user-name "$u" 2>/dev/null
  aws iam delete-user --user-name "$u" && echo "   utilisateur $u"
}

supprimer_groupe() {
  local g=$1 x
  for x in $(liste iam get-group --group-name "$g" --query 'Users[].UserName'); do
    aws iam remove-user-from-group --user-name "$x" --group-name "$g"; done
  for x in $(liste iam list-attached-group-policies --group-name "$g" --query 'AttachedPolicies[].PolicyArn'); do
    aws iam detach-group-policy --group-name "$g" --policy-arn "$x"; done
  for x in $(liste iam list-group-policies --group-name "$g" --query 'PolicyNames[]'); do
    aws iam delete-group-policy --group-name "$g" --policy-name "$x"; done
  aws iam delete-group --group-name "$g" && echo "   groupe $g"
}

supprimer_role() {
  local r=$1 x
  for x in $(liste iam list-instance-profiles-for-role --role-name "$r" --query 'InstanceProfiles[].InstanceProfileName'); do
    aws iam remove-role-from-instance-profile --instance-profile-name "$x" --role-name "$r"
    [[ $x =~ ^role-galerie-student[0-9]+$ ]] && aws iam delete-instance-profile --instance-profile-name "$x"; done
  for x in $(liste iam list-attached-role-policies --role-name "$r" --query 'AttachedPolicies[].PolicyArn'); do
    aws iam detach-role-policy --role-name "$r" --policy-arn "$x"; done
  for x in $(liste iam list-role-policies --role-name "$r" --query 'PolicyNames[]'); do
    aws iam delete-role-policy --role-name "$r" --policy-name "$x"; done
  aws iam delete-role-permissions-boundary --role-name "$r" 2>/dev/null
  aws iam delete-role --role-name "$r" && echo "   rôle $r"
}

supprimer_strategie() {
  local arn=$1 x
  # Une stratégie encore utilisée comme limite par une entité étrangère au cours : on n'y touche pas
  local limites
  limites=$(aws iam list-entities-for-policy --policy-arn "$arn" --policy-usage-filter PermissionsBoundary \
    --query '[PolicyUsers[].UserName, PolicyRoles[].RoleName][]' --output text 2>/dev/null | tr '\t' '\n' | grep -v -e '^None$' -e '^$')
  if [ -n "$limites" ]; then
    echo "   !! ${arn##*/} conservée : limite de permissions de $(echo "$limites" | tr '\n' ' ')"
    return
  fi
  for x in $(liste iam list-entities-for-policy --policy-arn "$arn" --query 'PolicyGroups[].GroupName'); do
    aws iam detach-group-policy --group-name "$x" --policy-arn "$arn"; done
  for x in $(liste iam list-entities-for-policy --policy-arn "$arn" --query 'PolicyUsers[].UserName'); do
    aws iam detach-user-policy --user-name "$x" --policy-arn "$arn"; done
  for x in $(liste iam list-entities-for-policy --policy-arn "$arn" --query 'PolicyRoles[].RoleName'); do
    aws iam detach-role-policy --role-name "$x" --policy-arn "$arn"; done
  for x in $(liste iam list-policy-versions --policy-arn "$arn" --query 'Versions[?!IsDefaultVersion].VersionId'); do
    aws iam delete-policy-version --policy-arn "$arn" --version-id "$x"; done
  aws iam delete-policy --policy-arn "$arn" && echo "   stratégie ${arn##*/}"
}

echo "Utilisateurs"; for u in $UTILISATEURS; do supprimer_utilisateur "$u"; done
echo "Groupes";      for g in $GROUPES; do supprimer_groupe "$g"; done
echo "Rôles";        for r in $ROLES; do supprimer_role "$r"; done
echo "Stratégies";   for s in $STRATEGIES; do supprimer_strategie "$s"; done

echo
echo "Terminé. Le réglage des crédits CPU par défaut (standard) est conservé ; pour revenir"
echo "au réglage d'origine : aws ec2 modify-default-credit-specification --region $REGION --instance-family t3 --cpu-credits unlimited"
